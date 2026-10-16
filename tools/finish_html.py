#!/usr/bin/env python3
"""finish_html.py -- the last step before any engine tool writes an HTML page.

    from finish_html import finish
    out.write_text(finish(page), encoding='utf-8')

Finished typography, curly quotes and real dashes, belongs to a practice set
and not to this engine: the writing set's curly-quotes practice says every
HTML output gets it (Morgan, 2026-10-16: "basically in any html file or html
output"), and its tools/typography.py is the one copy of the rules. That
file reaches tools/ in every repository where the set is in force, tracked
or not. So finish() applies its smarten_html() when typography.py is beside
this file, and hands the page back unchanged where it is not: a repository
that never took the rule gets no rule.

The engine's own pages call it -- doc_html.py's rendered documents,
precedent_review_page.py, precedent_stale_branches.py's branch cleanup page
(published as an Artifact) and deck/build_deck.py -- so each of them reads
the same in every repository the rule binds, without a copy of the rules in
any of them. A typography.py too old to have smarten_html() is treated as
absent, and so is one that raises: a page is never lost to its finish.

A PAGE THAT IS COMMITTED is finished only where the repository itself
tracks typography.py -- it declares the writing set. A set a person brings
puts an untracked copy beside the engine on their machine alone, so a
committed render finished there would read stale to every other checkout
and to GitHub's test, which re-render it without one, and would flip with
whoever rendered it last (2026-10-16: BestPractice's own
spec/PREFORK_AUDIT.html, the first time this ran). The same line
build_views.py draws for a set a person brings: never into a tracked file.
A page nobody commits -- a page published as an Artifact, the review page,
a deck sent to someone -- is finished wherever typography.py is present.
"""
import pathlib
import subprocess
import sys

_HERE = pathlib.Path(__file__).resolve().parent


def _tracked_here():
    """True when this repository's git index holds tools/typography.py."""
    try:
        r = subprocess.run(['git', '-C', str(_HERE), 'ls-files', '--error-unmatch',
                            'typography.py'], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def finish(page, committed=False):
    """-> `page` with typography.smarten_html() applied, where typography.py
    sits beside this file (and, for a `committed` page, where this
    repository tracks it); else `page` as it came."""
    if not (_HERE / 'typography.py').is_file():
        return page
    if committed and not _tracked_here():
        return page
    if str(_HERE) not in sys.path:
        sys.path.insert(0, str(_HERE))
    try:
        from typography import smarten_html
        return smarten_html(page)
    except Exception:                                        # noqa: BLE001
        return page
