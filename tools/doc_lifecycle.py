#!/usr/bin/env python3
"""doc_lifecycle.py -- the document status header, checked.

Implements the mechanical check spec/DOCUMENT_LIFECYCLE.md's "The mechanical
check" section specifies. Every document under spec/ (and record/, once that
exists) carries YAML frontmatter saying what KIND of document it is and what
STATE it is in, so a reader knows in three seconds whether they are holding a
plan, a procedure, or the record of something that already happened.

WHY A KIND AND NOT JUST A DATE. The kind decides what "outdated" can even
mean for a file. A `reference` states how the system works and can become
wrong. A `record` is a true observation of a date and stays true forever --
spec/LOADER.md's "52 practices" is not stale, it is the condition a
measurement ran under. Marking both with the same freshness idea is what
makes a reader distrust the wrong one.

practice: checkable-gets-checked -- this convention is straightforwardly
checkable, so it is not left advisory.

BLOCKING SINCE PHASE 2 (2026-09-07), when the backfill stamped all 24 spec
documents. An unstamped file is now a failure. `--warn-only` restores the
phase-1 behaviour -- report unstamped files, exit 0 -- which is what a repo
part-way through its own backfill wants, and is the mode this check was
introduced in so that a standard could be registered and read before any
tree satisfied it. Failing 22 files on the commit that introduces a
convention makes the convention something to switch off rather than satisfy.
"""
import datetime
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# kind -> the statuses that kind may legally hold. From the spec's matrix;
# a `record` cycles live/closed rather than moving one way, which is why no
# check here may assume a document only ever advances.
LEGAL = {
    'reference': {'current', 'superseded'},
    'procedure': {'current', 'superseded'},
    'brief':     {'open', 'closed', 'blocked'},
    'record':    {'live', 'closed'},
    'proposal':  {'drafted', 'accepted', 'executed', 'abandoned'},
}
REQUIRED = ('title', 'kind', 'status', 'opened', 'supersedes', 'audience',
            'summary')
AUDIENCES = {'session', 'contributor', 'adopter'}
SCAN_DIRS = ('spec', 'record')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def parse_frontmatter(text):
    """-> (dict, body) or (None, text) when there is no frontmatter block.

    Deliberately a small reader rather than a YAML dependency: the schema is
    flat scalars plus one list, the same shape practices/ already uses, and
    tools/split_practices.py reads those without YAML either.
    """
    if not text.startswith('---\n'):
        return None, text
    end = text.find('\n---\n', 3)
    if end == -1:
        return None, text
    fm, body = {}, text[end + 5:]
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        v = v.strip()
        if v.startswith('[') and v.endswith(']'):
            inner = v[1:-1].strip()
            v = [x.strip().strip('"\'') for x in inner.split(',')] if inner else []
        else:
            v = v.strip('"\'')
            if v == 'null':
                v = None
        fm[k.strip()] = v
    return fm, body


FENCE_RE = re.compile(r'^(```|~~~)', re.M)
CODESPAN_RE = re.compile(r'`[^`\n]*`')
LAST_UPDATED_RE = re.compile(r'<!--[^>]*Last updated:', re.S)


def has_last_updated_comment(text):
    """-> True only for a REAL `<!-- Last updated: ... -->` comment.

    A plain `'Last updated:' in text` fires on any document that merely
    QUOTES the convention -- which spec/DOCUMENT_LIFECYCLE.md, the document
    specifying this very check, does five times. A check that fails the one
    file explaining it is worse than no check: the first reader concludes
    the checker is broken and stops trusting the rest of its output. So
    fenced blocks and inline code spans are stripped before matching, and
    the match requires the comment delimiter, not the phrase.
    """
    out, fenced = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            out.append(CODESPAN_RE.sub('', line))
    return bool(LAST_UPDATED_RE.search('\n'.join(out)))


def first_heading(body):
    for line in body.splitlines():
        if line.startswith('# '):
            return line[2:].strip()
    return None


def check_file(path, rel, root=None):
    """-> [str] findings for one document.

    `root` is the repository the paths are relative to. It is a parameter,
    not the module-level ROOT, because this module is vendored: in the
    INSTALL.md layout it sits at <repo>/process/upstream/tools/, so its own
    parents[1] is the vendor directory and not the consuming repo at all.
    """
    root = pathlib.Path(root) if root else ROOT
    out = []
    text = path.read_text(encoding='utf-8', errors='replace')
    fm, body = parse_frontmatter(text)
    if fm is None:
        return [f'{rel}: no frontmatter block -- see spec/DOCUMENT_LIFECYCLE.md']

    for field in REQUIRED:
        if field not in fm:
            out.append(f'{rel}: missing required field `{field}`')
    kind, status = fm.get('kind'), fm.get('status')
    if kind not in LEGAL:
        out.append(f'{rel}: kind {kind!r} is not one of '
                   f'{", ".join(sorted(LEGAL))}')
    elif status not in LEGAL[kind]:
        out.append(f'{rel}: status {status!r} is not legal for kind '
                   f'{kind!r} -- allowed: {", ".join(sorted(LEGAL[kind]))}')

    if fm.get('audience') not in AUDIENCES:
        out.append(f'{rel}: audience {fm.get("audience")!r} is not one of '
                   f'{", ".join(sorted(AUDIENCES))}')
    opened = fm.get('opened')
    if opened and not DATE_RE.match(str(opened)):
        out.append(f'{rel}: opened {opened!r} is not YYYY-MM-DD')

    # closed exactly when status is closed; superseded_by exactly when
    # superseded, and it must resolve.
    if status == 'closed' and not fm.get('closed'):
        out.append(f'{rel}: status is `closed` but no `closed:` date')
    if status != 'closed' and fm.get('closed'):
        out.append(f'{rel}: has a `closed:` date but status is {status!r}')
    sb = fm.get('superseded_by')
    if status == 'superseded' and not sb:
        out.append(f'{rel}: status is `superseded` but no `superseded_by:`')
    if status != 'superseded' and sb:
        out.append(f'{rel}: has `superseded_by:` but status is {status!r}')
    if sb and not (root / sb).exists():
        out.append(f'{rel}: superseded_by {sb!r} does not exist')

    head = first_heading(body)
    if head is not None and fm.get('title') and head != fm['title']:
        out.append(f'{rel}: title {fm["title"]!r} != first heading {head!r}')

    summary = fm.get('summary') or ''
    if summary and not summary.rstrip().endswith('.'):
        out.append(f'{rel}: summary does not end in a period')

    # A `Last updated:` comment is a second, hand-maintained freshness claim
    # competing with `status`. Allowed only where the date IS the content.
    if kind not in ('record', 'brief') and has_last_updated_comment(text):
        out.append(f'{rel}: carries a `Last updated:` comment, which '
                   f'`status` replaces for kind {kind!r}')
    return out


def scan(root=None):
    root = pathlib.Path(root) if root else ROOT
    findings, unstamped, stamped = [], [], 0
    for d in SCAN_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for f in sorted(base.rglob('*.md')):
            rel = str(f.relative_to(root))
            text = f.read_text(encoding='utf-8', errors='replace')
            if parse_frontmatter(text)[0] is None:
                unstamped.append(rel)
                continue
            stamped += 1
            findings.extend(check_file(f, rel, root))
    return findings, unstamped, stamped


def main(argv):
    if '--help' in argv or '-h' in argv:
        print(__doc__)
        return 0
    # `--blocking` is still accepted so that anything wired against the
    # phase-1 spelling keeps working; it is now the default and a no-op.
    blocking = '--warn-only' not in argv
    findings, unstamped, stamped = scan()
    for f in findings:
        print(f'  {f}')
    if unstamped:
        print(f'  {len(unstamped)} document(s) not yet stamped: '
              f'{", ".join(unstamped[:6])}'
              + (' ...' if len(unstamped) > 6 else ''))
    verdict = 'FAIL' if (findings or (blocking and unstamped)) else 'OK'
    print(f'doc_lifecycle {verdict}: {stamped} stamped, {len(unstamped)} '
          f'unstamped, {len(findings)} finding(s)'
          + ('' if blocking else ' (--warn-only: unstamped files reported, '
                                'not failed)'))
    return 1 if (findings or (blocking and unstamped)) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
