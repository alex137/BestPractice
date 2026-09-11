#!/usr/bin/env python3
"""Make philosophy/ cross-references bidirectional.

Every item in the core philosophy documents carries a permanent slug. When
one item cites another, only the citing end says so; a reader landing on the
cited item has no way to discover who leaned on it. This tool reads the
whole citation graph and writes the reverse edge back under each cited item
as a `*Cited by: ...*` line.

The lines are generated, never hand-edited: run this after changing any
citation and commit what it writes. `--check` exits non-zero when the files
on disk disagree with the graph.

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


def strip_generated(lines):
    """Drop previously generated lines, and any blank line they introduced."""
    out = []
    for line in lines:
        if CITED_BY.match(line):
            # A generated paragraph in a numbered document is preceded by the
            # blank line that separates it; take that back too.
            if out and out[-1].strip() == "":
                out.pop()
            continue
        out.append(line)
    return out


def parse_items(name, lines):
    """Return [(slug, start, end)] -- end is exclusive, and excludes trailing
    blanks so an insertion lands against the item's own last line."""
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


def build_graph(docs):
    """slug-key -> [citing slug-key], in document then reading order."""
    cited_by = {}
    for name, (lines, items) in docs.items():
        for slug, start, end in items:
            for line in lines[start:end]:
                for m in LINK.finditer(line):
                    target = (m.group(1) or name, m.group(2))
                    if target[0] not in DOCS or target == (name, slug):
                        continue
                    cited_by.setdefault(target, [])
                    if (name, slug) not in cited_by[target]:
                        cited_by[target].append((name, slug))
    return cited_by


def render(target_doc, citers):
    parts = []
    for doc, slug in citers:
        link = f"[`{slug}`](#{slug})" if doc == target_doc \
            else f"[`{slug}`]({doc}#{slug}) in {DOCS[doc]}"
        parts.append(link)
    return PREFIX + "; ".join(parts) + ".*"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report drift instead of writing")
    args = ap.parse_args()

    docs = {}
    for name in DOCS:
        lines = strip_generated((HERE / name).read_text().split("\n"))
        docs[name] = (lines, parse_items(name, lines))

    cited_by = build_graph(docs)

    drift, written = [], 0
    for name, (lines, items) in docs.items():
        out = list(lines)
        # Insert from the bottom so earlier offsets stay valid.
        for slug, start, end in reversed(items):
            citers = cited_by.get((name, slug))
            if not citers:
                continue
            line = render(name, citers)
            if BULLET.match(lines[start]):
                out.insert(end, "  " + line)   # continues the list item
            else:
                out.insert(end, "")
                out.insert(end + 1, line)
        text = "\n".join(out)
        path = HERE / name
        if path.read_text() != text:
            drift.append(name)
            if not args.check:
                path.write_text(text)
                written += 1

    total = sum(len(v) for v in cited_by.values())
    if args.check:
        if drift:
            print("philosophy-backlinks: STALE in " + ", ".join(drift))
            return 1
        print(f"philosophy-backlinks: OK ({total} reverse edges)")
        return 0
    print(f"philosophy-backlinks: {total} reverse edges across "
          f"{len(cited_by)} items; rewrote {written} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
