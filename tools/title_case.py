#!/usr/bin/env python3
"""title_case.py — headline capitalization for markdown headings.

Checks (bare, the default) or applies (--write) New York Times headline
capitalization on every ATX heading in the files given, or, when none are
named, in every outward-facing document in the repo — everything except the
internal working files listed in INTERNAL_DIRS / INTERNAL_FILES below.

The rule, stated once so the output is arguable rather than magic:

  * The first and last word of a heading are always capitalized.
  * A word immediately after a colon or a dash is capitalized — it opens a
    new phrase.
  * Articles, coordinating conjunctions and short prepositions (SMALL below,
    the standard NYT list) are lowercased anywhere else.
  * Every other word gets its first letter capitalized and the REST OF THE
    WORD UNTOUCHED. That is what keeps AI, GitHub, PR and TODO intact
    without needing a dictionary of proper nouns.
  * Both halves of a hyphenated compound are capitalized (Multi-Person).

Fenced code blocks are skipped, so a ``` block containing a `# comment` is
never rewritten.

practice: headline-capitalization — this file IS that practice's definition,
not merely its enforcement: the rules above are stated here once so no
adopting repository restates them. Change them here and everywhere follows.
"""

import json
import pathlib
import re
import sys

# EVERY document is outward-facing unless it is named here. Stated as an
# exclusion on purpose (Morgan, 2026-09-06): an allowlist of outward
# directories silently misses each new one somebody adds, which is exactly
# what happened here — the practice shipped covering `documentation/` alone,
# and `content/` and `book*/` had to be added the same day. An exclusion
# fails the safe way round: a directory nobody has classified is treated as
# published, and the worst case is a heading capitalized that did not need to
# be.
#
# WHAT COUNTS AS INTERNAL: the project managing itself. Practice files, the
# engine, specs, briefs, decision records, evaluation fixtures, templates
# awaiting instantiation, and the instructions/index/catalogue documents a
# session reads to work here. None of it is published to anyone, and heading
# style in it is never to be "fixed".
INTERNAL_DIRS = (
    ".claude", ".github", "candidates", "decisions", "deck", "evals",
    "examples", "local", "practices", "process", "spec", "templates", "tools",
)

# A repository's root holds BOTH kinds, which is why directories alone cannot
# settle this: README.md and SETUP.md are the first things an outsider reads,
# while PRACTICES.md and PRACTICE_ENGINE_PLAN.md sit beside them and are pure
# internal machinery. Named individually, therefore. Three of these are also
# GENERATED (AGENTS.md, MAP.md, GLOSSARY.md) — rewriting a heading in one
# would be undone by the next tools/build_views.py run and fail its
# byte-identical check in between, so they could not be in scope even if they
# were outward-facing.
INTERNAL_FILES = (
    "AGENTS.md", "CLAUDE.md", "CHANGES_TO_TELL_ALEX.md", "GLOSSARY.md",
    "MAP.md", "PRACTICES.md", "PRACTICE_ENGINE_PLAN.md", "TODO.md",
)


def is_outward(rel_path):
    """Is a repo-relative path a document published to people outside the
    project? True for anything not excluded above."""
    parts = pathlib.PurePosixPath(str(rel_path).replace("\\", "/")).parts
    if not parts or not parts[-1].endswith(".md"):
        return False
    if parts[0] in INTERNAL_DIRS:
        return False
    if len(parts) == 1 and parts[0] in INTERNAL_FILES:
        return False
    return True


def outward_files(root=None):
    """Every outward-facing markdown file in the repo."""
    base = pathlib.Path(root) if root is not None else pathlib.Path(".")
    out = []
    for f in sorted(base.rglob("*.md")):
        rel = f.relative_to(base)
        if rel.parts and rel.parts[0] == ".git":
            continue
        if is_outward(rel):
            out.append(f)
    return out


# The standard New York Times list of words that stay lowercase inside a
# headline. Length is not the criterion — membership is.
SMALL = {
    "a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
    "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs.",
}

# Exact phrases that carry their own capitalization as part of their meaning,
# and so are exempt from the SMALL rule. "The Why" is a noun phrase — the
# reasoning behind a decision — not an article plus a word.
KEEP_PHRASES = ("The Why",)

HEADING = re.compile(r"^(#{1,6})(\s+)(.*?)(\s*)$")
FENCE = re.compile(r"^\s*(```|~~~)")
# A word is capitalized after one of these; each opens a new phrase.
OPENS_PHRASE = (":", "—", "–", "--")


def _cap(word: str) -> str:
    """Capitalize the first letter, leave every other character alone."""
    for i, ch in enumerate(word):
        if ch.isalpha():
            return word[:i] + ch.upper() + word[i + 1:]
    return word


def _lower(word: str) -> str:
    """Lowercase the first letter, leave every other character alone."""
    for i, ch in enumerate(word):
        if ch.isalpha():
            return word[:i] + ch.lower() + word[i + 1:]
    return word


def _core(token: str) -> str:
    """The token stripped of surrounding punctuation, for SMALL lookup."""
    return token.strip("([{\"'“”‘’),.!?;]}").lower()


def _cap_hyphenated(token: str) -> str:
    if "-" not in token:
        return _cap(token)
    return "-".join(_cap(part) for part in token.split("-"))


def title_case(text: str) -> str:
    tokens = text.split(" ")
    # Index of the last token that actually contains a letter — a trailing
    # "—" or "(cont.)" should not absorb the always-capitalize-the-last rule.
    last = max(
        (i for i, t in enumerate(tokens) if any(c.isalpha() for c in t)),
        default=len(tokens) - 1,
    )
    out = []
    for i, token in enumerate(tokens):
        if not token:
            out.append(token)
            continue
        after_break = i > 0 and tokens[i - 1].endswith(OPENS_PHRASE)
        if i == 0 or i == last or after_break:
            out.append(_cap_hyphenated(token))
        elif _core(token) in SMALL:
            out.append(_lower(token))
        else:
            out.append(_cap_hyphenated(token))
    result = " ".join(out)
    # Restore any phrase whose own capitalization is the point.
    for phrase in KEEP_PHRASES:
        result = re.sub(re.escape(phrase), phrase, result, flags=re.IGNORECASE)
    return result


def process(path: pathlib.Path, write: bool):
    """Return the list of (line_no, before, after) headings that differ."""
    lines = path.read_text(encoding="utf-8").split("\n")
    in_fence = False
    changes = []
    for n, line in enumerate(lines):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if not m:
            continue
        hashes, gap, text, tail = m.groups()
        fixed = title_case(text)
        if fixed != text:
            changes.append((n + 1, text, fixed))
            lines[n] = f"{hashes}{gap}{fixed}{tail}"
    if write and changes:
        path.write_text("\n".join(lines), encoding="utf-8")
    return changes


def main():
    args = [a for a in sys.argv[1:]]
    if "--help" in args or "-h" in args:
        print(__doc__.strip())
        print("\nRun:\n"
              "  python3 tools/title_case.py [FILE ...]"
              "           # check; exit 1 on any wrong heading\n"
              "  python3 tools/title_case.py --write [FILE ...]"
              "   # rewrite them in place\n"
              "  python3 tools/title_case.py --json [FILE ...]"
              "    # report as JSON\n"
              "\nWith no FILE, every outward-facing markdown file in the repo "
              "— that is, all of them except " + ", ".join(
                  f"{d}/" for d in INTERNAL_DIRS) + " and the internal "
              "root documents (" + ", ".join(INTERNAL_FILES) + ").")
        return 0
    write = "--write" in args
    as_json = "--json" in args
    paths = [pathlib.Path(a) for a in args if not a.startswith("--")]
    if not paths:
        paths = outward_files()
    paths = [p for p in paths if p.is_file()]
    if not paths:
        print("title_case: no markdown files to inspect")
        return 0

    total = 0
    report = {}
    for path in paths:
        changes = process(path, write)
        total += len(changes)
        if changes:
            report[str(path)] = changes
            if not as_json:
                print(f"{path}")
                for n, before, after in changes:
                    print(f"  {n}: {before}")
                    print(f"  {' ' * len(str(n))}  -> {after}")

    if as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    if not total:
        print(
            f"title_case OK: {len(paths)} file(s) — every heading is already "
            "in headline capitalization."
        )
        return 0
    if write:
        print(f"title_case: rewrote {total} heading(s) in {len(report)} file(s).")
        return 0
    print(
        f"title_case FAIL: {total} heading(s) in {len(report)} file(s) are not "
        "in headline capitalization. Re-run with --write to fix."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
