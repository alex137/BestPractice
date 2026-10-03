#!/usr/bin/env python3
"""Whether a line is inside a generated block, in both marker styles, closing marker required -- the one answer every scan that skips generated text uses

generated_blocks.py -- the one answer to "is this line inside a generated
block?", for every tool that has to skip generated text.

The engine writes generated text into hand-written documents in two marker
styles, and a reader has to know both:

    <!--gen:NAME-->                            doc_sync.py, one per PAIRS entry
    ...
    <!--/gen:NAME-->

    <!-- BEGIN GENERATED: precedent-loader -->   build_views.py, the loader block
    ...
    <!-- END GENERATED -->

Until 2026-09-29 each tool that skipped generated text matched the markers
itself, and each knew one style: doc_lint.py and doc_sync.py only `gen:`,
practice_audit.py, precedent_check.py and precedent_vendor_engine.py only
`BEGIN GENERATED`. A shared set's no-stale-counts check had the same blind
spot, and it surfaced when that set gained its first resident practice: the
loader block's header ("1 of 20 practices") read as a stale hand-written
count and a Promote was refused over generated text.

What counts as a block, and why:

  * A marker counts only ALONE ON ITS LINE (surrounding whitespace allowed).
    Prose that quotes a marker in backticks, mid-sentence, is not a marker.
  * A block needs its CLOSING marker. An opener with no closer below it
    hides nothing: a marker quoted in a document would otherwise hide every
    line after it, which is how the older copies here behaved.
  * `gen:` blocks close on the SAME name. The loader style closes on
    `<!-- END GENERATED -->`, with or without a name after it, the way
    build_views.py writes it.
  * Both marker lines belong to the block.

Standard library only, so a practice source's own checks can import it from
the vendored engine beside them the way they import precedent_resolve.
"""
import re

LOADER_BEGIN = '<!-- BEGIN GENERATED: precedent-loader -->'
LOADER_END = '<!-- END GENERATED -->'

_GEN_OPEN = re.compile(r'<!--gen:([\w-]+)-->')
_GEN_CLOSE = re.compile(r'<!--/gen:([\w-]+)-->')
_BEGIN = re.compile(r'<!--\s*BEGIN GENERATED(?::\s*[\w.-]+)?\s*-->')
_END = re.compile(r'<!--\s*END GENERATED(?::\s*[\w.-]+)?\s*-->')


def _closer_for(line):
    """-> a predicate matching the line that closes a block this line opens,
    or None when the line opens nothing."""
    s = line.strip()
    m = _GEN_OPEN.fullmatch(s)
    if m:
        name = m.group(1)

        def closes(t):
            c = _GEN_CLOSE.fullmatch(t.strip())
            return bool(c) and c.group(1) == name
        return closes
    if _BEGIN.fullmatch(s):
        return lambda t: bool(_END.fullmatch(t.strip()))
    return None


def spans(lines):
    """-> [(first, last)] zero-based inclusive line indexes of every closed
    generated block in `lines` (a list of strings, or a text to split)."""
    if isinstance(lines, str):
        lines = lines.splitlines()
    out, i, n = [], 0, len(lines)
    while i < n:
        closes = _closer_for(lines[i])
        if closes:
            for j in range(i + 1, n):
                if closes(lines[j]):
                    out.append((i, j))
                    i = j
                    break
        i += 1
    return out


def mask(lines):
    """-> one bool per line: True where the line is inside a generated
    block, its two marker lines included."""
    if isinstance(lines, str):
        lines = lines.splitlines()
    inside = [False] * len(lines)
    for a, b in spans(lines):
        for k in range(a, b + 1):
            inside[k] = True
    return inside


def blank(text):
    """-> `text` with every generated line emptied and every other line,
    and every line number, kept -- for a scan that reports line numbers."""
    lines = text.split('\n')
    return '\n'.join('' if hide else line
                     for line, hide in zip(lines, mask(lines)))
