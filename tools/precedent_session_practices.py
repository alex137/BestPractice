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

# WHICH LEVELS THIS FILE CARRIES: exactly the ones a public repo's tracked
# loader block leaves out, which is build_views.PRIVATE_LEVELS -- imported
# rather than restated, because the two answering differently is the whole
# failure mode. Restating it as `everything except universal` was wrong
# within hours: build_views began rendering repo-local into the block too,
# and this file would have duplicated it into every session.


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

    # WHAT THIS FILE CARRIES is whatever the TRACKED block could not, and
    # that line is drawn in exactly one place --
    # build_views.sources_for_tracked_block() -- so the two renderers cannot
    # disagree about it. This used to restate the line as
    # `level in bv.PRIVATE_LEVELS`, and the restatement was already wrong
    # twice: once when repo-local began rendering into the tracked block, and
    # again for a practice SET, whose tracked block carries only its own
    # practices however private the repo is. Nothing is left over -> no file
    # content, which is the honest condition and replaces the old
    # `not repo_is_public()` early-out.
    _tracked, deferred, split_notes = bv.sources_for_tracked_block(
        pathlib.Path(repo), sources)
    notes += split_notes
    deferred_paths = {str(pathlib.Path(s['path']).resolve()) for s in deferred}
    if not deferred:
        notes.append(
            'every source this repo declares is already carried by its '
            'tracked loader block, so there is nothing for this file to add.')
        return [], {}, notes

    extra, levels = [], {}
    for slug, p in sorted(res['practices'].items()):
        if not _from_deferred_source(p, deferred_paths):
            continue
        extra.append((p['fm'], p['sections'], pathlib.Path(p['file'])))
        levels[slug] = p['level']
    return extra, levels, notes


def _from_deferred_source(practice, deferred_paths):
    """Whether a resolved practice came out of one of the deferred sources.

    Matched by the practice FILE's location rather than by its level: in a
    practice set the deferred source is universal, and 'universal' is not a
    level the old PRIVATE_LEVELS test would ever have caught. A file sits
    under its source's declared path, so containment answers it for every
    level at once.
    """
    f = pathlib.Path(practice['file']).resolve()
    return any(str(f).startswith(d.rstrip('/') + '/') for d in deferred_paths)


def render(extra, levels, notes, repo=None):
    # WHY THIS FILE IS UNTRACKED differs by repo kind, and saying the wrong
    # reason is worse than saying none: a practice set reading "this
    # repository is public" about itself learns something false about a
    # private repo. Both reasons end in the same instruction, so only the
    # clause explaining it changes.
    source_set = bool(repo) and bv.repo_is_practice_source(pathlib.Path(repo))
    if source_set:
        why_untracked = (
            'it carries practice text belonging to another repository, and '
            'committing a copy of it here is a copy that goes stale')
        intro = (
            "These are **in addition to** this set's own practices in "
            "[AGENTS.md](../AGENTS.md)'s generated block. They bind work in "
            "this repository exactly as those do; they are here rather than "
            "there because their text belongs to the source it came from, "
            "and a committed copy of it here would be a second copy to keep "
            "in step.")
        title = '# Practices in force here from the sources this set declares'
    else:
        why_untracked = (
            'it carries practice text from private team and individual '
            'sources, and this repository is public')
        intro = (
            "These are **in addition to** the universal catalogue already in "
            "[AGENTS.md](../AGENTS.md)'s generated block. They bind work in "
            "this repository exactly as those do; they are here rather than "
            "there because this repository is public and their text is not.")
        title = ('# Practices in force here from the team, individual and '
                 'repo-local sources')
    head = [
        '<!-- GENERATED at session start by '
        'tools/precedent_session_practices.py. UNTRACKED and gitignored, on '
        f'purpose: {why_untracked}. Never commit it, never paste '
        'its contents into a commit message, a pull request or an issue. -->',
        '',
        title,
        '',
        intro,
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
    #
    # block_dir is OUT_DIR, not the repo root: this block lands one directory
    # down, so a resident Rule's relative links are placed against
    # `.precedent/`. Most of them cannot be placed at all here -- these
    # practices live in source clones OUTSIDE this repository, where no
    # relative path reaches and an absolute one would name a private repo --
    # and build_loader_block says so on stderr rather than inventing one.
    _repo = pathlib.Path(repo or _ENGINE_DIR.parent)
    block, _tokens, _count = bv.build_loader_block(
        extra, source_levels=levels,
        block_dir=_repo / OUT_DIR, repo_root=_repo)
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
        text = render(extra, levels, notes, repo=repo)
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
