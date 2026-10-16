#!/usr/bin/env python3
"""typography.py -- the one place plain Markdown typing becomes finished
typography, for every format built for an outside reader.

# practice: curly-quotes

Markdown is written with plain keys: straight quotes, a hyphen, and two
hyphens for a long dash. Nothing in a Markdown file has to change. Real
dashes and curly quotes typed into one are fine too, and pass through
untouched. The conversion happens when a builder makes something an
outside reader sees -- a Word document (create_word_doc.py), a web page,
whatever format comes next -- and every such builder calls smarten() here
rather than carrying a copy of its own (Morgan, 2026-10-13: "whenever we
format it for external use, such as creating a [Microsoft] Word document or on a
website, then the double dashes should always become an M dash").

The rules:
  "--" and "---"        always an em dash, spacing kept as typed
  1990-2000, 9-5,       a hyphen between two numbers that make a range is
  pages 10-20, 3:00-5:00  an en dash
  2026-10-13, 555-123-4567, PR-173, B-52
                        stay hyphens: a hyphen inside a run of three or more
                        number groups (a date, a phone number) or next to a
                        letter is never a range
  "word" / it's         curly quotes, opening after a space, an opening
                        bracket or a dash, closing anywhere else
A range in words ("Monday-Friday") keeps its hyphen: telling it from an
ordinary hyphenated word takes judgment a script cannot make, so a writer
who wants the en dash there types it.

Code is never changed: a code span (`--check`, `it's`) keeps every
character, and a builder sets a fenced code block as typed without calling
smarten() on it at all, because in code "--" and "-" mean something
exactly. A web link's address and a backslash-escaped character are never
changed either.
A caller that has already pulled links out of the text marks an address
with LINK_OPEN before it and LINK_MID after it (create_word_doc.py does).

    python3 tools/typography.py "a \\"quote\\" -- 1990-2000"   # prints the result
    python3 tools/typography.py --html < page.html                # an HTML file

An HTML page goes through smarten_html(), which changes the text a reader
sees and never a tag, an attribute, a comment, or code.
"""
import re
import sys

LINK_OPEN, LINK_MID = "\x01", "\x02"
EM, EN = "—", "–"
OPENS_AFTER = set(" \t\n([{<" + EM + EN + "-/“‘" + LINK_MID)

# A number: digits, optionally with one decimal, thousands or time part.
_NUM = r"\d+(?:[.,:]\d+)?"
# A hyphen between two numbers, neither of which is joined to a letter,
# another hyphen, or a further number group. The lookarounds are what keep
# 2026-10-13 and 555-123-4567 whole: every hyphen in them touches a
# neighbouring "-digit" group.
RANGE_RE = re.compile(
    r"(?<![\w.,:\-])(" + _NUM + r")-(" + _NUM + r")(?![\w\-]|[.,:]\d)")


def _ranges(segment):
    return RANGE_RE.sub(lambda m: m.group(1) + EN + m.group(2), segment)


def smarten(text, before=" "):
    """Curly quotes, em dashes for "--"/"---", en dashes for number ranges.
    An asterisk run is looked through, so '**"word"**' opens and closes
    properly. `before` is the character the reader sees just ahead of
    `text` -- smarten_html() passes the end of the previous run of text, so
    a quote right after an inline tag opens or closes as it reads."""
    out, prev, i, in_url = [], before, 0, False
    plain_start = 0          # where the current run of plain text began in `out`
    while i < len(text):
        ch = text[i]
        if ch == LINK_OPEN:
            in_url = True
        elif ch == LINK_MID:
            in_url = False
        if in_url or ch in (LINK_OPEN, LINK_MID):
            out.append(ch)
            prev = LINK_MID if ch == LINK_MID else prev
            i += 1
            continue
        if ch == "`":
            # A code span is code: "--check" and "it's" stay as typed.
            run = len(text) - i - len(text[i:].lstrip("`"))
            close = text.find("`" * run, i + run)
            while close != -1 and close + run < len(text) and text[close + run] == "`":
                close = text.find("`" * run, close + run + 1)
            if close != -1:
                out.append(text[i:close + run])
                prev = "`"
                i = close + run
                continue
        if ch == "\\" and i + 1 < len(text):
            out.append(text[i:i + 2])
            prev = text[i + 1]
            i += 2
            continue
        if text.startswith("--", i):
            run = len(text) - i - len(text[i:].lstrip("-"))
            # Two or three hyphens are a dash; four or more are something
            # else (a rule drawn in text) and stay as typed.
            out.append(EM if run <= 3 else "-" * run)
            prev = out[-1][-1]
            i += run
            continue
        if ch == '"':
            ch = "“" if prev in OPENS_AFTER else "”"
        elif ch == "'":
            ch = "‘" if prev in OPENS_AFTER else "’"
        out.append(ch)
        if ch != "*":
            prev = ch
        i += 1
    return _apply_ranges("".join(out))


# What the range step never touches: a marked link address, and a code span
# (a run of backticks, its text, the same run again).
PROTECTED_RE = re.compile(
    LINK_OPEN + "[^" + LINK_MID + "]*" + LINK_MID + r"|(`+)(?!`).*?(?<!`)\1(?!`)",
    re.S)


def _apply_ranges(text):
    """Number ranges, everywhere but inside a marked link address, a code
    span, or right after a backslash escape."""
    done, at = [], 0
    for m in list(PROTECTED_RE.finditer(text)) + [None]:
        part = text[at:m.start() if m else len(text)]
        # Keep an escaped hyphen ("1990\-2000") a hyphen: split it out.
        bits = re.split(r"(\\-)", part)
        done.append("".join(x if x == "\\-" else _ranges(x) for x in bits))
        if m is None:
            break
        done.append(m.group(0))
        at = m.end()
    return "".join(done)


# --- HTML -------------------------------------------------------------------
#
# Every HTML output gets the same finish as a Word file: a web page, a page
# published as a Claude Artifact, a generated site (Morgan, 2026-10-16:
# "it applies there and also it should apply when we make real web pages as
# well ... basically in any html file or html output"). smarten_html() runs
# smarten() over the text a reader sees and nothing else.

# Elements whose text is never changed: code, and what is not prose at all.
HTML_RAW = ("code", "pre", "kbd", "samp", "tt", "var", "script", "style",
            "textarea", "svg", "math")
# Tags that end a run of reading: a quote right after one opens. An inline
# tag (<a>, <b>, <em>, <span>) is looked through instead.
HTML_BREAKS = ("p", "br", "div", "li", "ul", "ol", "dl", "dt", "dd", "td",
               "th", "tr", "table", "thead", "tbody", "h1", "h2", "h3", "h4",
               "h5", "h6", "section", "article", "header", "footer", "nav",
               "main", "aside", "blockquote", "figure", "figcaption", "hr",
               "button", "label", "option", "title", "body", "head", "html")
_HTML_TOKEN_RE = re.compile(r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<![^>]*>|<\?.*?\?>|"
                            r"<(/?)([A-Za-z][\w:-]*)(?:\s[^>]*)?>", re.S)
# The straight-quote entities a page builder writes for " and '.
_QUOTE_ENTITY_RE = re.compile(r"&(?:quot|apos|#34|#39|#x22|#x27);", re.I)
_ENTITY_CHAR = {"quot": '"', "#34": '"', "#x22": '"',
                "apos": "'", "#39": "'", "#x27": "'"}


def _plain_quotes(text):
    return _QUOTE_ENTITY_RE.sub(
        lambda m: _ENTITY_CHAR[m.group(0)[1:-1].lower()], text)


def smarten_html(html):
    """`html` with smarten() applied to its visible text only.

    Never touched: a tag or any attribute in it (a link's address, a class
    name), a comment, a doctype, and everything inside an element of
    HTML_RAW -- code is set as typed, as in a Word file. An escaped straight
    quote (&quot;, &#39;) in text becomes a curly one; every other entity
    stays as written. Running it twice changes nothing more."""
    out, raw, prev, at = [], [], " ", 0
    for m in _HTML_TOKEN_RE.finditer(html):
        text = html[at:m.start()]
        if text:
            if raw:
                out.append(text)
            else:
                done = smarten(_plain_quotes(text), before=prev)
                out.append(done)
                prev = done[-1]
        out.append(m.group(0))
        closing, name = m.group(1), (m.group(2) or "").lower()
        if name in HTML_RAW and not m.group(0).endswith("/>"):
            if closing:
                if name in raw:
                    del raw[len(raw) - 1 - raw[::-1].index(name)]
            else:
                raw.append(name)
            prev = " " if name not in ("code", "kbd", "samp", "tt", "var") else "`"
        elif name in HTML_BREAKS:
            prev = " "
        at = m.end()
    tail = html[at:]
    out.append(tail if raw else smarten(_plain_quotes(tail), before=prev))
    return "".join(out)


if __name__ == "__main__":
    if sys.argv[1:2] in (["--help"], ["-h"]):
        print(__doc__)
        sys.exit(0)
    if sys.argv[1:2] == ["--html"]:
        print(smarten_html(sys.stdin.read()), end="")
        sys.exit(0)
    print(smarten(" ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()))
