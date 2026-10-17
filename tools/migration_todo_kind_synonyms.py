#!/usr/bin/env python3
"""Update Vendors' migration of open items filed with a kind build_todo_index.py does not know (task, todo, action, chore) to `manual`, saying which

migration_todo_kind_synonyms.py -- a migration, run by Update Vendors
(precedent_update.migrations_step), which runs every tools/migration_*.py
it finds and names none of them. migrate(repo, rep, pu): `rep` is the
update's Report. Once no repository carries such an item, this file is
deleted (practice: decommission-deletes-files).

WHY (2026-10-17, a document project's Update Vendors): an open item an
earlier engine wrote with `kind: task` made the update's generated-files
step fail half way, on build_todo_index.py's refusal ("A `task` is usually
`manual`"), and the session had to edit the item by hand and run again.
The refusal already names the answer, so the update gives it: each open
item whose kind is one of build_todo_index.KIND_SYNONYMS becomes `manual`,
and the report names every file it changed. Only the frontmatter's kind
line is touched, and only in todo/, which is the repository's own.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_todo_index as bti  # noqa: E402

TO = 'manual'
_KIND_LINE = re.compile(r'^(kind:\s*)(\S+)(\s*)$', re.M)
_STATUS_LINE = re.compile(r'^status:\s*(\S+)\s*$', re.M)


def changed_items(repo):
    """-> [(rel, old kind)] for each open todo/ item whose kind is a synonym
    build_todo_index.py would refuse, after rewriting each to `manual`."""
    out = []
    todo = pathlib.Path(repo) / 'todo'
    for path in sorted(todo.glob('todo-*.md')) if todo.is_dir() else []:
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        if not text.startswith('---\n'):
            continue
        end = text.find('\n---', 4)
        if end < 0:
            continue
        front = text[:end]
        status = _STATUS_LINE.search(front)
        kind = _KIND_LINE.search(front)
        if not status or status.group(1) != 'open' or not kind:
            continue
        old = kind.group(2).strip('"\'')
        if old.lower() not in bti.KIND_SYNONYMS:
            continue
        new_front = front[:kind.start()] + kind.group(1) + TO + kind.group(3) \
            + front[kind.end():]
        path.write_text(new_front + text[end:], encoding='utf-8')
        out.append((path.relative_to(repo).as_posix(), old))
    return out


def migrate(repo, rep, update):
    """Update Vendors' entry point (precedent_update.migrations_step)."""
    done = changed_items(repo)
    if done:
        rep.step('open items', f'{len(done)} open item(s) had a kind '
                 f'build_todo_index.py refuses, so each is now `{TO}`, the '
                 f'kind its refusal names: '
                 + ', '.join(f'{rel} (was `{old}`)' for rel, old in done))
