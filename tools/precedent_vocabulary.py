#!/usr/bin/env python3
"""precedent_vocabulary.py -- the command vocabulary, read off the practices
themselves (practice: vocabulary).

A Precedent repository carries a small set of standing phrases -- `Go merge`,
`Park it`, `Three Things` -- that a session is guaranteed to recognize. Each
one is defined by a practice file, and until this existed the LIST of them
lived in two hand-maintained places: a paragraph in a project instructions
file and a table in a reader-facing document. Both drifted the moment a
command was added, and a person asking "what can I say?" got whichever copy
the session happened to have read (practice: registry-source-of-truth --
the practice files are the registry; everything else derives).

A command practice declares itself in ONE frontmatter field:

    command: {"Go merge": "Save the work, publish it, and tell you where it went."}

-- an object mapping each trigger phrase to the plain-English sentence a
person who is not a developer reads. Two phrases for one command (`Go merge`
and `Approved`) are two entries in one object, not two practices.

    python3 tools/precedent_vocabulary.py             # the list, for a session
    python3 tools/precedent_vocabulary.py --plain     # just phrase + gloss
    python3 tools/precedent_vocabulary.py --emit vocabulary
                                                      # the doc_sync block

Alphabetical by phrase, deliberately: this is a lookup, and every other
order (by date coined, by importance) is a judgment that goes stale and that
nobody can predict from outside.

SOURCES. Every level is read -- universal, team, individual, repo-local --
because a person's own set may coin a command and a session that listed only
the universal ones would be confidently wrong about their own vocabulary.
Where a source did not resolve this session, that is NAMED rather than
silently dropped (practice: fail-gracefully): "I could not read your team
set" is a different answer from "your team set defines no commands".
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import split_practices as sp                                   # noqa: E402
import build_views as bv                                       # noqa: E402


def find_root(start):
    p = pathlib.Path(start).resolve()
    for parent in [p, *p.parents]:
        if (parent / '.git').exists():
            return parent
    return p


ROOT = find_root(__file__)


def _commands_in(fm):
    """-> {phrase: gloss} for one practice's frontmatter, or {}.

    Raw field text, per the practice-file reader's convention; a malformed
    value is reported by the caller rather than swallowed, because a command
    nobody can list is a command nobody can use.
    """
    raw = (fm.get('command') or '').strip()
    if not raw or raw == 'null':
        return {}
    return json.loads(raw)


def collect(root=ROOT):
    """-> (entries, notes). entries are (phrase, gloss, slug, level, source),
    sorted by phrase, case-insensitively."""
    notes = []
    found = {}                      # slug -> (level, source, fm)

    local = root / 'practices'
    if local.is_dir():
        for f in sorted(local.glob('*.md')):
            try:
                fm, _ = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            found[fm['slug']] = ('universal', '', fm)

    try:
        import precedent_resolve as pr
        sources = pr.load_config(root)
        res = pr.resolve(sources)
        for m in res.get('missing', []):
            notes.append(
                f"{m['level']}/{m['name']} did NOT resolve this session "
                f"({m.get('reason', 'no reason given')}), so any command it "
                f"defines is NOT listed below. That is unknown, not absent.")
        for slug, practice in res['practices'].items():
            found[slug] = (practice['level'], practice.get('source', ''),
                           practice['fm'])
    except ImportError:
        notes.append('precedent_resolve.py is not beside this script, so only '
                     "this repo's own practices/ was read.")
    except Exception as e:                                      # noqa: BLE001
        notes.append(f'the declared sources could not be resolved ({e}), so '
                     "only this repo's own practices/ was read.")

    entries = []
    for slug, (level, source, fm) in found.items():
        if not bv.is_in_force(fm):
            continue
        try:
            commands = _commands_in(fm)
        except json.JSONDecodeError as e:
            notes.append(f"{slug}'s `command:` field did not parse ({e}), so "
                         f"its phrases are missing from this list.")
            continue
        for phrase, gloss in commands.items():
            entries.append((phrase, gloss, slug, level, source))
    entries.sort(key=lambda e: (e[0].lower(), e[2]))
    return entries, notes


def emit_vocabulary(root=ROOT):
    """The generated block for the reader-facing vocabulary table."""
    entries, _notes = collect(root)
    lines = ['| Say this | And it will |', '|---|---|']
    for phrase, gloss, _slug, _level, _source in entries:
        lines.append(f'| **{phrase}** | {gloss} |')
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--emit', metavar='NAME',
                    help='print a doc_sync generated block (NAME: vocabulary)')
    ap.add_argument('--plain', action='store_true',
                    help='phrase and gloss only -- no slug, level or source')
    ap.add_argument('--repo', default=str(ROOT), help='repository to read')
    args = ap.parse_args(argv)
    root = pathlib.Path(args.repo).resolve()

    if args.emit:
        if args.emit != 'vocabulary':
            sys.exit(f'precedent_vocabulary: no block named {args.emit!r}')
        print(emit_vocabulary(root))
        return 0

    entries, notes = collect(root)
    if not entries:
        # An empty vocabulary is a broken read, not a repo without commands:
        # every Precedent repo ships `Go merge` (practice: fail-gracefully).
        print('No commands found. That is a failure to read the practices, '
              'not a repository without a vocabulary -- every Precedent '
              'catalogue carries at least `Go merge`.')
        for n in notes:
            print(f'  note: {n}')
        return 1

    width = max(len(p) for p, *_ in entries)
    for phrase, gloss, slug, level, source in entries:
        if args.plain:
            print(f'{phrase.ljust(width)}  {gloss}')
        else:
            where = f'{level}/{source}' if source else level
            print(f'{phrase.ljust(width)}  {gloss}  [{slug}, {where}]')
    for n in notes:
        print(f'\nnote: {n}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
