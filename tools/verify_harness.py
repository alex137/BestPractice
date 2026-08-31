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


# The build is byte-identical to PRACTICES.md except for two documented,
# approved exceptions found while writing the converter -- both explained
# in spec/PRACTICE_FORMAT.md and in split_practices.py's module docstring:
#
#  1. Practice 39's raw body in the source is followed by a stray duplicate
#     of part of practice 34's body -- an upstream data-corruption artifact,
#     not authored content of practice 39's own. Dropped at conversion.
#     The duplicate is pasted MID-PARAGRAPH (it starts mid-word, on the line
#     immediately after practice 39's Install paragraph ends, with no blank
#     line between), so the dropped span starts at the marker itself. This
#     exception was originally written to start at the preceding BLANK line
#     instead, matching a converter that made the same mistake -- which
#     deleted practice 39's whole Install paragraph and passed every check
#     in this file, because each one compared the lossy output against a
#     source parsed through the same lossy fixup. See
#     check_corruption_drop_is_a_duplicate below, which tests the boundary
#     against a property that does not depend on the boundary.
#  2. A single extra blank line between practices 40 and 41 in the source
#     (everywhere else in the file uses exactly one blank line between
#     practices) -- a pre-existing whitespace-only formatting quirk,
#     unrelated to the conversion.
#  3. Practice 39's "**Install.**" is the only label in the whole file
#     followed by a NEWLINE rather than a space, and cmd_build re-emits
#     every stripped canonical label with a space. Whitespace-only, same
#     class as (2); it only became reachable once (1) stopped deleting the
#     paragraph that contains it.
#
# This check does not take that on faith: it reproduces exactly those three,
# and only those three, transformations against the ORIGINAL text, and then
# requires the rebuild to match the result exactly.
def check_byte_identical_regeneration():
    original = CATALOGUE.read_text(encoding='utf-8')
    normalized = original.replace(
        "\n\n## 41. Search by purpose", "\n## 41. Search by purpose")
    normalized = normalized.replace(
        "\n\n**Install.**\n[templates/pull_request_template.md.template]",
        "\n\n**Install.** [templates/pull_request_template.md.template]")
    # search from practice 39's own header, not from the start of the file --
    # the marker's tail also occurs, legitimately, inside practice 34's own
    # body ("...acquir-ES a source's vocabulary..."), earlier in the file.
    p39_start = normalized.index('## 39. A default PR template')
    idx = normalized.find(sp.FIXUP_39_MARKER, p39_start)
    ok_marker_found = idx != -1
    if ok_marker_found:
        # the corrupted span runs from the duplicate fragment -- which starts
        # mid-paragraph, at the marker itself, NOT at the preceding blank
        # line (note 1 above) -- to just before "## 40.". Drop exactly that
        # span, nothing else.
        end_marker = "\n\n## 40. An option you invented"
        end_idx = normalized.index(end_marker, idx)
        normalized = normalized[:idx].rstrip('\n') + normalized[end_idx:]
    rebuilt = sp.cmd_build()
    ok = ok_marker_found and (normalized.rstrip('\n') + '\n') == rebuilt
    if not ok:
        import difflib
        diff = list(difflib.unified_diff(
            normalized.splitlines(keepends=True), rebuilt.splitlines(keepends=True),
            fromfile='normalized-original', tofile='rebuilt', n=1))
        print('  unexpected diff beyond the three documented exceptions:')
        for line in diff[:40]:
            print('  ' + line.rstrip('\n'))
    check('byte-identical regeneration (modulo the three documented exceptions)', ok)


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
    # practice_audit.py's own scrub is written for a DEPENDENT repo (it
    # diffs a vendored tree against process/manifest*.json's recorded
    # baselines) -- Precedent is upstream and does not vendor itself, so it
    # has no manifest for that tool to run against, and running it here
    # fails on a missing precondition rather than testing anything real.
    # The plan's actual leak gate ("no individual- or team-level term
    # appears anywhere in Precedent") has nothing to check yet either: no
    # team or individual content exists in this repo before phase 3. A
    # cheap, real check that IS meaningful now: practices/ contains no
    # residual reference to the personal-pack or team-pack vocabulary this
    # session has seen while building it (a blunt scan, not the real gate).
    banned = ['process/personal/', 'precedent-team-maintainers', 'precedent-individual',
              'morgan@westegg.com', 'Morgan F']
    hits = []
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        text = f.read_text(encoding='utf-8')
        for term in banned:
            if term in text:
                hits.append((f.name, term))
    if hits:
        check('leak gate (blunt scan for known team/individual vocabulary in practices/)',
              False, str(hits))
    else:
        not_applicable('leak gate (full form)',
                        'no team or individual practice sets exist yet (phase 3) for '
                        'anything to leak from; a blunt vocabulary scan over practices/ '
                        'found nothing, which is the only form of this check phase 1 can run')


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
    check_reachability(files)
    check_byte_identical_regeneration()
    original_text = CATALOGUE.read_text(encoding='utf-8')
    original_practices = {p['number']: p for p in sp.parse_catalogue(original_text)}
    check_no_invented_content(files, original_practices)
    check_no_lost_content(files, original_practices)
    check_corruption_drop_is_a_duplicate(original_practices)
    check_citation_integrity(files)
    check_leak_gate()
    check_glob_semantics()
    check_generated_views_regenerate()
    check_resident_subset(files)
    check_behavioral_replay()

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed, {len(NA)} not yet applicable.")
    return 1 if FAILED else 0


if __name__ == '__main__':
    sys.exit(main())
