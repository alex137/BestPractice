#!/usr/bin/env python3
"""check_install_declares_its_scope.py -- the mechanical check for
local/practices/install-declares-its-scope.md.

# practice: install-declares-its-scope

Scope: tree. INSTALL.md and SETUP.md each declare that an install does the
essentials and stops, name what is NEVER deferred, and mention
project-voice.md or project-visual-identity.md only beside a deferral
marker.

Assertion 3 is a POSITIVE requirement on purpose. The obvious form -- grep
for "walk them through" -- fires on SETUP.md's own correct text, which says
*do not walk them through the sections*. A check that cannot tell an
instruction from its negation is worse than no check
(# practice: control-asserts-which-failure is the same idea one level down:
a signal that fires for the wrong reason proves nothing).

Contract, shared with every other per-source check script: no arguments;
ROOT derived from this file's own location; exit 0 and print nothing when
clean; exit 1 and print the finding plus the Rule when violated; exit 2
when the check cannot run at all -- reported as SKIPPED, never as a pass.
"""
import os
import pathlib
import sys

SOURCE_ROOT = pathlib.Path(__file__).resolve().parents[3]
ROOT = pathlib.Path(os.environ.get('PRECEDENT_CHECK_ROOT') or SOURCE_ROOT)
PRACTICE_FILE = (SOURCE_ROOT / 'local' / 'practices'
                 / 'install-declares-its-scope.md')

# The two documents an install, upgrade or migration is driven from.
INSTALL_DOCS = ('INSTALL.md', 'SETUP.md')

# 1. The scope declaration. Searched across the whole document rather than
#    in headings alone: SETUP.md's section is called "What an Install Does
#    Not Do", which declares the scope perfectly well and contains no
#    heading word this could match.
SCOPE_PHRASES = (
    'does the essentials', 'do the essentials', 'essentials and stop',
    'essentials only', 'essentials, and stop',
)

# 2. The counterpart, without which "essentials only" is an excuse rather
#    than a scope. Any one of these phrasings satisfies it.
COUNTERPART = (
    'never deferred', 'not deferred', 'never be skipped', 'never skipped',
    'must not be skipped', 'not be deferred', 'is never deferred',
)

# 3. The optional files, and the markers that make a mention a deferral
#    rather than an instruction.
#
#    Scoped to paragraphs naming BOTH, which is the shape every instruction
#    about them takes -- "instantiate project-voice.md and
#    project-visual-identity.md", "both ship near-empty". Scanning every
#    paragraph naming EITHER was tried first (when this still read
#    'VOICE.md') and flagged three passages that are not install
#    instructions at all: a S0 layout table about the templates, an
#    update-path worked example, and the export gate's rule about where a
#    generic writing rule belongs. A check that fires on correct text gets
#    switched off, which is worse than not having it.
#
#    'project-voice.md' and 'project-visual-identity.md' (not their full
#    'local/practices/' paths) on purpose: a substring match, so it still
#    catches a mention that gives only the filename. STYLEGUIDE.md joined
#    project-voice.md as a repo-local practice on 2026-09-22
#    (project-visual-identity.md), so both names here now point at
#    local/practices/ files rather than one root document and one
#    practice.
OPTIONAL_FILES = ('project-voice.md', 'project-visual-identity.md')
DEFERRAL_MARKERS = (
    'optional', 'out of scope', 'skeleton', 'do not', "don't", 'never',
    'stay that way', 'stays that way', 'not part of', 'left for later',
    'later conversation', 'any time', 'local-only', 'local to',
)


class NotApplicable(Exception):
    """The check could not run. Exit 2, never a silent pass."""


def rule_text():
    if not PRACTICE_FILE.is_file():
        return f'(no practice file at {PRACTICE_FILE})'
    out, inrule = [], False
    for line in PRACTICE_FILE.read_text(encoding='utf-8').splitlines():
        if line.startswith('## Rule'):
            inrule = True
            continue
        if inrule and line.startswith('## '):
            break
        if inrule:
            out.append(line)
    return '\n'.join(out).strip() or '(no Rule recorded)'


def paragraphs(text):
    """Blank-line separated blocks, with their 1-based starting line."""
    out, buf, start = [], [], 1
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip():
            if not buf:
                start = n
            buf.append(line)
        elif buf:
            out.append((start, '\n'.join(buf)))
            buf = []
    if buf:
        out.append((start, '\n'.join(buf)))
    return out


def find_violations():
    present = [d for d in INSTALL_DOCS if (ROOT / d).is_file()]
    if not present:
        raise NotApplicable(
            'neither ' + ' nor '.join(INSTALL_DOCS) + ' exists here -- this '
            'is a consuming repo, where the install path lives upstream')

    findings = []
    for name in present:
        text = (ROOT / name).read_text(encoding='utf-8')
        low = text.lower()

        if not any(s in low for s in SCOPE_PHRASES):
            findings.append(
                f'{name}: nothing declares the essentials-only scope. An '
                f'install that never says what it defers defers nothing, and '
                f'grows a question per release.')

        if not any(c in low for c in COUNTERPART):
            findings.append(
                f'{name}: the scope is declared but its counterpart is not -- '
                f'nothing here says what is NEVER deferred. Without that half '
                f'"essentials only" excuses skipping the blocklist, the commit '
                f'identity or the audit.')

        for line_no, para in paragraphs(text):
            if not all(f in para for f in OPTIONAL_FILES):
                continue
            if not any(m in para.lower() for m in DEFERRAL_MARKERS):
                first = para.splitlines()[0].strip()
                findings.append(
                    f'{name}:{line_no}: names project-voice.md and '
                    f'project-visual-identity.md together with no deferral '
                    f'marker -- reads as an instruction to fill them in '
                    f'during the install. Say they are optional, out of '
                    f'scope, or ship as skeletons. '
                    f'Paragraph opens: {first[:70]!r}')
    return findings


if __name__ == '__main__':
    try:
        results = find_violations()
    except NotApplicable as e:
        print(f'SKIPPED: {PRACTICE_FILE.stem}: {e}')
        sys.exit(2)
    if results:
        print(f'VIOLATION: {PRACTICE_FILE.stem}')
        for r in results:
            print(f'  {r}')
        print('\nthe rule:')
        print('  ' + rule_text().replace('\n', '\n  '))
        sys.exit(1)
    sys.exit(0)
