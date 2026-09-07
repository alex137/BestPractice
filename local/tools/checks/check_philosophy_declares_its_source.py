#!/usr/bin/env python3
"""check_philosophy_declares_its_source.py -- the mechanical check for
local/practices/philosophy-declares-its-source.md.

# practice: philosophy-declares-its-source

Scope: tree. Every markdown file under philosophy/ opens with an HTML
comment naming where its text originally came from -- the document and
version it was taken from, or that it was written here.

The philosophy/ tree is the ONLY copy of these essays. They were written
in a separate notebook repository which was retired on 2026-09-07, so
there is no upstream, nothing to sync, and nothing to diff against.

The line is therefore a HISTORICAL record, and this check cannot verify a
version number against anything -- deliberately, and permanently. What it
enforces is that the question "where did this text come from?" has an
answer on the page. That is what stops an essay argued out over forty
revisions from reading, later, as though someone typed it once.

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
                 / 'philosophy-declares-its-source.md')

PHILOSOPHY_DIR = 'philosophy'
# Either half satisfies the rule: a copied document names its source, a
# document written here says so.
MARKERS = ('source:', 'written here')


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


def find_violations():
    base = ROOT / PHILOSOPHY_DIR
    if not base.is_dir():
        raise NotApplicable(
            f'{PHILOSOPHY_DIR}/ does not exist in this repository')
    files = sorted(base.rglob('*.md'))
    if not files:
        raise NotApplicable(
            f'{PHILOSOPHY_DIR}/ holds no markdown files to check')

    findings = []
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        # Read only what is needed: the first line decides.
        first = ''
        for line in f.read_text(encoding='utf-8').splitlines():
            first = line.strip()
            break
        if not first.startswith('<!--'):
            findings.append(
                f'{rel}: line 1 is not an HTML-comment provenance line. A '
                f'copy that does not say what it is a copy of diverges '
                f'silently.')
        elif not any(m in first.lower() for m in MARKERS):
            findings.append(
                f'{rel}: line 1 is a comment but names no origin -- it must '
                f'carry `source: <upstream file>, version <N>` or say the '
                f'document was written here.')
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
