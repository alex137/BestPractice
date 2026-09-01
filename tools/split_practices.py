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

cmd_build() also rebases cross-practice links: a practice file links a
sibling bare ('](some-slug.md)'), correct from inside practices/, and
cmd_build() prefixes it to 'practices/some-slug.md' so the same text still
resolves once embedded in this root-level file. Path rewrite only, not
content -- see spec/PRACTICE_FORMAT.md, "Citing Other Practices".

One documented exception to the "move and drop only" rule: practice 39's
raw body in the source file is followed, in the source, by a stray duplicate
of part of practice 34's body (a corruption in the upstream file, not
authored content of practice 39's own — see FIXUP_39_MARKER below and
spec/PRACTICE_FORMAT.md). That duplicate is dropped, precisely and only
there, and the byte-identical-regeneration check treats exactly that
removal as the one approved exception to an otherwise-exact diff.

Run:
  python3 tools/split_practices.py split           # PRACTICES.md -> practices/*.md
  python3 tools/split_practices.py build            > /tmp/PRACTICES.rebuilt.md
  python3 tools/split_practices.py build --diff      # compare rebuild vs PRACTICES.md
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / 'PRACTICES.md'
PRACTICES_DIR = ROOT / 'practices'
METADATA = json.loads((ROOT / 'tools' / 'practice_metadata.json').read_text(encoding='utf-8'))['practices']

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

        if number == '39' and FIXUP_39_MARKER in body:
            body = body[:body.index(FIXUP_39_MARKER)]
            # Walk back to the start of the corrupted paragraph fragment
            # (a line-wrapped continuation with no blank line before it).
            body = body.rstrip('\n')
            last_blank = body.rfind('\n\n')
            body = body[:last_blank] if last_blank != -1 else body

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


def cmd_split():
    text = CATALOGUE.read_text(encoding='utf-8')
    practices = parse_catalogue(text)
    PRACTICES_DIR.mkdir(exist_ok=True)
    seen_slugs = set()
    for p in practices:
        meta = METADATA.get(p['number'])
        if not meta:
            sys.exit(f"split FAIL: no tools/practice_metadata.json entry for practice {p['number']} "
                      f"({p['title']!r}) -- add one before splitting.")
        slug = meta['slug']
        if slug in seen_slugs:
            sys.exit(f"split FAIL: duplicate slug {slug!r}")
        seen_slugs.add(slug)
        out = [_frontmatter(p, meta)]
        out.append('## Rule\n')
        out.append(p['rule'] + '\n')
        out.append('\n## Why\n')
        out.append((p['why'] + '\n') if p['why'] else '')
        out.append('\n## Story\n')
        out.append('\n## Install\n')
        out.append((p['install'] + '\n') if p['install'] else '')
        (PRACTICES_DIR / f'{slug}.md').write_text(''.join(out), encoding='utf-8')
    print(f"split OK: wrote {len(practices)} practice file(s) to {PRACTICES_DIR}")
    return 0


FM_FIELD_RE = re.compile(r'^([a-z_]+):\s*(.*)$')


def _read_practice_file(path):
    text = path.read_text(encoding='utf-8')
    assert text.startswith('---\n')
    end = text.index('\n---\n', 4)
    fm_text, body = text[4:end], text[end + 5:]
    fm = {}
    for line in fm_text.splitlines():
        m = FM_FIELD_RE.match(line)
        if m:
            fm[m.group(1)] = m.group(2)
    sections = {}
    cur = None
    buf = []
    for line in body.split('\n'):
        m = re.match(r'^## (Rule|Why|Story|Install)$', line)
        if m:
            if cur:
                sections[cur] = '\n'.join(buf).strip('\n')
            cur = m.group(1).lower()
            buf = []
        else:
            buf.append(line)
    if cur:
        sections[cur] = '\n'.join(buf).strip('\n')
    return fm, sections


CROSS_PRACTICE_LINK_RE = re.compile(r'\]\(([a-z0-9]+(?:-[a-z0-9]+)*\.md)\)')


def _rebase_practice_links(text):
    """practices/*.md bodies link sibling practices bare ('](some-slug.md)'),
    correct from inside practices/. Embedded here in a root-level document,
    that same relative link needs the practices/ prefix to still resolve.
    Mechanical path-rewrite only -- no content change -- so it does not
    conflict with the converter's no-invented-content rule."""
    return CROSS_PRACTICE_LINK_RE.sub(r'](practices/\1)', text)


def cmd_build():
    files = sorted(PRACTICES_DIR.glob('*.md'),
                    key=lambda p: int(_read_practice_file(p)[0]['source_practice_number']))
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
        rule = _rebase_practice_links(sections.get('rule', ''))
        rule_block = rule if fm.get('source_rule_unlabeled') == 'true' else _labeled('Rule', rule)
        parts = [f'## {num}. {title}', rule_block]
        why = _rebase_practice_links(sections.get('why', ''))
        if why:
            parts.append(_labeled('Why', why))
        install = _rebase_practice_links(sections.get('install', ''))
        if install:
            parts.append(_labeled('Install', install))
        blocks.append('\n\n'.join(parts))
    return '\n\n'.join(blocks).rstrip('\n') + '\n'


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ('split', 'build'):
        sys.exit(__doc__)
    if args[0] == 'split':
        return cmd_split()
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
