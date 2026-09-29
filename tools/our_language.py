#!/usr/bin/env python3
"""our_language -- the short list of words a person needs to follow a
conversation about Precedent, read from tools/our_language.json.

The registry is the one source. documentation/OUR_LANGUAGE.md carries a
generated block rendered from it, kept honest by tools/doc_sync.py
(practices: registry-source-of-truth, computed-numbers-in-scripts):

    python3 tools/our_language.py                 # print the words
    python3 tools/our_language.py --emit words    # the page's table block

Plan: spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md, Part 1.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = Path(__file__).resolve().parent / 'our_language.json'


def load(registry=REGISTRY):
    """-> [(word, meaning), ...] in the registry's own order.

    Fails loudly on a malformed entry rather than rendering a hole: a word
    with no meaning on the page is worse than no page."""
    data = json.loads(Path(registry).read_text(encoding='utf-8'))
    words = []
    seen = set()
    for i, entry in enumerate(data.get('words', [])):
        word = str(entry.get('word', '')).strip()
        meaning = str(entry.get('meaning', '')).strip()
        if not word or not meaning:
            sys.exit(f'our_language: entry {i} needs both a word and a meaning')
        if word.lower() in seen:
            sys.exit(f'our_language: {word!r} is listed twice')
        if '|' in word or '|' in meaning or '\n' in meaning:
            sys.exit(f'our_language: {word!r} would break the table '
                     f'(a pipe or a line break)')
        seen.add(word.lower())
        words.append((word, meaning))
    if not words:
        sys.exit('our_language: the registry lists no words')
    return words


def emit_words(registry=REGISTRY):
    """The markdown table the page's `words` block holds."""
    lines = ['| Word | What it means |', '|---|---|']
    lines += [f'| **{w}** | {m} |' for w, m in load(registry)]
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--emit', metavar='NAME',
                    help="print a generated block for doc_sync ('words')")
    args = ap.parse_args(argv)
    if args.emit:
        if args.emit != 'words':
            sys.exit(f'our_language: no block named {args.emit!r}')
        print(emit_words())
        return 0
    for word, meaning in load():
        print(f'{word}: {meaning}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
