#!/usr/bin/env python3
"""split_practices.py — convert PRACTICES.md into one file per practice
(practices/<slug>.md), and the reverse: rebuild a PRACTICES.md-equivalent
catalogue view from those files, for the harness's byte-identical-regeneration
check (see spec/PRACTICE_FORMAT.md).

MECHANICAL, NOT EDITORIAL. Per the practice-engine plan (PRACTICE_ENGINE_PLAN.md,
"The Converter"): "no sentence may appear in the output that does not appear in
the input. The converter may move and drop text, never invent it." This script
follows that to the letter — the only judgment it embeds is the fixed label ->
section mapping below, applied uniformly, never a per-practice content read.

BestPractice's PRACTICES.md is NOT uniformly structured (found while writing
this): practices 1-46ish open with explicit **Rule.**/**Why.**/**Install.**
bold labels; practices 40-43 use **The practice.** instead of **Rule.**;
practices 47-52 have no leading bold label at all — the body just starts as
plain prose. A purely regex-anchored "grab the **Why.** paragraph" extractor
breaks on the second group. So parsing is done as a general label/carry-forward
walk instead: read the body as a sequence of paragraphs; track a
"current section", which starts at 'rule' and only changes when a paragraph
OPENS with a recognized bold label (**Rule.**, **The practice.**, **Why...**,
**Install.**, **Related...**); every other paragraph — including one that opens
with an UNRECOGNIZED bold sub-heading, e.g. practice 20's "**Proportionality
guard.**" — stays in whatever section is already open. This carries every
sentence into some section with zero content invented and zero content lost,
regardless of which of the two source formats a given practice used.

Two structural decisions this makes, stated so they can be revisited:

  - Story is not populated. The plan's Rule/Why/Story split additionally asks
    for the *incident* to be separated out from the *reasoning* within Why —
    that is real editorial judgment, described in the plan itself as
    "LLM-assisted and human-reviewed, once per practice" (Migration, "The
    Converter"). Doing that with real care for 52 practices in one pass,
    unreviewed, risked mischaracterizing exactly the content this plan is
    built to preserve faithfully. So for phase 1: `## Story` exists as a
    section header in every practice file, with no body — a deliberate,
    flagged gap, not a silent one. Splitting it is follow-on work.
  - `## Install` is a fourth section, alongside Rule/Why/Story, not present
    in the plan's own illustrative frontmatter example. BestPractice's
    "Install." text (how a dependent repo actually installs the practice —
    template paths, tool names, wiring) has no other home in the plan's
    three-section spec, and dropping it would both violate the no-invented-
    /no-lost-content rule and break "byte-identical regeneration", since the
    original PRACTICES.md is Rule+Why+Install and nothing else per practice.
    See spec/PRACTICE_FORMAT.md for the full note on this.

One documented exception to the "move and drop only" rule: practice 39's
raw body in the source file is followed, in the source, by a stray duplicate
of part of practice 34's body (a corruption in the upstream file, not
authored content of practice 39's own — see FIXUP_39_MARKER below and
spec/PRACTICE_FORMAT.md). That duplicate is dropped, precisely and only
there, and the byte-identical-regeneration check treats exactly that
removal as the one approved exception to an otherwise-exact diff.

The duplicate is pasted MID-PARAGRAPH — it begins mid-word on the line
immediately after practice 39's own "**Install.**" paragraph ends, with no
blank line between — so the drop must begin at the marker itself. An
earlier version walked back to the preceding blank line, which deleted
practice 39's whole Install paragraph along with the corruption, silently
and with the harness fully green: every check compared the lossy output
against a source parsed through the same lossy fixup. The span actually
dropped is now recorded on each parsed practice as `dropped_corruption`,
and verify_harness.py's check_corruption_drop_is_a_duplicate asserts that
whatever is dropped occurs verbatim elsewhere in the file — a property of
the text rather than of the boundary, so it fails on an over-broad drop.

Run:
  python3 tools/split_practices.py split           # PRACTICES.md -> practices/*.md
                                                    # (refuses if practices/ is non-empty;
                                                    # see cmd_split's docstring comment --
                                                    # pass --force for a deliberate redo)
  python3 tools/split_practices.py build            > /tmp/PRACTICES.rebuilt.md
  python3 tools/split_practices.py build --diff      # compare rebuild vs PRACTICES.md

NOTE on `build --diff`: it used to be expected to come back empty, and
verify_harness.py gated on that. It no longer is. The phase-1.5 editorial
re-split (tools/resplit_sections.py) moves text between Rule/Why/Story/
Install, which moves where this command re-emits each "**Why.**" label, so
a non-empty diff is now the normal output and shows the re-split rather than
a defect. What proves the practice files still hold exactly BestPractice's
content is verify_harness.py's sentence-for-sentence check against
PRACTICES.md, which is stronger than this diff ever was and does not care
how the sections are divided.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / 'PRACTICES.md'
PRACTICES_DIR = ROOT / 'practices'
METADATA_PATH = ROOT / 'tools' / 'practice_metadata.json'


def load_metadata():
    """Loaded on demand, not at import. Only `split` uses it, but every
    tool in this directory imports this module -- including
    precedent_show.py, which is the RUNTIME path an agent loads a practice
    through. A corrupt or missing build-time metadata file used to take
    that down with a raw json.decoder traceback at import time, which is
    neither graceful nor informative."""
    try:
        raw = METADATA_PATH.read_text(encoding='utf-8')
    except OSError as e:
        sys.exit(f"split FAIL: cannot read {METADATA_PATH}: {e}")
    try:
        return json.loads(raw)['practices']
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        sys.exit(f"split FAIL: {METADATA_PATH} is not valid practice metadata "
                 f"({type(e).__name__}: {e}) -- expected a JSON object with a "
                 f"'practices' key.")

HEADER_RE = re.compile(r'^## (\d+)\. (.+)$')
LABEL_RE = re.compile(r'^\*\*([A-Za-z][^*]{0,60}?)[.:]\*\*\s*(.*)$', re.DOTALL)

# The exact corrupted fragment (see module docstring). Distinctive enough
# that a substring search cannot false-positive elsewhere in the file.
FIXUP_39_MARKER = "es a source's vocabulary within a single session, has no"


CANONICAL_LABELS = {'rule', 'why', 'install'}


def _label_to_section(label):
    """(section, strip) -- section routes the paragraph; strip says whether
    the label text itself should be dropped (only for the exact canonical
    words, which cmd_build re-emits) or kept as content (any other label,
    e.g. "The practice.", "Why it evades the usual checks.", "Related." --
    real authored words, not interchangeable boilerplate, so replacing them
    with the bare canonical word would be exactly the "invent/alter content"
    move the converter must not make)."""
    low = label.lower()
    if low in CANONICAL_LABELS:
        return low, True
    if low == 'the practice':
        return 'rule', False
    if low.startswith('why'):
        return 'why', False
    if low.startswith('install'):
        return 'install', False
    # "**Related.**" and any other bold sub-heading: not a section boundary
    # at all -- carries forward whatever section is already open, label kept.
    return None, False


def parse_catalogue(text):
    """-> list of dicts: {number, title, rule, why, install}, in file order."""
    chunks = re.split(r'\n(?=## \d+\. )', text)
    practices = []
    for chunk in chunks:
        if not chunk.startswith('## '):
            continue
        lines = chunk.split('\n', 1)
        m = HEADER_RE.match(lines[0])
        if not m:
            continue
        number, title = m.group(1), m.group(2)
        body = lines[1] if len(lines) > 1 else ''
        dropped_corruption = ''

        if number == '39' and FIXUP_39_MARKER in body:
            # The corrupted fragment is pasted mid-paragraph, with no blank
            # line before it: practice 39's own "**Install.**" paragraph
            # ends "...not just the template itself." and the very next
            # LINE is the stray duplicate, starting mid-word ("...acquir"
            # + "es a source's vocabulary..."). So the drop begins exactly
            # at the marker. An earlier version of this walked back to the
            # previous BLANK line instead, which silently swallowed the
            # whole of practice 39's Install paragraph along with the
            # corruption -- real authored content, lost with no check
            # firing (the no-invented-content check is a subset test, so
            # a deletion passes it, and the byte-identical check's own
            # "approved exception" span had been written to match the same
            # over-broad boundary).
            kept = body[:body.index(FIXUP_39_MARKER)].rstrip('\n')
            # Record exactly what was dropped, so verify_harness.py can test
            # THIS span rather than re-deriving a boundary of its own -- a
            # check that recomputes the boundary cannot catch a converter
            # that got the boundary wrong.
            dropped_corruption = body[len(kept):].strip()
            body = kept

        paragraphs = re.split(r'\n\n+', body.strip('\n'))
        sections = {'rule': [], 'why': [], 'install': []}
        current = 'rule'
        # Does the body open with *any* recognized label at all? Practices
        # 47-52 open on bare prose -- no "**Rule.**"/"**The practice.**",
        # nothing. cmd_build must not inject a label there that the
        # original never had, so this is recorded and carried through
        # (source_rule_unlabeled in the frontmatter) rather than inferred
        # later from content shape, which can't tell "label stripped" from
        # "no label ever existed" apart once both leave no leading "**".
        first_para = next((p for p in paragraphs if p.strip()), '')
        rule_unlabeled = not bool(LABEL_RE.match(first_para))
        stripped_once = set()  # a repeated canonical label (practice 28 has
                                # two separate "**Install.**" blocks) can only
                                # be stripped the first time -- cmd_build has
                                # nowhere to put a second re-emitted label, so
                                # a repeat is kept as literal content instead.
        for para in paragraphs:
            if not para.strip():
                continue
            m2 = LABEL_RE.match(para)
            if m2:
                label, rest = m2.group(1), m2.group(2)
                target, strip = _label_to_section(label)
                if strip and target in stripped_once:
                    strip = False
                if target:
                    current = target
                    if strip:
                        stripped_once.add(target)
                        para = rest.strip()
                        if not para:
                            continue
                # else: non-canonical or unrecognized label -- the whole
                # paragraph, label text included, stays as content of
                # whichever section is now open
            sections[current].append(para)
        practices.append({
            'number': number,
            'title': title,
            'rule': '\n\n'.join(sections['rule']).strip(),
            'why': '\n\n'.join(sections['why']).strip(),
            'install': '\n\n'.join(sections['install']).strip(),
            'rule_unlabeled': rule_unlabeled,
            'dropped_corruption': dropped_corruption,
        })
    return practices


def _frontmatter(practice, meta):
    slug = meta['slug']
    lines = [
        '---',
        f'slug:        {slug}',
        f'title:       {practice["title"]}',
        'tier:        on-demand',
        'severity:    default',
        'applies_to:  ' + json.dumps(meta['applies_to']),
        'occasion:    ' + json.dumps(meta['occasion']),
        'checked_by:  ' + (json.dumps(meta['checked_by']) if meta['checked_by'] else 'null'),
        'defines:     []',
        'status:      active',
        'supersedes:  []',
        'overrides:   null',
        'added:       null',
        'approved_by: "BestPractice (pre-fork)"',
        f'source_practice_number: {practice["number"]}',
    ]
    if practice['rule_unlabeled']:
        lines.append('source_rule_unlabeled: true')
    lines += ['---', '']
    return '\n'.join(lines)


def cmd_split(force=False):
    # split is a one-time phase-1 converter (PRACTICES.md -> practices/*.md).
    # Re-running it after phase 2 would silently overwrite every phase-2
    # curation decision this-file's frontmatter can't reproduce from
    # PRACTICES.md at all -- tier: resident, defines:, any future severity
    # or checked_by hand-edit -- with the phase-1 defaults baked into
    # _frontmatter() below. Refuse by default; --force is for a deliberate
    # from-scratch reconversion, not routine use.
    existing = sorted(PRACTICES_DIR.glob('*.md')) if PRACTICES_DIR.exists() else []
    if existing and not force:
        sys.exit(f"split FAIL: {PRACTICES_DIR} already has {len(existing)} practice file(s). "
                 f"Re-splitting would overwrite phase-2 curation (tier: resident, defines:, "
                 f"any hand-edit) with phase-1 defaults -- pass --force if you really mean "
                 f"a from-scratch reconversion.")
    metadata = load_metadata()
    text = CATALOGUE.read_text(encoding='utf-8')
    practices = parse_catalogue(text)

    # Validate the WHOLE catalogue before writing a single file. This used
    # to be checked inside the write loop, so a missing metadata entry for
    # practice 39 left practices/ holding 38 files and 14 missing -- a
    # half-converted tree, from a command that had already refused to run
    # over a non-empty directory precisely to avoid clobbering one.
    seen_slugs = {}
    problems = []
    for p in practices:
        meta = metadata.get(p['number'])
        if not meta:
            problems.append(f"no tools/practice_metadata.json entry for practice "
                            f"{p['number']} ({p['title']!r})")
            continue
        slug = meta.get('slug')
        if not slug:
            problems.append(f"practice {p['number']}: metadata entry has no 'slug'")
            continue
        for field in ('applies_to', 'occasion', 'checked_by'):
            if field not in meta:
                problems.append(f"practice {p['number']} ({slug}): metadata entry is "
                                f"missing required field {field!r}")
        if slug in seen_slugs:
            problems.append(f"duplicate slug {slug!r} (practices {seen_slugs[slug]} "
                            f"and {p['number']})")
        seen_slugs[slug] = p['number']
    if problems:
        sys.exit("split FAIL: nothing written. "
                 + str(len(problems)) + " metadata problem(s):\n  - "
                 + "\n  - ".join(problems))

    PRACTICES_DIR.mkdir(exist_ok=True)
    for p in practices:
        meta = metadata[p['number']]
        slug = meta['slug']
        out = [_frontmatter(p, meta)]
        out.append('## Rule\n')
        out.append(p['rule'] + '\n')
        # Empty at split time, exactly as ## Story is: the mechanical converter
        # routes by the source's own bold labels, and BestPractice's catalogue
        # has no "Detail." label to route on. Filling it is the editorial pass
        # (tools/resplit_sections.py), which moves text by reference.
        out.append('\n## Detail\n')
        out.append('\n## Why\n')
        out.append((p['why'] + '\n') if p['why'] else '')
        out.append('\n## Story\n')
        out.append('\n## Install\n')
        out.append((p['install'] + '\n') if p['install'] else '')
        (PRACTICES_DIR / f'{slug}.md').write_text(''.join(out), encoding='utf-8')
    print(f"split OK: wrote {len(practices)} practice file(s) to {PRACTICES_DIR}")
    return 0


FM_FIELD_RE = re.compile(r'^([a-z_]+):\s*(.*)$')


class PracticeFileError(ValueError):
    """A practices/*.md file that cannot be parsed. Named and raised rather
    than asserted: `assert` produces a bare AssertionError that does not
    even say WHICH file, disappears entirely under `python3 -O`, and takes
    the whole harness down with a traceback instead of a reported failure.
    Practice files are hand-authored from phase 3 on, so a malformed one is
    an expected input, not an impossible state."""


def _read_practice_file(path):
    return _parse_practice_text(path.read_text(encoding='utf-8'), path)


def _parse_practice_text(text, path='<text>'):
    """The parser, split out from the reader so a caller holding a practice
    file's EARLIER content (from `git show`) can parse it the same way. Added
    at phase 4: tools/precedent_check.py's cite-the-incident check has to
    compare a practice's Rule against its previous Rule to tell a new rule
    from a frontmatter edit, and there was no way to parse text that is not
    on disk. One parser, per the plan's "one code path"; the alternative was
    a second extractor to drift from this one."""
    if not text.startswith('---\n'):
        raise PracticeFileError(
            f"{path}: not a practice file -- it must open with a '---' "
            f"frontmatter fence on line 1 (see spec/PRACTICE_FORMAT.md).")
    end = text.find('\n---\n', 4)
    if end == -1:
        raise PracticeFileError(
            f"{path}: frontmatter is never closed -- no '---' line after the "
            f"opening fence (see spec/PRACTICE_FORMAT.md).")
    fm_text, body = text[4:end], text[end + 5:]
    fm = {}
    for line in fm_text.splitlines():
        m = FM_FIELD_RE.match(line)
        if m:
            fm[m.group(1)] = m.group(2)
    sections = {}
    cur = None
    buf = []
    for lineno, line in enumerate(body.split('\n'), 1):
        # \s*$ tolerates trailing whitespace (including a tab) on the heading
        # line. Without it a single accidental trailing space ("## Detail ")
        # silently merged that entire section -- heading text included --
        # into whatever section came before it, with no error:
        # precedent_show.py --detail would then report "(no detail recorded
        # yet)" while the Rule silently carried the corrupted trailing
        # content.
        m = re.match(r'^## (Rule|Detail|Why|Story|Install)\s*$', line)
        if m:
            if cur:
                sections[cur] = '\n'.join(buf).strip('\n')
            cur = m.group(1).lower()
            buf = []
            continue
        # A level-2 heading that ISN'T one of the five exact names is almost
        # always the same failure the whitespace fix above closed, one
        # character over: a case typo ("## detail") reproduces the identical
        # silent merge -- heading text and body both swallowed into the
        # PRECEDING section with no error -- because the regex above simply
        # never matches it, and there is nothing else in this file's shape
        # that would ever legitimately put a bare `## ` line in a practice
        # body (no practices/*.md file does, as of this check). So any such
        # line fails loudly here instead of corrupting content that goes on
        # to be loaded into a session's context.
        near = re.match(r'^## \s*(\S.*?)\s*$', line)
        if near and near.group(1).strip().lower() in (
                'rule', 'detail', 'why', 'story', 'install'):
            raise PracticeFileError(
                f"{path}:{lineno}: {line!r} looks like a section heading but "
                f"is not spelled exactly right (expected one of '## Rule', "
                f"'## Detail', '## Why', '## Story', '## Install' -- exact "
                f"case, one space after '##'). Left uncorrected this heading "
                f"is not recognized as a heading at all and its whole "
                f"section, including this line, is silently merged into "
                f"the section above it.")
        buf.append(line)
    if cur:
        sections[cur] = '\n'.join(buf).strip('\n')
    return fm, sections


def cmd_build():
    # The catalogue view is a phase-1 migration artifact: it rebuilds
    # PRACTICES.md from the practices that came OUT of it, ordered by their
    # original number. A practice minted fresh (a promoted team or
    # individual one, from phase 3 on) has no source_practice_number by
    # design -- spec/PRACTICE_FORMAT.md says so explicitly -- so name that
    # case instead of dying on a KeyError inside a sort key.
    unnumbered = []
    keyed = []
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        fm, _sections = _read_practice_file(f)
        num = fm.get('source_practice_number')
        if num is None:
            unnumbered.append(f.name)
        else:
            keyed.append((int(num), f))
    if unnumbered:
        sys.exit(f"build FAIL: {len(unnumbered)} practice file(s) have no "
                 f"source_practice_number, so they have no place in a rebuild of "
                 f"BestPractice's numbered catalogue: {', '.join(sorted(unnumbered))}. "
                 f"This command is the phase-1 round-trip check, not a general "
                 f"catalogue renderer -- see spec/PRACTICE_FORMAT.md.")
    files = [f for _num, f in sorted(keyed)]
    blocks = ['# The practice catalog']
    blocks.append('''Each practice: the **rule**, **why** (the abstracted incident that motivated
it — every one of these was learned the expensive way in a real repo), and
**install** (what a dependent repo does about it). Templates referenced here
live in `templates/`; tools in `tools/`.''')
    def _labeled(canonical, content):
        # Content that already opens with its own bold label (a non-canonical
        # one preserved verbatim at split time, e.g. "**The practice.**" or
        # "**Why it evades the usual checks.**") is not double-labeled.
        return content if content.startswith('**') else f'**{canonical}.** {content}'

    for f in files:
        fm, sections = _read_practice_file(f)
        num = fm['source_practice_number']
        title = fm['title']
        rule = sections.get('rule', '')
        rule_block = rule if fm.get('source_rule_unlabeled') == 'true' else _labeled('Rule', rule)
        parts = [f'## {num}. {title}', rule_block]
        # Detail is normative text that used to sit inside Rule, so it rebuilds
        # immediately after it, under Rule's own label. Emitting it anywhere
        # else would reorder the practice against its source.
        detail = sections.get('detail', '')
        if detail:
            parts.append(detail)
        why = sections.get('why', '')
        if why:
            parts.append(_labeled('Why', why))
        install = sections.get('install', '')
        if install:
            parts.append(_labeled('Install', install))
        blocks.append('\n\n'.join(parts))
    return '\n\n'.join(blocks).rstrip('\n') + '\n'


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ('split', 'build'):
        sys.exit(__doc__)
    if args[0] == 'split':
        return cmd_split(force='--force' in args)
    rebuilt = cmd_build()
    if '--diff' in args:
        original = CATALOGUE.read_text(encoding='utf-8')
        import difflib
        diff = list(difflib.unified_diff(original.splitlines(keepends=True),
                                          rebuilt.splitlines(keepends=True),
                                          fromfile='PRACTICES.md (original)',
                                          tofile='PRACTICES.md (rebuilt)'))
        if diff:
            sys.stdout.writelines(diff)
            return 1
        print("build --diff: rebuild is byte-identical to PRACTICES.md")
        return 0
    sys.stdout.write(rebuilt)
    return 0


if __name__ == '__main__':
    sys.exit(main())
