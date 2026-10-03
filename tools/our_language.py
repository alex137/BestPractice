#!/usr/bin/env python3
"""Our language: the short list of words a person needs to follow a conversation about Precedent, read from tools/our_language.json and rendered into documentation/OUR_LANGUAGE.md's generated table (spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md)

our_language -- the short list of words a person needs to follow a
conversation about Precedent, read from tools/our_language.json.

The registry is the one source. documentation/OUR_LANGUAGE.md carries a
generated block rendered from it, kept honest by tools/doc_sync.py
(practices: registry-source-of-truth, computed-numbers-in-scripts):

    python3 tools/our_language.py                 # print the words
    python3 tools/our_language.py --emit words    # the page's table block
    python3 tools/our_language.py --retired       # live uses of retired words

Plan: spec/FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md, Part 1.
"""

import argparse
import json
import re
import subprocess
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


def load_retired(registry=REGISTRY):
    """-> [(word, replacement, [compiled pattern, ...]), ...] from the
    registry's `retired` list. A malformed entry fails loudly, same as
    load(): a retired word the check silently cannot see is how the last
    one survived."""
    data = json.loads(Path(registry).read_text(encoding='utf-8'))
    out = []
    for i, entry in enumerate(data.get('retired', [])):
        word = str(entry.get('word', '')).strip()
        repl = str(entry.get('replacement', '')).strip()
        pats = entry.get('patterns') or []
        if not word or not repl or not pats:
            sys.exit(f'our_language: retired entry {i} needs a word, a '
                     f'replacement and at least one pattern')
        out.append((word, repl, [re.compile(p, re.I) for p in pats]))
    return out


# What counts as history, which keeps a retired word on purpose (practice:
# rename-updates-links: "a use that quotes or records the past keeps the old
# name"). Everything else is live text and follows the new word.
HISTORY_DIRS = ('todo/', 'decisions/', 'gotchas/', 'record/', 'evals/')
# The finished states of tools/doc_lifecycle.py's LEGAL table (a brief
# closed, a proposal accepted, executed or abandoned, a reference
# superseded), plus a practice's own retired and deduplicated. A `record` of
# any status is history by definition: "a true observation of a date".
HISTORY_STATUSES = {'closed', 'executed', 'accepted', 'abandoned', 'superseded',
                    'retired', 'deduplicated'}
# A line talking about the retirement itself names the old word by necessity.
ABOUT_RETIREMENT = re.compile(
    r'retir|formerly|renamed|\bold (?:name|word|spelling)|pre-rename|'
    r'used to be|was called|at the time', re.I)
# A quotation keeps its words: text in double quotes that reads as a
# sentence (it has a space), or in curly quotes, is somebody's words.
# An italic quotation opens with *" before a word and closes with "* after
# one -- never the ["**"] of a glob list.
QUOTE_OPEN = re.compile(r'(?<!\*)\*"(?=[\w\u2018\u2019\'(.])')
QUOTE_CLOSE = re.compile(r'(?<=[^\s"])"\*(?!\*)')
QUOTED = re.compile(r'"[^"\n]*\s[^"\n]*"|\u201c[^\u201d\n]*\u201d')


def _front(text):
    if not text.startswith('---\n'):
        return {}
    end = text.find('\n---\n', 4)
    fm = {}
    for line in text[4:end if end > 0 else 0].split('\n'):
        m = re.match(r'^([a-z_]+):\s*(.*)$', line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').lower()
    return fm


def is_history(rel, text):
    """True when REL, whose content is TEXT, records the past."""
    if rel.startswith(HISTORY_DIRS):
        return True
    fm = _front(text)
    if fm.get('kind') == 'record':
        return True
    # A practice's own `status` (active, retired...) is not a document
    # lifecycle, except that a retired or deduplicated practice is history.
    return fm.get('status') in HISTORY_STATUSES


def _history_row(line):
    """A Markdown table row one of whose cells is a finished status --
    MAP.md's withdrawn-practice rows, a registry of superseded documents --
    records the past, and its text (a withdrawn practice's own Story, often)
    keeps its words. Found 2026-09-29: an individual set's regenerated MAP.md
    quoted a deduplicated practice's Story ("the three team sets"), and the
    retired-word check refused an update over it."""
    if not line.lstrip().startswith('|'):
        return False
    cells = {c.strip().strip('`*').lower() for c in line.strip().strip('|').split('|')}
    return bool(cells & HISTORY_STATUSES)


def retired_uses_in(rel, text, retired):
    """-> [(line_number, word, replacement, line)] for each live use."""
    if is_history(rel, text):
        return []
    out = []
    section = None
    in_approved = False
    in_quote = False
    fm_end = text.find('\n---\n', 4)
    fm_end = text[:fm_end].count('\n') + 1 if text.startswith('---\n') and fm_end > 0 else 0
    for n, line in enumerate(text.split('\n'), 1):
        # A quotation in this repo's own style runs from *" to "*, often
        # over several lines of a paragraph; the parts of a line inside one
        # are somebody's words and keep them. A blank line ends a paragraph,
        # and with it any quote left open by a typo.
        if not line.strip():
            in_quote = False
        if _history_row(line):
            continue
        in_front = text.startswith('---\n') and n <= fm_end
        live_parts, i = [], 0
        while not in_front and i <= len(line):
            if in_quote:
                m = QUOTE_CLOSE.search(line, i)
                if not m:
                    break
                in_quote, i = False, m.end()
            else:
                m = QUOTE_OPEN.search(line, i)
                live_parts.append(line[i:] if not m else line[i:m.start()])
                if not m:
                    break
                in_quote, i = True, m.end()
        if in_front:
            live_parts = [line]
        m = re.match(r'^##\s+(\w+)', line)
        if m:
            section = m.group(1)
        if section == 'Story':
            continue
        # approved_by is a quotation of the person who approved, often
        # folded over several indented lines.
        if line.startswith('approved_by:'):
            in_approved = True
        elif in_approved and not line.startswith((' ', '\t')):
            in_approved = False
        if in_approved:
            continue
        if ABOUT_RETIREMENT.search(line):
            continue
        live = ' '.join(live_parts)
        # Frontmatter values are quoted strings but are live text (a title,
        # an index clause); only prose quotations are somebody's words.
        if not in_front:
            live = QUOTED.sub('', live)
        for word, repl, pats in retired:
            if any(p.search(live) for p in pats):
                out.append((n, word, repl, line.strip()))
                break
    return out


def retired_uses(root=ROOT, paths=None, registry=REGISTRY):
    """-> [(rel, line_number, word, replacement, line)] over the Markdown
    files under ROOT git tracks or would add (or just PATHS, when given)."""
    retired = load_retired(registry)
    if not retired:
        return []
    root = Path(root)
    if paths is None:
        # Untracked-but-not-ignored files too: a document just written is
        # exactly when a retired word is cheapest to catch, and the planted
        # case in verify_harness.py found the tracked-only read missed it.
        r = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached',
                            '--others', '--exclude-standard', '*.md'],
                           capture_output=True, text=True)
        paths = r.stdout.split()
    out = []
    for rel in paths:
        if not rel.endswith('.md'):
            continue
        try:
            text = (root / rel).read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        out += [(rel, *hit) for hit in retired_uses_in(rel, text, retired)]
    return out


def emit_words(registry=REGISTRY):
    """The markdown table the page's `words` block holds."""
    lines = ['| Word | What it means |', '|---|---|']
    lines += [f'| **{w}** | {m} |' for w, m in load(registry)]
    return '\n'.join(lines)


def emit_retired(registry=REGISTRY):
    """The markdown table the page's `retired` block holds."""
    data = json.loads(Path(registry).read_text(encoding='utf-8'))
    lines = ['| Retired word | Say instead | Since |', '|---|---|---|']
    for e in data.get('retired', []):
        lines.append(f"| {e['word']} | **{e['replacement']}** | {e.get('retired', '')} |")
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--retired', action='store_true',
                    help='list live uses of retired words, with the replacement')
    ap.add_argument('--emit', metavar='NAME',
                    help="print a generated block for doc_sync ('words' or 'retired')")
    args = ap.parse_args(argv)
    if args.retired:
        hits = retired_uses()
        for rel, n, word, repl, line in hits:
            print(f'{rel}:{n}: {word} -> {repl}: {line[:140]}')
        print(f'{len(hits)} live use(s) of a retired word')
        return 1 if hits else 0
    if args.emit:
        blocks = {'words': emit_words, 'retired': emit_retired}
        if args.emit not in blocks:
            sys.exit(f'our_language: no block named {args.emit!r}')
        print(blocks[args.emit]())
        return 0
    for word, meaning in load():
        print(f'{word}: {meaning}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
