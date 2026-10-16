#!/usr/bin/env python3
"""finish_html.py -- the last step before any engine tool writes an HTML page.

    from finish_html import finish
    out.write_text(finish(page), encoding='utf-8')

Every HTML output gets finished typography -- curly quotes, real dashes --
in the text a reader sees (practice: curly-quotes; Morgan, 2026-10-16:
"basically in any html file or html output"). typography.py is the one copy
of those rules and an engine file, so it sits beside this one in every
repository. finish() runs a page through its smarten_html(), which never
touches a tag, an attribute, a comment, a script or code.

The engine's own pages call it -- doc_html.py's rendered documents,
precedent_review_page.py, precedent_stale_branches.py's branch cleanup page
(published as an Artifact) and deck/build_deck.py -- so none of them carries
a copy of the rules.

WHY IT IS THIS SMALL NOW. For a day the practice lived in the writing
practice set, and typography.py reached tools/ only where that set was in
force -- for some people only on their own machine, untracked. finish()
then had to ask whether the file was there and whether this repository
tracked it, or a committed render finished on one machine read stale on
every other (BestPractice's spec/PREFORK_AUDIT.html, the first time it ran).
Moving the practice here, with typography.py made an engine file, made the
page read the same everywhere and took both questions away.

A tree without typography.py (an engine copied in part), or one too old to
have smarten_html(), gets the page back as built: a page is never lost to
its finish.
"""
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent


def finish(page):
    """-> `page` with typography.smarten_html() applied to its visible text."""
    if str(_HERE) not in sys.path:
        sys.path.insert(0, str(_HERE))
    try:
        from typography import smarten_html
    except ImportError:
        return page
    return smarten_html(page)
