#!/usr/bin/env python3
"""summary_text.py — the one way a generator turns prose into a summary field.

A summary, an index row, a log line or any other length-capped field is a
COPY of prose that lives somewhere else, and the full text is one link away.
So a link inside the copy buys nothing, and shortening one breaks it:
`[:120]` can land inside `(../meeting-notes/some-long-name.md)` and leave an
open parenthesis in the row. That row renders as a broken link, and a link
checker whose pattern is allowed to cross lines pairs the stray `(` with the
next row's `)` and reports a broken link that is really two rows glued
together. Found 2026-09-25 in a consumer repo's generated todo/TODO.md; the
same cut had already left three unclosed links in this repo's own
todo/TODO.md and todo/CLOSED.md, where nothing had noticed them.

The fix is to drop the links BEFORE shortening, everywhere, through this one
module rather than a regex copied into each generator:

  unlink(text)             [text](url) -> text, ![alt](src) -> alt,
                           [text][ref] and [text][] -> text, <https://x> -> https://x,
                           and a `[ref]: url` definition line is dropped.
  one_line(text, limit, ellipsis)
                           unlink, collapse whitespace, then cut at `limit`
                           characters -- backing off to the start of a bare
                           URL rather than cutting through it -- and append
                           `ellipsis` only when something was actually cut.

The row that points AT the item keeps its own link; only links inside the
copied prose go.

Run as a script, it checks itself (`python3 tools/summary_text.py`).
"""
import re
import sys

# The URL part never contains whitespace -- CommonMark only allows spaces in
# a destination written as <...>, handled separately below -- so `[^)\s]`
# rather than `[^)]`. The looser class is exactly the one that let a
# consumer's link checker pair a `(` on one line with a `)` on the next.
_INLINE_LINK_RE = re.compile(
    r'!?\[([^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*)\]'   # text, one level of [] inside
    r'\((?:<[^<>\n]*>|[^)\s]*)(?:\s+"[^"\n]*")?\)')  # (dest "optional title")
_REF_LINK_RE = re.compile(r'!?\[([^\[\]\n]+)\]\[[^\[\]\n]*\]')
_AUTOLINK_RE = re.compile(r'<((?:https?|mailto|ftp):[^<>\s]+)>')
_REF_DEF_RE = re.compile(r'^[ ]{0,3}\[[^\]\n]+\]:[ \t]*\S+.*$', re.MULTILINE)
_BARE_URL_RE = re.compile(r'(?:https?|ftp)://\S*$')


def unlink(text):
    """`text` with every markdown link replaced by what it displays."""
    if not text:
        return text
    text = _REF_DEF_RE.sub('', text)
    # Applied until nothing changes: `[![alt](img)](url)` unwraps from the
    # inside out, one layer per pass.
    while True:
        new = _INLINE_LINK_RE.sub(r'\1', text)
        new = _REF_LINK_RE.sub(r'\1', new)
        if new == text:
            break
        text = new
    return _AUTOLINK_RE.sub(r'\1', text)


def one_line(text, limit=None, ellipsis=''):
    """`text` as one unlinked line, at most `limit` characters before
    `ellipsis`. A cut that would land inside a bare URL drops the partial URL
    instead: half a URL is a broken link in any renderer that autolinks."""
    text = re.sub(r'\s+', ' ', unlink(text or '')).strip()
    if limit is None or len(text) <= limit:
        return text
    cut = text[:limit]
    if not text[limit].isspace():
        m = _BARE_URL_RE.search(cut)
        if m:
            cut = cut[:m.start()]
    return cut.rstrip() + ellipsis


def _self_check():
    cases = [
        ('see [the plan](spec/PLAN.md) first', 'see the plan first'),
        ('[`x.py`](../tools/x.py)\'s job', '`x.py`\'s job'),
        ('![logo](a.png) and [t](u "title")', 'logo and t'),
        ('[a [nested] b](u)', 'a [nested] b'),
        ('[![img](i.png)](u)', 'img'),
        ('ref [text][r] and [short][]', 'ref text and short'),
        ('go to <https://example.com/x>', 'go to https://example.com/x'),
        ('body\n[r]: https://example.com\n', 'body\n\n'),
        ('a (b) [c] d', 'a (b) [c] d'),
    ]
    bad = [(i, unlink(i), w) for i, w in cases if unlink(i) != w]
    long = 'Confirm where it belongs in [p/AI.md](../p/AI.md) and more text ' * 3
    for n in range(1, len(long)):
        s = one_line(long, n, '…')
        if '](' in s or s.count('(') != s.count(')'):
            bad.append((long, s, f'balanced at {n}'))
    s = one_line('see https://example.com/a/long/path now', 20, '…')
    if s != 'see…':
        bad.append(('bare url', s, 'see…'))
    for inp, got, want in bad:
        print(f'summary_text FAIL: {inp!r} -> {got!r}, want {want!r}')
    if not bad:
        print(f'summary_text: {len(cases)} unlink cases and every cut of a '
              f'linked line pass.')
    return 1 if bad else 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(_self_check())
