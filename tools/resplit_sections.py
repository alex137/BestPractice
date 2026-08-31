#!/usr/bin/env python3
"""resplit_sections.py — the phase-1.5 editorial re-split, applied as data.

Phase 1's converter was mechanical: it routed each paragraph by the bold
label that opened it. That is lossless but not editorial, and it left the
plan's headline claim undelivered. PRACTICE_ENGINE_PLAN.md's premise is:

    "BestPractice's median practice is 38 lines; the instruction inside it
     is three or four. Splitting removes roughly nine tenths of the resident
     text without deleting a word."

After phase 1, `## Rule` was 44% of the corpus, not a tenth: sixteen
practices had Rules over 150 words, the longest ran to 1,340, and the six
practices whose source opened on bare prose (47-52) had their ENTIRE body
land in `## Rule` because the label walk never saw a `**Why.**` to leave on.
Two of them are resident, so over half the always-loaded token budget was
text that belongs in Why.

This tool performs the second, editorial half of the split the plan
describes as "LLM-assisted and human-reviewed, once per practice" -- moving
text between Rule / Detail / Why / Story / Install without touching a
character of it.

`## Detail` was added at phase 3 (plan v20), for the reason phase 1.5
measured: `## Rule` came out at 40% of the corpus rather than the predicted
tenth, because a large share of each practice is genuinely NORMATIVE text
that is neither reasoning, nor an incident, nor wiring -- numbered policy
rules, worked decision procedures, sub-rules with their own tests -- and had
nowhere else to go. Two constraints govern what may move there, both from the
plan's phase-3 row: `## Rule` must stay loadable ON ITS OWN, so a session
reading only the Rule knows what to DO rather than merely that something
applies; and `## Detail` comes from the same `precedent show` command, never
a second one.

The consequence, worth stating because it limits what this pass could
achieve: this mechanism moves text, it cannot write it. Where a practice's
actionable instruction lives inside a paragraph that cannot be sliced -- a
markdown list, or a lead-in whose colon dangles without what follows -- there
is no split that leaves a loadable Rule behind, and the honest outcome is to
leave that practice's Rule whole. Three did: see spec/PRACTICE_FORMAT.md.

WHY THIS IS A TOOL AND A DATA FILE RATHER THAN 52 HAND-EDITS. Re-homing
52 practices by editing each file is 52 opportunities to retype a sentence
slightly differently, and a reviewer cannot tell a faithful move from a
silent paraphrase by reading the diff. Here the editorial judgment lives in
tools/section_split.json as a list of REFERENCES to existing source
paragraphs, and this script moves the text by reference. Retyping is not
something the mechanism can do. The decisions are reviewable on their own,
separately from their effect, and the pass is re-runnable.

A reference names a paragraph of the practice's ORIGINAL body, as phase 1's
mechanical converter parsed it out of PRACTICES.md:

    R0    Rule paragraph 0          W2   Why paragraph 2
    I1    Install paragraph 1

Referencing the SOURCE rather than the file being rewritten is what makes
this idempotent: applying the spec twice is a no-op, `--check` is meaningful,
and an editorial decision recorded here keeps meaning the same thing however
many times the pass is re-run. (There is no `S` prefix: the source has no
Story section -- populating one is part of what this pass does.)

and may carry a sentence slice for the cases where one paragraph opens with
the imperative and continues into rationale:

    R0.s0-1   sentences 0 and 1 of Rule paragraph 0
    R0.s2-    sentence 2 to the end

Every reference must be used exactly once across the five target sections:
this script refuses to run otherwise, so a paragraph cannot be silently
dropped or accidentally duplicated by a typo in the spec. That is a
structural guard, not the real one -- tools/verify_harness.py's
sentence-for-sentence check against PRACTICES.md is what actually proves
the pass lost nothing.

Run:
  python3 tools/resplit_sections.py            # apply the spec
  python3 tools/resplit_sections.py --check    # verify the tree matches it
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRACTICES_DIR = ROOT / 'practices'
SPEC_PATH = ROOT / 'tools' / 'section_split.json'

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp

SECTIONS = ('rule', 'detail', 'why', 'story', 'install')
SOURCE_SECTIONS = ('rule', 'why', 'install')
PREFIX = {'R': 'rule', 'W': 'why', 'I': 'install'}
REF_RE = re.compile(r'^([RWI])(\d+)(?:\.s(\d+)-(\d*))?$')

_PARA_SPLIT = re.compile(r'\n\s*\n')
_SENT_SPLIT = re.compile(r'(?<=[.!?])[ \t]+(?=[A-Z0-9*\[(“"`—-])')


def paragraphs(text):
    return [p.strip('\n') for p in _PARA_SPLIT.split(text or '') if p.strip()]


def sentences(para):
    """Split a one-paragraph string into sentences, PRESERVING the original
    text of each (not a normalized form) so a slice can be re-emitted
    verbatim."""
    return [s for s in _SENT_SPLIT.split(' '.join(para.split())) if s.strip()]


def resolve(ref, paras):
    m = REF_RE.match(ref)
    if not m:
        sys.exit(f"resplit FAIL: malformed reference {ref!r} "
                 f"(expected e.g. R0, W2, R0.s0-1, W1.s2-)")
    section = PREFIX[m.group(1)]
    idx = int(m.group(2))
    if idx >= len(paras[section]):
        sys.exit(f"resplit FAIL: reference {ref!r} names {section} paragraph {idx}, "
                 f"but that section has {len(paras[section])}")
    para = paras[section][idx]
    if m.group(3) is None:
        return para
    # A sentence slice re-wraps what it takes, which destroys the line
    # structure of a markdown list: the tokenizer treats "2." as its own
    # sentence, so slicing across a numbered list silently turns its items
    # into running prose. Caught once, by verify_harness's list-structure
    # check, on practice 47. Refuse it here instead, where the message can
    # say what to do about it.
    if re.search(r'^\s*([-*+]|\d+\.)\s', para, re.M):
        sys.exit(f"resplit FAIL: reference {ref!r} slices a paragraph containing a "
                 f"markdown list. Slicing re-wraps, which would flatten the list -- "
                 f"place the paragraph whole, or restructure the source first.")
    sents = sentences(para)
    lo = int(m.group(3))
    hi = int(m.group(4)) if m.group(4) else len(sents)
    if lo >= len(sents) or hi > len(sents) or lo >= hi:
        sys.exit(f"resplit FAIL: reference {ref!r} slices sentences {lo}-{hi} of a "
                 f"paragraph that has {len(sents)}")
    return ' '.join(sents[lo:hi])


def _all_refs(paras):
    out = []
    for letter, section in PREFIX.items():
        out += [f"{letter}{i}" for i in range(len(paras[section]))]
    return out


def _covered(spec_for_practice):
    """Which whole-paragraph refs the spec accounts for, expanding slices."""
    seen = {}
    for target in SECTIONS:
        for ref in spec_for_practice.get(target, []):
            m = REF_RE.match(ref)
            if not m:
                sys.exit(f"resplit FAIL: malformed reference {ref!r}")
            base = m.group(1) + m.group(2)
            seen.setdefault(base, []).append(ref)
    return seen


def rewrap(text, width=76):
    """Re-wrap a moved paragraph to the catalogue's column width. Only ever
    applied to text that was sliced out of a larger paragraph -- a paragraph
    moved whole keeps its original line breaks, so the diff stays readable
    and `git blame` still points at the right place."""
    words, lines, cur = text.split(), [], ''
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return '\n'.join(lines)


def source_paragraphs(fm, source_by_number):
    """The practice's ORIGINAL Rule/Why/Install paragraphs, re-parsed from
    PRACTICES.md rather than read back out of the file this script is about
    to overwrite."""
    num = fm.get('source_practice_number')
    orig = source_by_number.get(num)
    if orig is None:
        sys.exit(f"resplit FAIL: practice {num!r} not found in PRACTICES.md -- this "
                 f"pass re-homes BestPractice's own text and cannot place a practice "
                 f"that has no source entry.")
    return {s: paragraphs(orig[s]) for s in SOURCE_SECTIONS}


def build_new_body(path, spec_for_practice, source_by_number):
    fm, _sections = sp._read_practice_file(path)
    paras = source_paragraphs(fm, source_by_number)

    covered = _covered(spec_for_practice)
    expected = set(_all_refs(paras))
    missing = expected - set(covered)
    unknown = set(covered) - expected
    if missing:
        sys.exit(f"resplit FAIL: {path.name}: spec does not account for "
                 f"{sorted(missing)} -- every source paragraph must be placed, so a "
                 f"paragraph cannot be dropped by omission.")
    if unknown:
        sys.exit(f"resplit FAIL: {path.name}: spec references {sorted(unknown)}, "
                 f"which do not exist in this practice.")
    for base, refs in covered.items():
        if len(refs) > 1 and any('.' not in r for r in refs):
            sys.exit(f"resplit FAIL: {path.name}: {base} is used {len(refs)} times "
                     f"({refs}) -- a whole paragraph may be placed exactly once.")

    out = {}
    for target in SECTIONS:
        blocks = []
        for ref in spec_for_practice.get(target, []):
            text = resolve(ref, paras)
            blocks.append(rewrap(text) if '.' in ref else text)
        out[target] = '\n\n'.join(blocks)
    return fm, out


def render(path, fm_text, sections):
    body = []
    for name in SECTIONS:
        body.append(f"## {name.capitalize()}\n")
        if sections[name]:
            body.append(sections[name].rstrip('\n') + '\n')
        if name != SECTIONS[-1]:
            body.append('\n')
    return fm_text + ''.join(body)


def frontmatter_text(path):
    text = path.read_text(encoding='utf-8')
    end = text.index('\n---\n', 4)
    return text[:end + 5]


def main():
    check = '--check' in sys.argv
    spec = json.loads(SPEC_PATH.read_text(encoding='utf-8'))
    source_by_number = {p['number']: p
                        for p in sp.parse_catalogue(sp.CATALOGUE.read_text(encoding='utf-8'))}
    changed, drift = [], []
    for slug, practice_spec in sorted(spec.items()):
        path = PRACTICES_DIR / f'{slug}.md'
        if not path.exists():
            sys.exit(f"resplit FAIL: no practices/{slug}.md for spec entry {slug!r}")
        _fm, new_sections = build_new_body(path, practice_spec, source_by_number)
        new_text = render(path, frontmatter_text(path), new_sections)
        if new_text != path.read_text(encoding='utf-8'):
            (drift if check else changed).append(slug)
            if not check:
                path.write_text(new_text, encoding='utf-8')
    if check:
        if drift:
            print(f"resplit --check FAIL: {len(drift)} practice(s) differ from the "
                  f"spec in tools/section_split.json: {', '.join(drift)}")
            return 1
        print(f"resplit --check OK: all {len(spec)} spec'd practices match "
              f"tools/section_split.json")
        return 0
    print(f"resplit OK: {len(changed)} of {len(spec)} practice(s) rewritten")
    return 0


if __name__ == '__main__':
    sys.exit(main())
