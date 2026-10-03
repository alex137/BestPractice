#!/usr/bin/env python3
"""Rebuilds the generated files whose inputs a commit touches, and stages them -- run by the commit backstop, never refuses a commit

precedent_regenerate.py -- the commit-time half of "generated files are
never hand-edited" (spec/GENERATED_FILES_PLAN.md step 3; Morgan,
2026-10-03: generated files are always generated, and "auto-updated" as
their sources change).

    python3 tools/precedent_regenerate.py --staged   what the commit backstop runs
    python3 tools/precedent_regenerate.py --all      rebuild every listed file now

Reads the repository's list of generated files, tools/generated_files.json.
An entry is rebuilt when a staged path matches one of its inputs: its
`inputs` globs when it names them, else its `edit_instead` glob, plus the
tool that generates it and the list itself. Each distinct `regenerate`
command runs once. An entry with no `check` (a log or a snapshot nothing
offline can rebuild) is never run.

It FIXES a commit and never refuses one: every failure is said and the
commit goes ahead, and the push check still judges what was committed.

It never loses work (practice: repair-cannot-discard-work):
  * a generated file that has changes of the session's own that are not
    staged is rebuilt but NOT staged, and said, so nothing unstaged is
    swept into the commit -- AGENTS.md carries hand-written text around its
    generated blocks;
  * a generated file already changed in the checkout, which the rebuild
    then changes again, is copied first to .git/precedent-regenerate/, and
    said: most often an earlier rebuild, sometimes a hand edit -- the
    mistake this exists to prevent -- but either way it is kept, never
    thrown away.
"""
import fnmatch
import json
import pathlib
import shlex
import shutil
import subprocess
import sys

REGISTRY = 'tools/generated_files.json'


def _git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args],
                          capture_output=True, text=True)


def _entries(root):
    path = pathlib.Path(root) / REGISTRY
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding='utf-8')).get('files') or []
    except (ValueError, AttributeError):
        return []


def _inputs(entry):
    globs = list(entry.get('inputs') or ([entry['edit_instead']]
                                          if entry.get('edit_instead') else []))
    if entry.get('generated_by'):
        globs.append(entry['generated_by'])
    return globs + [REGISTRY]


def due(entries, staged):
    """-> the entries whose inputs one of `staged` matches, in list order.
    An entry that cannot be rebuilt offline (no `check`) is never due."""
    out = []
    for e in entries:
        if not e.get('check') or not e.get('regenerate'):
            continue
        if any(fnmatch.fnmatch(p, g) for p in staged for g in _inputs(e)):
            out.append(e)
    return out


def _blob(root, spec):
    r = subprocess.run(['git', '-C', str(root), 'show', spec],
                       capture_output=True)
    return r.stdout if r.returncode == 0 else None


def regenerate(root, entries, say=print, stage=True):
    """Run each due entry's `regenerate` once and stage what it rewrote.
    -> the paths staged."""
    root = pathlib.Path(root)
    paths = sorted({e['path'] for e in entries})
    before = {p: (root / p).read_bytes() if (root / p).is_file() else None
              for p in paths}
    unstaged = {p for p in paths
                if _git(root, 'diff', '--quiet', '--', p).returncode != 0}
    for cmd in dict.fromkeys(e['regenerate'] for e in entries):
        argv = shlex.split(cmd)
        if argv and argv[0] in ('python3', 'python'):
            argv[0] = sys.executable
        r = subprocess.run(argv, cwd=str(root), capture_output=True, text=True)
        if r.returncode != 0:
            say(f'precedent_regenerate: `{cmd}` failed, so what it writes was '
                f'left as it was; the push check will say what is stale. '
                f'{(r.stdout + r.stderr).strip()[-300:]}')
    staged = []
    for p in paths:
        now = (root / p).read_bytes() if (root / p).is_file() else None
        if now == before[p]:
            continue
        if p in unstaged:
            say(f'precedent_regenerate: rebuilt {p}, but it also has changes of '
                f'yours that are not staged, so it was NOT added to this commit. '
                f'Stage it yourself once you have looked: git add {p}')
            continue
        if before[p] is not None and before[p] != _blob(root, f'HEAD:{p}'):
            keep = root / '.git' / 'precedent-regenerate' / p
            gd = _git(root, 'rev-parse', '--absolute-git-dir').stdout.strip()
            if gd:
                keep = pathlib.Path(gd) / 'precedent-regenerate' / p
            keep.parent.mkdir(parents=True, exist_ok=True)
            keep.write_bytes(before[p])
            say(f'precedent_regenerate: {p} was already changed in this '
                f'checkout and the rebuild changed it again; the earlier version '
                f'is kept at {keep}. It is generated: change its sources, never '
                f'the file.')
        if stage:
            _git(root, 'add', '--', p)
            staged.append(p)
    if staged:
        say(f'precedent_regenerate: rebuilt and staged {", ".join(staged)} '
            f'(their sources changed in this commit).')
    return staged


def main(argv):
    if not argv or argv[0] not in ('--staged', '--all') or len(argv) > 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    top = _git(pathlib.Path.cwd(), 'rev-parse', '--show-toplevel').stdout.strip()
    if not top:
        return 0
    entries = _entries(top)
    if argv[0] == '--all':
        regenerate(top, [e for e in entries if e.get('check') and e.get('regenerate')],
                   stage=False)
        return 0
    staged = [l for l in _git(top, 'diff', '--cached', '--name-only').stdout.splitlines() if l]
    todo = due(entries, staged)
    if todo:
        regenerate(top, todo, say=lambda m: print(m, file=sys.stderr))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:  # a fixer never blocks a commit
        print(f'precedent_regenerate: skipped ({exc})', file=sys.stderr)
        sys.exit(0)
