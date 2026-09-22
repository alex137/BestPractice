#!/usr/bin/env python3
"""precedent_vocabulary.py -- the command vocabulary, read off the practices
themselves (practice: vocabulary).

A Precedent repository carries a small set of standing phrases -- `Go merge`,
`Drop it`, `Three Things` -- that a session is guaranteed to recognize. Each
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
and `Approved`) are two entries in one object, not two practices, and they
render as ONE row: the first key is the phrase the list leads with, and
every other key trails it as "Synonym: ...", in the order declared.

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


def collect(root=ROOT, resolved_view=False):
    """-> (entries, notes). entries are
    (phrase, gloss, slug, level, source, synonyms), sorted by phrase,
    case-insensitively. `phrase` is the first key declared in the
    practice's `command:` object; `synonyms` is every other key it
    declares, in that same order -- one row per command, never one per
    trigger phrase.

    THE PRECEDENCE, AND WHY IT IS NOT A PLAIN OVERWRITE (2026-09-22). This
    builds one dict keyed by slug: the local `practices/*.md` first, then
    everything precedent_resolve.py returns. That second pass used to
    assign `found[slug] = ...` with no guard at all. For an ordinary
    CONSUMING repo that is exactly right -- the local half is that repo's
    own rules and the resolved half is everyone else's, and the slugs do
    not collide. In a repo that IS one of those sources, both halves are
    the same practice read from two different checkouts, and the edit in
    front of you lost in silence.

    It cost an hour to find, because every other check agrees with you: a
    session removed a `command:` field, ran this tool to confirm, and got
    the old row back, with `cat` and `git diff` both showing the edit. The
    story is in gotchas/, under the 2026-09-21 entry about editing a
    practice in its own source repo.

    So: where a resolved practice for a slug comes from a DIFFERENT FILE
    than the local one, the local file wins and the swap is NAMED. A
    session standing in a source repo is asking about the file it is
    standing on, essentially always. `resolved_view=True` restores the old
    precedence for a caller that genuinely wants the resolved answer --
    which is a flag, not a silent default.

    What the local half does NOT get to decide is its own level. The local
    loop cannot know whether it is reading a universal, shared or
    individual set, so it guesses `universal`; the resolver knows. Local
    content, resolved label.
    """
    notes = []
    found = {}                      # slug -> (level, source, fm)
    local_files = {}                # slug -> the local path it came from

    local = root / 'practices'
    if local.is_dir():
        for f in sorted(local.glob('*.md')):
            try:
                fm, _ = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            found[fm['slug']] = ('universal', '', fm)
            local_files[fm['slug']] = f.resolve()

    try:
        import precedent_resolve as pr
        sources = pr.load_config(root)
        res = pr.resolve(sources)
        for m in res.get('missing', []):
            notes.append(
                f"{m['level']}/{m['name']} did NOT resolve this session "
                f"({m.get('reason', 'no reason given')}), so any command it "
                f"defines is NOT listed below. That is unknown, not absent.")
        shadowed = []
        for slug, practice in res['practices'].items():
            resolved_file = pathlib.Path(practice['file']).resolve()
            local_file = local_files.get(slug)
            if local_file is not None and local_file != resolved_file:
                # Same practice, two checkouts. Keep the local CONTENT and
                # the resolved LABEL, and say so -- see this function's
                # docstring for the hour this silence cost.
                shadowed.append((slug, local_file, resolved_file))
                if not resolved_view:
                    found[slug] = (practice['level'],
                                   practice.get('source', ''),
                                   found[slug][2])
                    continue
            found[slug] = (practice['level'], practice.get('source', ''),
                           practice['fm'])
        for slug, local_file, resolved_file in shadowed:
            winner = resolved_file if resolved_view else local_file
            notes.append(
                f'{slug} is defined twice -- {local_file} (this repo) and '
                f'{resolved_file} (resolved). Read from {winner}. '
                + ('Pass no --resolved-view to read the local file instead.'
                   if resolved_view else
                   'Pass --resolved-view to read the resolved one instead.'))
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
        if not commands:
            continue
        pairs = list(commands.items())            # insertion order, preserved
        phrase, gloss = pairs[0]
        synonyms = [p for p, _ in pairs[1:]]
        entries.append((phrase, gloss, slug, level, source, synonyms))
    entries.sort(key=lambda e: (e[0].lower(), e[2]))
    return entries, notes


def emit_vocabulary(root=ROOT):
    """The generated block for the reader-facing vocabulary table."""
    entries, _notes = collect(root)
    lines = ['| Say this | And it will |', '|---|---|']
    for phrase, gloss, _slug, _level, _source, synonyms in entries:
        syn = f' Synonym: {", ".join(synonyms)}' if synonyms else ''
        lines.append(f'| **{phrase}** | {gloss}{syn} |')
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--emit', metavar='NAME',
                    help='print a doc_sync generated block (NAME: vocabulary)')
    ap.add_argument('--plain', action='store_true',
                    help='phrase and gloss only -- no slug, level or source')
    ap.add_argument('--repo', default=str(ROOT), help='repository to read')
    ap.add_argument('--resolved-view', action='store_true',
                    help='when a slug is defined both here and in a resolved '
                         'source, read the resolved copy rather than this '
                         "repo's own file (the default since 2026-09-22)")
    args = ap.parse_args(argv)
    root = pathlib.Path(args.repo).resolve()

    if args.emit:
        if args.emit != 'vocabulary':
            sys.exit(f'precedent_vocabulary: no block named {args.emit!r}')
        print(emit_vocabulary(root))
        return 0

    entries, notes = collect(root, resolved_view=args.resolved_view)
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
    for phrase, gloss, slug, level, source, synonyms in entries:
        syn = f'  Synonym: {", ".join(synonyms)}' if synonyms else ''
        if args.plain:
            print(f'{phrase.ljust(width)}  {gloss}{syn}')
        else:
            where = f'{level}/{source}' if source else level
            print(f'{phrase.ljust(width)}  {gloss}{syn}  [{slug}, {where}]')
    for n in notes:
        print(f'\nnote: {n}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
