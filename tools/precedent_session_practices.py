#!/usr/bin/env python3
"""precedent_session_practices.py — write the practices in force from EVERY
declared source into an untracked file a session reads at start.

THE PROBLEM (measured, spec/PRELAUNCH_AUDIT.md, 2026-09-06). This repo's
precedent.json declares a universal, a team and a repo-local source, and a
user-level config adds an individual one -- 114 practices in force. The
generated AGENTS.md carries 65 of them. Of the rest, 43 were reachable by no
loading channel at all: a session working here was never shown the team's or
the person's own rules, while the config said they bind the work. A rule
nothing can load is not in force; it is filed.

WHY THE COMMITTED VIEWS CANNOT SIMPLY BE MADE MULTI-SOURCE, which is the
obvious fix and is wrong here. BestPractice is PUBLIC. AGENTS.md's generated
block carries each practice's Rule text and index clause, so rendering the
resolved set into it would publish private team and individual practice
content -- precisely what tools/leak_gate.py exists to prevent, and it would
do so on the very commit that added the feature.

THE SPLIT THAT RESOLVES IT: the constraint is on COMMITTING private text, not
on LOADING it. So the multi-source block is generated at session start into
`.precedent/SESSION_PRACTICES.md`, which is gitignored. The private text
reaches the session that needs it and never reaches a commit, a push or the
public repo. Nothing about the committed AGENTS.md changes.

WHAT THIS DELIBERATELY DOES NOT DO: it does not materialize the other
sources' CHECK SCRIPTS, so their practices become readable here, not
enforced. That is a separate and bigger step -- the same audit found that of
the source-supplied checks run against this tree, six report things this repo
cannot act on because the practice is about a different KIND of repository.
Turning them on before precedent.json's `not_binding` is populated would make
the gate red for reasons nobody has judged yet. Reading first, enforcement
when the exemptions are written.

DEGRADES LOUDLY, NEVER FATALLY. A session-start hook that fails takes the
session with it, so this always exits 0 and always writes the file. A source
that could not be resolved is NAMED in the output rather than silently
omitted -- "this source was unreachable" and "this source has no practices"
must not look the same, which is the failure mode this repo's own
environment-gotchas section already records twice.

Run:
  python3 tools/precedent_session_practices.py            # write the file
  python3 tools/precedent_session_practices.py --check    # report, write nothing
  python3 tools/precedent_session_practices.py --repo DIR
"""
import pathlib
import sys

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))
import build_views as bv            # noqa: E402
import precedent_resolve as pr      # noqa: E402

OUT_DIR = '.precedent'
OUT_NAME = 'SESSION_PRACTICES.md'
# Practices from THIS source are already in the committed AGENTS.md, so
# repeating them here would double every session's resident block. Only the
# sources AGENTS.md does not carry are written.
ALREADY_IN_AGENTS_MD = 'universal'


def collect(repo):
    """-> (extra_practices, levels, notes). `extra_practices` is in
    build_views.load_practices()' (fm, sections, file) shape so the loader
    block is rendered by the SAME code that renders AGENTS.md -- a second
    renderer here would drift from that one, which is the whole reason
    build_loader_block takes a practice list rather than reading a directory."""
    notes = []
    try:
        sources = pr.load_config(repo)
    except Exception as e:                                   # noqa: BLE001
        return [], {}, [f'no source set could be read: {e}']

    try:
        res = pr.resolve(sources)
    except Exception as e:                                   # noqa: BLE001
        return [], {}, [f'the declared sources could not be resolved: {e}']

    for m in res.get('missing', []):
        notes.append(
            f"{m['level']}/{m['name']} did NOT resolve this session "
            f"({m.get('reason', 'no reason given')}) -- its practices are not "
            f"below. Treat that as unknown, not as 'that source has no rules'.")

    extra, levels = [], {}
    for slug, p in sorted(res['practices'].items()):
        if p['level'] == ALREADY_IN_AGENTS_MD:
            continue
        extra.append((p['fm'], p['sections'], pathlib.Path(p['file'])))
        levels[slug] = p['level']
    return extra, levels, notes


def render(extra, levels, notes):
    head = [
        '<!-- GENERATED at session start by '
        'tools/precedent_session_practices.py. UNTRACKED and gitignored, on '
        'purpose: it carries practice text from private team and individual '
        'sources, and this repository is public. Never commit it, never paste '
        'its contents into a commit message, a pull request or an issue. -->',
        '',
        '# Practices in force here from the team, individual and repo-local sources',
        '',
        "These are **in addition to** the universal catalogue already in "
        "[AGENTS.md](../AGENTS.md)'s generated block. They bind work in this "
        "repository exactly as those do; they are here rather than there "
        "because this repository is public and their text is not.",
        '',
    ]
    if notes:
        head += ['## Sources that did not resolve this session', '']
        head += [f'- {n}' for n in notes]
        head += ['']
    if not extra:
        head += ['## Nothing to add', '',
                 'No non-universal source resolved, so this session is bound by '
                 'the universal catalogue alone. If you expected a team or '
                 'individual set here, the note above says why it is missing.',
                 '']
        return '\n'.join(head)
    # build_loader_block returns (text, resident_tokens, resident_count) --
    # the same renderer AGENTS.md uses, so this block cannot drift from it.
    block, _tokens, _count = bv.build_loader_block(extra, source_levels=levels)
    head += [block, '']
    return '\n'.join(head)


def main():
    args = sys.argv[1:]
    if any(a in ('--help', '-h') for a in args):
        print((__doc__ or '').strip())
        return 0
    repo = str(_ENGINE_DIR.parent)
    if '--repo' in args:
        i = args.index('--repo')
        if i + 1 >= len(args):
            print('precedent_session_practices: --repo needs a value.', file=sys.stderr)
            return 0
        repo = args[i + 1]
    check_only = '--check' in args

    extra, levels, notes = collect(repo)
    try:
        text = render(extra, levels, notes)
    except Exception as e:                                   # noqa: BLE001
        # This runs from a session-start hook, where an exception takes the
        # whole session down. Reproduced while writing it: build_loader_block
        # returns a tuple, this joined it as a string, and the traceback would
        # have been a session that failed to start rather than one missing an
        # optional file. Degrading here is the difference between a degraded
        # session and no session.
        print(f'precedent session practices: could not render the block '
              f'({type(e).__name__}: {e}) -- continuing without it.',
              file=sys.stderr)
        return 0

    for n in notes:
        print(f'precedent session practices: {n}', file=sys.stderr)

    if check_only:
        print(f'{len(extra)} practice(s) from non-universal sources would be '
              f'written; {len(notes)} source(s) unresolved.')
        return 0

    out_dir = pathlib.Path(repo) / OUT_DIR
    try:
        out_dir.mkdir(exist_ok=True)
        (out_dir / OUT_NAME).write_text(text, encoding='utf-8')
    except OSError as e:
        # Never fatal: a session-start hook that fails takes the session
        # with it, and not having the extra practices is a degraded session,
        # not a broken one.
        print(f'precedent session practices: could not write '
              f'{out_dir / OUT_NAME}: {e}', file=sys.stderr)
        return 0

    if extra:
        by_level = {}
        for slug, lvl in levels.items():
            by_level[lvl] = by_level.get(lvl, 0) + 1
        detail = ', '.join(f'{n} {lvl}' for lvl, n in sorted(by_level.items()))
        print(f'precedent session practices: {OUT_DIR}/{OUT_NAME} written '
              f'({len(extra)} practice(s): {detail}). Read it -- these bind '
              f'work here and are not in AGENTS.md.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
