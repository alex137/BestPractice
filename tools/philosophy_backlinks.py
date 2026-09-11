#!/usr/bin/env python3
"""Check that philosophy/ cross-references run both ways.

Every item in the core philosophy documents carries a permanent slug. When
one item cites another, a reader landing on the cited end should be able to
find their way back -- so a citation is expected to be reciprocated, in the
cited item's own prose, the same way the forward citation is written.

This tool does NOT write those sentences. An earlier version generated a
`*Cited by: ...*` line under each cited item; Morgan read the result on
2026-09-11 and said it made the documents confusing -- machine output bolted
under prose reads as exactly that. So the back-reference is written by hand,
in the document's voice, and this tool only reports which ones are missing.

Experimental (2026-09-11). See philosophy/doc-recipes/backlinks.recipe.md.
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent / "philosophy"

# The core documents only. ASSORTED_NOTES.md is a dated brainstorm with no
# item list, and README.md is an index of files rather than of ideas.
DOCS = {
    "CORE_PILLARS.md": "Core Pillars",
    "OUR_PHILOSOPHY.md": "Our Philosophy",
    "REASONS_WHY.md": "Reasons Why",
    "COMPANY_BUILDING_RULES.md": "Company Building Rules",
    "AI_GOVERNANCE_TO_COCREATE.md": "AI Governance",
    "HUMANS_AT_OUR_BEST.md": "Humans at Our Best",
    "RULES_NOW_TESTING.md": "Rules Now Testing",
}

ANCHOR = re.compile(r'<a id="([a-z0-9-]+)"></a>')
LINK = re.compile(r'\]\((?:([A-Z_]+\.md))?#([a-z0-9-]+)\)')
CITED_BY = re.compile(r'^\s*\*Cited by:.*\*\s*$')
BULLET = re.compile(r'^- ')
HEADING = re.compile(r'^#{1,6} ')

PREFIX = "*Cited by: "


def parse_items(name, lines):
    """Return [(slug, start, end)] -- end exclusive, trailing blanks trimmed."""
    starts = [(i, m.group(1)) for i, line in enumerate(lines)
              if (m := ANCHOR.search(line))]
    items = []
    for n, (i, slug) in enumerate(starts):
        limit = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        # RULES_NOW_TESTING.md puts the anchor above the heading it names,
        # so the item's own title must not be read as the terminator.
        body = i + 1
        while body < limit and lines[body].strip() == "":
            body += 1
        if body < limit and HEADING.match(lines[body]):
            body += 1
        end = limit
        for j in range(body, limit):
            # A heading ends the item: whatever follows belongs to the
            # document, not to this entry. So does the next bullet, for the
            # two documents whose items are list entries.
            if HEADING.match(lines[j]) or (BULLET.match(lines[i]) and BULLET.match(lines[j])):
                end = j
                break
        while end > body and lines[end - 1].strip() == "":
            end -= 1
        items.append((slug, i, end))
    return items


def links_in(name, lines, start, end):
    """The items this item cites, as (document, slug)."""
    out = []
    for line in lines[start:end]:
        for m in LINK.finditer(line):
            target = (m.group(1) or name, m.group(2))
            if target[0] in DOCS and target != (name, start):
                out.append(target)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true",
                    help="print the count only")
    args = ap.parse_args()

    docs, cites = {}, {}
    for name in DOCS:
        lines = (HERE / name).read_text().split("\n")
        items = parse_items(name, lines)
        docs[name] = (lines, items)
        for slug, start, end in items:
            cites[(name, slug)] = {t for t in links_in(name, lines, start, end)
                                   if t != (name, slug)}

    missing, total = [], 0
    for source, targets in sorted(cites.items()):
        for target in sorted(targets):
            if target not in cites:
                continue          # a slug that is not an item -- nothing to do
            total += 1
            if source not in cites[target]:
                missing.append((target, source))

    if args.quiet:
        print(f"philosophy-backlinks: {total - len(missing)}/{total} reciprocated")
        return 1 if missing else 0

    if missing:
        print(f"philosophy-backlinks: {len(missing)} citation(s) run one way only.\n"
              f"Write the return reference into the cited item's own prose -- "
              f"a clause in the document's voice, not a generated list.\n")
        for (tdoc, tslug), (sdoc, sslug) in missing:
            print(f"  {tdoc}#{tslug}")
            print(f"      is cited by {sdoc}#{sslug}, and does not point back")
        return 1
    print(f"philosophy-backlinks: OK -- all {total} citations run both ways")
    return 0


if __name__ == "__main__":
    sys.exit(main())
