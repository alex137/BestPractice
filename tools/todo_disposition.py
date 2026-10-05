#!/usr/bin/env python3
"""records "Drop it" on a todo item in both places a park lives, in one go

Writes an open item's disposition the way open-item-disposition and park-it
define it, so no session writes it by hand.

code-cites-practice: park-it

WHY THIS EXISTS. A park lives in two places in a per-item todo file: the
frontmatter `disposition:` field, which tools/build_todo_index.py and every
other reader actually acts on, and a `**Disposition:** parked (<date>, <who>)`
line in the body, which carries who said it and when. Until 2026-10-05
nothing wrote either: every park was typed by a session, the practice text
named only the body line, and one parked item ended up with the frontmatter
and no date or name anywhere. A session that followed the practice's words
literally would have left the frontmatter at `ask`, and the item it was told
to drop would have kept being raised. One writer for both copies, and a
check (open-item-disposition, in tools/precedent_check.py) as the backstop.

A PARK THAT CONFLICTS WITH A PRACTICE. When a practice says an item should
keep being raised and the person says "Drop it", the session parks it first
-- the person's word is carried out, never argued with before -- and then
raises the conflict once: should the practice change, or is this a one-off?
`--conflict SLUG` records that the question was asked, so no later session
asks it again. The tool cannot see the conflict itself; spotting it is the
session's reading.

Run:
  python3 tools/todo_disposition.py park SLUG --by NAME [--date YYYY-MM-DD]
                                         [--conflict PRACTICE] [--repo DIR]

SLUG is the item's file name with or without `todo/` and `.md`. NAME is who
said "Drop it" -- the person's own word in that session, never a name
guessed for them; write `who not recorded` when it is unknown. The date
defaults to today in the person's zone (practice: timestamps-carry-offset).
Exit 0 when the item ends up parked (including when it already was), 1 on
any refusal.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # practice: timestamps-carry-offset

FRONTMATTER_RE = re.compile(r'\A---\n(.*?)\n---\n', re.S)
DISPOSITION_FIELD_RE = re.compile(r'^(disposition:)([ \t]*)(.*?)[ \t]*$', re.M)
BODY_PARK_RE = re.compile(r'^[ \t]*\*\*Disposition:\*\*[ \t]*parked\b', re.M)
CONFLICT_RE = re.compile(r'^[ \t]*\*\*Park conflict raised:\*\*[ \t]*(.*)$', re.M)
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def item_path(repo, slug):
    """-> the todo file SLUG names under REPO, or None."""
    name = slug.strip()
    if name.startswith('todo/'):
        name = name[len('todo/'):]
    if name.endswith('.md'):
        name = name[:-len('.md')]
    path = repo / 'todo' / f'{name}.md'
    return path if path.is_file() else None


def _insert_before_next_heading(text, start, line):
    """TEXT with LINE added at the end of the section that opens at START:
    before the next `## ` heading, or at the end of the file."""
    nxt = re.compile(r'^## ', re.M).search(text, start)
    cut = nxt.start() if nxt else len(text)
    head = text[:cut].rstrip('\n')
    tail = text[cut:]
    return f'{head}\n\n{line}\n' + (f'\n{tail}' if tail else '')


def park(text, date, who, conflict=None):
    """-> (new_text, notes) for TEXT with the park written in both places.

    Idempotent: a frontmatter already `parked` is left as it is, and a body
    line already saying parked is not written twice. The body line goes at
    the end of `## What`, where the existing parks carry it, or at the end
    of the file when the item has no such section."""
    fm = FRONTMATTER_RE.match(text)
    if not fm:
        raise ValueError('no frontmatter -- not a per-item todo file')
    notes = []
    block = fm.group(1)
    field = DISPOSITION_FIELD_RE.search(block)
    if field and field.group(3).strip('"\'') == 'parked':
        notes.append('frontmatter already says parked')
    elif field:
        block = (block[:field.start()]
                 + f'{field.group(1)}{field.group(2) or " "}parked'
                 + block[field.end():])
        notes.append(f'frontmatter: {field.group(3) or "null"} -> parked')
    else:
        block = block + '\ndisposition:       parked'
        notes.append('frontmatter: added disposition: parked')
    text = f'---\n{block}\n---\n' + text[fm.end():]

    if BODY_PARK_RE.search(text):
        notes.append('body already carries a parked line')
    else:
        line = f'**Disposition:** parked ({date}, {who})'
        what = re.compile(r'^## What[ \t]*$', re.M).search(text)
        if what:
            text = _insert_before_next_heading(text, what.end(), line)
        else:
            text = text.rstrip('\n') + f'\n\n{line}\n'
        notes.append(f'body: {line}')

    if conflict:
        already = CONFLICT_RE.search(text)
        if already:
            notes.append(f'conflict already raised: {already.group(1).strip()} '
                         f'-- do not ask again')
        else:
            line = (f'**Park conflict raised:** {date}, with {who}: the '
                    f'`{conflict}` practice says this item should keep coming '
                    f'up. Asked once whether the practice should change; not '
                    f'to be asked again.')
            text = text.rstrip('\n') + f'\n\n{line}\n'
            notes.append(f'conflict recorded against {conflict} -- ask the '
                         f'person once now, then never again')
    return text, notes


def verify(text):
    """-> list of problems if TEXT does not hold a complete park."""
    problems = []
    fm = FRONTMATTER_RE.match(text)
    field = DISPOSITION_FIELD_RE.search(fm.group(1)) if fm else None
    if not field or field.group(3).strip('"\'') != 'parked':
        problems.append('frontmatter disposition is not parked')
    if not BODY_PARK_RE.search(text):
        problems.append('body carries no **Disposition:** parked line')
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Record "Drop it" on a todo item: frontmatter and body together.')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('park', help='park an item')
    p.add_argument('slug')
    p.add_argument('--by', required=True,
                   help='who said "Drop it"; `who not recorded` when unknown')
    p.add_argument('--date', help='YYYY-MM-DD; default today in the person\'s zone')
    p.add_argument('--conflict', metavar='PRACTICE',
                   help='the practice that says this item should keep being raised')
    p.add_argument('--repo', default=str(ROOT))
    args = ap.parse_args(argv)

    repo = pathlib.Path(args.repo).resolve()
    path = item_path(repo, args.slug)
    if path is None:
        print(f'todo_disposition: no todo/{args.slug} in {repo}', file=sys.stderr)
        return 1
    who = args.by.strip()
    if not who:
        print('todo_disposition: --by is empty -- name who said it, or '
              '`who not recorded`', file=sys.stderr)
        return 1
    date = args.date or precedent_time.today(repo)
    if not DATE_RE.match(date):
        print(f'todo_disposition: --date {date!r} is not YYYY-MM-DD', file=sys.stderr)
        return 1

    before = path.read_text(encoding='utf-8')
    try:
        after, notes = park(before, date, who, args.conflict)
    except ValueError as e:
        print(f'todo_disposition: {path.relative_to(repo)}: {e}', file=sys.stderr)
        return 1
    if after != before:
        path.write_text(after, encoding='utf-8')
    # practice: verify-postcondition -- re-read the file, not the string.
    problems = verify(path.read_text(encoding='utf-8'))
    rel = path.relative_to(repo).as_posix()
    for n in notes:
        print(f'{rel}: {n}')
    if problems:
        for pr in problems:
            print(f'todo_disposition: {rel}: {pr}', file=sys.stderr)
        return 1
    print(f'{rel}: parked ({date}, {who})' if after != before
          else f'{rel}: already parked; nothing changed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
