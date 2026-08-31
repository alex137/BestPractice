#!/usr/bin/env python3
"""precedent_show.py — the one code path every loading channel calls
(PRACTICE_ENGINE_PLAN.md, "Loading a Practice Means Loading Its Rule, Not
Its File"). An agent never reads a practices/*.md file directly: it calls
this, and only this command's output enters context. That is what makes the
Rule/Why/Story split actually save tokens — reading the file directly would
front-load the whole thing, Story included, defeating the split.

  precedent show SLUG [SLUG...]           the ## Rule section of each
  precedent show SLUG [SLUG...] --why      the ## Why section of each
  precedent show SLUG [SLUG...] --story    the ## Story section of each
  precedent show SLUG [SLUG...] --install  the ## Install section of each
                                            (not in the plan's own three-
                                            section spec -- see
                                            spec/PRACTICE_FORMAT.md for why
                                            this repo's practice files carry
                                            a fourth section)

Multiple slugs concatenate, each under its own "### slug" heading, so a
caller loading several practices for one occasion gets one block back.

Exit 1, with a clear message naming the missing slug, on any slug that
doesn't resolve to a practices/*.md file -- this is a degrade-gracefully
tool (personal pack fail-gracefully, generalized): a bad slug in an occasion
index entry should be loud, not a silent empty read.
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRACTICES_DIR = ROOT / 'practices'

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp

SECTION_FLAGS = {'--why': 'why', '--story': 'story', '--install': 'install'}


def main():
    args = sys.argv[1:]
    section = 'rule'
    for flag, sec in SECTION_FLAGS.items():
        if flag in args:
            section = sec
            args = [a for a in args if a != flag]
    slugs = [a for a in args if not a.startswith('--')]
    if not slugs:
        sys.exit(__doc__)

    out = []
    missing = []
    for slug in slugs:
        path = PRACTICES_DIR / f'{slug}.md'
        if not path.exists():
            missing.append(slug)
            continue
        _fm, sections = sp._read_practice_file(path)
        body = sections.get(section, '').strip()
        out.append(f"### {slug}\n{body if body else '(no ' + section + ' recorded yet)'}")

    if missing:
        sys.exit(f"precedent show FAIL: unknown slug(s), no practices/*.md file for: "
                 f"{', '.join(missing)}")

    print('\n\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
