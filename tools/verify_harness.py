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
import collections, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time

# A FIXTURE COMMIT IS NOT A PERSON'S COMMIT. Since 2026-09-07 the commit
# identity hook installs a backstop at core.hooksPath -- global, because that
# is the only hook location reaching a repository attached mid-session, which
# is where three wrong-author incidents came from. It therefore also reaches
# the throwaway repos this harness builds by the dozen, and refused them for
# a +0000 offset, taking the whole run down with a RuntimeError on the first
# `git commit -qm base`.
#
# Set here, once, for every subprocess: the override the backstop itself
# documents. It is the right answer rather than a workaround -- nothing in a
# temporary directory is anybody's authorship. The two checks that exercise
# the backstop's own refusals pop this back out of their fixture env, so the
# coverage is not weakened by it.
os.environ.setdefault('PRECEDENT_ALLOW_ANY_AUTHOR', '1')

# Same problem, opposite direction: the harness must OWN the identity its
# fixtures assert on, instead of inheriting whatever the session exports.
#
# check_identity_reaches_a_repo_that_did_not_exist_yet builds a fixture in a
# temporary HOME, sets a global identity inside it, and asserts that commits
# made there used it. But GIT_AUTHOR_* outrank `git config --global user.*`,
# so a session that exports them -- the individual practice set's
# .claude/settings.json does -- authored every fixture commit as the real
# person, and 4 of that check's 11 stated cases failed, none of them real.
# Three failed in the confusing direction: a bot identity the fixture plants
# in LOCAL config was never the author any more, so the refusal the case
# waits for correctly did not fire, and a working backstop read as broken.
#
# Measured 2026-09-07, same tree, no code change: `1 failed` with the two
# variables exported, `0 failed` under `env -u`. Dropped here, once, rather
# than in the single fixture that happened to notice -- a fixture written
# later would inherit the same invisible dependency and the same hour of
# misdiagnosis. GIT_AUTHOR_DATE goes with them because the same check
# asserts on the author-date offset, which that variable equally overrides.
#
# The GIT_COMMITTER_* trio is deliberately NOT dropped: nothing in this
# harness or in commit-identity.sh reads the committer (the hook resolves
# `git var GIT_AUTHOR_IDENT`), so removing them would be a guess at a
# problem nobody has had.
for _var in ('GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL', 'GIT_AUTHOR_DATE'):
    os.environ.pop(_var, None)

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
    # Added 2026-09-06 by the broken-relative-link sweep (see
    # CHANGES_TO_TELL_ALEX.md, "Relative-link sweep in practices/"): a
    # practice file lives one directory down, so a link written
    # `](tools/doc_lint.py)` resolved to `practices/tools/doc_lint.py` and
    # 404'd on GitHub for every reader of the practice file itself. 67
    # such links across 28 files were repointed to `](../...)`. Only the
    # link TARGET changed -- no prose, and the word-multiset checks above
    # still pass untouched -- but the sentence-identity check compares the
    # rendered target too, so the eight practices whose changed links sit
    # inside a checked section are declared here rather than exempted
    # silently.
    'doc-references-are-links', 'github-setup-disclosed',
    'lead-with-what-it-is', 'orientation-map', 'pr-template-honest-gates',
    'quick-index', 'reply-links-files', 'section-order-by-frequency',
    # Added 2026-09-07 by the Story backfill (see CHANGES_TO_TELL_ALEX.md,
    # "Story backfill across the catalogue"): 30 practices carried an empty
    # `## Story`, and one -- reply-links-files -- an empty `## Why` as well.
    # A Story is by definition text BestPractice's frozen original does not
    # contain, so writing one fails the word-multiset and sentence checks on
    # every word of it. The exemption covers a real, disclosed edit rather
    # than a conversion bug, exactly as the citation sweeps above do. Most of
    # the 30 were already listed here for earlier sweeps; these three were
    # not.
    'cite-the-incident', 'no-version-suffix',
    # Scrubbed the same day: a private repo's name replaced with a general
    # description, after the leak gate's private vocabulary half was run
    # against this tree for the first time.
    'migration-scrubs-vocabulary',
    # Added 2026-09-07 by the Why backfill (see CHANGES_TO_TELL_ALEX.md,
    # "Why backfill"). Distinct from the Story backfill the same day: these
    # nine already HAD their incident recorded in a real ## Story. What they
    # lacked was the reasoning, because their source practice never had a
    # paragraph opening with a **Why.** label for the converter's
    # carry-forward walk to route there. The new text is derived from each
    # practice's own Rule and Story, so it is invented relative to
    # PRACTICES.md and needs this exemption. Seven of the nine were already
    # listed above for earlier sweeps.
    'docs-are-current-state', 'label-describes-content',
    # Added 2026-09-08 when Alex's `main` check-in was carried onto this
    # branch (see CHANGES_TO_TELL_ALEX.md, "Alex's 2026-09-08 main
    # check-in"). Upstream appended a ratings corollary to the ledger
    # practice's own section in PRACTICES.md; here PRACTICES.md is frozen,
    # so the corollary was split across this file's Rule/Why/Story instead
    # and is invented relative to the frozen original. verify-decomposition
    # took the same check-in's dual-direction clause and is already listed
    # above for an earlier sweep.
    'name-both-sides-of-ledger',
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
            # it is not part of the migrated set this check is about.
            # split_practices.py drops a `null` field rather than storing
            # the string, so this guard is live -- it was dead until
            # 2026-09-06 and `int('null')` below crashed instead.
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
        # _json_str, not the raw field: a title containing ': ' has to be
        # quoted for the frontmatter to be valid YAML at all (see
        # split_practices._yaml_scalar), and the quotes are encoding, not
        # content. Comparing raw would report ten false title rewrites.
        if bv._json_str(fm.get('title', '')).strip() != orig['title'].strip():
            ok = False
            print(f"  {f.name}: title differs from PRACTICES.md\n"
                  f"      file:   {bv._json_str(fm.get('title',''))!r}\n"
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


GITHUB_REPO_URL_RE = re.compile(
    r'https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)')
UPSTREAM_OWNER_REPO = 'alex137/BestPractice'


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


def check_practices_link_only_reachable_repos(files):
    """No practice file links a GitHub repository other than this one.

    practices/ is what ships. Every consuming repo materializes these files
    verbatim, and the people who read them are strangers to this project's
    other repositories -- so a link to one of them is a 404 for the reader
    and, worse, an advertisement of a private repository's existence and
    path from a public document.

    Found 2026-09-06: practices/very-deep-check.md linked
    `themorgan/precedent-individual` and `themorgan/precedent-team-maintainers`
    -- both private -- as illustrative examples, in a universal practice
    every adopter gets. Naming the practice instead of linking the page
    says the same thing and costs the reader nothing.

    Deliberately narrow to `practices/`. spec/ and decisions/ are this
    project's own internal record, read by people who do have access, and
    a link there is correct."""
    ok = True
    for _stem, (_fm, _sections, f) in sorted(files.items()):
        text = f.read_text(encoding='utf-8', errors='ignore')
        for m in GITHUB_REPO_URL_RE.finditer(text):
            owner_repo = f'{m.group(1)}/{m.group(2)}'
            if owner_repo.lower() == UPSTREAM_OWNER_REPO.lower():
                continue
            ok = False
            print(f"  {f.name}: links {owner_repo}, a repository the reader "
                  f"of a shipped practice has no reason to be able to open "
                  f"-- name it instead of linking it")
    check('practice files link no repository but this one (they ship verbatim '
          'into every consuming repo, and are read by strangers to this '
          "project's other repositories)", ok)


def _seed_consumer_engine(dest_tools, extra=(), only=None):
    """Copy the engine a CONSUMING repo actually receives into dest_tools.

    THE ONE PLACE THAT LIST LIVES, and why it had to become one.
    Fixtures here hand-listed the engine files they needed --
    `('precedent_resolve.py', 'split_practices.py', 'build_views.py', ...)`
    -- which is correct until an engine module is added, and then silently
    wrong: the fixture keeps copying a precedent_resolve.py that imports a
    companion the fixture has never heard of. On 2026-09-10 a new module
    (precedent_identity.py, carved out of the resolver) broke TWO fixtures
    that way in a single change, and one of them carried a comment warning
    about precisely this failure -- the warning did not help, because the
    list it guarded was still a hand-list.

    Reading precedent_vendor_engine's own CONSUMER_ENGINE_FILES is what
    makes a fixture a consumer rather than a curated subset of one
    (practice: fixture-owns-its-state -- the state a fixture owns includes
    which files a real consumer gets).

    `extra` adds non-engine companions a fixture needs (data files, the
    leak gate). `only` narrows to a subset by name for a fixture that is
    deliberately testing a partial engine -- pass it explicitly, so a
    narrow copy is a stated choice rather than an accident of drift."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as _pve
    names = list(_pve.CONSUMER_ENGINE_FILES) + list(extra)
    if only is not None:
        names = [n for n in names if n in set(only) | set(extra)]
    dest_tools = pathlib.Path(dest_tools)
    dest_tools.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in names:
        src = ROOT / 'tools' / name
        if src.is_file():
            shutil.copy2(src, dest_tools / name)
            copied.append(name)
    return copied


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
    the structural layer is a real pass or fail either way.

    --structural-only, by name, for the same reason continuous integration
    passes it: this harness runs with no private blocklist, and since
    2026-09-08 the gate REFUSES rather than reporting PARTIAL when
    precedent.json declares a private source. That refusal is correct for a
    person about to push and wrong for a bare caller, so a bare caller says
    which half it is asking for. Without the flag this check went red on a
    clean tree -- the fix belonged in the caller, not in weakening the gate.
    """
    result = subprocess.run([sys.executable, str(ROOT / 'tools' / 'leak_gate.py'),
                             '--structural-only'],
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

        # 10. the single ALLOWED_PATHS exemption, from both sides. The
        #     vendored-private-set rule matches a path SEGMENT beginning
        #     'precedent-individual', which is also the start of the canonical
        #     SessionStart hook's FILENAME -- so installing the hook this
        #     project tells every adopter to install failed the gate
        #     (2026-09-06, the moment BestPractice installed its own). The
        #     exemption is one exact path, so the directory case it was
        #     written for must still fail.
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

        def gate_output(text):
            blocklist.write_text(text, encoding='utf-8')
            env = dict(os.environ)
            env['PRECEDENT_LEAK_BLOCKLIST'] = str(blocklist)
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'leak_gate.py')],
                capture_output=True, text=True, cwd=str(repo), env=env)
            return r.returncode, r.stdout + r.stderr

        rc, out = gate_output(declared)
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
            declared + '# visibility-audit: allow fixtureacct/Kestrelwood -- fixture\n')
        cases.append(('an `allow` line for the repo silences the note',
                      'Kestrelwood' not in out_allowed))

        # And with no owner declared at all the survey must not run: it would
        # otherwise print private repository names into a CI log, which for a
        # public repo is a build log anyone can read.
        _rc, out_inert = gate_output('\\bquillon[\\w-]*\n')
        cases.append(('no private-owner declaration means no survey at all, so '
                      'no name reaches a public build log',
                      'Kestrelwood' not in out_inert
                      and 'allowlist is INERT' in out_inert))

        ok = all(passed for _, passed in cases)
        for name, passed in cases:
            if not passed:
                print(f"  stem-coverage note did NOT behave as stated: {name}")
        check(f'the leak gate notes a private clone with no blocklist stem '
              f'({len(cases)} stated cases, each asserting the printed text)', ok)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
        cases.append(('two team-level sources defining one slug is a loud '
                      'failure, not a silent last-one-wins',
                      r_two.returncode == 1 and 'shared' in out_two
                      and 'same level' in out_two))

        # ...and two team sources that DON'T collide still resolve fine --
        # the rule must not have turned "more than one team source" into an
        # error by itself.
        (t_a / 'practices' / 'shared.md').unlink()
        practice(t_a, 'a-only', level_note='Only in A.')
        r_ok = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_resolve.py'),
             '--repo', str(two_teams), '--json'], capture_output=True, text=True)
        slugs_ok = ({p['slug'] for p in json.loads(r_ok.stdout).get('practices', [])}
                    if r_ok.returncode == 0 else set())
        cases.append(('two non-colliding team sources still resolve together',
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
          f'an anchor and templates/ are not)', ok)


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


def check_build_views_summary_matches_what_it_wrote():
    """build_views.py's summary line reports the block it actually wrote.

    THE INCIDENT (2026-09-07). The summary re-derived its figures with a
    second build_loader_block() call, from the single-source catalogue,
    while the block itself had been built from the multi-source resolve. A
    run printed "resident 7/69 practices" and wrote a file whose own header
    said "7 of 72" -- the artifact was right and the line a session reads to
    confirm the run was wrong, which is the worse half to have wrong. It
    surfaced only because a merge happened to add repo-local practices and
    somebody read both numbers in the same minute.

    Runs against a COPY: this is a real write run, not --check, because the
    disagreement lived between what was printed and what was written and
    only a write produces both.
    """
    import tempfile, shutil
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-summary-'))
    try:
        repo = tmp / 'repo'
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '*.pyc', 'prompts'))
        r = subprocess.run(
            [sys.executable, str(repo / 'tools' / 'build_views.py')],
            capture_output=True, text=True, cwd=str(repo))
        if r.returncode != 0:
            check('build_views summary reports the block it wrote', False,
                  f'build_views exited {r.returncode}: '
                  f'{(r.stdout + r.stderr).strip()[:300]}')
            return
        m_out = re.search(r'resident (\d+)/(\d+) practices, ~(\d+) tokens',
                          r.stdout)
        header = (repo / 'AGENTS.md').read_text(encoding='utf-8')
        m_file = re.search(
            r'## Resident block \(~(\d+) of \d+ token budget, '
            r'(\d+) of (\d+) practices', header)
        if not m_out or not m_file:
            check('build_views summary reports the block it wrote', False,
                  f'could not parse both figures (stdout matched: '
                  f'{bool(m_out)}, AGENTS.md matched: {bool(m_file)})')
            return
        printed = (int(m_out.group(1)), int(m_out.group(2)), int(m_out.group(3)))
        written = (int(m_file.group(2)), int(m_file.group(3)), int(m_file.group(1)))
        check('build_views summary reports the block it wrote '
              '(resident, total and token count all match AGENTS.md)',
              printed == written,
              f'printed {printed}, wrote {written}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_legacy_status_migration():
    """A practice written under the OLD status vocabulary can be classified,
    and cannot be classified by guessing.

    THE GAP THIS CLOSES. `status: retired` used to mean two different things
    -- a redundant copy of a rule still fully in force elsewhere, and a rule
    withdrawn everywhere -- and a legacy record does not say which. The
    records are in the private practice sets; BestPractice's own catalogue
    never had one, which is exactly why nothing here would otherwise
    exercise this. So the fixtures below reproduce both real cases:

      bestpractice-sync   the surviving copy has the SAME slug, in another
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

        team_sync = make('team', 'bestpractice-sync', 'retired',
                         'Moved to the individual set.', legacy=True)
        team_caps = make('team', 'header-caps', 'retired',
                         'The universal catalogue carries this now.', legacy=True)
        make('individual', 'bestpractice-sync')
        make('universal', 'headline-capitalization')
        against = [str(tmp / 'individual'), str(tmp / 'universal')]

        recs = pms.legacy_records(tmp / 'team' / 'practices')
        cases.append(('a legacy record (non-active, no in_force_at) is found',
                      {fm.get('slug') for _f, fm, _s in recs}
                      == {'bestpractice-sync', 'header-caps'}))

        live = pms.active_slugs(against)
        cases.append(('only ACTIVE slugs count as a surviving copy',
                      'bestpractice-sync' in live and 'headline-capitalization' in live))

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
                      and 'in_force_at: bestpractice-sync' in sync_after))

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
    env_clean = {k: v for k, v in os.environ.items() if k != 'PRECEDENT_LEAK_BLOCKLIST'}

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

    pats, source, private_configured = lg.load_blocklist()
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

    # It genuinely blocks a push, not merely matches in a unit test.
    probe = ROOT / 'ZZ_leakprobe_fixture.md'
    try:
        probe.write_text(f'# Fixture\n\nThis {word}ing line must be caught.\n',
                         encoding='utf-8')
        r = gate()
        cases.append(('a planted instance FAILS the whole gate, not just a regex',
                      r.returncode == 1 and 'LEAK' in r.stdout))
    finally:
        probe.unlink(missing_ok=True)

    # A private list is merged with the default, never replaces it.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        priv = pathlib.Path(td) / 'private.txt'
        priv.write_text('acme-corp-secret-codename\n', encoding='utf-8')
        os.environ['PRECEDENT_LEAK_BLOCKLIST'] = str(priv)
        try:
            merged, src, configured = lg.load_blocklist()
        finally:
            os.environ.pop('PRECEDENT_LEAK_BLOCKLIST', None)
        cases.append(('a private list is MERGED with the default, never replaces '
                      'it -- configuring one must not silently drop the other',
                      configured and len(merged) == len(pats) + 1
                      and any(p.search('acme-corp-secret-codename') for p in merged)
                      and any(p.search(f'{word}ing') for p in merged)))

    # A private list inside the repo is still refused -- the guard that makes
    # the whole split safe.
    inside = ROOT / 'ZZ_inside_blocklist.txt'
    try:
        inside.write_text('secret-term\n', encoding='utf-8')
        r = gate(env={**env_clean, 'PRECEDENT_LEAK_BLOCKLIST': str(inside)})
        cases.append(('a PRIVATE blocklist located inside this repo is still '
                      'refused -- the guard that makes a committed default safe '
                      'is that only the default may live here',
                      r.returncode == 1 and 'INSIDE' in (r.stdout + r.stderr)))
    finally:
        inside.unlink(missing_ok=True)

    bad = [n for n, ok in cases if not ok]
    check(f'the default blocklist makes the vocabulary layer actually run, and '
          f'the private half stays external ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


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
        # A repo declaring universal (itself) + a team source.
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
                        {'level': 'team', 'name': 'precedent-team-maintainers',
                         'path': str(tmp / 'team')}]}), encoding='utf-8')

        extra, levels, notes = psp.collect(str(repo))
        slugs = {fm['slug'] for fm, _s, _f in extra}
        cases.append(("a team source's practice IS collected for the session",
                      'team-only-rule' in slugs))
        cases.append(('...and the universal one is NOT duplicated -- it is already '
                      'in the committed AGENTS.md, and repeating it would double '
                      'every session\'s resident block',
                      'universal-one' not in slugs))
        cases.append(('the level is carried, so the block can say where a rule came from',
                      levels.get('team-only-rule') == 'team'))

        text = psp.render(extra, levels, notes)
        cases.append(('the rendered block names the team practice',
                      'team-only-rule' in text))
        cases.append(('...and warns, in the file itself, never to commit it',
                      'Never commit it' in text))

        # An unreachable source is NAMED, not silently dropped.
        (repo / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'visibility': 'public',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': '.'},
                        {'level': 'team', 'name': 'precedent-team-maintainers',
                         'path': str(tmp / 'no-such-dir')}]}), encoding='utf-8')
        _extra, _levels, notes2 = psp.collect(str(repo))
        cases.append(('an unresolved source is NAMED in the output -- "unreachable" '
                      'and "that source has no rules" must not look the same',
                      any('precedent-team-maintainers' in n for n in notes2)))
        cases.append(('...and the file still renders rather than failing',
                      'did not resolve' in psp.render(_extra, _levels, notes2)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

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
                        {'level': 'team', 'name': 'precedent-team-maintainers',
                         'path': str(fx / 'team')}]}), encoding='utf-8')
        _sh.copy(ROOT / 'tools' / 'precedent_session_practices.py', repo / 'tools')
        hook = repo / '.claude' / 'hooks' / 'session-start.sh'

        def findings():
            saved = _pc.ROOT
            _pc.ROOT = repo
            try:
                return len(_pc._practice_is_reachable(None) or [])
            finally:
                _pc.ROOT = saved

        hook.write_text('#!/bin/bash\n# no loader here\n', encoding='utf-8')
        cases.append(('with the session channel NOT wired, a private-level '
                      'practice is still reported unreachable -- the channel is '
                      'never assumed', findings() == 1))
        hook.write_text('#!/bin/bash\npython3 tools/precedent_session_practices.py\n',
                        encoding='utf-8')
        cases.append(('...and once the hook invokes it, the same practice counts '
                      'as reachable, so the gap stops reading as open',
                      findings() == 0))
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
            {"slug": "commit-author", "reason": "about a repo one person authors alone"}]})
        cases.append(('a well-formed exemption is read, reason and all',
                      pr.load_not_binding(tmp) ==
                      {"commit-author": "about a repo one person authors alone"}))

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
                      refuses({**base, "not_binding": ["commit-author"]})))

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


def check_codeowners_check_is_a_check():
    """`build_codeowners.py --check` verifies without writing, and its output
    is a function of its source rather than of when it ran.

    TWO DEFECTS, both found 2026-09-06 by a caller trying to VERIFY that
    CODEOWNERS was current and instead dirtying the tree mid-PR:

      1. `--check` was not a flag at all. main() ignored argv, so the flag
         fell through and the tool WROTE -- a checker that answers "is this
         current?" by making it current cannot return a wrong answer, and
         cannot return a useful one. Same shape as verify-postcondition's
         own rule one level up: the check reported success by causing the
         state it was asked to confirm.
      2. The header stamped `git rev-parse HEAD`, so regenerating produced a
         diff after EVERY commit whether or not approvers changed. A derived
         file must be a function of its SOURCE; stamped with the time it was
         built, "is it current?" has no stable answer.

    BestPractice has no approvers.json -- it is not a team set -- so none of
    this is exercised by the tree, and that is exactly why it went unnoticed
    while the tool was private to one team set. The fixture supplies one.
    Now that build_codeowners.py is in ENGINE_FILES, every source set the
    bootstrap creates inherits whichever behavior this has."""
    import tempfile, shutil
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-codeowners-'))
    cases = []
    try:
        (tmp / 'tools').mkdir()
        shutil.copy(ROOT / 'tools' / 'build_codeowners.py', tmp / 'tools')
        approvers = tmp / 'approvers.json'
        codeowners = tmp / 'CODEOWNERS'
        approvers.write_text(
            '{"approvers": [{"name": "A", "github": "a"}, '
            '{"name": "B", "github": "b"}]}', encoding='utf-8')

        def run(*args):
            return subprocess.run(
                [sys.executable, str(tmp / 'tools' / 'build_codeowners.py'), *args],
                capture_output=True, text=True)

        r = run('--check')
        cases.append(('--check on a missing CODEOWNERS fails', r.returncode == 1))
        cases.append(('...and does NOT create it -- a checker that repairs is '
                      'a builder, and the caller cannot tell the two apart '
                      'afterwards', not codeowners.exists()))

        cases.append(('a plain run writes it', run().returncode == 0 and codeowners.is_file()))
        first = codeowners.read_bytes()
        cases.append(('--check on a current file passes', run('--check').returncode == 0))
        cases.append(('...having written nothing', codeowners.read_bytes() == first))

        run()
        cases.append(('regeneration is byte-identical when approvers.json is '
                      'unchanged -- the HEAD-sha churn that made every check '
                      'a false positive is gone', codeowners.read_bytes() == first))

        codeowners.write_bytes(first + b'# hand edit\n')
        cases.append(('a hand-edited CODEOWNERS is detected', run('--check').returncode == 1))

        run()
        approvers.write_text(
            '{"approvers": [{"name": "A", "github": "a"}]}', encoding='utf-8')
        cases.append(('a changed approver list is detected',
                      run('--check').returncode == 1))

        run()
        stable = codeowners.read_bytes()
        r = run('--chekc')
        cases.append(('a MISSPELLED flag is refused, not silently treated as '
                      '"no arguments" -- that fall-through is defect 1, and '
                      'doing the destructive thing on a typo is how it hid',
                      r.returncode != 0 and codeowners.read_bytes() == stable))

        approvers.unlink()
        cases.append(('an individual set (no approvers.json) exits 0 with a '
                      'note rather than failing', run('--check').returncode == 0))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [n for n, ok in cases if not ok]
    check(f'build_codeowners --check verifies without writing, and its output '
          f'depends on its source not its build time ({len(cases)} stated cases)',
          not bad, '; '.join(bad))


def check_status_contract():
    """A practice that is not `active` must say where its rule went.

    THE INCIDENT (2026-09-06). `status: retired` recorded that a rule stopped
    applying here but never whether anything replaced it. The forwarding
    address lived only as English prose in `## Story`, which no tool reads, so
    "deduplicated safely" and "dropped and forgotten" were indistinguishable to
    every check in the system. A routine per-commit check was dropped on the
    authority of an unrelated occasional one -- the two rules resembled each
    other, and resemblance was accepted as coverage. Nothing failed, because
    nothing could: no check had anything to compare.

    The vocabulary is the fix, and this is what gives it teeth
    (spec/PRACTICE_FORMAT.md, "Status"):

      active         no forwarding address; the rule applies here.
      deduplicated   the COPY is redundant; `in_force_at:` names a slug that
                     must RESOLVE IN FORCE, or `engine`.
      retired        wanted nowhere; `in_force_at: none` and a real ## Story.

    WHAT THIS CHECK REFUSES TO CLAIM. "Resolves in force" is only answerable
    against the actually-declared sources. When any of them is unreachable --
    a sibling clone this session does not have -- the resolved set is
    incomplete, and a "does not resolve" verdict would be an artifact of the
    missing checkout rather than a finding. In that case this degrades to the
    SHAPE check (a forwarding address is present and well-formed) and says so
    in its own name, rather than reporting a weaker check as the stronger
    one."""
    import tempfile, shutil
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_views as _bv
    import precedent_resolve as _pr

    # --- can we resolve for real this run? --------------------------------
    slug_in_force, resolution = None, 'shape only'
    try:
        sources = _pr.load_config(str(ROOT))
        res = _pr.resolve(sources)
        if res['missing']:
            gone = ', '.join(m['name'] for m in res['missing'])
            resolution = f'shape only -- source(s) unreachable this run: {gone}'
        else:
            in_force = set(res['practices'])
            slug_in_force = in_force.__contains__
            resolution = f'resolved against {len(sources)} source(s)'
    except Exception as e:                                # noqa: BLE001
        resolution = f'shape only -- sources unresolvable ({type(e).__name__}: {e})'

    # --- 1. every practice file in every source this repo owns -------------
    violations, scanned = [], 0
    dirs = [ROOT / 'practices']
    local = ROOT / 'local' / 'practices'
    if local.is_dir():
        dirs.append(local)
    for d in dirs:
        for f in sorted(d.glob('*.md')):
            try:
                fm, sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            scanned += 1
            v = _bv.status_contract_violation(fm, sections, slug_in_force)
            if v:
                violations.append(f"{f.relative_to(ROOT)}: {v}")
    check(f'status contract holds for every practice in this repo '
          f'({scanned} scanned, {resolution})',
          not violations, '; '.join(violations[:8]))

    # --- 2. the contract actually refuses each way of getting it wrong -----
    # BestPractice's own catalogue is 100% active, so without these the check
    # above passes vacuously and would go on passing if the validator were
    # gutted. Each case is a rule from the table in this docstring.
    def fm_of(status, in_force_at=None):
        d = {'status': status}
        if in_force_at is not None:
            d['in_force_at'] = in_force_at
        return d

    story = {'story': 'It stopped mattering when we dropped the tool.'}
    live = {'header-caps'}.__contains__
    cases = [
        ('an active practice with a forwarding address is contradictory',
         _bv.status_contract_violation(fm_of('active', 'header-caps')) is not None),
        ('an ordinary active practice is clean',
         _bv.status_contract_violation(fm_of('active')) is None),
        ('deduplicated with no in_force_at is refused -- this is exactly the '
         '"dropped and forgotten" case that used to be indistinguishable',
         _bv.status_contract_violation(fm_of('deduplicated')) is not None),
        ('deduplicated pointing at a slug that IS in force is accepted',
         _bv.status_contract_violation(fm_of('deduplicated', 'header-caps'),
                                       slug_in_force=live) is None),
        ('deduplicated pointing at a slug that is NOT in force is refused -- '
         'a surviving copy that is itself gone is not a surviving copy',
         _bv.status_contract_violation(fm_of('deduplicated', 'deep-check'),
                                       slug_in_force=live) is not None),
        ('deduplicated with in_force_at: engine is accepted -- the successor '
         'is code, not a slug',
         _bv.status_contract_violation(fm_of('deduplicated', 'engine'),
                                       slug_in_force=live) is None),
        ('deduplicated with in_force_at: none is refused -- in force nowhere '
         'is retirement, and needs retirement\'s evidence',
         _bv.status_contract_violation(fm_of('deduplicated', 'none')) is not None),
        ('retired pointing at a live slug is refused -- if the rule survives '
         'there, it was deduplicated',
         _bv.status_contract_violation(fm_of('retired', 'header-caps'), story,
                                       slug_in_force=live) is not None),
        ('retired with in_force_at: none and a real Story is accepted',
         _bv.status_contract_violation(fm_of('retired', 'none'), story) is None),
        ('retired with an empty Story is refused -- the one status no '
         'mechanism can verify must say why in prose',
         _bv.status_contract_violation(fm_of('retired', 'none'), {'story': ''})
         is not None),
        ('an unrecognized status is reported rather than waved through',
         _bv.status_contract_violation(fm_of('superseded', 'header-caps'))
         is not None),
        ('...and is NOT in force, so an unknown status fails closed',
         not _bv.is_in_force(fm_of('superseded'))),
    ]
    bad = [n for n, ok in cases if not ok]
    check(f'the status contract refuses each way of getting it wrong '
          f'({len(cases)} stated cases)', not bad, '; '.join(bad))

    # --- 3. the new word is wired to the FILTER, not just to the validator --
    # A status can be spelled correctly in the spec, validated correctly here,
    # and still be loaded into every session if the loader's own predicate
    # never learned it. That is the shape of the original defect, so it gets
    # its own end-to-end case rather than being assumed from case 2.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-dedup-'))
    try:
        (tmp / 'practices').mkdir()
        src = ROOT / 'practices'
        (tmp / 'practices' / 'repo-is-memory.md').write_text(
            (src / 'repo-is-memory.md').read_text(encoding='utf-8'), encoding='utf-8')
        dedup = (src / 'verify-postcondition.md').read_text(encoding='utf-8')
        dedup = re.sub(r'^status:(\s+)active$', r'status:\1deduplicated', dedup,
                       count=1, flags=re.M)
        dedup = re.sub(r'^in_force_at: null$', 'in_force_at: repo-is-memory',
                       dedup, count=1, flags=re.M)
        if 'deduplicated' not in dedup or 'in_force_at: repo-is-memory' not in dedup:
            raise RuntimeError('fixture did not actually become deduplicated')
        (tmp / 'practices' / 'verify-postcondition.md').write_text(dedup, encoding='utf-8')
        (tmp / 'AGENTS.md').write_text(
            '<!-- BEGIN GENERATED: precedent-loader -->\n<!-- END GENERATED -->\n',
            encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'build_views.py'),
             '--repo', str(tmp), '--agents-only'], capture_output=True, text=True)
        rendered = (tmp / 'AGENTS.md').read_text(encoding='utf-8')
        e2e = [
            ('a deduplicated practice is absent from the generated loader block',
             r.returncode == 0 and 'verify-postcondition' not in rendered),
            ('the active practice beside it is still emitted',
             'repo-is-memory' in rendered),
            ('the drop is announced by status name, not silently',
             'verify-postcondition' in r.stderr and 'deduplicated' in r.stderr),
        ]
        # ...and `precedent show` MARKS it rather than refusing, because a
        # session naming a slug explicitly is asking "what happened to this?"
        s = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_show.py'),
             'verify-postcondition', '--repo', str(tmp)],
            capture_output=True, text=True)
        e2e += [
            ('precedent show still resolves the slug rather than refusing it',
             s.returncode == 0),
            ('...and marks it NOT IN FORCE, naming where the rule lives now',
             'NOT IN FORCE' in s.stdout and 'repo-is-memory' in s.stdout),
            ('...with the marking ABOVE the rule text, so a session that '
             'stops reading early cannot take it as current',
             'NOT IN FORCE' in s.stdout.split('\n\n')[0]),
        ]
        bad_e2e = [n for n, ok in e2e if not ok]
        check(f'the deduplicated status is honored by the loading channels, '
              f'not merely spelled correctly ({len(e2e)} stated cases)',
              not bad_e2e,
              '; '.join(bad_e2e) + f' || build_views: {r.stdout}{r.stderr} '
              f'|| show: {s.stdout}{s.stderr}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_retired_practices_leave_the_views():
    """A practice that is not in force must not be in the loader block.

    build_views.py never read `status:` at all -- not in load_practices, not
    in the loader-block build, nowhere -- so a retired practice went on being
    emitted into AGENTS.md, MAP.md and GLOSSARY.md exactly like an active
    one. precedent_resolve.py had it right and printed `not in force`; the
    two channels disagreed, and the one a session actually loads was the
    wrong one.

    BestPractice's own catalogue has no retired practice, which is precisely
    why nothing here caught it: found 2026-09-06 in a private team set whose
    generated AGENTS.md listed all three of its retired practices, one of
    them retired that same day. So this case supplies a retired practice of
    its own rather than relying on the tree having one."""
    import tempfile, shutil
    cases = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-retired-'))
    try:
        (tmp / 'practices').mkdir()
        src = ROOT / 'practices'
        active = (src / 'repo-is-memory.md').read_text(encoding='utf-8')
        (tmp / 'practices' / 'repo-is-memory.md').write_text(active, encoding='utf-8')
        retired = (src / 'verify-postcondition.md').read_text(encoding='utf-8')
        retired = re.sub(r'^status:(\s+)active$', r'status:\1retired', retired,
                         count=1, flags=re.M)
        if 'status:      retired' not in retired and 'status: retired' not in retired:
            raise RuntimeError('fixture did not actually become retired')
        (tmp / 'practices' / 'verify-postcondition.md').write_text(retired, encoding='utf-8')
        (tmp / 'AGENTS.md').write_text(
            '<!-- BEGIN GENERATED: precedent-loader -->\n<!-- END GENERATED -->\n',
            encoding='utf-8')

        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'build_views.py'),
             '--repo', str(tmp), '--agents-only'],
            capture_output=True, text=True)
        rendered = (tmp / 'AGENTS.md').read_text(encoding='utf-8')
        cases.append(('a retired practice is absent from the generated loader '
                      'block -- retirement is not cosmetic',
                      r.returncode == 0 and 'verify-postcondition' not in rendered,
                      r.stdout + r.stderr + '\n---\n' + rendered))
        cases.append(('an active practice in the same directory is still '
                      'emitted -- the filter drops the retired one, not the '
                      'catalogue', 'repo-is-memory' in rendered, rendered))
        cases.append(('the drop is announced, not silent -- a retirement that '
                      'vanishes without a word is the same failure one size '
                      'down',
                      'verify-postcondition' in r.stderr and 'retired' in r.stderr,
                      r.stdout + r.stderr))

        sys.path.insert(0, str(ROOT / 'tools'))
        import build_views as _bv
        import precedent_resolve as _pr
        cases.append(('the loader and the resolver share one definition of '
                      '"in force", so they cannot drift apart again',
                      _pr.IN_FORCE_STATUS is _bv.IN_FORCE_STATUS,
                      f'{_pr.IN_FORCE_STATUS!r} vs {_bv.IN_FORCE_STATUS!r}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a retired practice leaves the generated views ({len(cases)} '
          f'stated cases)', not bad,
          '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


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
            # NO sibling sources are copied beside the fixture, deliberately.
            # build_views.py went multi-source on 2026-09-06 and the first
            # version of this fixture DID copy them, so that the regeneration
            # case exercised the real path instead of a degraded one. That
            # became wrong the same day, when the privacy guard widened: this
            # repo declares `visibility: public`, so private-level sources are
            # dropped from the block BEFORE resolution and their absence
            # cannot make it unverifiable. Copying them back in only gave
            # layered-practice-packs' baseline the real repo's 34 unreachable
            # team practices to report -- an open architectural question (see
            # TODO.md#unreachable-practices), not a defect a fixture planted,
            # and it made every planted case below prove nothing. A fixture
            # for a PRIVATE consumer's multi-source block would need them; the
            # coverage for that lives in
            # check_loader_block_covers_every_declared_source(), which runs
            # against the real tree with its real sources.
            return repo

        def run(repo, slug, *extra):
            env = dict(os.environ)
            env.pop('PRECEDENT_LEAK_BLOCKLIST', None)
            # The fixture must not resolve whoever's individual set happens
            # to be configured on this machine. It is found by ABSOLUTE path
            # from a user-level config, so unlike the team source (a relative
            # sibling that a temp-dir fixture cannot reach) it follows the
            # fixture anywhere -- and layered-practice-packs' baseline then
            # reports that developer's private practices, making the planted
            # case prove nothing. Pointed at a file that does not exist, so
            # the resolver takes its documented "this person has no
            # individual set" path rather than a half-configured one.
            env['PRECEDENT_USER_CONFIG'] = str(repo / '.no-user-config.json')
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

        def case(slug, plant, extra=(), setup=None, advisory=False):
            repo = fresh(slug)
            if setup:
                setup(repo)
            if plant:
                plant(repo)
            rc, out = run(repo, slug, *extra)
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
            clean = fresh(slug + '-clean')
            if setup:
                setup(clean)
            rc2, out2 = run(clean, slug, *extra)
            cases.append((f'{slug}: the same tree unplanted does not',
                          rc2 == 0 and 'VIOLATION' not in out2 and 'ADVISORY' not in out2))

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
            rewrite(repo, 'documentation/WHAT_IS_THIS_AND_BENEFITS.md',
                    lambda t: t.replace('## Learn More', '## Learn more', 1))
        case('headline-capitalization', _plant_headline)

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
        def _plant_unreachable(repo):
            rewrite(repo, 'AGENTS.md', lambda t: re.sub(
                r'\nWhen quoting or compressing someone else.s figures:\n'
                r'  quote-discipline[^\n]*\n', '\n', t))
        case('layered-practice-packs', _plant_unreachable, advisory=True)

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
                'Materialized from another source; it names `notes/ZZZ_OLD.md`\n'
                'as this convention\'s canonical example.\n', encoding='utf-8')
            (repo / 'tools' / 'checks').mkdir(parents=True, exist_ok=True)
            (repo / 'tools' / 'checks' / 'check_zzz_received.py').write_text(
                '# materialized check; its docstring names notes/ZZZ_OLD.md\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'materialized output from another source')
            git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')

        def _plant_received_only(repo):
            git(repo, 'mv', 'notes/ZZZ_OLD.md', 'notes/ZZZ_NEW.md')
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
            'See `notes/ZZZ_OLD.md` for the details.\n', encoding='utf-8')
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
            'A regenerated line naming notes/ZZZ_OLD.md.', 1))
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
                'A hand-written line naming notes/ZZZ_OLD.md.\n' + x)
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'hand-written half names the path')
        git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        _plant_received_only(repo)
        rc, out = run(repo, 'rename-updates-links')
        cases.append(('rename-updates-links: the same reference OUTSIDE the '
                      'generated block is still reported (skipped as a '
                      'region, not as a file)',
                      rc == 1 and 'VIOLATION' in out and 'AGENTS.md' in out))

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
                    lambda s: s.replace('Park it', 'the phrase'))
        case('park-it', _plant_park_it)

        # environment-gotchas -- an entry that is a bare fix
        def _plant_eg(repo):
            rewrite(repo, 'AGENTS.md', lambda t: t.replace(
                '- **`pip install cmarkgfm`',
                '- `pip install cmarkgfm`.\n\n- **`pip install cmarkgfm`', 1))
        case('environment-gotchas', _plant_eg)

        # session-bootstrap -- setup named in prose, no hook to run it
        case('session-bootstrap',
             lambda repo: shutil.rmtree(repo / '.claude' / 'hooks'))

        # declared-hooks-exist -- settings.json still declares a hook file
        # that is no longer there. This is the 2026-09-08 incident with the
        # variables swapped: there every hook path was right and the session
        # root was wrong, here the root is right and the file is gone. Both
        # render identically, as nothing at all, which is why a machine has
        # to be the one asking.
        def _plant_declared_hook(repo):
            (repo / '.claude' / 'hooks' / 'commit-identity.sh').unlink()
        case('declared-hooks-exist', _plant_declared_hook)
        cases.append(('declared-hooks-exist: the planted violation names the '
                      'hook that went missing, not just that something did',
                      'commit-identity.sh does not exist'
                      in planted['declared-hooks-exist'][1]))

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

        # parallel-artifact-ledger -- the check reads real git history, but
        # fresh() deliberately squashes each scratch copy's history into one
        # new "baseline" commit for isolation, so that commit's own hash has
        # to be in the ledger before "clean" means clean here.
        def _ledger_setup(repo):
            baseline_hash = git(repo, 'rev-parse', 'HEAD')
            rewrite(repo, 'templates/harness/LEDGER.md',
                   lambda t: t + f'\n<!-- harness-test baseline: {baseline_hash} -->\n')

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
        # Two more commits, because the check excludes two kinds of
        # inception: the repo's own root commit, and the commit that
        # FIRST created a given member directory (TODO.md item 18 --
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

        no_ledger = fn(None)
        ledger_path.write_text('no commit hashes here\n', encoding='utf-8')
        unreferenced = fn(None)
        ledger_path.write_text(f'{member_commit}\n', encoding='utf-8')
        referenced = fn(None)

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
            ("a ledger referencing the commit's hash clears the finding",
             referenced == []),
        ]
        bad = [n for n, ok in cases if not ok]
        check(f"parallel-artifact-ledger check fires ({len(cases)} stated cases: "
              f"no ledger, ledger missing the commit, ledger referencing it, "
              f"a family's own inception commit needing no row)",
              not bad, '; '.join(bad))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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


def check_source_sets_can_learn_they_are_stale():
    """A vendored source set must have some way to find out its engine is old.

    2026-09-06: `precedent-individual` and `precedent-team-tms` both sat at
    ef8b5d09 while this branch moved more than two hundred commits past it,
    and both were generating a loader block with a defect fixed upstream
    days earlier. Nothing was broken -- there was simply no channel through
    which "your copy is behind" could reach anyone. It surfaced because a
    session happened to have a clone attached and happened to run a check by
    hand.

    A CONSUMER repo never had this problem: it vendors process/upstream/ and
    its bootstrap runs a freshness check at session start. The asymmetry was
    the defect, and these cases assert the three channels that close it, so
    that removing any one of them fails here rather than going quiet for
    another two hundred commits.
    """
    cases = []

    # 1. No source template ships a scheduled workflow, and that is the
    #    decision, not an omission (2026-09-06). One was added here and
    #    pulled back out the same day: a cron job that phones a remote every
    #    week and opens pull requests is a real imposition on every adopter
    #    who inherits it, and a universal template is exactly the wrong place
    #    to make that choice for people. It lives at the individual level
    #    now, for whoever wants it. This case exists so the file cannot
    #    reappear here without someone deciding to put it back.
    for level in ('individual', 'team'):
        wf = ROOT / 'templates' / f'practice-set-{level}' / '.github' / 'workflows' / 'engine-refresh.yml'
        cases.append((f'the {level} source template ships no scheduled workflow '
                      f'(a per-person choice, not a universal default)',
                      not wf.exists(), str(wf.relative_to(ROOT)) if wf.exists() else ''))

    # 2. The bootstrap tool warns when the clone it is seeding FROM is behind.
    bs = (ROOT / 'tools' / 'precedent_bootstrap_source.py').read_text(encoding='utf-8')
    cases.append(('bootstrap warns when seeding from a stale checkout',
                  '_warn_if_clone_is_stale' in bs and '_warn_if_clone_is_stale()' in bs, ''))

    # 3. A session working HERE is told about stale attached sources.
    tool = ROOT / 'tools' / 'precedent_refresh_sources.py'
    cases.append(('precedent_refresh_sources.py exists', tool.is_file(), ''))
    hook = (ROOT / '.claude' / 'hooks' / 'session-start.sh').read_text(encoding='utf-8')
    cases.append(('the session-start hook runs it',
                  'precedent_refresh_sources.py' in hook, ''))

    if tool.is_file():
        # Both directions, against real fixtures: a set recording this
        # checkout's own tip is current; one recording anything else is not.
        # Without the "current" case, a detector that called everything stale
        # would pass.
        import shutil, tempfile
        import importlib.util
        spec = importlib.util.spec_from_file_location('_prs', tool)
        prs = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prs)
        tip, _ref = prs.head_commit()
        tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-staleness-'))
        try:
            def fake_set(name, commit):
                d = tmp / name
                (d / 'tools').mkdir(parents=True)
                (d / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                    json.dumps({'format_version': 1, 'kind': 'source',
                                'source_commit': commit}), encoding='utf-8')
                return d
            if tip:
                current = fake_set('current-set', tip)
                stale = fake_set('stale-set', '0' * 40)
                _t, _r, found = prs.survey([str(current), str(stale)])
                by = {e['repo'].name: e for e in found}
                cases.append(('a set recording this tip reports as current',
                              by.get('current-set', {}).get('stale') is False,
                              str(by.get('current-set'))))
                cases.append(('a set recording an older commit reports as STALE',
                              by.get('stale-set', {}).get('stale') is True,
                              str(by.get('stale-set'))))
            else:
                cases.append(('the staleness fixtures could run (needs '
                              f'origin/{prs.SOURCE_BRANCH} fetched)', False,
                              'branch not resolvable in this clone'))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'a vendored source set can learn its engine is stale '
          f'({len(cases)} stated cases: no templated cron, bootstrap warning, '
          f'attached-source detector)',
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

    def write_practice(path, slug, rule, tier='on-demand', occasion='x',
                       checked_by='null'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'---\nslug: {slug}\ntitle: Fixture\ntier: {tier}\n'
            f'severity: default\napplies_to: ["**"]\noccasion: "{occasion}"\n'
            f'gates: []\nindex_clause: "x"\nchecked_by: {checked_by}\ndefines: []\n'
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
        # Both fixture practices CLAIM the same check filename, which is
        # what makes the collision below a real one: since 2026-09-06
        # materialize only vendors a script some resolved practice's
        # `checked_by` names, so an unclaimed pair would simply be dropped
        # and never collide.
        write_practice(uni / 'practices' / 'uni-fixture.md', 'uni-fixture',
                        'A universal fixture Rule.', tier='resident',
                        checked_by='"tools/checks/check_shared_name.py"')
        write_practice(team / 'practices' / 'team-fixture.md', 'team-fixture',
                        'A team fixture Rule.', tier='resident',
                        checked_by='"tools/checks/check_shared_name.py"')
        write_check(uni / 'tools' / 'checks' / 'check_shared_name.py')
        write_check(team / 'tools' / 'checks' / 'check_shared_name.py')
        write_check(uni / 'tools' / 'checks' / 'tests' / 'test_shared_name.sh',
                    body='fixture\n')
        # Claimed by nothing: a script whose practice was retired, or lost
        # its slug to a higher-precedence source. Must not be vendored --
        # precedent-team-maintainers' retired `deep-check` shipped exactly
        # this into a consuming repo, where it registered under its own
        # filename and reported "not in force" forever.
        write_check(uni / 'tools' / 'checks' / 'check_orphan.py')
        write_check(uni / 'tools' / 'checks' / 'tests' / 'test_orphan.sh',
                    body='fixture\n')

        consumer = tmp / 'consumer'
        (consumer).mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(uni)},
                        {'level': 'team', 'name': 'precedent-team-fixture', 'path': str(team)}]
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

        cases.append(("a check script no resolved practice's checked_by names "
                      "is not vendored, and neither is its test",
                      materialized_ok
                      and not (consumer / 'tools' / 'checks' / 'check_orphan.py').exists()
                      and not (consumer / 'tools' / 'checks' / 'tests' / 'test_orphan.sh').exists()))
        cases.append(('a claimed check script and its test ARE vendored',
                      materialized_ok
                      and (consumer / 'tools' / 'checks' / 'check_shared_name.py').exists()
                      and (consumer / 'tools' / 'checks' / 'tests' / 'test_shared_name.sh').exists()))

        (consumer / 'tools').mkdir(parents=True, exist_ok=True)
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

        # --- the SAME scenario again, but run tools/build_views.py IN PLACE
        # (no copy) with --repo pointed at the fixture, instead of copying
        # the script into the fixture's own tools/ first. Before build_views
        # accepted --repo, this was the only way to test it against content
        # that isn't its own -- ROOT was always computed as two folders up
        # from wherever the running copy physically sat, so a script that
        # never moved could never be pointed elsewhere. This case is kept
        # ALONGSIDE the copy-based case above, not in place of it: a
        # consuming repo's own vendored copy (the documented, still-current
        # INSTALL.md model) is the copy-based shape, and a future vendored
        # engine invoked with --repo (this request's own stated motivation)
        # is this one -- both invocation styles have to keep working.
        (consumer / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')
        r2 = subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_views.py'),
                              '--repo', str(consumer), '--agents-only'],
                             capture_output=True, text=True)
        agents_text2 = (consumer / 'AGENTS.md').read_text(encoding='utf-8') \
            if (consumer / 'AGENTS.md').exists() else ''
        cases.append(("the real, un-relocated build_views.py run with --repo (no copy) "
                      "produces a resident block naming BOTH sources' practices too",
                      materialized_ok and r2.returncode == 0
                      and 'uni-fixture' in agents_text2 and 'team-fixture' in agents_text2))
        # The GENERATED test driver. tools/checks/tests/run_all.sh is the one
        # file this tool writes rather than copies: every source ships its own,
        # so copying would force a winner, but `deep-check` requires the file to
        # exist -- so before 2026-09-06 no consuming repo could satisfy that
        # practice, and its far more useful half (each check has a test; no test
        # outlives its check) never ran, because the check returns early on the
        # missing file. Four properties, each with its own way of regressing.
        run_all = consumer / 'tools' / 'checks' / 'tests' / 'run_all.sh'
        run_all_text = run_all.read_text(encoding='utf-8') if run_all.is_file() else ''
        cases.append(('the test driver is generated into the consumer even though '
                      'no source file was copied for it',
                      materialized_ok and run_all.is_file()))
        # deep-check greps for this exact glob; a driver naming specific tests
        # would pass a bare existence test while silently skipping new ones.
        cases.append(('the generated driver globs test_*.sh rather than naming '
                      'tests, so it runs whatever THIS repo materialized',
                      'test_*.sh' in run_all_text))
        # An unrecorded file is indistinguishable from a hand-dropped orphan to
        # a consuming repo's own orphan detection, which reads MANIFEST.json.
        manifest_path = consumer / 'MANIFEST.json'
        recorded = []
        if manifest_path.is_file():
            recorded = [c for c in json.loads(
                manifest_path.read_text(encoding='utf-8')).get('checks', [])
                if c.get('path', '').endswith('tests/run_all.sh')]
        cases.append(('the generated driver is recorded in MANIFEST.json, so a '
                      "consumer's orphan detection does not read it as hand-dropped",
                      len(recorded) == 1))
        # A repo that materialized no tests leaves the glob unexpanded; without
        # the guard the driver runs a file literally named test_*.sh and reports
        # a failure that is really an empty set.
        empty_dir = tmp / 'empty-driver'
        empty_dir.mkdir(parents=True, exist_ok=True)
        (empty_dir / 'run_all.sh').write_text(run_all_text or 'exit 1\n', encoding='utf-8')
        r3 = subprocess.run(['bash', 'run_all.sh'], cwd=str(empty_dir),
                            capture_output=True, text=True)
        cases.append(('the generated driver exits 0 in a repo that materialized '
                      'no tests, rather than failing on the unexpanded glob',
                      bool(run_all_text) and r3.returncode == 0))

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_materialize.py bridges the loader ({len(cases)} stated cases: '
          f'a checks/ collision refuses, an over-budget combined set refuses, a clean '
          f"materialize feeds both a copied and an in-place --repo build_views.py "
          f"both sources' content, and the test driver is generated rather than "
          f'copied -- present, globbing, recorded in the manifest, and exiting 0 '
          f'on an empty test set)',
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

    EXTENDED 2026-09-06 (TODO.md item 20, closed) to cover
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
        # read practices/*.md directly, same as precedent_show.py, and TODO
        # item 20 named them as needing the identical reachability note.
        write_practice(indiv / 'practices' / 'show-fixture-individual-routed.md',
                       'show-fixture-individual-routed', 'The routed individual fixture Rule.',
                       applies_to='["fixture-only/*.md"]', gates='["push"]')
        uni = tmp / 'uni-source'
        write_practice(uni / 'practices' / 'show-fixture-universal.md',
                       'show-fixture-universal', 'The universal fixture Rule.')

        consumer = tmp / 'consumer'
        (consumer).mkdir()
        (consumer / 'precedent.json').write_text(json.dumps({
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
                               capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        def gate(name):
            r = subprocess.run([sys.executable, gate_tool, name, '--repo', str(consumer)],
                               capture_output=True, text=True)
            return r.returncode, r.stdout + r.stderr

        def paths(*p):
            r = subprocess.run([sys.executable, paths_tool, *p, '--repo', str(consumer)],
                               capture_output=True, text=True)
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
                      'the gated individual-sourced slug (TODO item 20, closed)',
                      rc == 0 and 'NOT reachable this session' in out
                      and '(source: individual,' in out, out))

        rc, out = paths('fixture-only/x.md')
        cases.append(('unreachable: precedent_paths.py now carries the note for '
                      'the same slug matched by path (TODO item 20, closed)',
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


def check_sync_refuses_to_lose_a_recorded_practice():
    """A sync will not silently drop a rule the repository already published.

    The incident, 2026-09-07: promoting two practices out of a team set into
    the universal catalogue left every consumer pinned before the promotion
    with them in NEITHER source, so its next sync deleted both. `--check`
    named them; a real sync rmtree's practices/ and says nothing.

    THE BASELINE IS THE COMMITTED MANIFEST, and that is the whole design. A
    first attempt compared the working tree against the plan and had to be
    reverted -- it fired on a public repo withholding by design, on a sync
    already carrying --allow-missing-sources, and on a fixture re-syncing
    after its sources changed. "The tree differs from the plan" is true
    constantly. "This repository committed a catalogue containing rule X and
    X is about to vanish" is narrow enough to refuse on. The four cases below
    are the four that distinction has to get right.
    """
    import tempfile, shutil
    sync_tool = str(ROOT / 'tools' / 'precedent_sync_views.py')

    def _repo(tmp, extra_source=True):
        repo, team = tmp / 'c', tmp / 'precedent-team-x'
        (repo / 'precedent' / 'universal').mkdir(parents=True)
        shutil.copytree(PRACTICES_DIR, repo / 'precedent' / 'universal' / 'practices')
        (team / 'practices').mkdir(parents=True)
        (team / 'practices' / 'team-x-rule.md').write_text(
            '---\nslug: team-x-rule\ntitle: The rig is used\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "changing firmware"\n'
            'index_clause: "use the rig"\nstatus: active\n---\n'
            '## Rule\nUse the rig.\n\n## Story\nIt drifted.\n', encoding='utf-8')
        # A SECOND practice, so removing the first does not empty the source.
        # An existing guard already refuses a source that went completely
        # empty ("a sync would quietly drop that whole catalogue"), and the
        # first version of this fixture tripped that one instead of the one
        # under test -- a fixture proving the wrong thing passes just as
        # confidently as one proving the right thing.
        (team / 'practices' / 'team-x-keeper.md').write_text(
            '---\nslug: team-x-keeper\ntitle: The bench is logged\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "logging bench time"\n'
            'index_clause: "log the bench"\nstatus: active\n---\n'
            '## Rule\nLog it.\n\n## Story\nIt was not logged.\n',
            encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# C\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n', encoding='utf-8')
        srcs = [{'level': 'universal', 'name': 'precedent',
                 'path': 'precedent/universal'}]
        if extra_source:
            srcs.append({'level': 'team', 'name': 'precedent-team-x',
                         'path': str(team)})
        (repo / 'precedent.json').write_text(json.dumps({
            'format_version': 1, 'base_branch': 'main',
            'visibility': 'private', 'sources': srcs}), encoding='utf-8')
        user = tmp / 'u.json'
        user.write_text(json.dumps({'format_version': 1}), encoding='utf-8')
        for c in (['init', '-q', '-b', 'main'],
                  ['config', 'user.email', 'harness@example.com'],
                  ['config', 'user.name', 'Harness']):
            subprocess.run(['git', '-C', str(repo)] + c, capture_output=True)
        return repo, team, user

    def _sync(repo, user, *flags):
        return subprocess.run(
            [sys.executable, sync_tool, '--repo', str(repo),
             '--user-config', str(user)] + list(flags),
            capture_output=True, text=True)

    def _commit(repo):
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], capture_output=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'catalogue'],
                       capture_output=True)

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # 1. NO COMMITTED MANIFEST -- a fresh install has nothing to lose.
        repo, team, user = _repo(tmp)
        r = _sync(repo, user)
        cases.append(('a repo with no committed manifest syncs freely',
                      r.returncode == 0))

        # 2. The real case: publish a catalogue, then the source stops
        #    producing the rule while STILL being declared.
        _commit(repo)
        (team / 'practices' / 'team-x-rule.md').unlink()
        r = _sync(repo, user)
        cases.append(('a recorded practice vanishing from a still-declared '
                      'source REFUSES', r.returncode != 0))
        cases.append(('and it names the slug and its source',
                      'team-x-rule' in r.stderr and 'precedent-team-x' in r.stderr))
        cases.append(('and the practice file survives the refusal',
                      (repo / 'practices' / 'team-x-rule.md').exists()))

        # 3. --allow-removals is the deliberate override.
        r = _sync(repo, user, '--allow-removals')
        cases.append(('--allow-removals permits it',
                      r.returncode == 0
                      and not (repo / 'practices' / 'team-x-rule.md').exists()))

        # 4. DROPPING the source is a decision already made -- report, allow.
        repo2, team2, user2 = _repo(tmp / 'b')
        _sync(repo2, user2); _commit(repo2)
        cfg = json.loads((repo2 / 'precedent.json').read_text())
        cfg['sources'] = [s for s in cfg['sources'] if s['level'] != 'team']
        (repo2 / 'precedent.json').write_text(json.dumps(cfg), encoding='utf-8')
        r = _sync(repo2, user2)
        cases.append(('dropping a source from precedent.json is allowed, not '
                      'refused', r.returncode == 0))
        cases.append(('and it says which practices went with it',
                      'team-x-rule' in r.stderr))

    failed = [n for n, ok in cases if not ok]
    check(f'a sync refuses to lose a practice the committed manifest records '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


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


def check_commit_identity_derives_declared_timezone():
    """The declared timezone reaches the SESSION, not just the refusal message.

    The pre-commit backstop refuses a commit whose offset contradicts a
    declared timezone, and tells the person to rerun under `TZ=...`. Correct,
    and on its own it is a chore with no end: a hook cannot export TZ into the
    shells a session runs later, so the remedy gets retyped on every commit
    forever. 2026-09-07 the person running such a session said so plainly --
    "I'd rather a permanent fix than my having to do that manually."

    So the hook derives `env.TZ` into .claude/settings.local.json, which the
    harness reads for the whole of the NEXT session. Four properties have to
    hold together, and the fixture must be hermetic to test any of them: an
    early version of this test set no PRECEDENT_USER_CONFIG, so the case for
    "no declared zone" resolved the real user config, found a real declared
    zone, and reported a failure against completely correct behaviour.
      1. a DECLARED zone is written; a GUESSED one never is (writing a guess
         would enforce something nobody said).
      2. identity.json stays the source of truth -- a stale TZ already in the
         file is re-derived, not respected (registry-source-of-truth).
      3. nothing else in the file is disturbed, and an unparseable one is left
         entirely alone rather than overwritten.
      4. the file is per-machine, so the hook warns when it is not gitignored.
    """
    import tempfile, json as _json
    hook = ROOT / '.claude' / 'hooks' / 'commit-identity.sh'
    if not hook.exists():
        not_applicable('commit-identity derives the declared timezone into '
                       'the session',
                       '.claude/hooks/commit-identity.sh is not present here')
        return

    env = dict(os.environ)
    # Hermetic: without this the hook resolves the REAL user config and the
    # "no zone declared" case silently becomes a "zone declared" case.
    env['PRECEDENT_USER_CONFIG'] = '/nonexistent/precedent-config.json'
    env.pop('PRECEDENT_COMMIT_TZ', None)
    # And HOME, or the hook writes the REAL ~/.gitconfig and the REAL global
    # hooks directory. It gained that behaviour on 2026-09-07 and this
    # fixture -- which declares Europe/Berlin -- promptly set this machine's
    # global identity to a test value and installed a Berlin-offset backstop,
    # which then refused the very commit landing the fix. A test that mutates
    # the environment it runs in is not a test.
    _home = tempfile.mkdtemp(prefix='ci-home-')
    env['HOME'] = _home
    # And the system clock, for the same reason and one step worse: this
    # fixture declares Europe/Berlin, and the hook now REPOINTS the machine's
    # zone file at a declared zone. Without this the harness would put the
    # container on Berlin time and every later commit in the session would be
    # refused by the backstop for an offset the harness itself caused.
    env['PRECEDENT_LOCALTIME'] = os.path.join(_home, 'localtime')

    def _repo(base, zone, settings=None, gitignore=None):
        base.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-C', str(base), 'init', '-q'],
                       capture_output=True)
        if zone:
            (base / 'identity.json').write_text(_json.dumps(
                {'name': 'T', 'email': 't@example.com', 'timezone': zone}),
                encoding='utf-8')
        if settings is not None:
            (base / '.claude').mkdir(exist_ok=True)
            (base / '.claude' / 'settings.local.json').write_text(
                settings, encoding='utf-8')
        if gitignore is not None:
            (base / '.gitignore').write_text(gitignore, encoding='utf-8')
        e = dict(env, CLAUDE_PROJECT_DIR=str(base))
        r = subprocess.run(['bash', str(hook)], capture_output=True,
                           text=True, env=e, timeout=120)
        return base / '.claude' / 'settings.local.json', r

    def _tz(f):
        try:
            return _json.loads(f.read_text(encoding='utf-8'))['env']['TZ']
        except Exception:
            return None

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        f, r = _repo(tmp / 'declared', 'America/Argentina/Buenos_Aires')
        cases.append(('a declared zone lands in settings.local.json',
                      _tz(f) == 'America/Argentina/Buenos_Aires'))
        cases.append(('and the hook still exits 0', r.returncode == 0))
        before = f.read_bytes()
        e = dict(env, CLAUDE_PROJECT_DIR=str(tmp / 'declared'))
        r2 = subprocess.run(['bash', str(hook)], capture_output=True,
                            text=True, env=e, timeout=120)
        cases.append(('a second run rewrites nothing', f.read_bytes() == before))
        cases.append(('and says nothing about it',
                      'settings.local.json' not in r2.stderr))

        # A person whose zone could not be resolved gets the DECLARED
        # FALLBACK written, not nothing. This assertion is the reverse of
        # what it was before 2026-09-09 (practice: timestamps-carry-offset):
        # writing nothing left the container on UTC, so every unidentified
        # person's commits and generated dates came out +0000 and could not
        # be ordered against anyone else's. The fallback is applied for that
        # reason and still never ENFORCED -- case 3 below holds that line.
        #
        # The expected value is DERIVED, never typed here. Typed, it is a
        # fourth copy of a constant that already lives in four places, and on
        # 2026-09-10 -- when the engine fallback moved off one person's zone
        # onto a generic one -- these two assertions were the only thing that
        # failed, because they were the copies nobody knew to change.
        f, r3 = _repo(tmp / 'guessed', None)
        cases.append((f'an unresolved zone still writes the declared fallback '
                      f'({_declared_fallback_tz()})',
                      _tz(f) == _declared_fallback_tz()))
        cases.append(('and says out loud that it is a fallback, not this '
                      "person's own zone",
                      'DECLARED FALLBACK' in r3.stderr))

        f, _ = _repo(tmp / 'existing', 'Europe/Berlin',
                     settings='{"env":{"OTHER":"keep"},'
                              '"permissions":{"allow":["Bash(ls)"]}}')
        try:
            d = _json.loads(f.read_text(encoding='utf-8'))
        except Exception:
            d = {}
        cases.append(('an existing file keeps its other keys',
                      d.get('env', {}).get('TZ') == 'Europe/Berlin'
                      and d.get('env', {}).get('OTHER') == 'keep'
                      and d.get('permissions', {}).get('allow') == ['Bash(ls)']))

        f, _ = _repo(tmp / 'stale', 'Europe/Berlin',
                     settings='{"env":{"TZ":"UTC"}}')
        cases.append(('a stale TZ is re-derived, not respected',
                      _tz(f) == 'Europe/Berlin'))

        f, _ = _repo(tmp / 'broken', 'Europe/Berlin', settings='not json at all')
        cases.append(('an unparseable settings file is left untouched',
                      f.read_text(encoding='utf-8') == 'not json at all'))

        _, r = _repo(tmp / 'ignored', 'Europe/Berlin',
                     gitignore='.claude/settings.local.json\n')
        cases.append(('no gitignore warning when the file IS ignored',
                      'NOT gitignored' not in r.stderr))
        _, r = _repo(tmp / 'notignored', 'Europe/Berlin')
        cases.append(('the gitignore warning fires when it is not',
                      'NOT gitignored' in r.stderr))

    failed = [n for n, ok in cases if not ok]
    check(f'commit-identity derives the declared timezone into the session '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_refresh_survives_an_upstream_rename():
    """A file removed upstream must not brick every consumer's refresh.

    `refresh` runs the consumer's OWN vendored copy of the vendoring tool,
    and that copy carries the file list it was vendored with. So the first
    refresh after upstream renames or drops an engine file asks git for a
    path that is genuinely gone. That used to be a hard exit:

      precedent_vendor_engine FAIL: precedent-beta-v01 @ <sha> has no
      tools/precedent_retire_path.py

    with no documented way forward -- the fix a consumer needs is inside the
    very file it cannot fetch. The tool's own comments already describe this
    shape for an ADDED file, where it merely stops one file short and the
    second pass converges; for a REMOVED file it was fatal. Reproduced
    2026-09-07 on a real consumer, renaming precedent_retire_path.py ->
    precedent_decommission.py.

    A missing source file is therefore a REMOVAL: skipped with a notice, and
    left out of the manifest rather than recorded as present. The second
    pass then runs the new list, which does not ask for it at all.

    THE ONE FILE THAT STAYS FATAL is the vendoring tool itself. It is what
    carries the corrected list, so without it there is no second pass and
    nothing to converge on -- and a missing one really does mean a broken
    ref rather than a removal. That distinction is the whole point of the
    case below: skipping everything would trade a loud failure for a silent
    one.
    """
    import tempfile, json as _json, shutil as _shutil, importlib
    vend = ROOT / 'tools' / 'precedent_vendor_engine.py'
    if not vend.exists():
        not_applicable('refresh survives an upstream rename',
                       'tools/precedent_vendor_engine.py is not present here')
        return

    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # A throwaway "upstream" whose tools/ is MISSING one file the
        # consumer's list still asks for -- exactly what a rename leaves.
        up = tmp / 'upstream'
        (up / 'tools').mkdir(parents=True)
        _ve = importlib.import_module('precedent_vendor_engine')
        for name in sorted(set(_ve.KINDS['consumer']) | {'routing_scope.json'}):
            if name == 'precedent_show.py':
                continue                      # the "renamed away" file
            src = ROOT / 'tools' / name
            if src.is_file():
                _shutil.copy2(src, up / 'tools' / name)
        subprocess.run(['git', '-C', str(up), 'init', '-q'], capture_output=True)
        for c in (['config', 'user.email', 'h@example.com'],
                  ['config', 'user.name', 'H']):
            subprocess.run(['git', '-C', str(up)] + c, capture_output=True)
        subprocess.run(['git', '-C', str(up), 'add', '-A'], capture_output=True)
        subprocess.run(['git', '-C', str(up), 'commit', '-qm', 'upstream'],
                       capture_output=True, env=env)
        up_head = subprocess.run(['git', '-C', str(up), 'rev-parse', 'HEAD'],
                                 capture_output=True, text=True).stdout.strip()

        # A consumer seeded from THIS tree -- so its list still names the file
        # the upstream above no longer has.
        cons = tmp / 'consumer'
        cons.mkdir()
        subprocess.run(['git', '-C', str(cons), 'init', '-q'], capture_output=True)
        r = subprocess.run(
            [sys.executable, str(vend), 'seed', str(cons), '--kind', 'consumer'],
            capture_output=True, text=True, timeout=300, env=env)
        if r.returncode != 0:
            not_applicable('refresh survives an upstream rename',
                           'could not seed a consumer engine here')
            return
        _shutil.copy2(vend, cons / 'tools' / 'precedent_vendor_engine.py')

        r = subprocess.run(
            [sys.executable, str(cons / 'tools' / 'precedent_vendor_engine.py'),
             'refresh', str(up), '--force', '--from-ref', up_head],
            capture_output=True, text=True, timeout=600, cwd=str(cons), env=env)
        out = r.stdout + r.stderr
        cases.append(('a file removed upstream does not fail the refresh',
                      r.returncode == 0))
        cases.append(('and the run says the file was removed or renamed, '
                      'rather than reporting a broken clone',
                      'removed or renamed' in out))
        try:
            m = _json.loads((cons / 'tools' / 'ENGINE_MANIFEST.json')
                            .read_text(encoding='utf-8'))
        except (OSError, ValueError):
            m = {}
        cases.append(('the missing file is left OUT of the manifest, not '
                      'recorded as present',
                      'precedent_show.py' not in (m.get('files') or [])
                      and 'precedent_show.py' not in (m.get('sha256') or {})))
        cases.append(('every file the manifest DOES record exists on disk',
                      all((cons / 'tools' / f).is_file()
                          for f in (m.get('files') or []))))

        # THE MUST-STAY-FATAL CASE: the vendoring tool itself is gone.
        up2 = tmp / 'upstream-no-tool'
        _shutil.copytree(up, up2)
        (up2 / 'tools' / 'precedent_vendor_engine.py').unlink()
        subprocess.run(['git', '-C', str(up2), 'add', '-A'], capture_output=True)
        subprocess.run(['git', '-C', str(up2), 'commit', '-qm', 'drop the tool'],
                       capture_output=True, env=env)
        up2_head = subprocess.run(['git', '-C', str(up2), 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True).stdout.strip()
        r2 = subprocess.run(
            [sys.executable, str(cons / 'tools' / 'precedent_vendor_engine.py'),
             'refresh', str(up2), '--force', '--from-ref', up2_head],
            capture_output=True, text=True, timeout=600, cwd=str(cons), env=env)
        out2 = r2.stdout + r2.stderr
        cases.append(('a missing VENDORING TOOL is still fatal -- there is no '
                      'corrected list to converge on', r2.returncode != 0))
        cases.append(('and says that, rather than calling it a removal',
                      'not a removal' in out2))

    failed = [n for n, ok in cases if not ok]
    check(f'a file removed upstream does not brick a consumer refresh '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


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


def check_refresh_removes_dropped_engine_files():
    """A file dropped from the engine set leaves every consumer, not just this repo.

    refresh() only ever added and overwrote. Rename or drop a file from KINDS
    and every consumer that already had it kept it forever: the new manifest
    stops listing it, so nothing tracks it, nothing updates it, and no later
    reader can tell whether it still does something. That is the exact state
    decommission-deletes-files exists to prevent, produced by the tool that
    distributes that practice.

    Found 2026-09-07 costing the retirement->decommission rename: the tool
    being renamed is IN the consumer engine set, so the rename would have
    pushed the new name out and left the old one beside it in perpetuity --
    two repos that day, and every consumer created afterwards.

    Safety rests entirely on the manifest. Only files the PREVIOUS manifest
    recorded as vendored are candidates, so a consuming repo's own tools/
    cannot be touched whatever it is named -- that is the case this test
    spends a fixture on, because getting it wrong deletes somebody's work
    rather than merely leaving litter.

    And a hand-edited copy is KEPT and reported. _local_drift already refuses
    the whole refresh over one unless --force, so arriving here modified
    means somebody asked to overwrite -- which is not the same as asking to
    throw the edit away.
    """
    import tempfile, json as _json, shutil as _shutil
    vend = ROOT / 'tools' / 'precedent_vendor_engine.py'
    if not vend.exists():
        not_applicable('refresh removes dropped engine files',
                       'tools/precedent_vendor_engine.py is not present here')
        return

    env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')

    def _consumer(base):
        """Seed a real consumer engine from THIS working tree."""
        base.mkdir(parents=True)
        subprocess.run(['git', '-C', str(base), 'init', '-q'], capture_output=True)
        r = subprocess.run(
            [sys.executable, str(vend), 'seed', str(base), '--kind', 'consumer'],
            capture_output=True, text=True, timeout=300, env=env)
        if r.returncode != 0:
            return None
        # AND OVERWRITE THE SEEDED TOOL WITH THIS WORKING TREE'S. `seed`
        # vendors via git, so it copies the COMMITTED engine -- a fixture
        # built on it silently tests the code as it was before your change.
        # Cost this exact test three red cases before the cause was found,
        # and cost the rename-updates-links test the same thing an hour
        # earlier, which is why it is spelled out in both.
        _shutil.copy2(vend, base / 'tools' / 'precedent_vendor_engine.py')
        return base

    def _manifest(base):
        return _json.loads(
            (base / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        base = _consumer(tmp / 'consumer')
        if base is None:
            not_applicable('refresh removes dropped engine files',
                           'could not seed a consumer engine here')
            return

        m = _manifest(base)
        victim = 'precedent_show.py'
        cases.append(('the fixture starts with the file it will drop',
                      victim in (m.get('files') or [])
                      and (base / 'tools' / victim).is_file()))

        # A file the engine NEVER vendored, sitting in the same directory.
        # Nothing may touch this, ever.
        own = base / 'tools' / 'this_repos_own_tool.py'
        own.write_text('# not the engine\'s\n', encoding='utf-8')

        # Simulate the drop by rewriting the PREVIOUS manifest to claim one
        # more file than the current KINDS list has -- which is exactly the
        # shape a real rename leaves behind.
        extra = 'precedent_retired_name.py'
        (base / 'tools' / extra).write_text('# stale vendored tool\n', encoding='utf-8')
        m['files'] = list(m.get('files') or []) + [extra]
        m.setdefault('sha256', {})[extra] = hashlib.sha256(
            (base / 'tools' / extra).read_bytes()).hexdigest()
        (base / 'tools' / 'ENGINE_MANIFEST.json').write_text(
            _json.dumps(m, indent=2), encoding='utf-8')

        r = subprocess.run(
            [sys.executable, str(base / 'tools' / 'precedent_vendor_engine.py'),
             'refresh', str(ROOT), '--force', '--from-ref', 'HEAD'],
            capture_output=True, text=True, timeout=600, cwd=str(base), env=env)
        out = r.stdout + r.stderr

        cases.append(('a file the current set no longer includes is deleted',
                      not (base / 'tools' / extra).exists()))
        cases.append(('and the run says which file went, and why it was safe',
                      extra in out and 'no longer includes' in out))
        cases.append(("a file the engine never vendored is UNTOUCHED -- the "
                      "manifest is what makes this safe", own.is_file()))
        cases.append(('a file still in the set survives',
                      (base / 'tools' / victim).is_file()))

        # NEGATIVE CONTROL on the hand-edit rule: a dropped file whose
        # content no longer matches what was vendored is kept, not deleted.
        base2 = _consumer(tmp / 'edited')
        if base2 is not None:
            m2 = _manifest(base2)
            (base2 / 'tools' / extra).write_text('# stale\n', encoding='utf-8')
            m2['files'] = list(m2.get('files') or []) + [extra]
            m2.setdefault('sha256', {})[extra] = 'deadbeef' * 8   # wrong on purpose
            (base2 / 'tools' / 'ENGINE_MANIFEST.json').write_text(
                _json.dumps(m2, indent=2), encoding='utf-8')
            r2 = subprocess.run(
                [sys.executable, str(base2 / 'tools' / 'precedent_vendor_engine.py'),
                 'refresh', str(ROOT), '--force', '--from-ref', 'HEAD'],
                capture_output=True, text=True, timeout=600, cwd=str(base2), env=env)
            out2 = r2.stdout + r2.stderr
            cases.append(('a hand-edited dropped file is KEPT',
                          (base2 / 'tools' / extra).is_file()))
            cases.append(('and said so, rather than deleted silently',
                          'hand-edited' in out2))

    failed = [n for n, ok in cases if not ok]
    check(f'refresh removes engine files the set no longer includes, and only '
          f'those ({len(cases)} stated cases)', not failed, '; '.join(failed))


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


def check_commit_identity_prevents_the_wrong_offset():
    """The declared zone is made TRUE for the session, not merely enforced.

    Three mechanisms already existed and every one of them acts after git has
    resolved an offset: the pre-commit backstop refuses the commit, the
    prepare-commit-msg twin refuses the merge, and the settings.local.json
    derivation applies from the NEXT session because the harness reads
    environment before hooks run. So on a fresh container's first commit --
    the case that matters -- the person is told to retype `TZ=... git commit`
    and the wrong offset was produced in the first place. Asked 2026-09-08:
    "why do we have it do the wrong offset and block it rather than prevent
    the wrong offset?" -- and the honest answer was that nothing prevented it.

    git falls back to the SYSTEM zone when TZ is unset, and the system zone is
    the one lever a hook can move mid-session that every later shell, tool and
    `git merge` picks up without cooperating. So the hook repoints it.

    Measured here that day: the container's zone was Etc/UTC, TZ was unset in
    every tool shell, and .claude/settings.local.json already declared the
    right zone and was inert.

    The two must-not-do cases are the point of the test, not the happy path.
    A GUESSED zone is never written to the machine -- it is not enforced for
    the same reason, and moving a container's clock on a guess is worse than
    a warning. And an unwritable clock must WARN and name the fallback, never
    fall through claiming success.
    """
    import tempfile, json as _json
    hook = ROOT / '.claude' / 'hooks' / 'commit-identity.sh'
    if not hook.exists():
        not_applicable('commit-identity prevents the wrong offset',
                       '.claude/hooks/commit-identity.sh is not present here')
        return

    ZONE = 'America/Argentina/Buenos_Aires'
    if not pathlib.Path('/usr/share/zoneinfo', ZONE).exists():
        not_applicable('commit-identity prevents the wrong offset',
                       f'no zoneinfo for {ZONE} on this machine')
        return

    def _env(home, localtime, now='UTC'):
        e = dict(os.environ)
        # Hermetic on every axis the hook writes: the clock, the global git
        # config, the global hooks dir, and the user-level config it would
        # otherwise resolve a REAL declared zone from.
        e['HOME'] = home
        e['PRECEDENT_LOCALTIME'] = localtime
        e['PRECEDENT_GLOBAL_HOOKS'] = os.path.join(home, 'git-hooks')
        e['PRECEDENT_USER_CONFIG'] = '/nonexistent/precedent-config.json'
        e.pop('PRECEDENT_COMMIT_TZ', None)
        # And what the container's clock currently READS, which the hook
        # compares against before deciding to act. Without pinning this, the
        # test passes only while the machine is on some OTHER zone: the first
        # full-harness run after the fix landed reported four failures, purely
        # because the fix had already put this container on the declared zone
        # and the hook was correctly doing nothing.
        e['TZ'] = now
        return e

    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        def _repo(name, zone):
            base = tmp / name
            base.mkdir(parents=True)
            subprocess.run(['git', '-C', str(base), 'init', '-q'],
                           capture_output=True)
            if zone:
                (base / 'identity.json').write_text(_json.dumps(
                    {'name': 'T', 'email': 't@example.com',
                     'timezone': zone}), encoding='utf-8')
            return base

        # 1. a DECLARED zone repoints the clock.
        declared = _repo('declared', ZONE)
        home = str(tmp / 'h1'); os.makedirs(home)
        lt = str(tmp / 'lt1')
        r = subprocess.run(['bash', str(hook)], capture_output=True, text=True,
                           timeout=120,
                           env=dict(_env(home, lt), CLAUDE_PROJECT_DIR=str(declared)))
        cases.append(('a declared zone repoints the system zone file',
                      os.path.islink(lt)
                      and os.readlink(lt) == f'/usr/share/zoneinfo/{ZONE}'))
        cases.append(('and says what it did, and why it is prevention',
                      'prevention' in r.stderr and ZONE in r.stderr))

        # 2. an UNRESOLVED zone repoints the clock too, to the declared
        # fallback. Reversed 2026-09-09 (practice: timestamps-carry-offset):
        # this used to assert the machine was left alone, which in practice
        # meant left on the container's UTC. See the fallback's own note in
        # precedent.json for why applying beats abstaining, and why applying
        # is still not enforcing.
        guessed = _repo('guessed', None)
        home = str(tmp / 'h2'); os.makedirs(home)
        lt2 = str(tmp / 'lt2')
        r2 = subprocess.run(['bash', str(hook)], capture_output=True, text=True,
                            timeout=120,
                            env=dict(_env(home, lt2), CLAUDE_PROJECT_DIR=str(guessed)))
        cases.append((f'an unresolved zone repoints the clock to the fallback '
                      f'({_declared_fallback_tz()})',
                      os.path.islink(lt2) and os.readlink(lt2)
                      == f'/usr/share/zoneinfo/{_declared_fallback_tz()}'))
        cases.append(('and names it a fallback rather than this person\'s zone',
                      'DECLARED FALLBACK' in r2.stderr))
        # The line that must NOT move: applied is not enforced. A hook run
        # that resolved no zone leaves the pre-commit backstop with no
        # offset to refuse on.
        pre = pathlib.Path(guessed) / '.git' / 'hooks' / 'pre-commit'
        cases.append(('and the backstop still refuses no offset, because '
                      'nobody declared one',
                      pre.exists()
                      and 'expected_offset=""' in pre.read_text(encoding='utf-8')))

        # 3. an unreachable clock warns and names the fallback. A missing
        # parent dir, not a chmod: this runs as root in the container, where
        # a chmod control would pass for the wrong reason.
        home = str(tmp / 'h3'); os.makedirs(home)
        r3 = subprocess.run(
            ['bash', str(hook)], capture_output=True, text=True, timeout=120,
            env=dict(_env(home, str(tmp / 'no-such-dir' / 'lt3')),
                     CLAUDE_PROJECT_DIR=str(declared)))
        cases.append(('an unwritable clock warns rather than claiming success',
                      'not writable' in r3.stderr
                      and 'prevention' not in r3.stderr))
        cases.append(('and names the backstop as what still catches it',
                      'backstop will refuse' in r3.stderr))

        # 4. already on the declared zone: no write, no message. A hook that
        # announces itself every session is one people stop reading.
        home = str(tmp / 'h4'); os.makedirs(home)
        lt4 = str(tmp / 'lt4')
        r4 = subprocess.run(
            ['bash', str(hook)], capture_output=True, text=True, timeout=120,
            env=dict(_env(home, lt4, now=ZONE), CLAUDE_PROJECT_DIR=str(declared)))
        cases.append(('a clock already on the declared zone is left alone, '
                      'silently', not os.path.lexists(lt4)
                      and 'system timezone was' not in r4.stderr))

    failed = [n for n, ok in cases if not ok]
    check(f'commit-identity prevents the wrong offset, not only refuses it '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_source_clone_is_pinned_to_a_branch():
    """A source clone must not ask the remote which branch to use.

    `git clone <url> <dir>` with no --branch checks out whatever the server's
    HEAD symref names -- a setting on a web page, invisible to every tool
    here. 2026-09-09: two practice-source repositories had that setting
    pointed at a feature branch, so every session-start clone of them landed
    on an older tree, and a plain sync from a consuming repo would have
    written that older text over newer committed text, deleting a practice's
    Story block and a clause of its Rule, reporting success. The consuming
    repo had never been stale.

    Three cases, and the third is the one that decides whether the fix is
    safe rather than merely effective: a source clone can be somebody's
    working copy, and a pin that quietly moves a dirty checkout would trade
    one silent loss for another."""
    import tempfile
    import precedent_source_bootstrap as psb

    def git(cwd, *a):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        return subprocess.run(['git', '-C', str(cwd), *a], capture_output=True,
                              text=True, env=env)

    def branch_of(p):
        return git(p, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()

    cases = []
    with tempfile.TemporaryDirectory() as td:
        W = pathlib.Path(td)
        src = W / 'src'
        src.mkdir()
        git(src, 'init', '-q', '-b', 'main')
        (src / 'rule.md').write_text('old\n', encoding='utf-8')
        git(src, 'add', '-A')
        git(src, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', 'a')
        git(src, 'branch', 'claude/feature')
        (src / 'rule.md').write_text('NEWER, with the Story block\n', encoding='utf-8')
        git(src, 'add', '-A')
        git(src, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', 'b')
        # The measured situation: the server's default is a feature branch
        # whose tree is behind main.
        git(src, 'symbolic-ref', 'HEAD', 'refs/heads/claude/feature')
        url = f'file://{src}'

        clone = W / 'clone'
        ok, out = psb._try_sync(url, clone)
        cases.append((f'a fresh clone lands on the pinned branch, not the '
                      f'remote\'s default (got {branch_of(clone)!r}, {out!r})',
                      ok and branch_of(clone) == 'main'))
        cases.append(('and therefore has the newer content the default branch '
                      'lacks',
                      'Story block' in (clone / 'rule.md').read_text(encoding='utf-8')))

        # An existing clone already sitting wrong: the half that made the real
        # incident persist, since `git pull --ff-only` pulls whatever branch
        # the checkout is on.
        git(clone, 'checkout', '-q', 'claude/feature')
        ok, out = psb._try_sync(url, clone)
        cases.append((f'an existing clone on the wrong branch is put back '
                      f'(got {branch_of(clone)!r}, {out!r})',
                      ok and branch_of(clone) == 'main'))

        git(clone, 'checkout', '-q', 'claude/feature')
        (clone / 'rule.md').write_text('work nobody committed\n', encoding='utf-8')
        ok, out = psb._try_sync(url, clone)
        cases.append(('a wrong-branch clone with uncommitted work is REFUSED, '
                      'naming both branches, not silently moved',
                      (not ok) and 'claude/feature' in out and "'main'" in out))
        cases.append(('and that uncommitted work is still there',
                      'work nobody committed' in
                      (clone / 'rule.md').read_text(encoding='utf-8')))

        # THE ONE CASE THE PIN GIVES WAY. A source whose only branch is
        # named something else must still clone: git's default branch name is
        # per-machine, so whoever created that set may never have decided it,
        # and refusing would take its practices out of force for a naming
        # accident. Distinct from the incident, where the pinned branch DID
        # exist and the remote's default named a different one.
        other = W / 'other'
        other.mkdir()
        git(other, 'init', '-q', '-b', 'master')
        (other / 'r.md').write_text('x\n', encoding='utf-8')
        git(other, 'add', '-A')
        git(other, '-c', 'user.email=f@x', '-c', 'user.name=f', 'commit', '-qm', 'a')
        oc = W / 'other-clone'
        ok, out = psb._try_sync(f'file://{other}', oc)
        cases.append((f'a source with no branch of that name clones anyway '
                      f'rather than falling out of force (got '
                      f'{branch_of(oc) if oc.exists() else None!r}, {out!r})',
                      ok and branch_of(oc) == 'master'))

    failed = [n for n, ok in cases if not ok]
    check(f'a source clone is pinned to a branch rather than asking the '
          f'remote ({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_generator_wires_every_template_guard_mode():
    """The generator must not fall behind the adapter template again.

    Three files describe how session hooks get wired: the adapter template
    at templates/harness/claude-code/settings.json, whose own _comment calls
    itself the canonical wiring; this repo's .claude/settings.json,
    dogfooding it; and _install_session_hooks() in
    precedent_bootstrap_source.py, which is what a newly bootstrapped source
    actually receives. The third fell behind the first around 2026-09-06 --
    it wired SessionStart and PreToolUse and not UserPromptSubmit -- so every
    set bootstrapped after that date silently lacked the freshness guard's
    `user-prompt` mode. That is the only mode that keeps firing: SessionStart
    is spent at the start and pre-write at the first write, so a session left
    open across a break has spent both and nothing rechecks the checkout
    however far origin moves underneath it. All five real downstream sets sat
    in that state for days and none of them knew.

    NOT strict equality, deliberately. The adapter legitimately wires MORE
    than the generator installs -- a Stop hook, session-start.sh,
    precedent-paths.sh -- so asserting the same event set would fail on
    arrival and force an unrelated design decision about which of those a
    bootstrapped set should get. The assertion is CONTAINMENT of the guard's
    modes, plus commit-identity.sh wired on both sides.

    Modes, never whole command strings: the base branch is passed explicitly
    and differs per repo on purpose -- this repo's own base is
    precedent-beta-v01, not main -- so comparing commands would report that
    deliberate difference as drift.

    Both sides are derived at runtime. A hardcoded list of expected modes
    would be a FOURTH copy of this wiring, and copies of this wiring drifting
    from one another is the exact failure being checked."""
    import tempfile
    import precedent_bootstrap_source as pbs
    cases = []
    want = pbs._template_guard_modes()
    cases.append(('the adapter template wires at least one guard mode, so '
                  'there is something to compare against', bool(want)))
    with tempfile.TemporaryDirectory() as td:
        dest = pathlib.Path(td)
        pbs._install_session_hooks(dest, 'main')
        have = pbs._source_guard_modes(dest)
        gap = sorted(want - have)
        cases.append((f'the generator wires every guard mode the adapter '
                      f'does (missing: {gap or "none"})', not gap))

        settings = dest / '.claude' / 'settings.json'
        tmpl_text = (ROOT / 'templates' / 'harness' / 'claude-code'
                     / 'settings.json').read_text(encoding='utf-8')
        gen_text = settings.read_text(encoding='utf-8')
        cases.append(('commit-identity.sh is wired by the adapter and by the '
                      'generator alike',
                      'commit-identity.sh' in tmpl_text
                      and 'commit-identity.sh' in gen_text))

        # A hook that is not executable silently never runs, which is why
        # _install_session_hooks chmods; assert the property, not the call.
        cases.append(('both installed hooks are executable',
                      all(os.access(dest / '.claude' / 'hooks' / n, os.X_OK)
                          for n in pbs.SESSION_HOOKS)))

        # The negative control, run rather than asserted in a report: with
        # the UserPromptSubmit block taken back out, the comparison above has
        # to name exactly the mode that went (practice:
        # control-asserts-which-failure -- a check that cannot fail is not a
        # check, and "it failed" is not evidence it failed for the reason
        # claimed).
        data = json.loads(gen_text)
        data['hooks'].pop('UserPromptSubmit', None)
        settings.write_text(json.dumps(data), encoding='utf-8')
        reverted = sorted(want - pbs._source_guard_modes(dest))
        cases.append((f'with the UserPromptSubmit wiring removed the same '
                      f'comparison names exactly user-prompt (got '
                      f'{reverted})', reverted == ['user-prompt']))

    failed = [n for n, ok in cases if not ok]
    check(f'the generator wires every guard mode the adapter template does '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_verify_reports_a_source_wired_for_fewer_moments():
    """verify() asked whether a hook RUNS and never at which moments, so a
    source wired for fewer moments than the adapter wires it for audited
    perfectly clean. That is structurally why the five downstream sets sat
    mis-wired for days: the check that should have caught it could not.

    The three cases below are the ones that decide whether the fix is right
    rather than merely present -- a wiring check is easy to write in a way
    that is correct on the standard layout and wrong everywhere else."""
    import tempfile
    import precedent_bootstrap_source as pbs

    def _wiring_findings(root, cmds):
        (root / '.claude').mkdir(parents=True, exist_ok=True)
        (root / '.claude' / 'settings.json').write_text(json.dumps(
            {'hooks': {'SessionStart': [{'hooks': [
                {'type': 'command', 'command': c} for c in cmds]}]}}),
            encoding='utf-8')
        return [m for m in pbs.verify('team', root) if 'NOT WIRED' in m]

    D = '$CLAUDE_PROJECT_DIR'
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # 1. PATH INDEPENDENCE. The individual set wires its guard from a
        # tracked bootstrap/ directory rather than .claude/hooks/, on purpose
        # -- one copy, nothing to drift from it -- and its own practice
        # documents that layout. A check that reads the directory instead of
        # the declared command calls that set broken, which would make the
        # check wrong rather than the set.
        a = tmp / 'bootstrap-layout'
        found = _wiring_findings(a, [
            f'{D}/bootstrap/freshness-guard.sh {m} main'
            for m in sorted(pbs._template_guard_modes())])
        cases.append((f'a source wiring every mode from bootstrap/ rather '
                      f'than .claude/hooks/ is clean (got {found})', not found))

        # 2. THE NEGATIVE CASE. One mode removed, and the finding has to name
        # that mode -- not merely be non-empty.
        b = tmp / 'missing-user-prompt'
        found = _wiring_findings(b, [
            f'{D}/.claude/hooks/freshness-guard.sh session-start main',
            f'{D}/.claude/hooks/freshness-guard.sh pre-write main'])
        cases.append((f'a source missing one mode is reported, naming that '
                      f'mode (got {found})',
                      len(found) == 1 and 'user-prompt' in found[0]
                      and 'NOT WIRED' in found[0]))

        # 3. DIRECTION. want - have, never the reverse: a source wiring more
        # than the adapter is doing something deliberate, not something broken.
        c = tmp / 'wires-extra'
        found = _wiring_findings(c, [
            f'{D}/.claude/hooks/freshness-guard.sh {m} main'
            for m in sorted(pbs._template_guard_modes()) + ['some-future-mode']])
        cases.append((f'a source wiring MORE modes than the adapter is not '
                      f'flagged (got {found})', not found))

    failed = [n for n, ok in cases if not ok]
    check(f'verify() reports a source wired for fewer moments than the '
          f'adapter ({len(cases)} stated cases)', not failed, '; '.join(failed))


def _declared_fallback_tz():
    """This repository's declared last-resort timezone, read from the engine
    rather than typed into a test.

    precedent_check.py's `timestamps-carry-offset` already asserts that
    precedent.json, precedent_time.FALLBACK_TZ and both copies of
    commit-identity.sh agree, so reading any one of them is reading all four
    -- and reading beats restating, which is what turned a one-line value
    change into two mystery failures once already."""
    import precedent_time
    return precedent_time.FALLBACK_TZ


def check_commit_identity_copies_are_identical():
    """The hook exists three times and every copy must be the same file.

    templates/harness/claude-code/hooks/ is what an adopter instantiates,
    .claude/hooks/ is what this repo runs on itself (a drift there is this
    repo failing to run what it ships), and the individual practice source
    carries a third copy that session-start.sh runs for ATTACHED repos, whose
    own hooks never fire. 2026-09-07 the merge backstop -- the fix for git
    not running pre-commit on a merge commit, which is how a wrong-offset
    commit reached main in the first place -- was added to the individual
    source's copy alone and sat there unpropagated for hours, so the repo
    that defines the fix did not have it. parallel-artifact-ledger names this
    exact shape; this makes it mechanical instead.
    """
    import hashlib as _h
    here = ROOT / '.claude' / 'hooks' / 'commit-identity.sh'
    tmpl = ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks' / 'commit-identity.sh'
    if not (here.exists() and tmpl.exists()):
        not_applicable('every copy of commit-identity.sh is byte-identical',
                       'not every copy is present in this tree')
        return
    digests = {p: _h.sha256(p.read_bytes()).hexdigest()
               for p in (here, tmpl)}
    # The individual source is outside this repo and only sometimes attached,
    # so it is compared when reachable and skipped -- named -- when not.
    #
    # WHICH clone of the individual source. There are routinely two on one
    # machine and they are not interchangeable: the config-named one
    # (~/.config/precedent/config.json), which precedent-individual-bootstrap.sh
    # `git pull --ff-only`s from origin at every session start, and an
    # ATTACHED sibling beside this repo, which is the one a session actually
    # edits and pushes from. The attached one therefore wins here. Comparing
    # against the config-named clone instead reports drift for every
    # uncommitted edit in progress -- which this check did on its very first
    # run, against a change being made three directories away. That is the
    # same two-clone trap AGENTS.md's gotchas section already records; the
    # rule that resolves it is: the pulled clone can only ever be BEHIND, so
    # it is never the better evidence of what the source says.
    third, note = None, ''
    try:
        import json as _json
        cfg = pathlib.Path(os.environ.get(
            'PRECEDENT_USER_CONFIG',
            str(pathlib.Path.home() / '.config' / 'precedent' / 'config.json')))
        path = None
        if cfg.exists():
            path = (_json.loads(cfg.read_text(encoding='utf-8'))
                    .get('individual') or {}).get('path')
        cands = []
        if path:
            attached = ROOT.parent / pathlib.Path(path).name
            if attached != ROOT and attached.is_dir():
                cands.append(attached)
            cands.append(pathlib.Path(path))
        for base in cands:
            cand = base / 'bootstrap' / 'commit-identity.sh'
            if cand.exists():
                third = cand
                digests[cand] = _h.sha256(cand.read_bytes()).hexdigest()
                break
    except Exception:
        pass

    # EVERY OTHER ATTACHED SOURCE'S COPY, and this is where the check had a
    # hole. It compared three copies -- this repo's two and the individual
    # source's -- and a TEAM set carries one too, at .claude/hooks/. Nothing
    # looked there, so both team sets sat three generations behind
    # (2026-09-07: missing the merge backstop, the timezone derivation AND
    # the global identity fix) while this check reported every copy
    # identical. A check that names the copies it compares is only as good
    # as that list, so the list is now discovered rather than written down.
    for sib in sorted(ROOT.parent.glob('precedent-team-*')):
        cand = sib / '.claude' / 'hooks' / 'commit-identity.sh'
        if cand.exists():
            digests[cand] = _h.sha256(cand.read_bytes()).hexdigest()
    if third is None:
        note = (' (the individual source\'s copy was not reachable from here '
                'and was NOT compared)')
    uniq = set(digests.values())
    check(f'every reachable copy of commit-identity.sh is byte-identical '
          f'({len(digests)} copies found){note}',
          len(uniq) == 1,
          '; '.join(f'{p.relative_to(ROOT) if ROOT in p.parents else p}='
                    f'{d[:12]}' for p, d in digests.items()))


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
        return repo

    def _run(repo, clone, override=False):
        env = dict(os.environ)
        env.pop('PRECEDENT_ALLOW_PINNED_UPDATE', None)
        if override:
            env['PRECEDENT_ALLOW_PINNED_UPDATE'] = '1'
        script = repo / 'process' / 'upstream' / 'tools' / 'checkin.py'
        r = subprocess.run([sys.executable, str(script), 'update', str(clone)],
                           capture_output=True, text=True, cwd=str(repo),
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

        _, out = _run(repo, clone, override=True)
        cases.append(('the override gets past the hold',
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

    failed = [n for n, ok in cases if not ok]
    check(f'a leftover pre-migration practice pack is flagged after migration '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


def check_identity_reaches_a_repo_that_did_not_exist_yet():
    """The commit identity covers repos ATTACHED AFTER the hook ran.

    Three wrong-author incidents in two days, each "fixed", each recurring,
    because every fix was aimed at the wrong scope. A SessionStart hook
    configures the checkouts that exist when it fires. A repository attached
    mid-turn with `add_repo`, cloned, or `git init`ed during the session was
    never seen by that pass -- and inherits the container's GLOBAL identity,
    which is the agent bot account. The per-checkout fix cannot cover it even
    in principle, and no amount of care in the session can either: the third
    incident happened to a session that had already written two documents
    about the first two.

    Measured rather than reasoned about, 2026-09-07: `git config --global
    user.email` read `noreply@anthropic.com`, and a repository created
    seconds later committed as `Claude <noreply@anthropic.com>`.

    So the identity is set GLOBALLY, and a backstop is installed at
    `core.hooksPath`, which is the one hook location that reaches a
    repository that does not exist yet.

    THE TWO CASES THAT MUST NOT FIRE are what make it safe. `core.hooksPath`
    makes git look there AND NOWHERE ELSE, so a global hooks directory
    silently disables every repository's own `.git/hooks/*` -- a worse bug
    than the one being fixed. Each hook therefore chains to the repository's
    own hook of the same name first. And a merely INFERRED identity is never
    written globally: a guess in global config follows the user into every
    unrelated repository on the machine.

    practice: control-asserts-which-failure. The chaining case caught its own
    fixture: it planted the "repository's own" hook via
    `rev-parse --git-path hooks`, which RESPECTS core.hooksPath, so with the
    backstop installed it wrote into the global directory and the test failed
    against a working chain. `--absolute-git-dir` is the resolution that
    means what it says.
    """
    import tempfile
    script = ROOT / '.claude' / 'hooks' / 'commit-identity.sh'
    if not script.exists():
        not_applicable('the commit identity reaches a later-attached repo',
                       '.claude/hooks/commit-identity.sh is not present here')
        return

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        home = tmp / 'home'
        home.mkdir()
        env = dict(os.environ)
        env['HOME'] = str(home)
        env['PRECEDENT_USER_CONFIG'] = '/nonexistent/precedent-config.json'
        env.pop('PRECEDENT_ALLOW_ANY_AUTHOR', None)
        env.pop('PRECEDENT_COMMIT_EMAIL', None)
        env.pop('PRECEDENT_COMMIT_TZ', None)
        ZONE = 'America/Argentina/Buenos_Aires'

        def g(*a, cwd=None):
            return subprocess.run(['git'] + list(a), capture_output=True,
                                  text=True, env=env,
                                  cwd=str(cwd) if cwd else None, timeout=120)

        # The container's starting condition, reproduced.
        g('config', '--global', 'user.name', 'Claude')
        g('config', '--global', 'user.email', 'noreply@anthropic.com')

        src = tmp / 'individual'
        src.mkdir()
        g('init', '-q', str(src))
        (src / 'identity.json').write_text(
            '{"name":"Morgan F","email":"m@example.com","timezone":"%s"}' % ZONE,
            encoding='utf-8')
        r = subprocess.run(['bash', str(script)], capture_output=True, text=True,
                           env=dict(env, CLAUDE_PROJECT_DIR=str(src)), timeout=180)
        first = r.stderr

        cases = [
            ('the global identity stops being the bot',
             g('config', '--global', 'user.email').stdout.strip() == 'm@example.com'),
            ('and the displacement is announced',
             'GLOBAL git identity was the container' in first),
        ]

        # THE REGRESSION: a repository that did not exist when the hook ran.
        later = tmp / 'attached-later'
        later.mkdir()
        g('init', '-q', str(later))
        (later / 'f').write_text('x', encoding='utf-8')
        g('add', 'f', cwd=later)
        subprocess.run(['git', 'commit', '-q', '-m', 'later'], cwd=str(later),
                       capture_output=True, text=True,
                       env=dict(env, TZ=ZONE), timeout=120)
        cases.append(('a repo created AFTER the hook commits as the person',
                      g('log', '-1', '--format=%ae', cwd=later).stdout.strip()
                      == 'm@example.com'))

        # The backstop still refuses if something overrides identity anyway.
        g('config', 'user.email', 'noreply@anthropic.com', cwd=later)
        (later / 'g').write_text('y', encoding='utf-8')
        g('add', 'g', cwd=later)
        r = subprocess.run(['git', 'commit', '-m', 'bot'], cwd=str(later),
                           capture_output=True, text=True,
                           env=dict(env, TZ=ZONE), timeout=120)
        out = r.stdout + r.stderr
        cases.append(('a bot-authored commit is refused there',
                      "container's own agent account" in out))
        cases.append(('and the refusal names itself as the global backstop',
                      'GLOBAL backstop' in out))

        g('config', 'user.email', 'm@example.com', cwd=later)
        r = subprocess.run(['git', 'commit', '-m', 'tz'], cwd=str(later),
                           capture_output=True, text=True,
                           env=dict(env, TZ='UTC'), timeout=120)
        cases.append(('a wrong-offset commit is refused there',
                      'declared timezone' in (r.stdout + r.stderr)))
        r = subprocess.run(['git', 'commit', '-q', '-m', 'ok'], cwd=str(later),
                           capture_output=True, text=True,
                           env=dict(env, TZ=ZONE), timeout=120)
        cases.append(('a correct commit is not blocked', r.returncode == 0))

        # MUST NOT FIRE 1: a repository's own hook is not disabled.
        own = tmp / 'own-hooks'
        own.mkdir()
        g('init', '-q', str(own))
        hd = pathlib.Path(g('rev-parse', '--absolute-git-dir',
                            cwd=own).stdout.strip()) / 'hooks'
        hd.mkdir(parents=True, exist_ok=True)
        (hd / 'pre-commit').write_text(
            '#!/bin/sh\necho "REPO OWN HOOK RAN" >&2\nexit 1\n', encoding='utf-8')
        (hd / 'pre-commit').chmod(0o755)
        (own / 'f').write_text('z', encoding='utf-8')
        g('add', 'f', cwd=own)
        r = subprocess.run(['git', 'commit', '-m', 'chain'], cwd=str(own),
                           capture_output=True, text=True,
                           env=dict(env, TZ=ZONE), timeout=120)
        out = r.stdout + r.stderr
        cases.append(("a repository's OWN pre-commit hook still runs",
                      'REPO OWN HOOK RAN' in out))
        cases.append(('and its refusal is still honoured',
                      not g('log', '--oneline', cwd=own).stdout.strip()))

        # MUST NOT FIRE 2: a GUESSED identity never reaches global config.
        g('config', '--global', '--unset', 'core.hooksPath')
        g('config', '--global', 'user.email', 'noreply@anthropic.com')
        bare = tmp / 'bare'
        bare.mkdir()
        g('init', '-q', str(bare))
        r = subprocess.run(['bash', str(script)], capture_output=True, text=True,
                           env=dict(env, CLAUDE_PROJECT_DIR=str(bare)), timeout=180)
        cases.append(('a GUESSED identity is not written globally',
                      g('config', '--global', 'user.email').stdout.strip()
                      == 'noreply@anthropic.com'))
        cases.append(('and the hook still exits 0', r.returncode == 0))

    failed = [n for n, ok in cases if not ok]
    check(f'the commit identity reaches a repo attached after the hook ran '
          f'({len(cases)} stated cases)', not failed, '; '.join(failed))


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
                      allowed.get('acct/named-on-purpose') == 'declared source'))

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
        cases.append(('and names what still guards the export path',
                      'practice_audit' in out))

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

        # visibility DECLARED, not defaulted: this fixture is a PRIVATE
        # consumer, which is the case it exercises -- all four sources
        # materialized into one tracked tree. An undeclared visibility now
        # counts as public (build_views.repo_is_public), which would
        # correctly withhold the team and individual sources and make this
        # test assert the wrong thing for the right reason.
        (consumer / 'precedent.json').write_text(json.dumps({
            'visibility': 'private',
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': str(universal)},
                        {'level': 'team', 'name': 'precedent-team-fixture', 'path': str(team)},
                        {'level': 'repo-local', 'name': 'local', 'path': 'local'}]
        }), encoding='utf-8')
        user_cfg = tmp / 'user.json'
        user_cfg.write_text(json.dumps({
            'individual': {'name': 'precedent-individual', 'path': str(individual)}}), encoding='utf-8')
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
            'sources': [{'level': 'universal', 'name': 'precedent', 'path': '.'}]
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
        other = tmp / 'precedent-team-other'
        write_practice(selfref2 / 'practices' / 'shared.md', 'shared',
                        'HAND-AUTHORED -- MUST SURVIVE.')
        write_practice(other / 'practices' / 'shared.md', 'shared',
                        'TEAM VERSION.')
        (selfref2 / 'precedent.json').write_text(json.dumps({
            'sources': [{'level': 'team', 'name': 'precedent-team-other', 'path': str(other)},
                        {'level': 'universal', 'name': 'precedent', 'path': '.'}]
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
        # --- --check writes NOTHING (2026-09-06) --------------------------
        # It used to guard only the AGENTS.md write while materialize() ran
        # underneath it unconditionally, so the documented read-only drift
        # check rewrote practices/, tools/checks/ and MANIFEST.json every
        # time a session ran it. Found against a real four-source consumer,
        # where it made a genuine light-check failure vanish by overwriting
        # the drifted file, and -- with one source unreachable, the ordinary
        # state of a session before add_repo has run -- deleted 57 tracked
        # files while printing a check verdict. Both directions are pinned:
        # the clean case must not write, and the unreachable-source case
        # must not delete.
        run()  # take a clean sync first, so any later difference is the check's

        def snapshot():
            out = {}
            for sub in ('practices', 'tools'):
                d = consumer / sub
                for f in sorted(d.rglob('*')) if d.is_dir() else []:
                    if f.is_file():
                        out[str(f.relative_to(consumer))] = f.read_bytes()
            mf = consumer / 'MANIFEST.json'
            if mf.is_file():
                out['MANIFEST.json'] = mf.read_bytes()
            return out

        before = snapshot()
        rc_chk, out_chk = run('--check')
        cases.append(('--check on an already-synced repo exits 0',
                      rc_chk == 0, out_chk))
        cases.append(('--check writes nothing at all -- not practices/, not '
                      'tools/checks/, not MANIFEST.json',
                      snapshot() == before,
                      f'{len(set(before) ^ set(snapshot()))} file(s) added/removed'))

        # A source that cannot be reached is the ordinary state of a fresh
        # session, not an error state. --check must report it, never act on it.
        hidden = tmp / 't-hidden'
        team.rename(hidden)
        try:
            rc_gone, out_gone = run('--check')
            after_gone = snapshot()
        finally:
            hidden.rename(team)
        cases.append(('--check with a source unreachable FAILS rather than '
                      'reporting clean', rc_gone != 0, out_gone))
        cases.append(('--check with a source unreachable deletes nothing -- '
                      'the tree is byte-identical afterwards',
                      after_gone == before,
                      f'{len(set(before) - set(after_gone))} file(s) deleted'))
        cases.append(('and it names the missing practice rather than only '
                      'the loader block',
                      'team-fixture' in out_gone, out_gone))

        # Real drift must still be reported, or the two cases above could be
        # satisfied by a --check that reports nothing at all.
        victim = consumer / 'practices' / 'uni-fixture.md'
        victim.write_text(victim.read_text(encoding='utf-8') + '\nhand-edited\n',
                          encoding='utf-8')
        rc_drift, out_drift = run('--check')
        cases.append(('a hand-edited materialized practice is reported as '
                      'drift', rc_drift != 0 and 'uni-fixture' in out_drift,
                      out_drift))
        run()  # restore the fixture for the cases below

        # --- the OTHER writer of the same block must agree with this one ---
        # Both commands are documented for a consuming repo: session start
        # runs precedent_sync_views.py, and generated-artifact-provenance
        # runs `build_views.py --check` on every precedent_check.py. They
        # rendered different header lines for the same catalogue ("6 of 61
        # practices (6 universal)" vs "6 of 61 practices"), because only
        # sync_views passed source_levels -- a permanent, unresolvable
        # "hand-edited or stale" report in every consuming repo, whichever
        # ran last. build_views.py now reads the levels back out of
        # MANIFEST.json, so the two agree by construction.
        bv_tool = str(ROOT / 'tools' / 'build_views.py')
        subprocess.run([sys.executable, sync_tool, '--repo', str(consumer)],
                       capture_output=True, text=True)
        r_agree = subprocess.run([sys.executable, bv_tool, '--repo', str(consumer),
                                  '--agents-only', '--check'],
                                 capture_output=True, text=True)
        cases.append(('build_views.py --check agrees with the block '
                      'precedent_sync_views.py just wrote (one loader block, '
                      'two documented writers)',
                      r_agree.returncode == 0, r_agree.stdout + r_agree.stderr))
        before_agents = (consumer / 'AGENTS.md').read_text(encoding='utf-8')
        subprocess.run([sys.executable, bv_tool, '--repo', str(consumer),
                        '--agents-only'], capture_output=True, text=True)
        cases.append(('and running build_views.py for real changes nothing',
                      (consumer / 'AGENTS.md').read_text(encoding='utf-8')
                      == before_agents))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2] if len(c) > 2 else '') for c in cases if not c[1]]
    check(f'precedent_sync_views.py syncs a consuming repo across all four '
          f'sources ({len(cases)} stated cases: clean sync, both resident '
          f'sources shown, correct level-of-resident counting, occasion '
          f'index reaches on-demand practices, --check both directions, a '
          f'self-referential source is refused rather than crashed or '
          f'silently overwritten, alone or shadowed, and build_views.py '
          f'--check agrees with what this tool wrote)',
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
            # practice: match-parsed-id-not-prefix -- `glob(f'{slug}-*.md')`
            # also matches every LONGER slug sharing this one's prefix, so
            # this helper could hand back a different candidate entirely.
            # It is the exact bug the prefix case below tests for, in the
            # helper that builds that case's fixtures; the call site there
            # had already been hand-narrowed to 'prefix-2*.md' to work
            # around it, which is the workaround that names the defect.
            # Matched on each file's own parsed slug instead.
            found = []
            for f in sorted((repo / 'candidates').glob('*.md')):
                fm, _sections = sp._read_practice_file(f)
                if (fm.get('slug') or '').strip('" ') == slug:
                    found.append(f)
            if not found:
                raise RuntimeError(
                    f"fixture candidate for slug {slug!r} was created but no "
                    f"candidates/*.md parses back to that slug")
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
        # The short slug's own file, kept from its own creation. This line
        # used to be a hand-narrowed `glob('pipeline-fixture-prefix-2*.md')`
        # -- a workaround for make_candidate() globbing by prefix and handing
        # back the LONGER candidate created just below. The helper matches on
        # each file's parsed slug now, so no narrowing is needed and the test
        # no longer contains a private instance of the bug it tests for.
        # ORDER MATTERS, and is the negative control. The LONGER slug is
        # created first, so a prefix glob (`glob(f'{slug}-*.md')`, sorted,
        # last) hands back 'pipeline-fixture-prefix-longer-<date>.md' when
        # asked for the short slug -- 'l' sorts after the date's '2'. Created
        # the other way round, the old prefix-matching helper returns the
        # right file by luck and this case proves nothing. Reordered
        # 2026-09-06, after a control run showed exactly that: reverting the
        # helper to the prefix glob still passed.
        make_candidate('pipeline-fixture-prefix-longer', recurrence=1,
                        **{'cost-if-once': 'unrelated candidate, shares a slug prefix'})
        f_prefix = make_candidate('pipeline-fixture-prefix', recurrence=1)
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
        team_repo = tmp / 'precedent-team-fixture'
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
                        '--name', 'precedent-individual', '--dest', str(indiv_dest))
        cases.append(('bootstrapping an individual set succeeds and writes its files',
                      rc == 0 and (indiv_dest / 'practices' / 'example-starter.md').is_file()
                      and (indiv_dest / 'config.json.sample').is_file(), out))

        rc, out = pyrun(bootstrap_tool, '--level', 'team',
                        '--name', 'precedent-team-harness-fixture', '--dest', str(team_dest))
        cases.append(('bootstrapping a team set without --approver is refused',
                      rc == 1 and 'approver' in out, out))

        rc, out = pyrun(bootstrap_tool, '--level', 'team',
                        '--name', 'precedent-team-harness-fixture', '--dest', str(team_dest),
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
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_bootstrap_source_engine_is_functional():
    """spec/BOOTSTRAP_NEW_SOURCES.md's newer claim, tested rather than
    trusted: precedent_bootstrap_source.py's output carries a real, working
    engine (tools/precedent_vendor_engine.py's seed()), not just files
    copied into place -- the same rigor check_materialize_bridges_loader()
    already applies to materialize()'s output, and check_bootstrap_source_
    produces_resolvable_set() above already applies to the practice content
    half of bootstrap's output. This is the engine half.

    Fixture: bootstrap one individual set, then run its OWN vendored copies
    of build_views.py/precedent_gate.py/precedent_paths.py/precedent_show.py
    IN PLACE (real subprocesses, cwd set to the bootstrapped dest, no --repo
    -- exactly how a source repo's own AGENTS.md tells a session to invoke
    them) against a second, fixture practice added after bootstrap, proving
    each command produces real output naming that practice -- not merely
    that the files exist and are byte-identical to something. Also asserts
    ENGINE_MANIFEST.json's recorded hashes actually match what got written
    (status() against this repo's own checkout must find zero drift right
    after a fresh seed), which is the property tools/precedent_vendor_
    engine.py's whole refresh-refusal mechanism depends on."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-bootstrap-engine-'))
    cases = []
    try:
        bootstrap_tool = str(ROOT / 'tools' / 'precedent_bootstrap_source.py')
        dest = tmp / 'engine-set'
        r = subprocess.run([sys.executable, bootstrap_tool, '--level', 'individual',
                            '--name', 'precedent-individual', '--dest', str(dest)],
                           capture_output=True, text=True)
        cases.append(('bootstrapping succeeds', r.returncode == 0, r.stdout + r.stderr))

        manifest_path = dest / 'tools' / 'ENGINE_MANIFEST.json'
        engine_files = ['build_views.py', 'precedent_gate.py', 'precedent_paths.py',
                        'precedent_show.py', 'split_practices.py',
                        'precedent_vendor_engine.py', 'routing_scope.json']
        cases.append(('every engine file is present',
                      all((dest / 'tools' / f).is_file() for f in engine_files),
                      str([f for f in engine_files if not (dest / 'tools' / f).is_file()])))
        cases.append(('ENGINE_MANIFEST.json exists and names the source repo',
                      manifest_path.is_file()
                      and 'BestPractice' in (manifest_path.read_text(encoding='utf-8')), ''))

        # -- the recorded sha256 for every file actually matches what's on
        # disk -- the exact property refresh()'s drift check relies on --
        import hashlib
        manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.is_file() else {}
        mismatched = [f for f, h in manifest.get('sha256', {}).items()
                     if hashlib.sha256((dest / 'tools' / f).read_bytes()).hexdigest() != h]
        cases.append(('every recorded sha256 matches the file actually written',
                      manifest.get('sha256') and not mismatched, str(mismatched)))

        # -- status(), run from the bootstrapped set's OWN vendored copy of
        # the tool, against this repo's real checkout, finds zero drift
        # immediately after a fresh seed --
        r = subprocess.run([sys.executable, str(dest / 'tools' / 'precedent_vendor_engine.py'),
                            'status', str(ROOT)], capture_output=True, text=True)
        cases.append(('status() against a real BestPractice checkout finds no drift '
                      'right after seeding', r.returncode == 0, r.stdout + r.stderr))


        # -- status() must not turn "this clone has no SOURCE_BRANCH" into
        # "upstream has moved". _git() discards exit codes, and a plain
        # `git rev-parse <missing-ref>` PRINTS THE REF NAME, so status() used to
        # bind clone_head='origin/<SOURCE_BRANCH>', find it != recorded, and
        # advise running `refresh` -- which, before refresh() became read-only,
        # would then check the reader's own BestPractice clone out onto
        # SOURCE_BRANCH. A false alarm wired to a destructive remedy. Fixed
        # 2026-09-06 while auditing every _git() call site in that tool.
        #
        # An initialized repo with no commits covers both halves at once: it has
        # no SOURCE_BRANCH, and its HEAD is unborn -- the one state where
        # `rev-parse HEAD` echoes 'HEAD' on stdout (a non-repo prints nothing,
        # which is why the plain form looked fine for years).
        norefs = tmp / 'clone-without-source-branch'
        norefs.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-C', str(norefs), 'init', '-q'], capture_output=True)
        r = subprocess.run([sys.executable, str(dest / 'tools' / 'precedent_vendor_engine.py'),
                            'status', str(norefs)], capture_output=True, text=True)
        status_out = r.stdout + r.stderr
        cases.append(('status() on a clone with no SOURCE_BRANCH reports COULD NOT VERIFY '
                      'and does NOT claim upstream has moved',
                      'COULD NOT VERIFY' in status_out
                      and 'has moved since this engine' not in status_out,
                      status_out))

        # -- and the resolver underneath it. seed() does
        # `_head_commit(ROOT) or 'unknown'`, so a truthy 'HEAD' was recorded as
        # ENGINE_MANIFEST.json's source_commit, after which every status() and
        # refresh() compared a real hash against the string "HEAD" and reported
        # upstream as moved, permanently.
        import precedent_vendor_engine as _pve
        cases.append(("_rev() returns '' for an unborn HEAD rather than the string 'HEAD', "
                      "so seed()'s `or 'unknown'` fallback actually fires",
                      _pve._rev(norefs, 'HEAD') == '' and _pve._head_commit(norefs) == '',
                      f"_rev={_pve._rev(norefs, 'HEAD')!r} "
                      f"_head_commit={_pve._head_commit(norefs)!r}"))

        # -- add a second, fixture practice AFTER bootstrap (example-starter
        # alone proves too little: its own occasion text could coincidentally
        # match without the loader actually parsing frontmatter) --
        (dest / 'practices' / 'engine-fixture-slug.md').write_text(
            '---\nslug: engine-fixture-slug\ntitle: Fixture\ntier: on-demand\n'
            'severity: default\napplies_to: ["fixture-only/**"]\n'
            'occasion: "testing the bootstrapped engine is functional"\n'
            'gates: []\nindex_clause: "engine-fixture-slug — a bootstrap-harness fixture"\n'
            'checked_by: null\ndefines: []\nstatus: active\nsupersedes: []\n'
            'overrides: null\nadded: 2026-09-05\n'
            'approved_by: "harness, 2026-09-05"\nsource_practice_number: null\n'
            '---\n## Rule\nA fixture-only rule, present in no other repo.\n\n'
            '## Why\nx\n\n## Story\nx\n\n## Install\nx\n', encoding='utf-8')
        (dest / 'AGENTS.md').write_text(
            '# fixture\n\n<!-- BEGIN GENERATED: precedent-loader -->\n'
            '<!-- END GENERATED -->\n', encoding='utf-8')

        # build_views.py --agents-only, run IN PLACE (no --repo), cwd == dest
        r = subprocess.run([sys.executable, 'tools/build_views.py', '--agents-only'],
                           capture_output=True, text=True, cwd=str(dest))
        agents_text = (dest / 'AGENTS.md').read_text(encoding='utf-8') if (dest / 'AGENTS.md').exists() else ''
        cases.append(('the vendored build_views.py, run in place with no --repo, '
                      'regenerates AGENTS.md naming the fixture practice',
                      r.returncode == 0 and 'engine-fixture-slug' in agents_text,
                      r.stdout + r.stderr))

        # precedent_gate.py --list, run in place
        r = subprocess.run([sys.executable, 'tools/precedent_gate.py', '--list'],
                           capture_output=True, text=True, cwd=str(dest))
        cases.append(('the vendored precedent_gate.py lists the real (trimmed) gate '
                      'vocabulary', r.returncode == 0 and 'merge' in r.stdout
                      and 'review' in r.stdout, r.stdout + r.stderr))

        # precedent_paths.py, run in place, against a path the fixture's
        # applies_to actually matches
        r = subprocess.run([sys.executable, 'tools/precedent_paths.py', 'fixture-only/x.md'],
                           capture_output=True, text=True, cwd=str(dest))
        cases.append(('the vendored precedent_paths.py matches the fixture practice by '
                      'its real applies_to glob', r.returncode == 0
                      and 'engine-fixture-slug' in r.stdout, r.stdout + r.stderr))

        # precedent_show.py, run in place
        r = subprocess.run([sys.executable, 'tools/precedent_show.py', 'engine-fixture-slug'],
                           capture_output=True, text=True, cwd=str(dest))
        cases.append(('the vendored precedent_show.py returns the fixture practice\'s '
                      'real Rule text', r.returncode == 0
                      and 'present in no other repo' in r.stdout, r.stdout + r.stderr))

        # -- refresh(), run from the bootstrapped set's OWN vendored copy of
        # the tool against this repo's real checkout, must leave that checkout
        # exactly where it stood. refresh() used to `git checkout
        # SOURCE_BRANCH` + `git pull` in the clone it reads FROM, which moved
        # the caller's repository: for a person, off the branch they were
        # working on; in CI, the workspace itself, mid-job, so every LATER
        # step in that job silently ran against SOURCE_BRANCH instead of the
        # commit under test. That is what PR #110 spent two rounds of
        # diagnosis on -- and `git status` stays clean the whole time (a
        # branch checkout leaves no dirty file to notice), which is why no
        # amount of content verification found it. Asserted against the real
        # ROOT on purpose: a fixture clone would not have caught the bug,
        # because the bug is precisely about which repo gets moved.
        def root_state():
            return tuple(subprocess.run(['git', '-C', str(ROOT)] + argv,
                                        capture_output=True, text=True).stdout.strip()
                         for argv in (['rev-parse', 'HEAD'],
                                      ['rev-parse', '--abbrev-ref', 'HEAD'],
                                      ['status', '--porcelain']))

        before = root_state()
        # --from-ref HEAD: vendor the tree under test, not whatever
        # origin/precedent-beta-v01 holds. Without it, adding a file to
        # ENGINE_FILES turns this case red until the addition is published,
        # and a contributor's stale local branch fails it with a message
        # about a missing engine file that has nothing to do with the
        # property this case actually asserts.
        r = subprocess.run([sys.executable, str(dest / 'tools' / 'precedent_vendor_engine.py'),
                            'refresh', str(ROOT), '--force', '--from-ref', 'HEAD'],
                           capture_output=True, text=True)
        after = root_state()
        cases.append(('refresh() against a real BestPractice checkout leaves its HEAD, '
                      'branch and working tree exactly as they were -- it reads blobs, '
                      'it never checks the clone out',
                      before == after,
                      f'before={before}\nafter={after}\n{r.stdout}{r.stderr}'))
        cases.append(('refresh() against a real BestPractice checkout succeeds',
                      r.returncode == 0, r.stdout + r.stderr))

        # The ALREADY-CURRENT path -- no --force, nothing to write, an early
        # return. It had no case of its own, and that is how the identical
        # NameError (`_warn_catalogue_skew(dest, ...)`, where refresh's local
        # is dest_tools) shipped TWICE on 2026-09-06: once on the write path
        # and, a commit later, again on this one. Both printed their success
        # line before raising, so only an exit code ever showed it. A branch
        # with no case is a branch that gets a crash added to it.
        r2 = subprocess.run([sys.executable, str(dest / 'tools' / 'precedent_vendor_engine.py'),
                             'refresh', str(ROOT), '--from-ref', 'HEAD'],
                            capture_output=True, text=True)
        cases.append(('refresh() on the already-current path returns cleanly '
                      'rather than raising after its own success message',
                      r2.returncode == 0 and 'Traceback' not in (r2.stdout + r2.stderr),
                      r2.stdout + r2.stderr))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'bootstrap_source\'s output engine is real and functional, not just present '
          f'({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def _write_fixture_practice(path, slug, applies_to, rule_text):
    """Same frontmatter shape check_bootstrap_source_engine_is_functional's
    own fixture practice uses -- kept as a helper here because this check
    needs three of these (one per source level) instead of one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\nslug: {slug}\ntitle: Fixture\ntier: on-demand\n'
        f'severity: default\napplies_to: {json.dumps(applies_to)}\n'
        f'occasion: "testing the vendored consumer engine"\n'
        f'gates: []\nindex_clause: "{slug} — a consumer-engine-harness fixture"\n'
        'checked_by: null\ndefines: []\nstatus: active\nsupersedes: []\n'
        'overrides: null\nadded: 2026-09-05\n'
        'approved_by: "harness, 2026-09-05"\nsource_practice_number: null\n'
        f'---\n## Rule\n{rule_text}\n\n## Why\nx\n\n## Story\nx\n\n## Install\nx\n',
        encoding='utf-8')


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
        optional = ('doc_lint.py', 'doc_sync.py', 'title_case.py',
                    'precedent_resolve.py')
        absent = [m for m in optional if not (dest / 'tools' / m).is_file()]
        cases.append(('the four optional modules are genuinely absent, so the '
                      'skips below are real', len(absent) == len(optional),
                      f'absent: {absent}'))

        # Put the two practices whose checks import the previously-bare
        # modules IN FORCE here, or the runner skips them for "practice not
        # in force" before either import is ever attempted -- and the guards
        # would go untested while the check reported success.
        for slug in ('headline-capitalization', 'source-naming'):
            src = ROOT / 'practices' / f'{slug}.md'
            if src.is_file():
                shutil.copy2(src, dest / 'practices' / f'{slug}.md')
        in_force = sorted(f.stem for f in (dest / 'practices').glob('*.md'))
        cases.append(('the two import-dependent practices are in force in the '
                      'fixture, so their checks actually reach the import',
                      set(in_force) >= {'headline-capitalization', 'source-naming'},
                      f'in force: {in_force}'))

        r = subprocess.run([sys.executable, 'tools/precedent_check.py'],
                           cwd=str(dest), capture_output=True, text=True)
        out = r.stdout + r.stderr
        cases.append(('it runs in a source set without a traceback',
                      'Traceback' not in out, out[-400:]))
        cases.append(('nothing ERRORED -- an absent optional dependency is '
                      'not a broken tool', ' 0 errored' in out, out[-400:]))
        cases.append(('no VIOLATION on a bare source set -- a check that '
                      'fires on a correct fresh install is one people learn '
                      'to ignore', 'VIOLATION' not in out, out[-600:]))
        cases.append(('a skip names the module that was missing, rather than '
                      'going quiet', 'did not import' in out, out[-600:]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for name, ok, detail in cases:
        check(f'precedent_check.py in a source set: {name}', ok,
              '' if ok else str(detail)[:500])


def check_vendor_engine_consumer_case():
    """TODO.md item 18, tested rather than trusted: tools/precedent_vendor_
    engine.py's 'consumer' kind (added 2026-09-05, piloted against a real
    private consumer repo) produces a genuinely working
    four-source engine in a consumer repo, the same rigor
    check_bootstrap_source_engine_is_functional() already applies to the
    narrower source-set case -- not just that the right files land in the
    right place.

    Distinct from that check in what it has to prove: a source set's
    vendored engine only ever reads ONE practices/ directory (its own). A
    consumer's vendored engine has to actually RESOLVE three real, separate
    sources (universal = this repo's own checkout, a fixture team set, a
    fixture repo-local set) through precedent_resolve.py/precedent_
    materialize.py/precedent_sync_views.py into one materialized tree
    BEFORE build_views.py/precedent_gate.py/precedent_paths.py/
    precedent_show.py have anything to read -- so this fixture wires all
    three, seeds the consumer's own vendored engine with `--kind consumer`,
    then proves a fixture practice AT EACH LEVEL survives the whole pipeline
    into AGENTS.md and into each command's real output."""
    import shutil, tempfile

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-consumer-engine-'))
    cases = []
    try:
        consumer = tmp / 'consumer'
        team_dir = tmp / 'precedent-team-consumer-fixture'
        consumer.mkdir()

        _write_fixture_practice(team_dir / 'practices' / 'consumer-fixture-team.md',
                                 'consumer-fixture-team', ['team-only/**'],
                                 'A team-level fixture rule, present in no other repo.')
        _write_fixture_practice(consumer / 'local' / 'practices' / 'consumer-fixture-local.md',
                                 'consumer-fixture-local', ['local-only/**'],
                                 'A repo-local fixture rule, present in no other repo.')

        (consumer / 'precedent.json').write_text(json.dumps({
            'format_version': 1,
            'visibility': 'private',   # declared, not defaulted -- see above
            'sources': [
                {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)},
                {'level': 'team', 'name': 'precedent-team-consumer-fixture', 'path': str(team_dir)},
                {'level': 'repo-local', 'name': 'local', 'path': 'local'},
            ],
        }), encoding='utf-8')
        (consumer / 'AGENTS.md').write_text(
            f'# fixture consumer\n\n{bv.BEGIN_MARKER}\n{bv.END_MARKER}\n', encoding='utf-8')

        # -- seed the consumer's OWN vendored engine, from THIS checkout,
        # exactly how INSTALL.md's consumer procedure runs it --
        r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_vendor_engine.py'),
                            'seed', str(consumer), '--kind', 'consumer'],
                           capture_output=True, text=True)
        cases.append(('seeding the consumer engine succeeds', r.returncode == 0,
                      r.stdout + r.stderr))

        manifest_path = consumer / 'tools' / 'ENGINE_MANIFEST.json'
        consumer_files = ['build_views.py', 'precedent_gate.py', 'precedent_paths.py',
                          'precedent_show.py', 'split_practices.py',
                          'precedent_materialize.py', 'precedent_resolve.py',
                          'precedent_sync_views.py', 'precedent_vendor_engine.py',
                          'routing_scope.json']
        cases.append(('every consumer engine file is present -- all 8 content files plus '
                      'the vendoring tool itself',
                      all((consumer / 'tools' / f).is_file() for f in consumer_files),
                      str([f for f in consumer_files if not (consumer / 'tools' / f).is_file()])))

        manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.is_file() else {}
        cases.append(("ENGINE_MANIFEST.json records kind: consumer",
                      manifest.get('kind') == 'consumer', str(manifest.get('kind'))))

        # -- an engine file hand-dropped beside a correctly vendored engine
        # is reported, not silently carried. Both directions, because the
        # real incident (precedent-team-maintainers, 2026-09-06) looked
        # HEALTHY to every mechanism that existed: the manifest's own files
        # all matched, so drift detection saw nothing, while the stray file
        # -- from a later upstream commit -- broke build_views.py outright.
        def _vendor_status(repo):
            r = subprocess.run(
                [sys.executable, str(repo / 'tools' / 'precedent_vendor_engine.py'),
                 'status', str(ROOT)],
                capture_output=True, text=True, cwd=str(repo))
            return r.returncode, r.stdout + r.stderr

        rc_clean, out_clean = _vendor_status(consumer)
        cases.append(('a freshly seeded engine reports no untracked engine file',
                      'UNTRACKED ENGINE FILE' not in out_clean, out_clean[:400]))

        # The faithful shape of the real incident: the file sits on disk
        # while the manifest -- written at an EARLIER upstream commit, before
        # that file joined the engine -- does not record it. Planting it by
        # dropping the manifest entry rather than by adding a file is what
        # makes this the real case: every remaining recorded file still
        # matches, so drift detection stays silent, exactly as it did.
        manifest_backup = manifest_path.read_text(encoding='utf-8')
        older = json.loads(manifest_backup)
        older['files'] = [f for f in older['files'] if f != 'build_codeowners.py']
        older.get('sha256', {}).pop('build_codeowners.py', None)
        manifest_path.write_text(json.dumps(older, indent=2), encoding='utf-8')
        rc_stray, out_stray = _vendor_status(consumer)
        cases.append(('an engine file present on disk but absent from the manifest '
                      'is reported, and exits non-zero',
                      rc_stray == 1 and 'UNTRACKED ENGINE FILE' in out_stray
                      and 'build_codeowners.py' in out_stray, out_stray[:400]))

        # a file that is NOT an engine file is the repo's own business
        own = consumer / 'tools' / 'the_repos_own_script.py'
        own.write_text('# this repo wrote this itself\n', encoding='utf-8')
        rc_own, out_own = _vendor_status(consumer)
        cases.append(("a repo's own non-engine script in tools/ is not reported",
                      'the_repos_own_script.py' not in out_own, out_own[:400]))
        cases.append(('drift detection stayed silent on the same tree -- which is '
                      'why the untracked check had to exist separately',
                      'LOCAL DRIFT' not in out_stray, out_stray[:400]))
        manifest_path.write_text(manifest_backup, encoding='utf-8')
        own.unlink()

        # -- refresh converges on a repo whose engine predates an added file.
        # The commit matches; only the FILE SET is short. Before this, the
        # commit alone decided, so such a repo was told "already current"
        # forever and could never acquire the file -- reproduced across all
        # three of this account's practice sets on 2026-09-06, and the reason
        # one of them had a hand-copied build_codeowners.py in the first place.
        older = json.loads(manifest_path.read_text(encoding='utf-8'))
        older['files'] = [f for f in older['files'] if f != 'build_codeowners.py']
        older.get('sha256', {}).pop('build_codeowners.py', None)
        manifest_path.write_text(json.dumps(older, indent=2), encoding='utf-8')
        (consumer / 'tools' / 'build_codeowners.py').unlink()
        head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                              capture_output=True, text=True).stdout.strip()
        r_conv = subprocess.run(
            [sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
             'refresh', str(ROOT), '--from-ref', head],
            capture_output=True, text=True, cwd=str(consumer))
        out_conv = r_conv.stdout + r_conv.stderr
        restored = json.loads(manifest_path.read_text(encoding='utf-8'))
        cases.append(('refresh writes an engine file the manifest is missing even '
                      'when the recorded commit already matches',
                      (consumer / 'tools' / 'build_codeowners.py').is_file()
                      and 'build_codeowners.py' in restored.get('files', []),
                      out_conv[:500]))
        cases.append(('and says why it refreshed rather than claiming nothing to do',
                      'missing' in out_conv and 'nothing to do' not in out_conv,
                      out_conv[:500]))

        # A MISSING file is a finding, not a crash. This read_bytes() used to
        # be unguarded, so a refresh that failed earlier in the fixture took
        # the WHOLE harness down with a FileNotFoundError -- 120-odd unrelated
        # checks never ran, and the traceback named a file
        # (build_codeowners.py) that had nothing to do with the cause.
        # Reproduced 2026-09-07 renaming a vendored engine file: fixtures
        # vendor from committed HEAD, so between the rename and its commit the
        # refresh legitimately fails, and this line turned that into a total
        # outage (practice: fail-gracefully).
        missing = [f for f in manifest.get('sha256', {})
                   if not (consumer / 'tools' / f).is_file()]
        mismatched = [f for f, h in manifest.get('sha256', {}).items()
                      if (consumer / 'tools' / f).is_file()
                      and hashlib.sha256((consumer / 'tools' / f).read_bytes()).hexdigest() != h]
        cases.append(('every recorded sha256 matches the file actually written',
                      bool(manifest.get('sha256')) and not mismatched and not missing,
                      f'mismatched={mismatched} missing={missing}'))

        # -- status(), run from the consumer's OWN vendored copy, against
        # this real checkout, finds zero drift right after seeding --
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                            'status', str(ROOT)], capture_output=True, text=True)
        cases.append(('status() against a real BestPractice checkout finds no drift '
                      'right after seeding', r.returncode == 0, r.stdout + r.stderr))

        # -- the drift-refusal / --force pair, the same property status()
        # depends on and that refresh() must actually honor (a real,
        # reproduced bug: --force used to no-op silently when the upstream
        # commit had not moved -- see refresh()'s own comment) --
        hand_edited = (consumer / 'tools' / 'build_views.py')
        original_bytes = hand_edited.read_bytes()
        hand_edited.write_bytes(original_bytes + b'\n# hand edit\n')

        # refresh() reads from a DISPOSABLE clone, never this repo's own
        # checkout. Handing it str(ROOT) is what moved the CI workspace
        # mid-job: refresh() used to `git checkout SOURCE_BRANCH` in the clone
        # it read FROM, so step 5 left the workspace on SOURCE_BRANCH and
        # every later step in the job silently ran against the wrong commit
        # (see precedent_vendor_engine._source_tools_at's docstring, and
        # check_bootstrap_source_engine_is_functional's own refresh case,
        # which asserts that no longer happens). refresh() is read-only now,
        # so str(ROOT) would no longer corrupt anything -- but a test that
        # vendors FROM a throwaway clone does not depend on that guarantee
        # continuing to hold, which is the point.
        upstream = tmp / 'upstream-clone'
        r = subprocess.run(['git', 'clone', '--quiet', str(ROOT), str(upstream)],
                           capture_output=True, text=True)
        cases.append(('a throwaway clone of this checkout is available to vendor from',
                      r.returncode == 0 and (upstream / '.git').exists(),
                      r.stdout + r.stderr))
        # Give the clone SOURCE_BRANCH by name so _source_tools_at resolves it
        # with no network and no assumption about which refs the caller's
        # checkout carries: on a GitHub Actions runner the workspace holds only
        # the ref under test, so `origin/<SOURCE_BRANCH>` need not exist at all.
        # Read the name from the tool rather than hardcoding it -- its own
        # docstring says SOURCE_BRANCH becomes 'main' once the beta lands.
        m = re.search(r"^SOURCE_BRANCH = '([^']+)'",
                      (ROOT / 'tools' / 'precedent_vendor_engine.py').read_text(encoding='utf-8'),
                      re.M)
        cases.append(("precedent_vendor_engine.py's SOURCE_BRANCH is readable, so this "
                      "fixture cannot drift from it", m is not None, ''))
        source_branch = m.group(1) if m else 'precedent-beta-v01'
        # Repoint the clone's `origin` at ITSELF first. _source_tools_at
        # runs `git fetch origin <SOURCE_BRANCH>` before it resolves
        # anything, so with origin still pointing at this checkout that
        # fetch overwrites the ref set below with whatever commit THIS
        # checkout's local precedent-beta-v01 happens to sit at -- and the
        # fixture silently tested that commit instead of the tree under
        # test. It failed on any working tree ahead of that branch, with a
        # message about a missing tools/precedent_vendor_engine.py that had
        # nothing to do with the property being tested. Self-origin keeps
        # both resolution paths real while making the fetch a no-op.
        subprocess.run(['git', '-C', str(upstream), 'remote', 'set-url',
                        'origin', str(upstream)], capture_output=True, text=True)
        # BOTH refs, deliberately. `git clone` copies this checkout's own
        # refs/heads/* into the clone's refs/remotes/origin/*, and
        # _source_tools_at prefers origin/<SOURCE_BRANCH> over a local
        # branch of that name -- so setting only the local ref left the
        # clone vendoring from whatever commit THIS checkout's local
        # precedent-beta-v01 happens to sit at, not from the tree under
        # test. That made the case below fail on any working tree ahead of
        # (or behind) that branch, with a message about a missing
        # tools/precedent_vendor_engine.py that had nothing to do with the
        # property being tested. Both refs point at the clone's HEAD, so
        # this fixture tests THIS tree whichever resolution path wins.
        for ref in (f'refs/heads/{source_branch}',
                    f'refs/remotes/origin/{source_branch}'):
            subprocess.run(['git', '-C', str(upstream), 'update-ref', ref, 'HEAD'],
                           capture_output=True, text=True)
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                            'refresh', str(upstream)], capture_output=True, text=True)
        cases.append(('refresh() without --force refuses a hand-edited vendored file',
                      r.returncode != 0 and 'hand-edited' in (r.stdout + r.stderr),
                      r.stdout + r.stderr))
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                            'refresh', str(upstream), '--force'], capture_output=True, text=True)
        cases.append(('refresh() with --force actually overwrites the hand-edited file '
                      '(not a silent no-op), even when the upstream commit has not moved',
                      r.returncode == 0 and hand_edited.read_bytes() == original_bytes,
                      r.stdout + r.stderr))

        # -- and again from a clone with NO origin/<SOURCE_BRANCH> ref at all,
        # which is exactly what a GitHub Actions workspace yields: the runner
        # checks out only the ref under test, so a clone taken from it has no
        # remote-tracking branch for SOURCE_BRANCH. refresh() must fall back to
        # the local branch of that name. Regression test for a real CI failure
        # (2026-09-06): "precedent-beta-v01 @ origin/prece has no
        # tools/build_views.py" -- plain `git rev-parse <missing-ref>` exits
        # non-zero but ECHOES THE REF NAME on stdout, and _git() keeps stdout
        # while discarding the exit code, so the `or <fallback>` never fired and
        # the ref name was carried forward as if it were a commit hash. Forced
        # here rather than left to the environment, so both resolution paths are
        # covered wherever this runs.
        subprocess.run(['git', '-C', str(upstream), 'update-ref', '-d',
                        f'refs/remotes/origin/{source_branch}'],
                       capture_output=True, text=True)
        cases.append(('the throwaway clone really has no origin/<SOURCE_BRANCH> ref',
                      subprocess.run(['git', '-C', str(upstream), 'rev-parse', '--verify',
                                      '--quiet', f'origin/{source_branch}'],
                                     capture_output=True, text=True).returncode != 0, ''))
        # Assert on RESOLUTION, not on the file being rewritten: the first
        # refresh above already replaced the consumer's own vendored
        # precedent_vendor_engine.py with SOURCE_BRANCH's copy (the tool
        # travels with the engine it defines, by design), so round two runs
        # upstream's semantics, not this working tree's -- and upstream may
        # legitimately short-circuit with "already current". What must hold
        # either way is that SOURCE_BRANCH resolved to a real commit: the bug
        # this guards produced a hard failure naming a truncated ref NAME
        # where a hash belonged.
        r = subprocess.run([sys.executable, str(consumer / 'tools' / 'precedent_vendor_engine.py'),
                            'refresh', str(upstream), '--force'], capture_output=True, text=True)
        out = r.stdout + r.stderr
        cases.append(('refresh() still resolves SOURCE_BRANCH from a clone with no '
                      'origin/<SOURCE_BRANCH>, falling back to the local branch instead '
                      'of carrying the ref NAME forward as a commit',
                      r.returncode == 0
                      and 'invalid object name' not in out
                      and f'@ origin/{source_branch[:12]}' not in out,
                      out))

        # -- the consumer's OWN vendored precedent_sync_views.py, run the way
        # a real consumer's AGENTS.md documents it (--repo .), resolves all
        # three sources and materializes + regenerates the loader block --
        r = subprocess.run([sys.executable, 'tools/precedent_sync_views.py', '--repo', '.'],
                           capture_output=True, text=True, cwd=str(consumer))
        cases.append(('precedent_sync_views.py --repo . resolves and materializes '
                      'cleanly', r.returncode == 0, r.stdout + r.stderr))

        agents_text = (consumer / 'AGENTS.md').read_text(encoding='utf-8') if (consumer / 'AGENTS.md').exists() else ''
        cases.append(('the regenerated AGENTS.md loader block names a real universal '
                      'practice (proves the universal source, not just the fixtures, '
                      'flowed through)', 'orientation-map' in agents_text, agents_text[:300]))

        team_practice = consumer / 'practices' / 'consumer-fixture-team.md'
        local_practice = consumer / 'practices' / 'consumer-fixture-local.md'
        cases.append(('the team fixture practice was materialized', team_practice.is_file(), ''))
        cases.append(('the repo-local fixture practice was materialized', local_practice.is_file(), ''))

        # -- precedent_gate.py / precedent_paths.py / precedent_show.py, run
        # IN PLACE (no --repo) against the materialized tree, same as the
        # source-set case's own rigor --
        r = subprocess.run([sys.executable, 'tools/precedent_gate.py', '--list'],
                           capture_output=True, text=True, cwd=str(consumer))
        cases.append(('the vendored precedent_gate.py lists the real (trimmed) gate '
                      'vocabulary against the materialized tree',
                      r.returncode == 0 and 'merge' in r.stdout, r.stdout + r.stderr))

        r = subprocess.run([sys.executable, 'tools/precedent_paths.py', 'team-only/x.md'],
                           capture_output=True, text=True, cwd=str(consumer))
        cases.append(('the vendored precedent_paths.py matches the team fixture by its '
                      'real applies_to glob', r.returncode == 0
                      and 'consumer-fixture-team' in r.stdout, r.stdout + r.stderr))

        r = subprocess.run([sys.executable, 'tools/precedent_show.py', 'consumer-fixture-local'],
                           capture_output=True, text=True, cwd=str(consumer))
        cases.append(("the vendored precedent_show.py returns the repo-local fixture's "
                      "real Rule text", r.returncode == 0
                      and 'repo-local fixture rule' in r.stdout, r.stdout + r.stderr))

        # -- a second sync, unchanged, is a clean --check (idempotency, and
        # the exact invocation a consumer's own session-start documents) --
        r = subprocess.run([sys.executable, 'tools/precedent_sync_views.py', '--repo', '.', '--check'],
                           capture_output=True, text=True, cwd=str(consumer))
        cases.append(('a second, unchanged sync passes --check cleanly (idempotent)',
                      r.returncode == 0, r.stdout + r.stderr))

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the vendored engine\'s "consumer" kind is real and functional against a real '
          f'four-source pipeline, not just present ({len(cases)} stated cases)',
          not bad,
          '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


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


def check_source_shape_is_verified():
    """A source is checked for the shape its skeleton defines, and for the
    shape its CONSUMERS need.

    precedent_bootstrap_source.py only ever ran for sources it created. A
    source migrated into place -- assembled by hand from an older system --
    never passed through it, and nothing afterwards asked whether it came
    out right. Both of this project's migrated sets were missing a skeleton
    file, and had been since migration (2026-09-06).

    File presence alone was the first version and was not enough: an
    approvers.json with no approvers, or an approver with no `github`, is
    present and useless -- build_codeowners.py refuses exactly those, so a
    source carrying one is already broken and has only not been run against
    yet. "Well-formed" is defined here by what a real consumer of the file
    needs, never by a wish list."""
    import importlib.util, tempfile, shutil, json as _json
    spec = importlib.util.spec_from_file_location(
        '_bss', ROOT / 'tools' / 'precedent_bootstrap_source.py')
    bss = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bss)

    cases = []
    with tempfile.TemporaryDirectory() as td:
        def fixture(level, **edits):
            d = pathlib.Path(td) / f'src{len(cases)}{level}{len(edits)}'
            shutil.copytree(ROOT / 'templates' / f'practice-set-{level}', d)
            (d / 'practices').mkdir(exist_ok=True)
            (d / 'practices' / 'x.md').write_text('---\nslug: x\n---\n## Rule\nx\n',
                                                  encoding='utf-8')
            if level == 'team':
                (d / 'approvers.json').write_text(_json.dumps(
                    {'approvers': [{'name': 'A', 'github': 'a'}]}), encoding='utf-8')
                (d / 'approvers.json.template').unlink(missing_ok=True)
            else:
                (d / 'config.json.sample').write_text(_json.dumps(
                    {'individual': {'name': 'n', 'path': '/p'}}), encoding='utf-8')
            (d / 'leak-blocklist.txt').write_text('# blank\n', encoding='utf-8')
            # The skeleton's README is full of {{PLACEHOLDER}}s by design;
            # bootstrap fills them. A fixture standing in for a FINISHED
            # source has to fill them too -- verify() caught this fixture
            # itself the first time it ran, which is the check working.
            (d / 'README.md').write_text('# A finished set\n', encoding='utf-8')
            # The two session hooks live in the harness adapter, not in
            # either skeleton (one copy per level would drift, and
            # _copy_skeleton writes plain text, while a hook without its
            # executable bit silently never runs) -- so a fixture standing
            # in for a FINISHED source installs them the same way
            # bootstrap() does, rather than by copying a tree that was
            # never going to contain them.
            bss._install_session_hooks(d)
            for rel, text in edits.items():
                if text is None:
                    (d / rel).unlink(missing_ok=True)
                else:
                    (d / rel).write_text(text, encoding='utf-8')
            return d

        cases.append(('a complete team set is well-formed',
                      bss.verify('team', fixture('team')) == []))
        cases.append(('a complete individual set is well-formed',
                      bss.verify('individual', fixture('individual')) == []))
        cases.append(('a source with no session hooks is reported -- they are '
                      'the one part of a source\'s shape that does not live '
                      'in the skeleton',
                      any('freshness-guard' in f for f in bss.verify(
                          'team', fixture('team',
                                          **{'.claude/hooks/freshness-guard.sh': None})))))
        # A source is free to keep its hooks somewhere other than where
        # bootstrap() writes them, as long as settings.json points at them:
        # what the shape check is really asking is whether the hook RUNS.
        # A real one does exactly this (its hooks live in bootstrap/), and
        # the literal-path check reported that working source as broken.
        _relocated = fixture('team', **{'.claude/hooks/freshness-guard.sh': None})
        (_relocated / 'bootstrap').mkdir(exist_ok=True)
        (_relocated / 'bootstrap' / 'freshness-guard.sh').write_text('#!/bin/sh\n')
        # Every mode the adapter wires, not just session-start: this fixture
        # stands in for a FINISHED source, and a finished source wires all of
        # them -- the real set this is modelled on was measured wiring exactly
        # the adapter's three. Wiring one made it a stand-in for a source that
        # is correct about WHERE its hooks live and wrong about WHEN they run,
        # which is a different fixture with a different purpose. Derived
        # rather than listed so this does not become another copy of the
        # wiring that drifts (see
        # check_generator_wires_every_template_guard_mode).
        (_relocated / '.claude' / 'settings.json').write_text(_json.dumps(
            {'hooks': {'SessionStart': [{'hooks': [
                {'type': 'command',
                 'command': f'$CLAUDE_PROJECT_DIR/bootstrap/freshness-guard.sh '
                            f'{_mode} main'}
                for _mode in sorted(bss._template_guard_modes())]}]}}))
        cases.append(('a session hook kept outside .claude/hooks/ but wired by '
                      'the source\'s own settings.json is NOT reported missing',
                      not any('freshness-guard' in f
                              for f in bss.verify('team', _relocated))))

        # The negative control for that leniency: wired at a path where
        # nothing is installed must still be reported, or the check above
        # would accept any settings.json that merely mentions the name.
        _dangling = fixture('team', **{'.claude/hooks/freshness-guard.sh': None})
        (_dangling / '.claude' / 'settings.json').write_text(_json.dumps(
            {'hooks': {'SessionStart': [{'hooks': [{'type': 'command',
             'command': '$CLAUDE_PROJECT_DIR/bootstrap/freshness-guard.sh'}]}]}}))
        cases.append(('a hook wired at a path where no file exists is still '
                      'reported missing',
                      any('freshness-guard' in f
                          for f in bss.verify('team', _dangling))))

        cases.append(('a report names the harness adapter, not the skeleton, '
                      'for the files the skeleton has never shipped',
                      all('templates/harness/claude-code/hooks/' in f
                          for f in bss.verify('team', fixture(
                              'team', **{'.claude/hooks/commit-identity.sh': None}))
                          if 'commit-identity' in f)))

        cases.append(('a missing skeleton file is reported',
                      any('leak-blocklist' in f for f in bss.verify(
                          'team', fixture('team', **{'leak-blocklist.txt': None})))))
        cases.append(('an approvers.json with no approvers is reported -- '
                      'build_codeowners.py refuses exactly this',
                      any('no approvers' in f for f in bss.verify(
                          'team', fixture('team', **{'approvers.json':
                              _json.dumps({'approvers': []})})))))
        cases.append(('an approver with no github is reported',
                      any('"github"' in f for f in bss.verify(
                          'team', fixture('team', **{'approvers.json':
                              _json.dumps({'approvers': [{'name': 'A'}]})})))))
        cases.append(('an unfilled {{PLACEHOLDER}} is reported -- bootstrapped '
                      'and never finished',
                      any('unfilled' in f for f in bss.verify(
                          'team', fixture('team',
                                          **{'leak-blocklist.txt': 'a {{NAME}} b'})))))
        cases.append(('an individual config missing individual.path is reported',
                      any('individual.path' in f for f in bss.verify(
                          'individual', fixture('individual', **{'config.json.sample':
                              _json.dumps({'individual': {'name': 'n'}})})))))
        d = fixture('team')
        for f in (d / 'practices').glob('*.md'):
            f.unlink()
        cases.append(('a source with no practice files is reported',
                      any('no practice files' in x for x in bss.verify('team', d))))

    bad = [n for n, ok in cases if not ok]
    for n in bad:
        print(f"  source-shape case did not behave as stated: {n}")
    check(f'a source is verified for shape AND well-formedness '
          f'({len(cases)} stated cases)', not bad)


def check_rendered_docs_are_current():
    """Every committed HTML render still matches its markdown source.

    tools/doc_html.py writes a .html beside each document in its own DOCS
    registry, and nothing checked that the committed render was still the
    one that source produces. It was not: on 2026-09-06 an accidental bare
    run of the tool -- during the sweep for tools that write when they
    should not -- regenerated spec/PREFORK_AUDIT.html and picked up a whole
    paragraph the source had gained and the render had never been rebuilt
    for. A stale render is worse than no render: it is a page that looks
    current, is linked as the readable view of the document, and disagrees
    with it silently.

    generated-artifact-provenance already holds this property for the
    generated VIEWS (MAP.md, GLOSSARY.md, AGENTS.md's block); this is the
    same property for the rendered ones, which that check does not reach.

    The build stamp is excluded from the comparison: it is the one line
    that legitimately differs on every run, so comparing it would make this
    fail constantly and mean nothing.
    """
    import importlib.util, re as _re, tempfile, shutil
    spec = importlib.util.spec_from_file_location(
        '_doc_html', ROOT / 'tools' / 'doc_html.py')
    try:
        dh = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dh)
    except Exception as e:
        not_applicable('rendered documents are current',
                       f'tools/doc_html.py could not be imported ({e}) -- '
                       f'not a pass')
        return
    if not getattr(dh, 'DOCS', None):
        not_applicable('rendered documents are current',
                       'doc_html.py registers no documents, so there is '
                       'no render to compare')
        return

    STAMP = _re.compile(r'<div class="renderstamp">[^<]*</div>')
    stale, missing = [], []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='render-check-'))
    try:
        for rel, title in dh.DOCS:
            src = ROOT / rel
            committed = src.with_suffix('.html')
            if not src.is_file():
                missing.append(f'{rel} (source missing)')
                continue
            if not committed.is_file():
                missing.append(str(committed.relative_to(ROOT)))
                continue
            out = tmp / (pathlib.Path(rel).stem + '.html')
            dh.render(src, out, title)
            a = STAMP.sub('', committed.read_text(encoding='utf-8'))
            b = STAMP.sub('', out.read_text(encoding='utf-8'))
            if a != b:
                stale.append(str(committed.relative_to(ROOT)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    check(f'every registered document\'s HTML render is current '
          f'({len(dh.DOCS)} registered)',
          not stale and not missing,
          '; '.join(
              ([f'stale: {", ".join(stale)}'] if stale else [])
              + ([f'missing: {", ".join(missing)}'] if missing else [])))


def check_philosophy_readme_lists_every_file():
    """philosophy/README.md's list names every file in philosophy/, and no other.

    The page was cut back to one sentence and that list on 2026-09-09, on
    Morgan's instruction, with "updated as the files are changed" as the
    standing requirement. A list that is a document's whole content and is
    maintained by hand is a list that goes stale the first time somebody
    adds a file in a hurry -- and the drift is invisible, because a missing
    entry looks exactly like a directory that never had that file.

    Set comparison, not order: the page orders by importance, which is a
    judgment no check should be holding an opinion about. The recipe at
    philosophy/doc-recipes/README.recipe.md is what this enforces.
    """
    d = ROOT / 'philosophy'
    readme = d / 'README.md'
    if not readme.is_file():
        not_applicable('philosophy README lists every file',
                       'philosophy/README.md does not exist -- not a pass')
        return
    on_disk = {p.name + ('/' if p.is_dir() else '')
               for p in d.iterdir() if p.name != 'README.md'}
    text = readme.read_text(encoding='utf-8')
    listed = set()
    for name in on_disk:
        target = name if name.endswith('/') else name
        if f']({target})' in text:
            listed.add(name)
    # An entry the page names that is not on disk is the other half: a link
    # left behind by a rename reads as a live document until somebody clicks.
    import re as _re
    linked = set(_re.findall(r'\]\((?!\.\.?/|https?:)([^)#]+)\)', text))
    stale = {L for L in linked
             if not (d / L.rstrip('/')).exists()}
    missing = on_disk - listed
    check('philosophy/README.md lists every file in philosophy/ '
          f'({len(on_disk)} on disk)',
          not missing and not stale,
          '; '.join(
              ([f'not listed: {", ".join(sorted(missing))}'] if missing else [])
              + ([f'listed but absent: {", ".join(sorted(stale))}'] if stale else [])))


def _looks_like_help(tool, out):
    """Does this output actually answer --help, or is it the tool running?

    The test is the tool's own module docstring: a help answer contains a
    real run of it. Deliberately not an exact match -- argparse prints its
    own usage/description rather than the raw docstring, and that is a
    perfectly good help answer.
    """
    import ast
    try:
        doc = ast.get_docstring(ast.parse(tool.read_text(encoding='utf-8')))
    except Exception:
        return True                      # unparseable: not this check's call
    if not doc:
        return True                      # nothing to compare against
    o = ' '.join(out.split()).lower()
    if 'usage:' in o:                    # argparse-generated help
        return True
    for line in doc.strip().splitlines():
        line = ' '.join(line.split())
        if len(line) >= 40 and line.lower() in o:
            return True
    return False


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
    # universal, and the team source that had authored it first kept a copy
    # to put the rule in force on itself, since a source repo consumes no
    # catalogue). Verified by reading the rendered line: it was universal's
    # index_clause, not the team's. A finding nobody can act on without
    # deleting a legitimate practice is one people learn to ignore.
    publishable = set()
    for s in declared:
        if s['level'] in ('team', 'individual'):
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

    missing, leaked = [], []
    for s in declared:
        d = pathlib.Path(s['path']) / 'practices'
        if not d.is_dir():
            continue                       # unreachable here; not evidence
        active = []
        for f in sorted(d.glob('*.md')):
            try:
                fm, _sec = sp._read_practice_file(f)
            except Exception:
                continue
            if (fm.get('status') or 'active').strip('" ') == 'active':
                active.append(fm.get('slug', f.stem))
        if not active:
            continue
        present = [a for a in active if a in named]
        if public and s['level'] in ('team', 'individual'):
            leaked += [a for a in present if a not in publishable]
        elif not present:
            missing.append(f"{s['level']}/{s['name']} ({len(active)} active "
                           f"practices, none in {name})")

    check('the loader block renders every publishable source '
          'precedent.json declares', not missing, '; '.join(missing))
    if public:
        check('no private-source practice reaches a public repo\'s tracked '
              'loader block',
              not leaked,
              f'{len(leaked)} leaked: {", ".join(sorted(leaked)[:6])}')


def check_tools_answer_help_without_writing():
    """`--help` is safe and informative on every tool in tools/.

    Two properties, both learned the hard way on 2026-09-06 by a sweep that
    simply ran `--help` across every script here to see what came back:

    * **It is answered, with exit 0.** The tools split three ways before that
      sweep -- a hard `FAIL: unknown option '--help'`, a silent fall-through
      that ran the whole audit as though nothing had been asked, or the
      docstring printed with a non-zero exit. `--help` is the first thing any
      reader types, and documentation/HOW_TO_USE_THIS_TECHNICAL.md points a
      public audience straight at these commands.

    * **It writes nothing.** tools/resplit_sections.py defaulted to WRITING:
      any argument it did not recognise, `--help` included, fell through to
      the write branch and silently rewrote 46 tracked practice files,
      reverting every edit made to them since phase 1.5 -- no confirmation,
      no diff, and the damage surfaced two steps later as an unrelated
      doc_sync DRIFT that looked like a numbers problem. A destructive
      DEFAULT on a spent migration tool is the dangerous shape: the safe mode
      has to be the one you get by accident.

    Run against a throwaway copy of the tracked tree, never against the real
    one -- a check for "does this tool clobber the repo" must not be able to
    clobber the repo while finding out.
    """
    import hashlib, shutil, tempfile
    tools = sorted((ROOT / 'tools').glob('*.py'))
    tracked = subprocess.run(['git', 'ls-files'], cwd=str(ROOT),
                             capture_output=True, text=True)
    if tracked.returncode != 0 or not tracked.stdout.strip():
        not_applicable('tools answer --help without writing',
                       'git ls-files returned nothing here, so there is no '
                       'tracked tree to copy and compare -- not a pass')
        return

    files = [f for f in tracked.stdout.splitlines() if f]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='help-sweep-'))
    try:
        for rel in files:
            src = ROOT / rel
            if not src.is_file():
                continue
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        def snapshot():
            out = {}
            for rel in files:
                f = tmp / rel
                if f.is_file():
                    out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
            return out

        before = snapshot()
        # A module with no `if __name__ == '__main__'` block is a library
        # (tools/table_fmt.py is one): it is imported, never invoked, so
        # "answer --help" is not a property it can have. Named here rather
        # than quietly dropped, so the exemption stays visible.
        libraries = [t for t in tools
                     if "__main__" not in t.read_text(encoding='utf-8')]
        tools = [t for t in tools if t not in libraries]
        bad_exit, silent, not_help = [], [], []
        for tool in tools:
            r = subprocess.run([sys.executable, str(tmp / 'tools' / tool.name),
                                '--help'],
                               cwd=str(tmp), capture_output=True, text=True,
                               timeout=120)
            if r.returncode != 0:
                bad_exit.append(f'{tool.name} exited {r.returncode}')
            elif not r.stdout.strip():
                silent.append(tool.name)
            elif not _looks_like_help(tool, r.stdout):
                # Exit 0 with output is NOT enough. A tool that simply
                # ignores an unrecognised flag runs its whole normal job and
                # exits 0, which passed every property above while answering
                # nothing -- build_views.py did exactly that until
                # 2026-09-06, silently regenerating MAP.md, GLOSSARY.md and
                # AGENTS.md's block on `--help`. In THIS repo those are
                # already current, so even the "writes nothing" property
                # held: an identical rewrite is invisible to a hash. It was
                # only visible in a consuming repo, where the same command
                # would have rewritten drifted views. So the output itself
                # has to be checked against the tool's own docstring.
                not_help.append(tool.name)
        after = snapshot()
        wrote = sorted(set(before) & set(after)
                       - {k for k in before if before[k] == after.get(k)})
        wrote += sorted(set(after) - set(before))

        check(f'every tool answers --help with exit 0 ({len(tools)} tools; '
              f'{len(libraries)} import-only module(s) exempt: '
              f'{", ".join(t.name for t in libraries) or "none"})',
              not bad_exit, '; '.join(bad_exit))
        check('every tool\'s --help actually prints something',
              not silent, ', '.join(silent))
        check('every tool\'s --help answers with its own usage text, rather '
              'than running the tool',
              not not_help, ', '.join(not_help))
        check('no tool writes to the tree when asked for --help',
              not wrote,
              f'{len(wrote)} file(s) changed: ' + ', '.join(wrote[:8]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_machine_readable_files_parse():
    """Every JSON and YAML file this change TOUCHED still parses.

    Changed-scope on purpose. This gates a push and runs constantly, so its
    question is "did I just break something", not "is the whole repo well".
    The whole-tree sweep is the very deep check's job
    (`tools/very_deep_check.py`), which is on-demand and is the only place a
    file nobody has touched in months gets looked at again.

    Nothing here parsed a YAML or JSON file at all until 2026-09-06 -- not
    .github/workflows/deep-check.yml, the file that RUNS this check in CI,
    and not precedent.json, MANIFEST.json, ENGINE_MANIFEST.json or
    routing_scope.json, each read by exactly one tool that would report its
    own confusing failure rather than "this file is malformed". A broken
    workflow is the worst of them: GitHub skips it silently, so the gate
    stops running and every push looks as green as the day before. That is
    the worst shape a check can have, and it applied to the check-running
    check itself."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_parse_check', ROOT / 'tools' / 'parse_check.py')
    pcheck = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pcheck)

    paths, scope = pcheck.changed(ROOT)
    failures, parsed, skipped = pcheck.validate(ROOT, paths)
    n = len(pcheck.candidates(ROOT, paths))
    for rel, why in failures:
        print(f"  {rel}: {why}")
    if skipped:
        not_applicable(f'{", ".join(skipped)} files in scope were not parsed',
                       'no parser installed here (pip install pyyaml) -- a '
                       'file nobody parsed is not a file that parses')
    check(f'every JSON/YAML file this change touched parses '
          f'({n} in scope; {scope})', not failures)

    # Scripts a workflow actually invokes, as opposed to mentions in prose.
    # Same class as vendored-engine-file-refs-resolve: a job calling a
    # missing script fails on every run, and nothing says so until somebody
    # reads a CI log. Whole-tree because there are three of them.
    RUN_SCRIPT = re.compile(r'python3?\s+((?:tools|process|deck)/[\w/.-]+\.py)')
    workflows = [f for f in pcheck.tracked(ROOT) if '/workflows/' in f]
    missing = []
    for rel in workflows:
        text = (ROOT / rel).read_text(encoding='utf-8')
        for name in sorted(set(RUN_SCRIPT.findall(text))):
            if not (ROOT / name).is_file():
                missing.append((rel, name))
    for rel, name in missing:
        print(f"  {rel}: runs {name}, which does not exist")
    check(f'every script a workflow runs exists ({len(workflows)} workflow '
          f'file(s))', not missing)


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
          out[-200:])


def check_frontmatter_is_real_yaml():
    """The fence says YAML, so a real YAML parser has to accept it.

    This repo's own reader takes everything after the first colon and is
    happy with `title: Build/buy: decompose before deciding`. PyYAML is
    not -- the second colon opens a nested mapping and it rejects the
    whole block. Ten of sixty-one practice files shipped that way, and
    nothing here noticed for as long as the format existed, because
    nothing here parses its own output the way the people downstream do.

    Found 2026-09-06 from the other side: a consuming repo's own light
    check, which uses PyYAML, reported them as invalid. A format whose
    only conforming parser is its author's is not a format, so the check
    belongs on the producing side. Skipped with a notice where PyYAML
    isn't installed rather than passing on having parsed nothing."""
    try:
        import yaml
    except ImportError:
        not_applicable('every --- fence holds valid YAML',
                        'PyYAML is not installed here, so nothing was parsed '
                        '-- `pip install pyyaml` to run it')
        return
    # Every tracked markdown file that OPENS with a --- fence, not only
    # practices/. A consuming repo vendors this whole tree and runs its own
    # YAML-based checks over all of it; four decisions/ records were
    # unparseable for a different reason than the practices were -- values
    # continued across lines with no block-scalar indicator -- and turned a
    # consumer's own commit gate red on vendored upstream content.
    bad = []
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '*.md'],
                             capture_output=True, text=True).stdout.split()
    for rel in tracked:
        f = ROOT / rel
        try:
            text = f.read_text(encoding='utf-8')
        except OSError:
            continue
        if not text.startswith('---\n'):
            continue                      # no frontmatter claimed, none checked
        m = re.match(r'---\n(.*?)\n---\n', text, re.S)
        if not m:
            bad.append((rel, 'opens a --- fence that is never closed'))
            continue
        try:
            yaml.safe_load(m.group(1))
        except Exception as e:
            bad.append((rel, str(e).split('\n')[0]))
    for n, why in bad:
        print(f"  {n}: frontmatter is not valid YAML -- {why}")
    check(f"every tracked markdown file that opens a --- fence has "
          f"frontmatter a real YAML library accepts, not only this repo's "
          f"own reader ({len(tracked)} file(s) scanned)", not bad)


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


def check_materialized_links_are_placed():
    """A practice's relative links are repointed for where the file lands.

    Practice files ship. A practice's links are written relative to its own
    directory in its own repository, and copied verbatim into a consuming
    repo they point at nothing -- `../tools/very_deep_check.py` and
    `../spec/ATTENTION_CEILING.md` are real in Precedent and absent from
    every repo that installs it. Every consuming repo was shipping ~60
    practice files with dead internal links, and
    precedent-team-maintainers' own light check had already had to exempt
    materialized practices/ from its broken-link scan to stay green.

    Four behaviours, and the last two are why this is not a blanket
    rewrite: a link that already resolves where it lands must be left
    exactly as it is, and a link this cannot place confidently must be
    left alone rather than mangled -- the output is a copy of somebody
    else's content."""
    import shutil, tempfile, importlib.util

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-matlinks-'))
    cases = []
    try:
        spec = importlib.util.spec_from_file_location(
            '_pm_links', ROOT / 'tools' / 'precedent_materialize.py')
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)

        # An "upstream" source repo with a real remote and a real commit,
        # so the rewrite has something honest to point at.
        upstream = tmp / 'upstream'
        (upstream / 'practices').mkdir(parents=True)
        (upstream / 'spec').mkdir()
        (upstream / 'tools').mkdir()
        (upstream / 'spec' / 'THING.md').write_text('x\n', encoding='utf-8')
        (upstream / 'tools' / 'engine.py').write_text('x\n', encoding='utf-8')
        (upstream / 'practices' / 'sibling.md').write_text('x\n', encoding='utf-8')
        src = upstream / 'practices' / 'p.md'
        src.write_text(
            'See [spec/THING.md](../spec/THING.md) and [engine](../tools/engine.py).\n'
            'Sibling: [sibling](sibling.md). External: [x](https://example.com/a).\n'
            'Missing at the source: [gone](../spec/GONE.md).\n', encoding='utf-8')
        for argv in (['init', '-q'], ['config', 'user.email', 'h@e'],
                     ['config', 'user.name', 'h'],
                     ['remote', 'add', 'origin', 'https://github.com/acme/upstream.git'],
                     ['add', '-A'], ['commit', '-qm', 'seed']):
            subprocess.run(['git', '-C', str(upstream), *argv], capture_output=True)
        commit = subprocess.run(['git', '-C', str(upstream), 'rev-parse', 'HEAD'],
                                capture_output=True, text=True).stdout.strip()

        consumer = tmp / 'consumer'
        (consumer / 'practices').mkdir(parents=True)
        (consumer / 'tools').mkdir()
        (consumer / 'tools' / 'engine.py').write_text('x\n', encoding='utf-8')
        out = pm._rewrite_links(src.read_bytes(), str(src), consumer,
                                sibling_slugs={'sibling'}).decode('utf-8')

        cases.append(('a target in another repository becomes a commit URL — '
                      'the branch could be deleted, the commit cannot',
                      f'https://github.com/acme/upstream/blob/{commit}/spec/THING.md'
                      in out, out))
        cases.append(('a sibling practice link is left exactly as it is — '
                      'recognised from the slug set this run is writing, not '
                      'from what happens to be on disk yet',
                      '](sibling.md)' in out, out))
        cases.append(('an external URL is left alone',
                      '](https://example.com/a)' in out, out))
        cases.append(('a link that already resolves where it LANDS is left '
                      'relative — the consumer has its own tools/engine.py, '
                      'so an absolute URL would send the reader to the wrong '
                      'copy', '](../tools/engine.py)' in out, out))
        cases.append(("a link already broken at the source is left alone, not "
                      "invented", '](../spec/GONE.md)' in out, out))

        # The repo-local direction: same family, opposite sign. A practice at
        # local/practices/x.md writing `../tools/` means local/tools/, which
        # is NOT what that link means once the file sits at practices/x.md.
        (consumer / 'local' / 'practices').mkdir(parents=True)
        (consumer / 'local' / 'tools').mkdir()
        (consumer / 'local' / 'tools' / 'own.py').write_text('x\n', encoding='utf-8')
        lsrc = consumer / 'local' / 'practices' / 'l.md'
        lsrc.write_text('Ours: [own](../tools/own.py).\n', encoding='utf-8')
        lout = pm._rewrite_links(lsrc.read_bytes(), str(lsrc), consumer).decode('utf-8')
        cases.append(('a repo-local source\'s link is recomputed as a relative '
                      'path from the new location, not turned into a URL — the '
                      'file is right there in the same repo',
                      '](../local/tools/own.py)' in lout, lout))

        # The privacy boundary. An individual source is named only in a
        # person's own user-level config -- load_config refuses one declared
        # in a shared repo -- so writing its repository's URL into a tracked
        # practices/ tree publishes exactly what that refusal protects, and
        # a consuming repo can be public.
        iout = pm._rewrite_links(src.read_bytes(), str(src), consumer,
                                 sibling_slugs={'sibling'},
                                 may_name_source_repo=False).decode('utf-8')
        cases.append(("an individual source's link is NOT turned into a URL "
                      "naming its private repository — the dead relative link "
                      "is the smaller failure",
                      'github.com/acme/upstream' not in iout
                      and '](../spec/THING.md)' in iout, iout))
        cases.append(('and the placements that do not name that repository '
                      'still happen for an individual source',
                      '](../tools/engine.py)' in iout and '](sibling.md)' in iout,
                      iout))

        # No remote, no rewrite: never guess a URL.
        noremote = tmp / 'noremote'
        (noremote / 'practices').mkdir(parents=True)
        (noremote / 'spec').mkdir()
        (noremote / 'spec' / 'THING.md').write_text('x\n', encoding='utf-8')
        nsrc = noremote / 'practices' / 'p.md'
        nsrc.write_text('See [t](../spec/THING.md).\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(noremote), 'init', '-q'], capture_output=True)
        nout = pm._rewrite_links(nsrc.read_bytes(), str(nsrc), consumer).decode('utf-8')
        cases.append(('a source with no usable remote leaves its links alone '
                      'rather than writing a URL it had to guess',
                      '](../spec/THING.md)' in nout, nout))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'a materialized practice\'s links are placed for where the file '
          f'lands ({len(cases)} stated cases: another repo becomes a commit '
          f'URL; a sibling, an external URL, a link that already resolves, '
          f'and a link broken at the source are all left alone; a repo-local '
          f'source is recomputed relative; an individual source never names '
          f'its own private repository; no remote means no rewrite)',
          not bad, '; '.join(f"{n} -- {d[:160]}" for n, d in bad))


def check_source_supplied_checks_run():
    """A `checked_by: tools/checks/check_x.py` claim actually RUNS.

    Before precedent_check.register_materialized_checks() existed, nothing
    anywhere invoked those scripts. precedent_materialize.py copied them
    into a consuming repo, precedent_land.py refused to land a team or
    individual practice without one, and spec/PRIVATE_ENFORCEMENT_BRIEF.md
    told a private set how to write one -- and then a consuming repo held
    fourteen real, tested check scripts (nine in precedent-team-maintainers,
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
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'source-supplied checks actually run ({len(cases)} stated cases: '
          f'all four exit statuses, both routes into a repo, and the slug '
          f'taken from the claiming practice)',
          not bad, '; '.join(f"{n} -- {d[:800]}" for n, d in bad))


def check_source_credentials():
    """tools/precedent_source_credentials.py, and the one property that
    matters most about it: the token never leaves the environment.

    The mechanism exists because `add_repo` refuses across GitHub owners
    (reproduced 2026-09-09 as a session's first tool call), so a private
    practice source has to be reachable some other way. What it cannot do is
    trade that problem for a worse one -- a secret written into a clone's
    .git/config, or into an argument list, is a secret somebody commits
    later. Cases 2, 3 and 7 are that property, asserted three ways.

    Every case here is hermetic: a file:// fixture, a fixture HOME, and a
    fixture repo whose precedent.json this test wrote
    (practice: fixture-owns-its-state). Nothing touches the network, and no
    case reads this container's own real credentials.

    NEGATIVE CONTROL, RUN 2026-09-09 rather than assumed
    (practice: control-asserts-which-failure). The helper was rewritten to
    interpolate the token's VALUE instead of its variable name, and case 2's
    "the token itself never appears in the arguments" went red, printing the
    fixture token in its own failure detail. So the case can fail, and it
    fails for the reason it claims to watch."""
    import shutil, tempfile

    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_source_credentials as psc
    import precedent_source_bootstrap as psb   # BASE_URL_ENV lives with the
    # tool that clones, not with the tool that reports -- the bootstrap has
    # to keep working in a tree vendored before the credentials module
    # existed, so it owns nothing it cannot resolve alone.

    TOKEN = 'fixture-token-never-a-real-one'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-source-cred-'))
    cases = []
    try:
        tool = ROOT / 'tools' / 'precedent_source_credentials.py'
        url = 'https://github.com/example/precedent-individual'

        # --- 1: no token, no credential flags ------------------------------
        args = psc.credential_args(url, env={})
        cases.append(('no token means no credential flags at all',
                      args == [], repr(args)))

        # --- 2: a token produces flags, and is NOT in them ------------------
        args = psc.credential_args(url, env={psc.TOKEN_ENV: TOKEN})
        joined = ' '.join(args)
        cases.append(('a token produces a helper that git can use',
                      len(args) == 4 and args[0] == '-c'
                      and 'credential.helper=' in args[1]
                      and psc.TOKEN_ENV in joined, repr(args)))
        cases.append(('the token itself never appears in the arguments -- '
                      'only the NAME of the variable git should read',
                      TOKEN not in joined, repr(args)))

        # --- 3: a hostile username cannot break out of the helper snippet ---
        args = psc.credential_args(url, env={psc.TOKEN_ENV: TOKEN,
                                             psc.TOKEN_USER_ENV: 'evil; rm -rf /'})
        cases.append(('a username that is not a plain identifier falls back '
                      'to the default rather than reaching the shell',
                      'rm -rf' not in ' '.join(args)
                      and f'username={psc.DEFAULT_TOKEN_USER}' in ' '.join(args),
                      repr(args)))
        args = psc.credential_args(url, env={psc.TOKEN_ENV: TOKEN,
                                             psc.TOKEN_USER_ENV: 'git-user_1.x'})
        cases.append(('a legitimate username override is honoured',
                      'username=git-user_1.x' in ' '.join(args), repr(args)))

        # --- 3b: the opt-in inherit mode -----------------------------------
        # Measured 2026-09-09 rather than reasoned about: `inherit` against a
        # real cross-owner private repo in this container was REFUSED by
        # GitHub ("Invalid username or token"), which is the outcome the mode
        # exists to make legible -- a credential was sent and rejected, not
        # absent. These cases assert the wiring that produced that outcome.
        inh = {psc.TOKEN_ENV: psc.INHERIT, 'GITHUB_TOKEN': TOKEN}
        cases.append(('inherit resolves to the NAME of the variable that '
                      'actually holds a token',
                      psc.token_var(inh) == 'GITHUB_TOKEN', str(psc.token_var(inh))))
        args = psc.credential_args(url, env=inh)
        joined = ' '.join(args)
        cases.append(('...and the helper interpolates THAT variable, so the '
                      'literal word "inherit" is never sent as a password',
                      'password=$GITHUB_TOKEN' in joined
                      and psc.INHERIT not in joined, repr(args)))
        cases.append(('...and the inherited token itself still never appears '
                      'in the arguments', TOKEN not in joined, repr(args)))
        empty_inh = {psc.TOKEN_ENV: psc.INHERIT}
        cases.append(('inherit with nothing to inherit is NO credential, not '
                      'the word "inherit" sent as one',
                      psc.token_var(empty_inh) is None
                      and psc.credential_args(url, env=empty_inh) == [],
                      repr(psc.credential_args(url, env=empty_inh))))
        # --- 4: only https gets the credential -----------------------------
        for scheme in (f'file://{tmp}/x', 'ssh://example.invalid/x'  # deliberately userless: a fixture URL
                       # carrying user@host reads as an email address
                       # to the leak gate, which scans this file too,
                       'http://example.com/x'):
            args = psc.credential_args(scheme, env={psc.TOKEN_ENV: TOKEN})
            cases.append((f'a {scheme.split(":")[0]}:// url is never offered '
                          f'the credential', args == [], repr(args)))

        # --- 5: assess() tells the three states apart ----------------------
        repo = tmp / 'consumer'
        (repo / 'local').mkdir(parents=True)
        home_empty = tmp / 'home-empty'
        (home_empty / '.config' / 'precedent').mkdir(parents=True)
        (home_empty / '.config' / 'precedent' / 'config.json').write_text(
            '{"format_version": 1}\n', encoding='utf-8')

        def write_cfg(team_path):
            sources = [{'level': 'universal', 'name': 'precedent', 'path': '.'},
                       {'level': 'repo-local', 'name': 'local', 'path': 'local'}]
            if team_path is not None:
                sources.insert(1, {'level': 'team', 'name': 'precedent-team-fixture',
                                   'path': team_path})
            (repo / 'precedent.json').write_text(
                json.dumps({'format_version': 1, 'sources': sources}), encoding='utf-8')

        write_cfg('../precedent-team-fixture')
        env_no_token = {'HOME': str(home_empty)}
        verdict, message = psc.assess(repo, env=env_no_token)
        cases.append(('an unresolved private source with no token reads as '
                      'MISSING, and the message names the variable to set',
                      verdict == 'missing' and psc.TOKEN_ENV in message,
                      f'{verdict}: {message}'))

        verdict, message = psc.assess(repo, env={**env_no_token, psc.TOKEN_ENV: TOKEN})
        cases.append(('the same repo WITH a token reads as SET -- a missing '
                      'credential is explicitly not the explanation',
                      verdict == 'set' and 'not the explanation' in message,
                      f'{verdict}: {message}'))

        verdict, message = psc.assess(repo, env={**env_no_token, **empty_inh})
        cases.append(('...and assess says which of the two missing states it '
                      'is: asked to inherit, nothing there',
                      verdict == 'missing' and 'nothing to inherit' in message,
                      f'{verdict}: {message}'))
        verdict, message = psc.assess(repo, env={**env_no_token, **inh})
        cases.append(('an inherited credential reads as SET and names where '
                      'it came from, since a harness token is usually scoped '
                      'to other repositories and will be refused',
                      verdict == 'set' and 'inherited from GITHUB_TOKEN' in message,
                      f'{verdict}: {message}'))

        # both sources genuinely present -> nothing to say
        team = tmp / 'precedent-team-fixture'
        (team / 'practices').mkdir(parents=True)
        indiv = tmp / 'indiv'
        (indiv / 'practices').mkdir(parents=True)
        home_ok = tmp / 'home-ok'
        (home_ok / '.config' / 'precedent').mkdir(parents=True)
        (home_ok / '.config' / 'precedent' / 'config.json').write_text(
            json.dumps({'format_version': 1,
                        'individual': {'name': 'precedent-individual',
                                       'path': str(indiv)}}), encoding='utf-8')
        verdict, _ = psc.assess(repo, env={'HOME': str(home_ok)})
        cases.append(('every private source on disk reads as ok, with or '
                      'without a token', verdict == 'ok', verdict))
        cases.append(('and remind() then says nothing at all, so the tools '
                      'that call it stay quiet',
                      psc.remind(repo, env={'HOME': str(home_ok)}) is None,
                      str(psc.remind(repo, env={'HOME': str(home_ok)}))))

        # --- 6: the CLI's own contract -------------------------------------
        def run(*args, env_extra=None):
            env = dict(os.environ)
            env.pop(psc.TOKEN_ENV, None)
            if env_extra:
                env.update(env_extra)
            r = subprocess.run([sys.executable, *args], capture_output=True,
                               text=True, env=env)
            return r.returncode, r.stdout + r.stderr

        rc, out = run(str(tool), '--repo', str(repo), env_extra={'HOME': str(home_empty)})
        cases.append(('the CLI reports MISSING and still exits 0 -- a missing '
                      'credential degrades a session, never takes one down',
                      rc == 0 and 'MISSING' in out, f'rc={rc} {out[:300]}'))
        rc, out = run(str(tool), '--repo', str(repo), '--check',
                      env_extra={'HOME': str(home_empty)})
        cases.append(('--check is the one caller that exits 1 on MISSING',
                      rc == 1 and 'MISSING' in out, f'rc={rc} {out[:300]}'))
        rc, out = run(str(tool), '--repo', str(repo), '--check',
                      env_extra={'HOME': str(home_ok)})
        cases.append(('--check exits 0 when every source is on disk '
                      '(the negative control: this case must be able to fail '
                      'the one above)', rc == 0 and 'OK' in out,
                      f'rc={rc} {out[:300]}'))

        # --- 7: end to end, the token never reaches disk --------------------
        source = tmp / 'source-repo'
        source.mkdir()
        for cmd in (['init', '-q'], ['config', 'user.email', 'harness@example.com'],
                    ['config', 'user.name', 'harness']):
            subprocess.run(['git', '-C', str(source), *cmd], check=True,
                           capture_output=True, text=True)
        (source / 'practices').mkdir()
        (source / 'practices' / 'p.md').write_text('fixture\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(source), 'add', '-A'], check=True,
                       capture_output=True, text=True)
        subprocess.run(['git', '-C', str(source), 'commit', '-qm', 'seed'],
                       check=True, capture_output=True, text=True)

        bootstrap = ROOT / 'tools' / 'precedent_source_bootstrap.py'
        clone, config = tmp / 'clone', tmp / 'cfg.json'
        rc, out = run(str(bootstrap), '--level', 'individual', '--name',
                      'precedent-individual', '--repo-url', f'file://{source}',
                      '--clone', str(clone), '--config', str(config),
                      '--remote-only', 'false',
                      env_extra={psc.TOKEN_ENV: TOKEN})
        cloned = (clone / 'practices' / 'p.md').is_file()
        on_disk = ''
        for f in (clone / '.git' / 'config', config):
            if f.is_file():
                on_disk += f.read_text(encoding='utf-8')
        cases.append(('the bootstrap clones with a token set, and the token '
                      'is in NEITHER the clone\'s git config NOR the config '
                      'file it writes', rc == 0 and cloned and TOKEN not in on_disk,
                      f'rc={rc} cloned={cloned} {out[:300]}'))

        # --- 8: a team source is cloned by path, and records nothing --------
        # A real repo to clone FROM, named the way the set is named: the URL
        # is built as <base>/<name>, which is the whole convention under test.
        remotes = tmp / 'remotes'
        remotes.mkdir()
        subprocess.run(['git', 'clone', '-q', f'file://{source}',
                        str(remotes / 'precedent-team-fixture')], check=True,
                       capture_output=True, text=True)
        write_cfg('../team-fixture-clone')
        rc, out = run(str(bootstrap), '--teams-from', str(repo),
                      '--remote-only', 'false',
                      env_extra={psb.BASE_URL_ENV: f'file://{remotes}',
                                 'HOME': str(home_empty)})
        # the fixture set is named precedent-team-fixture, so file://<tmp>/precedent-team-fixture
        cases.append(('--teams-from clones each declared team source to the '
                      'sibling path the repo declares',
                      rc == 0 and (repo.parent / 'team-fixture-clone' / 'practices').is_dir(),
                      f'rc={rc} {out[:400]}'))
        cases.append(('...and writes no user config for it: a team source '
                      'resolves by path, so there is nothing to record',
                      not (home_empty / '.config' / 'precedent' / 'config.json')
                      .read_text(encoding='utf-8').count('team'),
                      (home_empty / '.config' / 'precedent' / 'config.json')
                      .read_text(encoding='utf-8')))

        # --- 9: no base url is REPORTED, never silently skipped -------------
        shutil.rmtree(repo.parent / 'team-fixture-clone', ignore_errors=True)
        rc, out = run(str(bootstrap), '--teams-from', str(repo),
                      '--remote-only', 'false', env_extra={'HOME': str(home_empty)})
        cases.append(('with no base url the team source is named on stderr as '
                      'NOT in force, rather than passing quietly',
                      rc == 0 and psb.BASE_URL_ENV in out
                      and 'NOT in force' in out, f'rc={rc} {out[:300]}'))

        # --- 9b: a failed clone names WHICH failure it was -----------------
        # Each branch asserts the words that branch alone prints
        # (practice: control-asserts-which-failure): "it failed" is the
        # report that sends somebody to re-issue a credential that was fine.
        # The two live strings were taken from real git output against
        # github.com on 2026-09-09, not invented -- one with no credential,
        # one with a deliberately invalid PRECEDENT_GIT_TOKEN.
        for output, want in (
            ("fatal: could not read Username for 'https://github.com': "
             "terminal prompts disabled", 'NO CREDENTIAL was available'),
            ('remote: Invalid username or token. Password authentication is '
             'not supported for Git operations.', 'AUTHENTICATION was refused'),
            ('remote: Repository not found.', 'NOT FOUND'),
            ('error: some unrelated network thing', 'it'),
        ):
            got = psb._diagnose(output)
            cases.append((f'a clone failure reading {output[:38]!r} is '
                          f'diagnosed as {want!r}, not merely as a failure',
                          # the fallback is asserted as an EXACT value: 'it'
                          # is a substring of half the English language, so
                          # `want in got` would pass on any branch at all.
                          (got == want if want == 'it' else want in got), got))

        # --- 10: the announced degradation when the module is not vendored --
        lonely = tmp / 'lonely-tools'
        lonely.mkdir()
        shutil.copy(bootstrap, lonely / bootstrap.name)
        rc, out = run(str(lonely / bootstrap.name), '--level', 'individual',
                      '--name', 'x', '--repo-url', f'file://{source}',
                      '--clone', str(tmp / 'clone2'), '--config', str(tmp / 'c2.json'),
                      '--remote-only', 'false', env_extra={psc.TOKEN_ENV: TOKEN})
        cases.append(('a bootstrap vendored WITHOUT the credentials module '
                      'says so when a token is set, naming the file and the '
                      'remedy -- it does not ignore the token in silence',
                      'precedent_source_credentials.py is not beside this file' in out
                      and 'precedent_vendor_engine.py refresh' in out,
                      f'rc={rc} {out[:400]}'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [(c[0], c[2]) for c in cases if not c[1]]
    check(f'the private-source credential never reaches disk or argv, and its '
          f'absence is reported ({len(cases)} stated cases)',
          not bad, '; '.join(f"{n} -- {d[:600]}" for n, d in bad))


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

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-source-bootstrap-'))
    cases = []
    try:
        bootstrap_tool = ROOT / 'tools' / 'precedent_source_bootstrap.py'
        resolve_tool = ROOT / 'tools' / 'precedent_resolve.py'

        def run(*args, env_extra=None):
            env = dict(os.environ)
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
                          env_extra={'HOME': str(home6),
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
                            env={**os.environ, 'HOME': str(home_hook),
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
                             env={**os.environ, 'HOME': str(live_home),
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
        r13 = subprocess.run(['bash', str(nourl_hook)], capture_output=True,
                             text=True, timeout=180,
                             env={**os.environ, 'HOME': str(nourl_home),
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
        r14 = subprocess.run(['bash', str(raw_template)], capture_output=True,
                             text=True, timeout=180,
                             env={**os.environ, 'HOME': str(raw_home),
                                  'CLAUDE_PROJECT_DIR': str(ROOT),
                                  'CLAUDE_CODE_REMOTE': 'true'})
        cases.append(('the RAW template, run without being instantiated, still '
                      'recognises itself as uninstantiated and exits 0 without '
                      'trying to clone its own placeholder',
                      r14.returncode == 0
                      and 'no repository URL' in (r14.stdout + r14.stderr),
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


def check_instantiated_template_links_survive_the_copy():
    """A file a template tells you to COPY INTO A REPO ROOT cannot carry a
    link that only resolves from the template's own directory.

    templates/document-project/'s README says "copy every file
    in this directory into its root", and its AGENTS.md linked
    `../AGENTS.md.loader.template` and `../../INSTALL.md`. Both resolve
    inside templates/ and are dead the moment the file is where it is
    supposed to end up -- and the same file already linked three other
    upstream documents by absolute URL, so the convention was established
    and these two simply missed it. Found 2026-09-10 installing
    precedent-beta-v01 into a real project; nothing here looked for it.

    The rule is about the DESTINATION, not the file: a template's own
    README is read where it sits and is deleted at instantiation (its step
    6 says so), so `../harness/README.md` is correct THERE and wrong in
    AGENTS.md. So this excludes the READMEs and checks everything else.

    An upward link is the only failure mode: a link INTO the template's own
    subtree (`.claude/settings.json`, `precedent.json`) copies along with
    the file and keeps working."""
    import re
    template_root = ROOT / 'templates' / 'document-project'
    if not template_root.is_dir():
        check('instantiated template files carry no links that die on the '
              'copy', True, '')
        return
    link_re = re.compile(r'\]\(\s*(\.\./[^)\s]*)')
    bad = []
    for f in sorted(template_root.rglob('*.md')):
        if f.name == 'README.md':
            continue          # read in place, deleted at instantiation
        for i, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            for target in link_re.findall(line):
                bad.append(f'{f.relative_to(ROOT)}:{i} -> {target}')
    check('every file this template copies into a repo root links upstream '
          'documents absolutely, not by a path that only resolves inside '
          'templates/',
          not bad,
          '; '.join(bad))


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
            r = subprocess.run([sys.executable, 'tools/precedent_check.py'],
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
                      f'violated: {violated_slugs}\n' + out0[-900:]))
        cases.append(('the baseline summary counts no exemptions',
                      ' 0 exempted' in out0, out0[-300:]))
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
                          f'VIOLATION  {target}' not in out2, out2[-900:]))
            cases.append((f'and says so out loud: {target!r} is named EXEMPT '
                          f'with its recorded reason, never silently dropped',
                          f'EXEMPT     {target}' in out2
                          and 'exempted on purpose' in out2, out2[-900:]))
            cases.append(('the summary line carries `exempted` as its own '
                          'category', ' 1 exempted' in out2, out2[-300:]))

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
                      and ' 0 exempted' in out3, out3[-900:]))
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

        # §0: vendored catalogue, a live sibling team source, a repo-local
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
        cases.append(('and does NOT exclude a team source resolved from a '
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


def check_declared_identity_has_a_passing_state_in_a_shared_repo():
    """`commit-author` and `buenos-aires-dates` have to be able to PASS in
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
                  'precedent_identity.py, so its own commit-author and '
                  'buenos-aires-dates checks can import it',
                  (seeded / 'precedent_identity.py').is_file(),
                  str(sorted(f.name for f in seeded.iterdir()))))
    cases.append(('and still does NOT receive precedent_resolve.py -- the '
                  'consumer-only boundary this move was careful not to '
                  'erase',
                  not (seeded / 'precedent_resolve.py').is_file(),
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


def check_freshness_gate_fires():
    """The very deep check's freshness gate, as stated cases against
    throwaway repos (practice: very-deep-check).

    WHY AS FIXTURES RATHER THAN AGAINST THIS TREE. A gate that refuses a
    stale checkout is invisible when the checkout is current: running it
    here proves only that this clone happens to be up to date, which is a
    fact about the clone. The states that matter -- behind, diverged, dirty,
    branch-never-pushed -- have to be built. Both halves are asserted: that
    it refuses what it should, and that it does NOT refuse what it
    shouldn't, since a gate that fires on correct work is worse than none.

    The freshen half carries negative controls deliberately. Fast-forwarding
    a diverged branch deletes commits nobody asked it to delete, and a dirty
    tree left half-merged is worse than a stale one left alone -- so those
    two are asserted to change nothing, not merely to warn."""
    import tempfile
    import very_deep_check as vdc

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a],
                              capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        upstream, work = tmp / 'upstream', tmp / 'work'
        upstream.mkdir()
        _git(upstream, 'init', '-q', '-b', 'main')
        _git(upstream, 'config', 'user.email', 'harness@example.com')
        _git(upstream, 'config', 'user.name', 'Harness')
        (upstream / 'f.txt').write_text('one\n')
        _git(upstream, 'add', '-A'); _git(upstream, 'commit', '-qm', 'one')
        subprocess.run(['git', 'clone', '-q', f'file://{upstream}', str(work)],
                       capture_output=True, text=True)
        _git(work, 'config', 'user.email', 'harness@example.com')
        _git(work, 'config', 'user.name', 'Harness')

        results = []
        results.append(('current clone passes',
                        vdc.freshness(work)['status'] == 'current'))

        # A repo with no origin at all is not stale -- there is nothing to be
        # behind. Refusing it would fail every fixture repo pass 1 builds.
        solo = tmp / 'solo'; solo.mkdir()
        _git(solo, 'init', '-q', '-b', 'main')
        _git(solo, 'config', 'user.email', 'harness@example.com')
        _git(solo, 'config', 'user.name', 'Harness')
        (solo / 'f.txt').write_text('x\n')
        _git(solo, 'add', '-A'); _git(solo, 'commit', '-qm', 'x')
        results.append(('a repo with no origin is not reported stale',
                        vdc.freshness(solo)['status'] == 'no-remote'))

        # Not a git checkout at all: a repo-local source inside the parent.
        plain = tmp / 'plain'; plain.mkdir()
        results.append(('a non-checkout directory is skipped, not failed',
                        vdc.freshness(plain)['status'] == 'not-a-checkout'))

        # Behind.
        (upstream / 'f.txt').write_text('one\ntwo\n')
        _git(upstream, 'add', '-A'); _git(upstream, 'commit', '-qm', 'two')
        v = vdc.freshness(work)
        results.append(('a clone behind origin is refused',
                        v['status'] == 'behind' and v['behind'] == 1))

        # --freshen on a DIRTY tree must decline and change nothing.
        (work / 'scratch.txt').write_text('uncommitted\n')
        before = _git(work, 'rev-parse', 'HEAD').stdout.strip()
        v_dirty = vdc.freshen(work, vdc.freshness(work, fetch=False))
        after = _git(work, 'rev-parse', 'HEAD').stdout.strip()
        results.append(('--freshen declines a dirty tree and moves nothing',
                        v_dirty['status'] == 'behind' and before == after))
        (work / 'scratch.txt').unlink()

        # --freshen on a clean tree that is behind must actually advance it.
        v_clean = vdc.freshen(work, vdc.freshness(work, fetch=False))
        results.append(('--freshen fast-forwards a clean tree that is behind',
                        v_clean['status'] == 'current'))

        # Diverged: --freshen must refuse, and the local commit must survive.
        (upstream / 'f.txt').write_text('one\ntwo\nthree\n')
        _git(upstream, 'add', '-A'); _git(upstream, 'commit', '-qm', 'three')
        (work / 'local.txt').write_text('mine\n')
        _git(work, 'add', '-A'); _git(work, 'commit', '-qm', 'local only')
        v = vdc.freshness(work)
        mine = _git(work, 'rev-parse', 'HEAD').stdout.strip()
        v2 = vdc.freshen(work, v)
        results.append(('a diverged clone is refused, and --freshen leaves its '
                        'local commit alone',
                        v['status'] == 'diverged' and v2['status'] == 'diverged'
                        and _git(work, 'rev-parse', 'HEAD').stdout.strip() == mine
                        and (work / 'local.txt').exists()))

        # A branch that exists only locally: the network is fine, so the
        # verdict must say so rather than blaming the fetch.
        _git(work, 'checkout', '-q', '-b', 'never-pushed')
        v = vdc.freshness(work)
        results.append(('a local-only branch reports branch-not-on-origin, '
                        'not a fetch failure',
                        v['status'] == 'branch-not-on-origin'))

        failed = [name for name, ok in results if not ok]
        check(f'the very deep check refuses a stale repo ({len(results)} stated '
              f'cases: a current clone, a remoteless repo, a non-checkout, a '
              f'behind clone, --freshen against dirty and clean trees, a '
              f'diverged clone whose commit must survive, and a local-only '
              f'branch)',
              not failed,
              '; '.join(failed) if failed else '')


def check_unmerged_branch_verdicts():
    """The unmerged half of the very deep check's branch sweep (practice:
    very-deep-check).

    The case that carries this check is the rebased branch. `merge-base
    --is-ancestor` reads commit identity, so a branch whose every patch was
    replayed onto the integration branch stays "unmerged" forever while
    carrying no work at all. Reporting that as unlanded is not a cosmetic
    error: it is the finding that teaches a reader to wave the whole list
    through, at which point the genuinely-unlanded branch beside it goes
    with them. So both are asserted here, side by side in one fixture --
    one branch that really carries work, one that only appears to."""
    import tempfile
    import very_deep_check as vdc

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a],
                              capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # A branch whose one commit is genuinely not on main.
        _git(up, 'checkout', '-q', '-b', 'real-work')
        (up / 'feature.txt').write_text('unlanded\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'unlanded work')

        # A branch whose commit is replayed onto main -- a different commit
        # hash, an identical patch. This is the squash/rebase shape.
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'checkout', '-q', '-b', 'already-landed')
        (up / 'landed.txt').write_text('landed\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'landed work')
        patch = _git(up, 'format-patch', '-1', '--stdout').stdout
        _git(up, 'checkout', '-q', 'main')
        (tmp / 'p.patch').write_text(patch)
        _git(up, 'am', '-q', str(tmp / 'p.patch'))
        # Reword the replayed commit. `git am` preserves the author and the
        # author date, so with the same message, tree and parent it produces
        # a BYTE-IDENTICAL commit whenever both commits land in the same
        # second -- and then the branch really is an ancestor of main and
        # the fixture silently tests nothing. That made this case pass or
        # fail on the clock (observed both ways within one minute). A
        # reworded commit is also the truer shape: a squash-merge rewrites
        # the message.
        _git(up, 'commit', '-q', '--amend', '-m', 'landed work (squashed)')
        _git(up, 'checkout', '-q', 'main')

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        scan = vdc.scan_branches(work, 'main')
        rows = {r['name']: r for r in (scan or {}).get('unmerged', [])}

        results = [
            ('both branches are reported as not merged',
             set(rows) == {'real-work', 'already-landed'}),
            ('a branch carrying genuinely unlanded work is counted as such',
             rows.get('real-work', {}).get('unique') == 1
             and 'CARRIES' in (rows.get('real-work', {}).get('verdict') or '')),
            ('a rebased branch is NOT reported as unlanded work',
             rows.get('already-landed', {}).get('unique') == 0
             and 'ALREADY LANDED' in (rows.get('already-landed', {}).get('verdict') or '')),
            ('every unmerged branch carries a verdict, never none',
             all(r.get('verdict') for r in rows.values())),
            ('each row carries the evidence the verdict rests on',
             all(r.get('ahead') is not None and r.get('last')
                 for r in rows.values())),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the very deep check tells unlanded work from a rebased branch '
              f'({len(results)} stated cases, the rebased one being the '
              f'controlling case)',
              not failed, '; '.join(failed) if failed else '')


def check_endgame_merge_finds_the_silent_drop():
    """The endgame-merge rehearsal (practice: very-deep-check, pass 4).

    THE CASE THAT CARRIES THIS CHECK is the file that disappears without a
    conflict. A reverted merge on the base branch splits the integration
    branch's files into two classes, and only one of them is visible: a file
    touched again since the merge base conflicts and stops the merge, while
    a file untouched since simply does not arrive -- no conflict, no
    message. The 2026-09-07 rehearsal that missed this checked two files,
    found both present, and concluded the trap did not fire; both happened
    to be in the visible class.

    So a non-zero finding count is NOT what is asserted here. The fixture
    plants one file of each class and this check asserts WHICH path lands in
    WHICH set by name -- a rehearsal that reported the conflicting file and
    stayed silent about the dropped one would satisfy any count-based
    assertion while reproducing the exact miss.

    The clean case is asserted beside it, from the same fixture with the
    revert undone: a check that cannot come back clean is one that will be
    ignored the first time it is inconvenient."""
    import tempfile
    import very_deep_check as vdc

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a],
                              capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # The integration branch, with the two classes of file on it.
        _git(up, 'checkout', '-q', '-b', 'beta')
        (up / 'keep.txt').write_text('one\n')
        (up / 'drop.txt').write_text('one\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'beta work')

        # The accident: beta merged into main, then reverted. The revert
        # undoes the FILES and leaves the COMMITS in main's log, which is
        # what makes git treat them as already merged afterwards.
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'merge', '--no-ff', '-q', '-m', 'accidental merge', 'beta')
        merge_sha = _git(up, 'rev-parse', 'HEAD').stdout.strip()
        _git(up, 'revert', '-m', '1', '--no-edit', merge_sha)

        # Beta carries on: one of the two files is touched again (so it will
        # conflict), one is not (so it will vanish), plus new work that
        # never existed on main at all.
        _git(up, 'checkout', '-q', 'beta')
        (up / 'keep.txt').write_text('two\n')
        (up / 'later.txt').write_text('new\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'more beta work')
        _git(up, 'checkout', '-q', 'main')

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        r = vdc.endgame_merge(work, target='beta', base='main') or {}
        dropped, conflicts = set(r.get('dropped') or []), set(r.get('conflicts') or [])

        # Same fixture, revert undone: the merge must come back clean.
        _git(up, 'revert', '--no-edit', 'HEAD')   # revert the revert
        _git(work, 'fetch', '-q', 'origin')
        clean = vdc.endgame_merge(work, target='beta', base='main') or {}

        worktrees = _git(work, 'worktree', 'list').stdout.strip().splitlines()

        results = [
            ('the file untouched since the merge base is named as dropped',
             'drop.txt' in dropped),
            ('the file touched since the merge base is a CONFLICT, not a drop',
             'keep.txt' in conflicts and 'keep.txt' not in dropped),
            ('work newer than the merge base arrives cleanly, in neither set',
             'later.txt' not in dropped and 'later.txt' not in conflicts),
            ('the run is reported as carrying findings',
             r.get('status') == 'findings'),
            ('undoing the revert makes the same merge come back clean',
             clean.get('status') == 'clean' and not clean.get('dropped')),
            ('the throwaway worktree is removed, whatever the outcome',
             len(worktrees) == 1),
        ]
        failed = [name for name, ok in results if not ok]
        check(f'the endgame-merge rehearsal names the silently-dropped path '
              f'({len(results)} stated cases; the drop/conflict split is the '
              f'controlling one)',
              not failed,
              (f"{'; '.join(failed)} -- dropped={sorted(dropped)}, "
               f"conflicts={sorted(conflicts)}") if failed else '')


def check_branch_scan_sees_every_branch():
    """The branch sweep must enumerate what ORIGIN has, not what this clone
    happened to fetch (practice: very-deep-check).

    THE CASE THAT CARRIES THIS CHECK is the single-branch clone, which is
    not an edge case: it is what the harness hands every remote session
    (AGENTS.md's add_repo entry), and the freshness gate above fetches only
    the ONE branch it compares. `scan_branches` reads `refs/remotes/origin`,
    so on such a clone it enumerated two refs on a repo with forty and
    reported "(none)" -- which reads as a clean sweep, not as a scan that
    never ran. That is the same empty-result-reads-as-pass failure AGENTS.md
    records for the `scope: 'tree'` checks, and it costs more here: the
    sweep IS pass 4's branch bullet, so a false all-clear silently ends the
    only step that would have found unlanded work.

    Both halves are asserted. The first is the fix: a narrow clone must
    still see every branch. The second is the negative control that keeps
    the fix honest -- when origin genuinely cannot be reached, the scan must
    say it could not tell, NOT fall back to the empty lists that started
    this. A repair that turns one silent wrong answer into another is not a
    repair."""
    import tempfile
    import very_deep_check as vdc

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a],
                              capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up = tmp / 'up'; up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'f.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        for b in ('landed', 'open-one', 'open-two'):
            _git(up, 'checkout', '-q', '-b', b)
            (up / f'{b}.txt').write_text(b + '\n')
            _git(up, 'add', '-A'); _git(up, 'commit', '-qm', b)
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'merge', '-q', '--no-ff', 'landed', '-m', 'merge landed')

        # Exactly what the harness produces: one branch, one refspec.
        narrow = tmp / 'narrow'
        subprocess.run(['git', 'clone', '-q', '--single-branch', '--branch',
                        'main', f'file://{up}', str(narrow)],
                       capture_output=True, text=True)
        refs_before = len([r for r in _git(
            narrow, 'for-each-ref', '--format=%(refname:short)',
            'refs/remotes/origin').stdout.splitlines() if r])

        scan = vdc.scan_branches(narrow, 'main') or {}
        merged = {r['name'] for r in (scan.get('merged') or [])}
        unmerged = {r['name'] for r in (scan.get('unmerged') or [])}

        results = [
            ('the fixture really is a narrow clone (else this proves nothing)',
             refs_before <= 2),
            ('a merged branch on origin is found even though the clone never '
             'fetched it', 'landed' in merged),
            ('both unmerged branches on origin are found',
             {'open-one', 'open-two'} <= unmerged),
            ('the scan reports itself complete when it reached origin',
             not scan.get('unfetched') and not scan.get('unreachable')),
        ]

        # NEGATIVE CONTROL: origin unreachable. Empty lists are now a lie, so
        # the scan must mark itself incomplete rather than report them bare.
        dark = tmp / 'dark'
        subprocess.run(['git', 'clone', '-q', '--single-branch', '--branch',
                        'main', f'file://{up}', str(dark)],
                       capture_output=True, text=True)
        _git(dark, 'remote', 'set-url', 'origin', 'file:///nonexistent/gone.git')
        d = vdc.scan_branches(dark, 'main') or {}
        results.append(
            ('an unreachable origin is reported as "cannot tell", never as an '
             'empty (clean) sweep',
             not d.get('merged') and not d.get('unmerged')
             and bool(d.get('unreachable'))))

        failed = [name for name, ok in results if not ok]
        check(f'the very deep check\'s branch sweep sees every branch origin '
              f'has, not only what this clone fetched ({len(results)} stated '
              f'cases, the single-branch clone being the controlling case and '
              f'an unreachable origin the negative control)',
              not failed, '; '.join(failed) if failed else '')


def check_very_deep_check_authenticates_its_own_fetches():
    """very_deep_check's network calls carry the credential the environment
    holds (practice: very-deep-check; durable-fix).

    THE INCIDENT (2026-09-10). In a session where the credential route was
    working exactly as INSTALL.md section 8 describes -- all four private
    sources cloned before the first turn -- the very deep check refused to
    read a line: every source failed its freshness gate with "could not read
    Username for 'https://github.com'". The token was fine. `_run_git`
    shelled out to plain `git` while the credential lived behind a helper
    only precedent_source_bootstrap.py passed, so a source could be cloned
    at session start and then not fetched by the check that reads it.

    The controlling case is the NEGATIVE one: with no token in the
    environment the flags must be absent entirely. A tool that always
    passes a helper offers a credential to whatever transport is
    configured, and would pass a naive "are the flags there" assertion
    while being the worse bug.
    """
    import very_deep_check as vdc
    import tempfile

    real_env = dict(os.environ)
    try:
        os.environ.pop('PRECEDENT_GIT_TOKEN', None)
        vdc._ORIGIN_URL.clear()
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / 'r'
            repo.mkdir()
            subprocess.run(['git', '-C', str(repo), 'init', '-q'],
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', str(repo), 'remote', 'add', 'origin',
                            'https://github.com/example/example'],
                           capture_output=True, text=True)

            no_token = vdc._credential_args(repo)

            os.environ['PRECEDENT_GIT_TOKEN'] = 'not-a-real-token'
            vdc._ORIGIN_URL.clear()
            with_token = vdc._credential_args(repo)

            # A file:// remote needs no credential and must never be offered
            # one, whatever the environment holds.
            local = pathlib.Path(tmp) / 'l'
            local.mkdir()
            subprocess.run(['git', '-C', str(local), 'init', '-q'],
                           capture_output=True, text=True)
            subprocess.run(['git', '-C', str(local), 'remote', 'add', 'origin',
                            f'file://{tmp}/upstream'], capture_output=True, text=True)
            vdc._ORIGIN_URL.clear()
            local_args = vdc._credential_args(local)

            results = [
                ('no token in the environment means no credential flags at '
                 'all (the controlling case)', no_token == []),
                ('a token in the environment produces credential flags',
                 bool(with_token)),
                ('the flags clear any helper configured elsewhere first',
                 'credential.helper=' in with_token),
                ('the token VALUE never appears in the argument list',
                 not any('not-a-real-token' in a for a in with_token)),
                ('the helper names the variable instead',
                 any('PRECEDENT_GIT_TOKEN' in a for a in with_token)),
                ('a file:// remote is never offered a credential',
                 local_args == []),
                ('network subcommands are recognised by name, so a fetch '
                 'added later is covered too',
                 {'fetch', 'ls-remote', 'pull'} <= vdc._NETWORK_GIT),
                ('a non-network subcommand is not given credential flags',
                 'log' not in vdc._NETWORK_GIT and 'config' not in vdc._NETWORK_GIT),
            ]
            failed = [name for name, ok in results if not ok]
            check(f'the very deep check authenticates its own fetches '
                  f'({len(results)} stated cases, an empty environment being '
                  f'the negative control)',
                  not failed, '; '.join(failed) if failed else '')
    finally:
        os.environ.clear()
        os.environ.update(real_env)
        vdc._ORIGIN_URL.clear()


def check_merged_branches_carry_a_date_and_a_staleness_verdict():
    """A merged, undeleted branch is reported with the date it last moved
    and whether it is past the declared stale threshold
    (practice: very-deep-check, pass 4).

    THE GAP (asked 2026-09-10, by Morgan, of a real sweep). The merged half
    of the branch sweep was a bare list of names. That list ends in a
    deletion, and a name with no date cannot be acted on: the branch merged
    this morning and the one merged last quarter render identically, so the
    reader either deletes blind or -- what actually happens -- defers the
    whole list again. Measured on this repo the same day: 69 merged
    branches, median age 3 days, oldest 39, and no way to see any of that.

    The threshold is a DECLARED input, so the controlling case here is not
    "does 30 days work" but "does the declared number reach the sweep at
    all" -- a default silently overriding a repo's own value would mark the
    wrong branches and look exactly like a working feature.
    """
    import very_deep_check as vdc
    import tempfile, datetime

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a],
                              capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'base.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # Two merged branches at KNOWN ages, straddling the threshold. The
        # dates are forced through the commit environment rather than taken
        # from the clock, so this fixture owns its own state and cannot pass
        # or fail on when it happens to run (practice: fixture-owns-its-state
        # -- the neighbouring unmerged-verdict check was made to fail on the
        # clock exactly once, which is why this is explicit here).
        for branch, days in (('long-done', 400), ('just-landed', 1)):
            when = (datetime.datetime.now(datetime.timezone.utc)
                    - datetime.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S%z')
            _git(up, 'checkout', '-q', 'main')
            _git(up, 'checkout', '-q', '-b', branch)
            (up / f'{branch}.txt').write_text(branch + '\n')
            _git(up, 'add', '-A')
            subprocess.run(['git', '-C', str(up), 'commit', '-qm', branch],
                           capture_output=True, text=True,
                           env={**os.environ,
                                'GIT_AUTHOR_DATE': when,
                                'GIT_COMMITTER_DATE': when,
                                'PRECEDENT_ALLOW_ANY_AUTHOR': '1'})
            _git(up, 'checkout', '-q', 'main')
            _git(up, 'merge', '-q', '--no-ff', '-m', f'merge {branch}', branch)

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)

        scan = vdc.scan_branches(work, 'main', stale_days=90) or {}
        rows = {r['name']: r for r in (scan.get('merged') or [])}

        results = [
            ('both merged branches are reported as merged',
             set(rows) == {'long-done', 'just-landed'}),
            ('every merged row carries the date it last moved',
             all(r.get('last') and r.get('age_days') is not None
                 for r in rows.values())),
            ('the age is the real one, not the date of the merge or the clone',
             rows.get('long-done', {}).get('age_days', 0) >= 399),
            ('a branch past the threshold is marked stale',
             rows.get('long-done', {}).get('stale') is True),
            ('a branch inside the threshold is NOT marked stale',
             rows.get('just-landed', {}).get('stale') is False),
            ('the scan reports which threshold it applied',
             scan.get('stale_days') == 90),
        ]

        # NEGATIVE CONTROL, and the controlling case: the same fixture at a
        # threshold that puts BOTH branches on the recent side. If the
        # passed-in number were ignored in favour of the default, 'long-done'
        # would still read stale and every assertion above would still pass.
        loose = vdc.scan_branches(work, 'main', stale_days=1000) or {}
        loose_rows = {r['name']: r for r in (loose.get('merged') or [])}
        results.append(
            ('the DECLARED threshold decides, not a default compiled in -- '
             'at 1000 days nothing is stale',
             loose_rows and not any(r.get('stale') for r in loose_rows.values())))

        # And a repo declaring its own value gets it without being asked.
        (work / 'precedent.json').write_text(
            json.dumps({'format_version': 1, 'branch_stale_days': 90}), encoding='utf-8')
        declared = vdc.scan_branches(work, 'main') or {}
        results.append(
            ("a repo's own precedent.json branch_stale_days is read when no "
             "threshold is passed",
             declared.get('stale_days') == 90))

        failed = [name for name, ok in results if not ok]
        check(f'the very deep check dates every merged branch and marks the '
              f'stale ones ({len(results)} stated cases, a threshold that '
              f'makes nothing stale being the negative control)',
              not failed, '; '.join(failed) if failed else '')


def check_public_consumer_does_not_materialize_private_text():
    """A public consumer repo's TRACKED practices/ tree must not carry a
    private source's practice text (practice: very-deep-check, found by it).

    build_views.py already refuses to render a private source into a public
    repo's loader block, and precedent_materialize.py already refuses to
    mint a private repo's URL into the materialized tree -- but the whole
    practice FILE was copied in regardless, which discloses strictly more
    than the link so carefully withheld. Reproduced on a real fresh install
    built from INSTALL.md section 0: thirteen individual-level practices
    landed in a `visibility: public` consumer's tracked tree, one of them
    carrying a person's name and email address.

    Three properties, because fixing the first alone breaks the others:

    1. No private-level text in a public consumer's tree.
    2. NOTHING ELSE IS LOST. The private sources are dropped and the set
       RE-RESOLVED, not filtered out of a finished result -- a private
       practice can win a slug a publishable source also declares, and
       deleting the winner does not promote the runner-up. Filtering lost
       a universal practice exactly this way.
    3. The two renderers agree. precedent_sync_views.py must pass the same
       `omits_private` build_views.py computes for itself, or the standing
       instruction differs between them and `generated-artifact-provenance`
       reports the file the documented install step just wrote as
       hand-edited -- with no state of the repo able to satisfy it.

    A PRIVATE consumer is the control: nothing may be withheld there."""
    import tempfile, shutil
    import json as _json
    import precedent_sync_views as psv
    import build_views as bv

    def _consumer(tmp, visibility):
        repo = tmp / f'consumer-{visibility}'
        (repo / 'precedent' / 'universal').mkdir(parents=True)
        shutil.copytree(PRACTICES_DIR, repo / 'precedent' / 'universal' / 'practices')
        (repo / 'AGENTS.md').write_text(
            f'# Consumer\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n',
            encoding='utf-8')
        (repo / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main',
            'visibility': visibility,
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': 'precedent/universal'}]}), encoding='utf-8')
        return repo

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        # A stand-in individual source, declared the only way one may be:
        # in a user-level config, never in the repo's own tracked file.
        ind = tmp / 'precedent-individual'
        (ind / 'practices').mkdir(parents=True)
        (ind / 'practices' / 'private-only.md').write_text(
            '---\nslug: private-only\ntitle: A private rule\ntier: on-demand\n'
            'severity: default\napplies_to: ["**"]\noccasion: "x happens"\n'
            'index_clause: "do the private thing"\nstatus: active\n---\n'
            '## Rule\nSECRET-CANARY-VALUE applies.\n\n## Story\nBecause.\n',
            encoding='utf-8')
        user_cfg = tmp / 'user.json'
        user_cfg.write_text(_json.dumps(
            {'format_version': 1,
             'individual': {'name': 'precedent-individual',
                            'path': str(ind)}}),
            encoding='utf-8')

        results = []
        pub = _consumer(tmp, 'public')
        psv.sync(str(pub), user_config=str(user_cfg))
        pub_tree = sorted(f.name for f in (pub / 'practices').glob('*.md'))
        pub_text = '\n'.join(
            f.read_text(encoding='utf-8') for f in (pub / 'practices').glob('*.md'))
        # Every universal practice that is IN FORCE, not every file on
        # disk. A `status: retired` or `deduplicated` practice stays in the
        # tree as its own retirement record and is deliberately not
        # materialized -- precedent_materialize.py resolves the in-force
        # set, it does not copy a directory. Comparing against the raw glob
        # was correct only while the catalogue happened to hold no retired
        # practice; it failed the moment one did (2026-09-07,
        # merge-authorization-keyword), reporting a real, intended omission
        # as private-text filtering. (practice: verify-decomposition -- the
        # count was right, what it counted was not.)
        universal = sorted(
            f.name for f in PRACTICES_DIR.glob('*.md')
            if not re.search(r'^status:\s*(retired|deduplicated)\s*$',
                             f.read_text(encoding='utf-8'), re.M))

        results.append(('a public consumer materializes no private practice file',
                        'private-only.md' not in pub_tree))
        results.append(('nor any of its text',
                        'SECRET-CANARY-VALUE' not in pub_text))
        results.append(('and loses nothing the universal source defines -- the '
                        'set is re-resolved, not filtered',
                        set(universal) <= set(pub_tree)))
        # The other side of the same property, so relaxing the assertion
        # above cannot quietly become "materialize whatever you like": a
        # practice the catalogue has retired must be ABSENT. Conditional
        # because a catalogue with nothing retired has nothing to assert,
        # and a vacuous case that always passes is worse than no case.
        retired = sorted(set(f.name for f in PRACTICES_DIR.glob('*.md'))
                         - set(universal))
        if retired:
            results.append((f'and materializes no retired practice '
                            f'({len(retired)} in the catalogue) -- a '
                            f'retirement record is not an in-force rule',
                            not (set(retired) & set(pub_tree))))
        # The real property: regenerating with build_views.py must not change
        # the AGENTS.md that sync just wrote. That byte-comparison IS what
        # generated-artifact-provenance's check performs.
        after_sync = (pub / 'AGENTS.md').read_text(encoding='utf-8')
        # Run it the way the check does -- as its own process, against the
        # consumer's own root -- rather than reaching into an internal.
        shutil.copy(ROOT / 'tools' / 'build_views.py', pub / 'tools_bv.py')
        subprocess.run([sys.executable, str(pub / 'tools_bv.py'), '--agents-only'],
                       cwd=str(pub), capture_output=True, text=True)
        (pub / 'tools_bv.py').unlink(missing_ok=True)
        results.append(('build_views.py regenerates byte-identically to what '
                        'sync wrote, so generated-artifact-provenance can pass',
                        (pub / 'AGENTS.md').read_text(encoding='utf-8') == after_sync))

        priv = _consumer(tmp, 'private')
        psv.sync(str(priv), user_config=str(user_cfg))
        priv_tree = sorted(f.name for f in (priv / 'practices').glob('*.md'))
        results.append(('CONTROL: a private consumer still gets the private '
                        'practice -- nothing is withheld where the tree is not '
                        'published', 'private-only.md' in priv_tree))

        failed = [n for n, ok in results if not ok]
        check(f'a public consumer repo never materializes private practice '
              f'text into its tracked tree ({len(results)} stated cases, a '
              f'private consumer being the control)',
              not failed, '; '.join(failed) if failed else '')


def check_sync_refuses_to_write_from_incomplete_sources():
    """precedent_sync_views.py must not rewrite a repo's tracked tree when a
    declared source did not resolve (practice: very-deep-check, found by it).

    materialize() rebuilds practices/ by delete-and-rewrite, so an
    unreachable source does not merely go unrendered: every practice it
    contributed is DELETED from the tracked tree, with AGENTS.md and
    MANIFEST.json rewritten to match, one warning line, and exit 0. The diff
    reads as a deliberate removal.

    That is the CI state by definition -- a private team or individual
    source is unreachable in every continuous-integration checkout, which is
    exactly where an unattended sync would run. build_views.py already
    refuses this in as many words; this tool, the one the install and
    migration documents actually tell an adopter to run, did the opposite.
    The --check half of the same bug was found and fixed on 2026-09-06; the
    writing half was left, and it is the half that deletes.

    The two escape hatches are asserted too, because a refusal with no way
    past it would just be a different way to strand someone: --check must
    still inspect without writing, and --allow-missing-sources must still
    let a deliberate removal through."""
    import tempfile, shutil
    import json as _json
    import precedent_sync_views as psv
    import precedent_materialize as _pm
    import build_views as bv
    pm_MaterializeError = _pm.MaterializeError

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        repo, team = tmp / 'consumer', tmp / 'precedent-team-widgets'
        (repo / 'precedent' / 'universal').mkdir(parents=True)
        shutil.copytree(PRACTICES_DIR, repo / 'precedent' / 'universal' / 'practices')
        (team / 'practices').mkdir(parents=True)
        (team / 'practices' / 'widget-rule.md').write_text(
            '---\nslug: widget-rule\ntitle: Widgets are tested on the rig\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "changing widget firmware"\n'
            'index_clause: "test firmware on the rig, never the simulator"\n'
            'status: active\n---\n## Rule\nUse the rig.\n\n## Story\nIt drifted.\n',
            encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# Consumer\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n',
            encoding='utf-8')
        cfg = repo / 'precedent.json'
        cfg.write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main', 'visibility': 'private',
            'sources': [
                {'level': 'universal', 'name': 'precedent',
                 'path': 'precedent/universal'},
                {'level': 'team', 'name': 'precedent-team-widgets',
                 'path': str(team)}]}), encoding='utf-8')
        empty_user = tmp / 'user.json'
        empty_user.write_text(_json.dumps({'format_version': 1}), encoding='utf-8')

        psv.sync(str(repo), user_config=str(empty_user))
        landed = (repo / 'practices' / 'widget-rule.md').exists()

        # Now the CI state: the sibling clone is simply not there.
        shutil.rmtree(team)

        refused = False
        try:
            psv.sync(str(repo), user_config=str(empty_user))
        except pm_MaterializeError:
            refused = True
        survived = (repo / 'practices' / 'widget-rule.md').exists()

        # --check must still work: CI needs to inspect without writing.
        checked_ok = True
        try:
            psv.sync(str(repo), user_config=str(empty_user), check=True)
        except pm_MaterializeError:
            checked_ok = False
        survived_check = (repo / 'practices' / 'widget-rule.md').exists()

        # And the deliberate removal must still be possible.
        psv.sync(str(repo), user_config=str(empty_user), allow_missing=True)
        removed_on_request = not (repo / 'practices' / 'widget-rule.md').exists()

        results = [
            ('the team practice lands while its source is reachable', landed),
            ('an unreachable declared source REFUSES the write', refused),
            ('and the tracked practice it contributed survives', survived),
            ('--check still inspects without writing', checked_ok and survived_check),
            ('--allow-missing-sources still permits a deliberate removal',
             removed_on_request),
        ]
        failed = [n for n, ok in results if not ok]
        check(f'precedent_sync_views refuses to rewrite a tracked tree from an '
              f'incomplete source set ({len(results)} stated cases, the '
              f'unreachable-in-CI source being the controlling case)',
              not failed, '; '.join(failed) if failed else '')


def check_unlanded_work_is_reported_before_the_passes():
    """The very deep check must surface unlanded work BEFORE its checklist,
    not with the branch verdicts at the end (practice: very-deep-check).

    THE INCIDENT. The 2026-09-07 run rediscovered two missing source files
    from scratch, wrote them up as findings, and filed them as open TODO
    items -- while the fixes sat finished on a branch from the previous day,
    in both private sets, named in those branches' own commit subjects.
    Nothing had asked what was sitting unmerged, because the branch list only
    printed after every pass had already been worked.

    The sweep's two halves have different costs and different jobs. Deciding
    a branch's fate is judgment and stays in pass 4. Knowing what already
    exists is a list, costs nothing, and is the only step in the whole check
    that prevents work rather than finding it -- so it has to come first, and
    ORDER is the property, which is what this asserts.

    A branch carrying no unique commits (rebased or squash-merged in) must
    NOT appear here: it is a deletion candidate, not unlanded work, and
    listing it would train the reader to skim the section that exists to be
    read."""
    import tempfile, shutil
    import json as _json

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a],
                              capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir()
        _git(up, 'init', '-q', '-b', 'main')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'f.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')

        # A branch carrying real, unlanded work.
        _git(up, 'checkout', '-q', '-b', 'carries-work')
        (up / 'fix.txt').write_text('the fix nobody landed\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'a fix that never landed')
        _git(up, 'checkout', '-q', 'main')

        subprocess.run(['git', 'clone', '-q', f'file://{up}', str(work)],
                       capture_output=True, text=True)
        _git(work, 'config', 'user.email', 'harness@example.com')
        _git(work, 'config', 'user.name', 'Harness')
        (work / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': '.'}]}), encoding='utf-8')
        (work / 'practices').mkdir()
        shutil.copy(next(PRACTICES_DIR.glob('*.md')), work / 'practices')
        _git(work, 'add', '-A'); _git(work, 'commit', '-qm', 'declare a source')
        _git(work, 'push', '-q', 'origin', 'main')

        # HERMETIC, and it was not before.
        #
        # very_deep_check.py resolves the INDIVIDUAL source from a user-level
        # config outside any repo, so this fixture -- which declares one
        # universal source and nothing else -- was silently reaching the
        # machine's real precedent-individual clone. Its own output gave this
        # away once the failure detail above started printing it: a run
        # against a scratch repo was reporting "FRESHNESS -- declared
        # sources ... individual source 'precedent-individual'".
        #
        # That made the fixture inherit ambient state it never declared, and
        # the freshness gate is a HARD REFUSAL that returns before printing
        # anything -- so whenever that real clone was behind, diverged, or
        # slow to fetch, this check failed on a repository it is not testing.
        # It ran green for weeks and failed twice in the session that found
        # it, unreproducible in twelve isolated runs, which is exactly what a
        # test reading state it does not own looks like.
        #
        # Pointing PRECEDENT_USER_CONFIG at a path inside the temp directory
        # gives the resolver a config that legitimately declares no
        # individual source, so the fixture tests the fixture.
        env = dict(os.environ,
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-such-user-config.json'))
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
             '--repo', str(work)],
            capture_output=True, text=True, cwd=str(work), env=env)
        out = r.stdout

        results = []
        results.append(('the run produced output at all', bool(out.strip())))
        has_block = 'UNLANDED WORK' in out
        results.append(('unlanded work gets its own block', has_block))
        if has_block and 'Pass 1 —' in out:
            results.append(('it is printed BEFORE the checklist the session '
                            'works from -- the whole point',
                            out.index('UNLANDED WORK') < out.index('Pass 1 —')))
        else:
            results.append(('it is printed BEFORE the checklist the session '
                            'works from -- the whole point', False))
        results.append(('the branch carrying unlanded work is named',
                        'carries-work' in out.split('Pass 1 —')[0]))

        failed = [n for n, ok in results if not ok]
        # SAY WHAT THE TOOL ACTUALLY DID when this fails.
        #
        # This check ran green for weeks and then failed twice inside one
        # session (2026-09-07), both times reporting only which of its four
        # stated cases were false -- which is the symptom, never the cause.
        # It could not be reproduced in twelve isolated runs, so the cause is
        # something about a loaded full run, and the detail as written threw
        # away the one piece of evidence that would name it: what
        # very_deep_check.py itself printed and exited with. `UNLANDED WORK`
        # is printed UNCONDITIONALLY whenever the branch scan is not skipped,
        # so its absence means the tool returned before reaching that line --
        # most likely the freshness gate refusing, which it is designed to do
        # as a hard refusal rather than a warning. That is a guess until a
        # failing run says so itself, which is what this detail is for.
        #
        # Same lesson as the failure recap in main(): a count is not a
        # diagnosis, and re-running is what destroys the evidence.
        detail = ''
        if failed:
            tail = (out or '')[-400:].replace('\n', ' | ')
            detail = (f"{'; '.join(failed)} "
                      f"[very_deep_check.py exited {r.returncode}; "
                      f"stdout tail: {tail!r}; "
                      f"stderr tail: {(r.stderr or '')[-300:]!r}]")
        check(f'the very deep check reports unlanded work before its passes, '
              f'not after ({len(results)} stated cases)',
              not failed, detail)


def check_shallow_clone_never_fabricates_unlanded_work():
    """A branch whose merge base is out of reach must never be reported as
    carrying a COUNT of unlanded commits (practice: very-deep-check,
    control-asserts-which-failure).

    THE INCIDENT, 2026-09-08. The unlanded-work scan told a session that
    three branches of `precedent-individual` carried 22 commits of unlanded
    work. All three were plain ancestors of `main` -- every commit already
    landed, nothing to read. The scan had run against a shallow clone, where
    `git cherry` cannot find a merge base and answers by calling every commit
    unique.

    WHY THE EXISTING GUARD DID NOT FIRE. _unmerged_row already handled a
    shallow clone -- by checking `git cherry`'s exit code. There is no
    non-zero exit to catch: git exits 0 and prints a wrong answer, which is
    this repo's recurring shape (AGENTS.md records the same for `%P`
    reporting no parents and `rev-parse` printing a ref name where a hash
    belongs). A guard written for the wrong failure mode reads as coverage
    and is none.

    The direction of the error is what makes it expensive rather than merely
    wrong. This section exists to tell a session which branches to go read
    BEFORE the passes, so a fabricated count spends exactly the reading it
    was built to save -- and it fabricates in the environment every fresh
    session starts in.

    TWO CASES, because the fix has two outcomes and only one is a refusal.
    Deepening usually rescues the comparison, so the common path is a CORRECT
    answer, not an UNKNOWN one -- a control that only asserted the refusal
    would be satisfied by a tool that refused on every branch it saw.

    WHICH CASE DISCRIMINATES, measured rather than assumed: replayed against
    the pre-fix code, CASE 2 fails (on "no count of unlanded commits is
    invented" -- the bug itself) and CASE 1 PASSES. Case 1 is a regression
    guard on the right answer, NOT evidence the bug is caught, and a later
    session must not read it as such. The reason is worth knowing before
    trusting any fixture built this way: _fetch_all_heads falls back to an
    unbounded `git fetch origin` when its bounded one fails, so a local
    fixture gets full history handed to it and the buggy comparison comes
    out right anyway. In the wild the bounded fetch SUCCEEDED and simply did
    not reach far enough, no fallback ran, and the fabricated count stood --
    which is why the incident needed a real repository to show up at all.
    """
    import shutil, tempfile
    import json as _json

    def _git(d, *a):
        return subprocess.run(['git', '-C', str(d), *a],
                              capture_output=True, text=True)

    def _seed(up):
        _git(up, 'init', '-q', '-b', 'main')
        _git(up, 'config', 'user.email', 'harness@example.com')
        _git(up, 'config', 'user.name', 'Harness')
        (up / 'f.txt').write_text('base\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'base')
        _git(up, 'checkout', '-q', '-b', 'fully-landed')
        (up / 'g.txt').write_text('work that DID land\n')
        _git(up, 'add', '-A'); _git(up, 'commit', '-qm', 'landed work')
        _git(up, 'checkout', '-q', 'main')
        _git(up, 'merge', '-q', '--no-ff', 'fully-landed', '-m', 'merge it')
        # Deeper than the tool's routine --depth=50, so the merge base is
        # genuinely out of reach of a shallow clone. See the docstring.
        for i in range(70):
            (up / f'f{i}.txt').write_text(f'later {i}\n')
            _git(up, 'add', '-A'); _git(up, 'commit', '-qm', f'later {i}')

    def _consumer(work, tmp):
        _git(work, 'config', 'user.email', 'harness@example.com')
        _git(work, 'config', 'user.name', 'Harness')
        (work / 'precedent.json').write_text(_json.dumps({
            'format_version': 1, 'base_branch': 'main',
            'sources': [{'level': 'universal', 'name': 'precedent',
                         'path': '.'}]}), encoding='utf-8')
        (work / 'practices').mkdir(exist_ok=True)
        shutil.copy(next(PRACTICES_DIR.glob('*.md')), work / 'practices')
        _git(work, 'add', '-A'); _git(work, 'commit', '-qm', 'declare a source')

    def _run(work, tmp):
        env = dict(os.environ,
                   PRECEDENT_USER_CONFIG=str(tmp / 'no-such-user-config.json'))
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'very_deep_check.py'),
             '--repo', str(work)],
            capture_output=True, text=True, cwd=str(work), env=env)
        return r, r.stdout.split('Pass 1 —')[0]

    results = []
    diag = []

    # CASE 1 -- the real incident: shallow clone, origin still reachable.
    # The tool must deepen and give the CORRECT answer (nothing unlanded),
    # never a fabricated count.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        up, work = tmp / 'up', tmp / 'work'
        up.mkdir(); _seed(up)
        subprocess.run(['git', 'clone', '-q', '--depth', '1',
                        f'file://{up}', str(work)], capture_output=True)
        shallow = _git(work, 'rev-parse',
                       '--is-shallow-repository').stdout.strip()
        _consumer(work, tmp)
        _git(work, 'push', '-q', 'origin', 'main')
        r, head = _run(work, tmp)
        diag.append(f'case1 exit={r.returncode} shallow={shallow!r}')
        # The fixture must be the thing under test: a clone that quietly came
        # back full would make every case below pass for the wrong reason.
        results.append(('case 1: the fixture clone really is shallow',
                        shallow == 'true'))
        results.append(('case 1: the run reached the unlanded-work block',
                        'UNLANDED WORK' in r.stdout))
        # THE BUG ITSELF.
        results.append(('case 1: a fully-landed branch is NOT reported as '
                        'carrying unlanded commits',
                        'fully-landed' not in head))
        results.append(('case 1: and the scan says so affirmatively, rather '
                        'than falling silent',
                        'No branch carries unlanded work' in head))

    # CASE 2 -- deepening cannot rescue it. The tool must REFUSE, in words
    # that name the cause and the remedy.
    #
    # The origin here is itself a SHALLOW bare clone, so it is perfectly
    # reachable and simply has no deeper history to serve. Breaking the
    # origin outright was tried first and does not reach this code at all:
    # the freshness gate refuses the whole run before the branch scan, which
    # is correct behaviour and the wrong fixture.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        deep, mid, work = tmp / 'deep', tmp / 'mid', tmp / 'work'
        deep.mkdir(); _seed(deep)
        subprocess.run(['git', 'clone', '-q', '--bare', '--depth', '1',
                        f'file://{deep}', str(mid)], capture_output=True)
        _git(mid, 'fetch', '-q', '--depth=1', 'origin',
             '+refs/heads/fully-landed:refs/heads/fully-landed')
        subprocess.run(['git', 'clone', '-q', f'file://{mid}', str(work)],
                       capture_output=True)
        _git(work, 'fetch', '-q', 'origin',
             '+refs/heads/*:refs/remotes/origin/*')
        _consumer(work, tmp)
        _git(work, 'push', '-q', 'origin', 'main')
        r, head = _run(work, tmp)
        diag.append(f'case2 exit={r.returncode}')
        results.append(('case 2: the unmeasurable branch is reported at all',
                        'fully-landed' in head))
        results.append(('case 2: it is named as undetermined, not counted',
                        'COULD NOT DETERMINE' in head))
        # ASSERT THE MESSAGE, not merely the absence of the wrong one --
        # silence satisfies "no fabricated count" just as well, and silence
        # is the other way this fails.
        results.append(('case 2: the reason is the unreachable merge base',
                        'no merge base' in head))
        results.append(('case 2: the remedy is a bounded deepen',
                        '--depth=5000' in head))
        results.append(('case 2: no count of unlanded commits is invented',
                        'commit(s) with no patch-equivalent' not in head))
        # The false all-clear is the failure this check exists for.
        results.append(('case 2: the all-clear is NOT printed alongside an '
                        'unmeasurable branch',
                        'No branch carries unlanded work' not in head))

    failed = [n for n, ok in results if not ok]
    detail = ''
    if failed:
        detail = f"{'; '.join(failed)} [{'; '.join(diag)}]"
    check(f'a shallow clone never fabricates a count of unlanded work, and '
          f'says so when it cannot tell ({len(results)} stated cases)',
          not failed, detail)


def check_a_renamed_engine_file_never_survives_a_reseed():
    """Renaming an engine file upstream must not leave the old one behind
    in an adopter's tree (practice: decommission-deletes-files,
    control-asserts-which-failure).

    THE INCIDENT, 2026-09-08. Upstream renamed `precedent_retire_path.py`
    to `precedent_decommission.py`. Three real practice sets were then
    found each carrying the dead file, and every mechanism reported them
    healthy. Three separate holes lined up:

      1. `refresh` on a stale copy exited hard on the missing old path, so
         the ONLY way forward was a reseed (fixed upstream the same day --
         the skip-and-converge path).
      2. `seed`, the documented recovery, never called
         _remove_dropped_engine_files at all: it wrote the new set and a
         manifest that had already forgotten the old name, leaving the file
         on disk untracked.
      3. `refresh`'s early exit returned on a matching commit before any
         cleanup could run, so no later run would ever remove it -- and its
         `set_incomplete` test looked only for MISSING wanted files, never
         for PRESENT unwanted ones.

    After (2), the file is in no list any mechanism consults: gone from
    KINDS, gone from the manifest. _untracked_engine_files is keyed on the
    current lists and is deliberately blind to it. That is why
    RETIRED_ENGINE_FILES exists -- a name, once shipped, cannot be derived
    back out of the code that stopped shipping it.

    Three cases, one per hole. The reseed case is the one that would have
    caught the incident; the other two are the paths that made it
    permanent.
    """
    import shutil, tempfile
    import json as _json
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'pve', ROOT / 'tools' / 'precedent_vendor_engine.py')
    pve = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pve)

    results = []

    # MISSING IS A FAILURE, NOT A CRASH. Every symbol below is one this fix
    # introduced, so an engine that predates it raises AttributeError -- and
    # an uncaught one here takes the whole harness run down instead of
    # reporting one red check, which AGENTS.md records as its own hazard.
    # Reported as the absence it is (practice: fail-gracefully).
    missing_symbols = [n for n in ('RETIRED_ENGINE_FILES',
                                   '_retired_engine_files_present',
                                   '_remove_dropped_engine_files',
                                   '_seed_write')
                       if not hasattr(pve, n)]
    if missing_symbols:
        check('a renamed engine file never survives a reseed, and is '
              'reported when it already has (0 of 8 stated cases reached)',
              False,
              f"precedent_vendor_engine.py is missing "
              f"{', '.join(missing_symbols)} -- the removed-file cleanup is "
              f"not present in this engine at all, so a rename upstream "
              f"leaves the old file in every adopter's tree")
        return

    # The tombstone must not be empty in a way that makes every case below
    # vacuously true.
    results.append(('the engine records at least one retired file name',
                    bool(pve.RETIRED_ENGINE_FILES)))

    with tempfile.TemporaryDirectory() as tmp:
        tools = pathlib.Path(tmp) / 'tools'
        tools.mkdir(parents=True)
        dead = sorted(pve.RETIRED_ENGINE_FILES)[0]

        # CASE 1 -- a tombstoned file the manifest has FORGOTTEN is still
        # reported. This is the state a pre-fix reseed produced, and the one
        # nothing else could see.
        (tools / dead).write_text('# left behind by a rename\n')
        (tools / pve.MANIFEST_NAME).write_text(_json.dumps({
            'format_version': 1, 'kind': 'source', 'source_commit': 'x' * 40,
            'files': [], 'sha256': {}}), encoding='utf-8')
        reported = pve._retired_engine_files_present(tools)
        results.append(('an unrecorded retired file is reported',
                        [n for n, _ in reported] == [dead]))
        # ASSERT WHAT IT SAYS, not merely that it said something: the reason
        # is the whole value of the report, since the reader has no other
        # way to find out what the file was.
        results.append(('the report carries the reason it was retired',
                        bool(reported) and len(reported[0][1]) > 20))
        # It must NOT delete on its own -- see the function's own docstring.
        results.append(('reporting does not delete it',
                        (tools / dead).is_file()))

        # CASE 2 -- a tombstoned file the manifest still RECORDS is removed
        # by the sweep, which can hash-verify it first.
        (tools / pve.MANIFEST_NAME).write_text(_json.dumps({
            'format_version': 1, 'kind': 'source', 'source_commit': 'x' * 40,
            'files': [dead],
            'sha256': {dead: pve._sha256(tools / dead)}}), encoding='utf-8')
        manifest = pve._load_manifest(tools)
        pve._remove_dropped_engine_files(tools, manifest, 'source')
        results.append(('a recorded retired file is removed by the sweep',
                        not (tools / dead).is_file()))

        # CASE 2b -- SEEDING A REPO THAT HAS NO MANIFEST AT ALL still
        # works. This is seed's primary case, and the cleanup added above
        # broke it outright by reading the manifest through a helper that
        # sys.exit()s when there is none. Every fixture here had a manifest
        # already, so nothing caught it until a full harness run did.
        fresh = pathlib.Path(tmp) / 'never-vendored'
        r = subprocess.run(
            [sys.executable, str(ROOT / 'tools' / 'precedent_vendor_engine.py'),
             'seed', str(fresh), '--kind', 'source'],
            capture_output=True, text=True, cwd=str(ROOT))
        results.append(('seeding a repo with no manifest at all still '
                        'succeeds', r.returncode == 0
                        and (fresh / 'tools' / pve.MANIFEST_NAME).is_file()))

    # CASE 3 -- seed() routes through the cleanup. Asserted structurally:
    # building a whole second checkout to seed from is a fixture bigger than
    # the property, and the property is simply that seed does not bypass it.
    src = (ROOT / 'tools' / 'precedent_vendor_engine.py').read_text()
    seed_body = src[src.index('def seed('):]
    seed_body = seed_body[:seed_body.index('\ndef ', 1)]
    results.append(('seed writes through _seed_write, which cleans up, '
                    'rather than calling _write_engine_files directly',
                    '_seed_write(' in seed_body
                    and '_write_engine_files(' not in seed_body))
    results.append(('_seed_write actually calls the cleanup',
                    '_remove_dropped_engine_files' in
                    src[src.index('def _seed_write('):
                        src.index('def seed(')]))
    # And refresh's early exit must consider orphans, not only absences.
    ref = src[src.index('def refresh('):]
    results.append(('refresh\'s early exit checks for orphaned files too',
                    'set_orphaned' in ref))

    failed = [n for n, ok in results if not ok]
    check(f'a renamed engine file never survives a reseed, and is reported '
          f'when it already has ({len(results)} stated cases)',
          not failed, '; '.join(failed))


def check_withdrawn_table_never_links_a_successor_it_does_not_have():
    """The withdrawn-practices table must not link a successor that lives in
    another source (practice: doc-references-are-links,
    control-asserts-which-failure).

    THE INCIDENT, 2026-09-08. The withdrawn table landed that morning and
    rendered `in_force_at:` as `[slug](practices/slug.md)` unconditionally.
    The first team set to regenerate with it produced MAP.md linking
    `practices/headline-capitalization.md` -- a UNIVERSAL practice, in a repo
    that has no such file -- and that set then failed its own `light-check`
    on a broken relative link, inside a generated file its own header tells
    it never to hand-edit. Unfixable from within that repo.

    Deduplication is exactly the case where this bites: a team or individual
    rule is dropped BECAUSE a universal one already says it, so the successor
    is in a different repo more often than not. `in_force_at:` names a slug,
    never a source, so the renderer cannot assume locality.

    Both directions are asserted. A local successor must still be a link --
    fixing this by never linking would be a regression that no
    broken-link check could catch, since nothing at all would be broken.
    """
    import tempfile
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'bv', ROOT / 'tools' / 'build_views.py')
    bv = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        spec.loader.exec_module(bv)
    finally:
        sys.path.pop(0)

    results = []
    with tempfile.TemporaryDirectory() as tmp:
        pdir = pathlib.Path(tmp) / 'practices'
        pdir.mkdir(parents=True)
        # The successor that IS here.
        (pdir / 'local-successor.md').write_text('x')
        here = pdir / 'gone-local.md'
        here.write_text('x')
        away = pdir / 'gone-away.md'
        away.write_text('x')

        def row(slug, target, f):
            return ({'slug': slug, 'status': 'deduplicated',
                     'in_force_at': target},
                    {'Story': 'Because.'}, str(f))

        out = '\n'.join(bv._render_withdrawn([
            row('gone-local', 'local-successor', here),
            row('gone-away', 'no-such-practice', away),
        ]))

        results.append(('a successor present in this repo is still linked',
                        '[local-successor](practices/local-successor.md)' in out))
        results.append(('a successor that is NOT in this repo is not linked',
                        '(practices/no-such-practice.md)' not in out))
        # Assert what it says instead: silence would satisfy the case above.
        results.append(('the absent successor is still named, so the reader '
                        'can find it', 'no-such-practice' in out))
        results.append(('and is told where to look',
                        'another source' in out))

    failed = [n for n, ok in results if not ok]
    check(f'the withdrawn table never links a successor this repo does not '
          f'have ({len(results)} stated cases)', not failed,
          '; '.join(failed) + (f' [rendered: {out[-300:]!r}]' if failed else ''))


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

    _fixture_home_ctx = tempfile.TemporaryDirectory()
    _fixture_home = pathlib.Path(_fixture_home_ctx.name)

    cases = []
    UNIVERSAL = [{'level': 'universal', 'name': 'precedent', 'path': '.'}]
    # A private source that RESOLVES: its directory exists and carries a
    # practices/ tree, so the session can read its text.
    PRIVATE = UNIVERSAL + [{'level': 'team', 'name': 'precedent-team-x',
                            'path': '../precedent-team-x'}]

    with tempfile.TemporaryDirectory() as tmp:
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
                      rc == 1 and 'FAIL' in out, out[-400:]))
        cases.append(('and the refusal says the source RESOLVED, not merely '
                      'that precedent.json declares one',
                      'RESOLVED this session' in out, out[-400:]))
        rc3, out3 = run(repo, '--structural-only')
        cases.append(('the same repo PASSES under --structural-only, so CI '
                      'still works', rc3 == 0, out3[-300:]))
        cases.append(('and still says the private half did not run, rather '
                      'than reporting a clean bill',
                      'private ones were not' in out3, out3[-300:]))

    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp, UNIVERSAL)
        rc2, out2 = run(repo)
        cases.append(('a repo declaring NO private source is unaffected -- it '
                      'never had a vocabulary layer to lose, so this did not '
                      'become a gate everybody has to appease',
                      rc2 == 0, out2[-300:]))

    # THE CORRECTION, and the case that matters most: declared but NOT
    # resolved. The first version of this gate refused here too, which blocked
    # a real session out of pushing at all -- its commit "dies with the
    # container". The session that could not attach the source never read its
    # text and has nothing from it to leak; refusing bought no safety and cost
    # repo-is-memory. The path below simply does not exist.
    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp, UNIVERSAL + [{'level': 'team', 'name': 'precedent-team-absent',
                                        'path': '../precedent-team-absent'}])
        rc4, out4 = run(repo)
        cases.append(('a private source DECLARED but not resolved ALLOWS the '
                      'push -- the session could not read it, so it has '
                      'nothing from it to leak',
                      rc4 == 0, out4[-400:]))
        cases.append(('and it says so loudly, naming the residual risk it '
                      'does NOT cover rather than reporting a clean bill',
                      'nothing from them to leak' in out4
                      and 'some other way' in out4, out4[-400:]))

    _fixture_home_ctx.cleanup()

    ok = all(c[1] for c in cases)
    check(f'the leak gate requires the blocklist when a private source '
          f'RESOLVED, and not merely when one is declared ({len(cases)} '
          f'stated cases, config absent throughout)', ok,
          '; '.join(f'{n}: {d}' for n, o, d in cases if not o)[:900])


def check_title_case_knows_the_files_it_ships():
    """Every root file this project INSTANTIATES into an adopter must be
    classified correctly by title_case, including the ones upstream never
    has itself.

    THE INCIDENT, 2026-09-08, from a consumer repo taking the beta update:
    headline-capitalization fired on that repo's VOICE.md. `INTERNAL_FILES`
    had been built from UPSTREAM's own root names, and upstream ships
    VOICE.md and STYLEGUIDE.md as templates it never instantiates -- so the
    default was blind to exactly the files this project hands out, and every
    adopter got the same false positive on a file whose own header says it
    is LOCAL ONLY.

    IT FAILS IN THE DIRECTION NOBODY CHECKS, which is what makes it worth a
    standing control rather than a one-line fix: upstream's own gate stays
    green because upstream does not have the file. So this check does not
    ask "is VOICE.md classified right" -- it derives the list of shipped
    root files from templates/ and asks it of ALL of them, so a template
    added later is covered without anybody remembering to come back.
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

    # The two the incident was about, asserted BY NAME as well as by the
    # derivation above: a derivation that silently produced an empty list
    # would otherwise pass this whole check.
    for name in ('VOICE.md', 'STYLEGUIDE.md'):
        cases.append((f'{name} is shipped by a template',
                      name in shipped, str(shipped)))
        cases.append((f'{name} is INTERNAL -- its own template header says '
                      f'LOCAL ONLY, so no adopter should be told to '
                      f'headline-case it',
                      tc.is_outward(name) is False, ''))

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
    for name in ('README.md', 'SETUP.md', 'ADOPTING.md'):
        cases.append((f'{name} is still OUTWARD, so the fix did not just '
                      f'silence the check', tc.is_outward(name) is True, ''))

    # And the classification an adopter gets must not depend on a
    # precedent.json they have not written: is_outward() reads one when it
    # is there, and the default is what every fresh install starts from.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        cases.append(('VOICE.md is internal with NO precedent.json at all -- '
                      'the state a fresh adopter is in before they configure '
                      'anything', tc.is_outward('VOICE.md', root=tmp) is False,
                      ''))

    ok = all(c[1] for c in cases)
    check(f'title_case classifies the root files this project ships into '
          f'adopters ({len(cases)} stated cases, derived from templates/ '
          f'rather than listed)', ok,
          '; '.join(f'{n}: {d}' for n, o, d in cases if not o)[:800])


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


def check_doc_currency_finds_a_stale_document():
    """The documentation-currency sweep must find a document its subject
    outran, and must not invent one (practice: change-updates-its-docs).

    WHY EACH CASE IS HERE. The sweep is the backstop for a rule that lives
    in a person's habits, so a version of it that always says "none" is
    indistinguishable from a repository whose documents are all current --
    and would be believed, because that is the reassuring answer.

    THE ONE THAT MATTERS IS CASE 2, and it is built with the commits in a
    deliberate order: the document is committed FIRST, the thing it
    describes SECOND. Reverse those two and every implementation passes,
    including one that never compares timestamps at all. Case 1 is the
    unplanted control for it -- the same fixture with the second commit
    absent -- and case 1 alone does NOT discriminate, for the same reason.

    CASE 3 covers the half that fails silently in the real world: a spoken
    command nobody wrote down. The fixture plants a practice defining a
    capitalized phrase and a page that does not contain it. A run that only
    checks timestamps passes cases 1 and 2 and fails this one.

    CASE 6 is the shallow-clone reflex this repository has been bitten by
    four times: an unanswerable history must read UNKNOWN, never "current".
    """
    import tempfile
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'vdc_doc', ROOT / 'tools' / 'very_deep_check.py')
    vdc = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        spec.loader.exec_module(vdc)
    finally:
        sys.path.pop(0)

    if not hasattr(vdc, '_doc_currency'):
        check('the documentation-currency sweep discriminates '
              '(0 of 7 stated cases reached)', False,
              'very_deep_check.py has no _doc_currency -- nothing compares a '
              'document against what it describes')
        return

    def git(cwd, *args, check_rc=True):
        env = dict(os.environ, PRECEDENT_ALLOW_ANY_AUTHOR='1')
        r = subprocess.run(['git', '-C', str(cwd), *args],
                           capture_output=True, text=True, env=env)
        if check_rc and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    def build(tmp, with_later_change, page_text, practice_text):
        repo = pathlib.Path(tmp) / 'repo'
        (repo / 'documentation').mkdir(parents=True)
        (repo / 'practices').mkdir()
        (repo / 'tools').mkdir()
        git(repo.parent, 'init', '-q', str(repo))
        git(repo, 'config', 'user.email', 'harness@example.com')
        git(repo, 'config', 'user.name', 'Fixture')
        (repo / 'practices' / 'zzz-command.md').write_text(
            practice_text, encoding='utf-8')
        (repo / 'tools' / 'doc_coverage.json').write_text(json.dumps({
            'documents': {
                'documentation/PAGE.md': {
                    'describes': ['practices/zzz-command.md'],
                    'why': 'fixture',
                    'must_mention': 'spoken-commands',
                },
            },
            'must_mention': {'spoken-commands': {'why': 'fixture'}},
        }), encoding='utf-8')
        (repo / 'documentation' / 'PAGE.md').write_text(page_text,
                                                        encoding='utf-8')
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'page and practice together')
        if with_later_change:
            # The ONLY thing that separates case 1 from case 2, and it has to
            # be a genuinely later commit: --date alone does not move %ct.
            time.sleep(1.1)
            (repo / 'practices' / 'zzz-command.md').write_text(
                practice_text + '\nA later change nobody wrote up.\n',
                encoding='utf-8')
            git(repo, 'add', '-A')
            git(repo, 'commit', '-qm', 'change the practice, leave the page')
        return repo

    GOOD_PRACTICE = (
        '---\nslug:        zzz-command\ntitle:       A command\n'
        'tier:        on-demand\nseverity:    default\n'
        'applies_to:  ["**"]\noccasion:    "testing"\n'
        'index_clause: "a fixture"\nchecked_by:  null\n'
        'defines:     ["Zorp It"]\nstatus:      active\nsupersedes:  []\n'
        'overrides:   null\nadded:       null\napproved_by: "fixture"\n'
        '---\n\n## Rule\nSay it.\n')
    PAGE_WITH = '# Page\n\nSay **Zorp It** to do the thing.\n'
    PAGE_WITHOUT = '# Page\n\nThis page teaches you nothing.\n'

    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp, False, PAGE_WITH, GOOD_PRACTICE)
        found, notes = vdc._doc_currency(repo)
        cases.append(('a page committed WITH its subject reports no REVIEW',
                      not any('REVIEW' in f for f in found),
                      str(found)[:400]))
        cases.append(('and the spoken command it does carry is reported as '
                      'present, not silently skipped',
                      any('Zorp It' in n for n in notes), str(notes)[:400]))

    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp, True, PAGE_WITH, GOOD_PRACTICE)
        found, _notes = vdc._doc_currency(repo)
        review = [f for f in found if 'REVIEW' in f]
        cases.append(('a page whose subject changed AFTER it reports REVIEW',
                      len(review) == 1, str(found)[:400]))
        cases.append(('and the finding names the commit that outran it, so a '
                      'reader can go and look',
                      bool(review) and 'change the practice, leave the page'
                      in review[0], str(review)[:400]))

    with tempfile.TemporaryDirectory() as tmp:
        repo = build(tmp, False, PAGE_WITHOUT, GOOD_PRACTICE)
        found, _notes = vdc._doc_currency(repo)
        cases.append(('a spoken command missing from the page that teaches '
                      'the vocabulary is a FINDING, even with every '
                      'timestamp current',
                      any('Zorp It' in f and 'FINDING' in f for f in found),
                      str(found)[:400]))

    with tempfile.TemporaryDirectory() as tmp:
        # An empty repository: git can date nothing. UNKNOWN, never current.
        repo = pathlib.Path(tmp) / 'bare'
        (repo / 'documentation').mkdir(parents=True)
        (repo / 'tools').mkdir()
        git(repo.parent, 'init', '-q', str(repo))
        (repo / 'tools' / 'doc_coverage.json').write_text(json.dumps({
            'documents': {'documentation/PAGE.md': {
                'describes': [], 'why': 'fixture'}}}), encoding='utf-8')
        (repo / 'documentation' / 'PAGE.md').write_text('# Page\n',
                                                        encoding='utf-8')
        found, notes = vdc._doc_currency(repo)
        cases.append(('a document git cannot date reads as UNKNOWN or '
                      'uncommitted, never as current',
                      any('documentation/PAGE.md' in n for n in notes),
                      str(notes)[:400]))

    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp) / 'noreg'
        repo.mkdir()
        found, notes = vdc._doc_currency(repo)
        cases.append(('a repository with no registry says so and finds '
                      'nothing, rather than crashing',
                      found == [] and any('doc_coverage.json' in n
                                          for n in notes),
                      str((found, notes))[:400]))

    ok = all(c[1] for c in cases)
    check(f'the documentation-currency sweep discriminates '
          f'({len(cases)} stated cases, each built so a sweep that skipped '
          f'the comparison would fail it)', ok,
          '; '.join(f'{n}: {d}' for n, o, d in cases if not o)[:900])


def check_template_freshness_reads_the_skeleton_correctly():
    """The reverse-direction skeleton check must not invent gaps, and must
    not call one repo's habit a finding (practice: very-deep-check).

    WHY IT EXISTS. `precedent_bootstrap_source.verify()` reads a skeleton and
    asks whether a real source has everything in it. Nothing asked the
    reverse until 2026-09-08, so a skeleton could drift below reality and a
    newly bootstrapped source would be created missing something every real
    one has. That is how the individual skeleton came to ship no
    `identity.json` -- the file that decides whether the commit hook ENFORCES
    an author-date offset or merely guesses one.

    TWO FAILURES ON ITS FIRST RUN, both asserted here because both make the
    section useless in opposite ways:

      1. It reported `config.json.sample` as a gap. The skeleton plainly
         ships that file -- the scan stripped the `.sample` suffix and
         recorded only `config.json`, while a real source keeps the sample
         name verbatim. A check that flags what the template already has
         teaches the reader to skim it.
      2. Everything was labelled FINDING, including a level with exactly ONE
         resolved source. One repo is not evidence of a shape, and a
         permanent list of that repo's own working documents is the same
         noise problem from the other side.
    """
    import tempfile
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'vdc', ROOT / 'tools' / 'very_deep_check.py')
    vdc = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        spec.loader.exec_module(vdc)
    finally:
        sys.path.pop(0)

    results = []
    if not hasattr(vdc, '_template_freshness'):
        check('the template-freshness scan reads the skeleton correctly '
              '(0 of 5 stated cases reached)', False,
              'very_deep_check.py has no _template_freshness -- the reverse '
              'direction is not checked at all')
        return

    with tempfile.TemporaryDirectory() as tmp:
        # A source carrying exactly what the individual skeleton ships,
        # suffixes and all, plus one extra file.
        src = pathlib.Path(tmp) / 'a-source'
        (src / 'practices').mkdir(parents=True)
        skel = ROOT / 'templates' / 'practice-set-individual'
        for f in skel.iterdir():
            if f.is_file():
                (src / f.name).write_text('x')
        (src / 'ONLY_HERE.md').write_text('x')

        out = vdc._template_freshness(
            [{'level': 'individual', 'name': 'fixture', 'path': str(src)}])
        joined = ' | '.join(out)

        # THE FALSE POSITIVE.
        results.append(('a file the skeleton ships under its own '
                        '.sample/.template name is NOT reported as a gap',
                        'config.json' not in joined))
        # One source is not evidence.
        results.append(('a level with one source is reported as a note, not '
                        'a FINDING', 'FINDING' not in joined))
        results.append(('and says plainly that one source proves nothing',
                        'only ONE source' in joined))
        # It still has to SAY something -- silence would pass the two cases
        # above just as well, and silence is how the gap survived.
        results.append(('the file the skeleton really lacks is still named',
                        'ONLY_HERE.md' in joined))

    # The gap that motivated all of this must actually be closed.
    results.append(('the individual skeleton now ships an identity file',
                    any(f.name.startswith('identity.json')
                        for f in (ROOT / 'templates' /
                                  'practice-set-individual').iterdir())))

    failed = [n for n, ok in results if not ok]
    check(f'the template-freshness scan reads the skeleton correctly '
          f'({len(results)} stated cases)', not failed,
          '; '.join(failed) + (f' [scan said: {joined!r}]' if failed else ''))


def check_assumed_visibility_never_deletes_practices():
    """An ASSUMED visibility must never remove practice files that are
    already in a consumer's tree (practice: very-deep-check, reported by a
    real repo).

    repo_is_public() treats an undeclared `visibility` as public, and that
    default is right: it fails safe against publishing private practice text
    into a world-readable repo, which is the failure that motivated it.

    It fails UNSAFE in the other direction. An existing PRIVATE consumer that
    never declared the field loses every team- and individual-level practice
    from its tracked tree on its next sync -- silently, as a committable diff
    that reads like a deliberate removal. Reported 2026-09-07 by a real
    private repo updating to this engine: 15 practices would have gone, and
    the person caught it only by checking that repo's actual visibility by
    hand.

    So the assumption is allowed to WITHHOLD, and not allowed to DELETE. A
    declared visibility proceeds either way -- that is someone choosing.
    Three states, all asserted, because fixing this by simply reverting the
    default would restore the publication hazard it was written for."""
    import tempfile, shutil
    import json as _json
    import precedent_sync_views as psv
    import precedent_materialize as _pm
    import build_views as bv

    def _fixture(tmp, visibility):
        repo, team = tmp / 'consumer', tmp / 'team-src'
        (repo / 'precedent' / 'universal').mkdir(parents=True)
        shutil.copytree(PRACTICES_DIR, repo / 'precedent' / 'universal' / 'practices')
        (team / 'practices').mkdir(parents=True)
        (team / 'practices' / 'team-only-rule.md').write_text(
            '---\nslug: team-only-rule\ntitle: A rule only this team has\n'
            'tier: on-demand\nseverity: default\napplies_to: ["**"]\n'
            'occasion: "doing team things"\nindex_clause: "do the team thing"\n'
            'status: active\n---\n## Rule\nDo it.\n\n## Story\nDecided.\n',
            encoding='utf-8')
        (repo / 'AGENTS.md').write_text(
            f'# c\n\n{bv.BEGIN_MARKER} -->\n{bv.END_MARKER} -->\n', encoding='utf-8')
        cfg = {'format_version': 1, 'base_branch': 'main',
               'sources': [
                   {'level': 'universal', 'name': 'precedent',
                    'path': 'precedent/universal'},
                   {'level': 'team', 'name': 'precedent-team-x',
                    'path': str(team)}]}
        if visibility:
            cfg['visibility'] = visibility
        (repo / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        return repo

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        user = tmp / 'user.json'
        user.write_text(_json.dumps({'format_version': 1}), encoding='utf-8')
        results = []

        # Seed a PRIVATE consumer that really carries the team practice.
        repo = _fixture(tmp, 'private')
        psv.sync(str(repo), user_config=str(user))
        seeded = (repo / 'practices' / 'team-only-rule.md').exists()
        results.append(('a private consumer materializes the team practice', seeded))

        # Now the reported state: the declaration goes away.
        cfg = _json.loads((repo / 'precedent.json').read_text())
        cfg.pop('visibility', None)
        (repo / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        refused = False
        try:
            psv.sync(str(repo), user_config=str(user))
        except _pm.MaterializeError:
            refused = True
        results.append(('an ASSUMED visibility refuses rather than deleting',
                        refused))
        results.append(('and the practice file survives the refusal',
                        (repo / 'practices' / 'team-only-rule.md').exists()))

        # Declared private: keep it. This is the control that stops the fix
        # from simply blocking every consumer.
        cfg['visibility'] = 'private'
        (repo / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        psv.sync(str(repo), user_config=str(user))
        results.append(('declaring private keeps it',
                        (repo / 'practices' / 'team-only-rule.md').exists()))

        # Declared public: withhold it. The publication hazard the default
        # exists for must still be closed.
        cfg['visibility'] = 'public'
        (repo / 'precedent.json').write_text(_json.dumps(cfg), encoding='utf-8')
        psv.sync(str(repo), user_config=str(user))
        results.append(('declaring public still withholds it',
                        not (repo / 'practices' / 'team-only-rule.md').exists()))

        failed = [n for n, ok in results if not ok]
        check(f'an assumed visibility withholds but never deletes '
              f'({len(results)} stated cases: seeded, refused, survived, and '
              f'both declared states)',
              not failed, '; '.join(failed) if failed else '')


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
    check_practices_link_only_reachable_repos(files)
    check_leak_gate()
    check_leak_gate_fires()
    check_practice_audit_fires()
    check_freshness_gate_fires()
    check_unmerged_branch_verdicts()
    check_branch_scan_sees_every_branch()
    check_merged_branches_carry_a_date_and_a_staleness_verdict()
    check_very_deep_check_authenticates_its_own_fetches()
    check_public_consumer_does_not_materialize_private_text()
    check_assumed_visibility_never_deletes_practices()
    check_sync_refuses_to_write_from_incomplete_sources()
    check_unlanded_work_is_reported_before_the_passes()
    check_shallow_clone_never_fabricates_unlanded_work()
    check_a_renamed_engine_file_never_survives_a_reseed()
    check_leak_gate_refuses_a_fresh_container()
    check_title_case_knows_the_files_it_ships()
    check_carry_check_never_invents_lost_content()
    check_doc_currency_finds_a_stale_document()
    check_template_freshness_reads_the_skeleton_correctly()
    check_withdrawn_table_never_links_a_successor_it_does_not_have()
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
    check_build_views_summary_matches_what_it_wrote()
    check_default_blocklist_runs_the_vocabulary_layer()
    check_session_practices_load_without_publishing()
    check_not_binding_cannot_be_abused()
    check_codeowners_check_is_a_check()
    check_status_contract()
    check_legacy_status_migration()
    check_retired_practices_leave_the_views()
    check_resident_subset(files)
    check_behavioral_replay()
    check_precedent_check_fires()
    check_routing_scope(files)
    check_routing_audit_coverage()
    check_parallel_artifact_ledger_fires()
    check_gate_channel()
    check_loader_block_advertises_only_live_channels()
    check_source_sets_can_learn_they_are_stale()
    check_loader_tools_are_repo_relocatable()
    check_materialize_bridges_loader()
    check_show_flags_unreachable_materialized_source()
    check_sync_views_cross_source()
    check_sync_refuses_to_lose_a_recorded_practice()
    check_doc_lifecycle_fires_and_clears()
    check_commit_identity_derives_declared_timezone()
    check_superseded_source_says_so()
    check_refresh_removes_dropped_engine_files()
    check_refresh_survives_an_upstream_rename()
    check_retirement_record_is_not_a_stranded_link()
    check_commit_identity_prevents_the_wrong_offset()
    check_source_clone_is_pinned_to_a_branch()
    check_generator_wires_every_template_guard_mode()
    check_verify_reports_a_source_wired_for_fewer_moments()
    check_commit_identity_copies_are_identical()
    check_identity_reaches_a_repo_that_did_not_exist_yet()
    check_repo_reference_allowlist()
    check_leak_gate_scans_the_consuming_repo()
    check_update_refuses_while_a_branch_is_pinned()
    check_leftover_pack_is_flagged_after_migration()
    check_detect_restated_fires()
    check_creation_pipeline_fires()
    check_bootstrap_source_produces_resolvable_set()
    check_bootstrap_source_engine_is_functional()
    check_precedent_check_degrades_in_a_source_set()
    check_vendor_engine_consumer_case()
    check_rule_rewrite_detection()
    check_source_shape_is_verified()
    check_machine_readable_files_parse()
    check_null_frontmatter_is_absent()
    check_frontmatter_is_real_yaml()
    check_link_anchors_resolve()
    check_materialized_links_are_placed()
    check_source_supplied_checks_run()
    check_individual_source_bootstrap_self_heals()
    check_source_credentials()
    check_pretooluse_hook_fires()
    check_not_binding_actually_exempts_a_check()
    check_mirrored_prefixes_answers_both_install_models()
    check_declared_identity_has_a_passing_state_in_a_shared_repo()
    check_instantiated_template_links_survive_the_copy()
    check_tools_answer_help_without_writing()
    check_loader_block_covers_every_declared_source()
    check_title_case_leaves_code_and_first_word_alone()
    check_title_case_honours_repo_declared_internal_paths()
    check_title_case_never_corrupts_content()
    check_title_case_output_paths_inverts_the_default()
    check_checkin_update_never_mutates_the_clone()
    check_leak_gate_notes_an_uncovered_private_repo()
    check_visibility_audit_reads_the_blocklist_as_patterns()
    check_rendered_docs_are_current()
    check_philosophy_readme_lists_every_file()

    # RECAP THE FAILURES BY NAME, immediately before the summary line.
    #
    # This run prints one line per check, and there are over a hundred, so in
    # practice everyone reads the tail: AGENTS.md's own deep-check section
    # says "what matters is 0 failed", which is a summary-line instruction.
    # A `tail -3` therefore captured "110 passed, 1 failed" and NOT the FAIL
    # line hundreds of lines above it -- which happened on 2026-09-07, to a
    # failure that then did not reproduce in five further runs on the same
    # tree. The count said something was wrong and the output no longer
    # existed to say what. An intermittent failure you cannot name is one you
    # cannot fix, and re-running is exactly what destroys the evidence.
    #
    # Cheap, and it makes the tail self-sufficient: the last thing printed
    # now names every failure, so the shortest reading of this tool's output
    # that anyone actually does is enough to act on.
    if FAILED:
        print("\nFAILED CHECKS:")
        for name, detail in FAILED:
            print(f"  - {name}" + (f" -- {detail}" if detail else ""))
    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed, {len(NA)} not yet applicable.")
    return 1 if FAILED else 0


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/HOW_TO_USE_THIS_TECHNICAL.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
