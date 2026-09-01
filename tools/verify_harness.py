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
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        fm, sections = sp._read_practice_file(f)
        out[f.stem] = (fm, sections, f)
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


# Phase 1's original form of this check reproduced two documented,
# approved exceptions (the practice-39 upstream corruption; a stray blank
# line between practices 40 and 41) against the FROZEN pre-conversion
# PRACTICES.md text, and required the rebuild to match that exactly -- a
# one-time proof that the mechanical split lost and invented nothing. That
# proof already landed (see git history; spec/PRACTICE_FORMAT.md's "A
# Genuine Upstream Finding") and cannot be re-asserted forever: practices/*.md
# is now the source of truth and is expected to keep changing (e.g. the
# citation-to-slug-link sweep this check now runs alongside), so PRACTICES.md
# necessarily drifts from that frozen snapshot. What the check verifies from
# here on is the real, ongoing meaning of "generated view": PRACTICES.md
# on disk is exactly what cmd_build() produces from the current practices/*.md
# -- i.e. nobody hand-edited the catalogue out of sync with its source.
def check_byte_identical_regeneration():
    on_disk = CATALOGUE.read_text(encoding='utf-8')
    rebuilt = sp.cmd_build()
    ok = on_disk == rebuilt
    if not ok:
        import difflib
        diff = list(difflib.unified_diff(
            on_disk.splitlines(keepends=True), rebuilt.splitlines(keepends=True),
            fromfile='PRACTICES.md (on disk)', tofile='rebuilt', n=1))
        print('  PRACTICES.md is out of sync with practices/*.md -- run '
              '`python3 tools/split_practices.py build > PRACTICES.md`:')
        for line in diff[:40]:
            print('  ' + line.rstrip('\n'))
    check('byte-identical regeneration (PRACTICES.md == build(practices/*.md))', ok)


SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9(\[])')
WORD_RE = re.compile(r"[A-Za-z0-9']{3,}")


def _tokens(text):
    return collections.Counter(w.lower() for w in WORD_RE.findall(text))


# NOTE ON WHAT THIS STILL PROVES: this check's real, one-time job -- proving
# the phase-1 mechanical split invented nothing relative to BestPractice's
# original numbered catalogue -- already happened (see git history at the
# phase-1 landing commit) and cannot be meaningfully re-run: `main()` reads
# `original_practices_by_number` from the CURRENT PRACTICES.md, which is now
# a generated view kept in sync with practices/*.md by regeneration (see
# check_byte_identical_regeneration above), so in the normal workflow this
# comparison is tautological -- practices/*.md and PRACTICES.md say the same
# thing by construction, not because nothing was invented since. It still
# catches the one real case that survives: PRACTICES.md hand-edited to
# *contain* extra words a practices/*.md file doesn't have, independent of
# byte-identical-regeneration failing for the same edit.
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


CROSS_PRACTICE_LINK_RE = re.compile(r'\]\(([a-z0-9]+(?:-[a-z0-9]+)*)\.md\)')


def check_no_bare_numeric_citations(files):
    # The slug-link sweep (see spec/PRACTICE_FORMAT.md, "Citing Other
    # Practices") replaced every "practice N" cross-reference in practices/
    # body text with a markdown link to the slug. This is the regression
    # guard: the numeric form should never come back in body prose. (The
    # `source_practice_number` frontmatter field itself is exempt by
    # construction -- CITATION_RE requires "practice" immediately followed
    # by whitespace, which never matches the `source_practice_number:` key.)
    ok = True
    for stem, (fm, sections, f) in files.items():
        body = '\n\n'.join(sections.get(k, '') for k in ('rule', 'why', 'story', 'install'))
        for m in CITATION_RE.finditer(body):
            ok = False
            print(f"  {f.name}: body text cites 'practice {m.group(1)}' by number; "
                  f"convert to a [{{slug}}]({{slug}}.md) link instead")
    check('no bare numeric citations in body text (slugs are the official reference form)', ok)


def check_slug_link_integrity(files):
    ok = True
    valid_slugs = set(files.keys())
    for stem, (fm, sections, f) in files.items():
        body = '\n\n'.join(sections.get(k, '') for k in ('rule', 'why', 'story', 'install'))
        for m in CROSS_PRACTICE_LINK_RE.finditer(body):
            if m.group(1) not in valid_slugs:
                ok = False
                print(f"  {f.name}: links to '{m.group(1)}.md', which is not a "
                      f"known practice slug")
    check('slug-link citation integrity (every [slug](slug.md) cross-reference resolves)', ok)


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
    check_citation_integrity(files)
    check_no_bare_numeric_citations(files)
    check_slug_link_integrity(files)
    check_leak_gate()

    not_applicable('resident subset', 'no loader or resident-tier curation exists yet (phase 2)')
    not_applicable('behavioral replay', 'no loader exists yet to replay against (phase 2)')

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed, {len(NA)} not yet applicable.")
    return 1 if FAILED else 0


if __name__ == '__main__':
    sys.exit(main())
