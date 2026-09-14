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
import json
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
    # NOTES CARRY THEIR KIND, because two different things end up in this
    # list and only one of them is a problem. A source that did not RESOLVE
    # is a failure the reader must act on; a source DEFERRED to this file is
    # the mechanism working as designed. Both printed under one
    # "Sources that did not resolve this session" heading until 2026-09-13,
    # so a set reading its own generated file was told its working sources
    # had failed -- reported by a session doing the shape-3 rollout, which
    # is exactly the reader this file is for.
    notes = []   # [(kind, text)], kind in ('unresolved', 'deferred')
    try:
        sources = pr.load_config(repo)
    except Exception as e:                                   # noqa: BLE001
        return [], {}, [('unresolved', f'no source set could be read: {e}')]

    try:
        res = pr.resolve(sources)
    except Exception as e:                                   # noqa: BLE001
        return [], {}, [('unresolved',
                         f'the declared sources could not be resolved: {e}')]

    for m in res.get('missing', []):
        notes.append((
            'unresolved',
            f"{m['level']}/{m['name']} did NOT resolve this session "
            f"({m.get('reason', 'no reason given')}) -- its practices are not "
            f"below. Treat that as unknown, not as 'that source has no rules'."))

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
    notes += [('deferred', n) for n in split_notes]
    deferred_paths = {str(pathlib.Path(s['path']).resolve()) for s in deferred}
    if not deferred:
        notes.append((
            'deferred',
            'every source this repo declares is already carried by its '
            'tracked loader block, so there is nothing for this file to add.'))
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


def _declares_private(repo):
    """Whether this repo's own precedent.json says `visibility: private`.

    Only an explicit declaration counts. An ABSENT visibility is read as
    public everywhere else in the engine (build_views.visibility_is_declared
    documents why, and warns), and reading it any other way here would have
    this file contradict the tree it is generated beside."""
    if not repo:
        return False
    try:
        return json.loads(
            (pathlib.Path(repo) / 'precedent.json').read_text(
                encoding='utf-8')).get('visibility') == 'private'
    except (ValueError, OSError):
        return False


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
    elif _declares_private(repo):
        # A PRIVATE consumer. The reason above is false here and the file
        # says so to every session that opens it -- measured 2026-09-14 in a
        # private repo whose precedent.json declares `visibility: private`,
        # where this rendered "this repository is public" about a repository
        # that is not. What stays true is the instruction, so only the
        # clause explaining it changes: the file is regenerated at session
        # start from sources that move on their own, so a committed copy is
        # a copy that goes stale.
        why_untracked = (
            'it is regenerated at session start from sources that change on '
            'their own, so a committed copy is one that goes stale')
        intro = (
            "These are **in addition to** the universal catalogue already in "
            "[AGENTS.md](../AGENTS.md)'s generated block. They bind work in "
            "this repository exactly as those do; they are here rather than "
            "there because their text belongs to the sources it came from, "
            "which move on their own.")
        title = ('# Practices in force here from the team, individual and '
                 'repo-local sources')
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
    unresolved = [n for kind, n in notes if kind == 'unresolved']
    deferred_notes = [n for kind, n in notes if kind == 'deferred']
    if unresolved:
        head += ['## Sources that did not resolve this session', '',
                 'These are missing, and their practices are NOT below.', '']
        head += [f'- {n}' for n in unresolved]
        head += ['']
    if deferred_notes:
        head += ['## Why these are here rather than in the tracked block', '',
                 'These sources resolved fine. This is where they belong.', '']
        head += [f'- {n}' for n in deferred_notes]
        head += ['']
    if not extra:
        head += ['## Nothing to add', '',
                 'No source resolved that the tracked loader block does not '
                 'already carry, so this session is bound by that block alone. '
                 'If you expected a source here, a note above says why it is '
                 'missing.',
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
    # THIS FILE'S OWN CEILING, not AGENTS.md's. Until 2026-09-13 this call
    # inherited build_views.RESIDENT_BUDGET_TOKENS, which is the tracked
    # block's allocation, and the mismatch made the untracked file
    # unbuildable in two real practice sets the day shape 3 rolled out:
    # universal's residents are ~1,396 tokens and the sets' tracked-block
    # allocations are 425 and 550, numbers that were never about this file.
    # Both sets got `build_views FAIL ... over the N-token hard cap` from a
    # SessionStart hook and no practices at all. The registry already had the
    # right row; nothing read it.
    budget = bv.surface_budget(f'{OUT_DIR}/{OUT_NAME}', 4000)
    try:
        block, _tokens, _count = bv.build_loader_block(
            extra, source_levels=levels,
            block_dir=_repo / OUT_DIR, repo_root=_repo,
            budget_tokens=budget)
    except bv.ResidentBudgetExceeded as e:
        # OVER BUDGET STILL WRITES, loudly. This runs from a session-start
        # hook: refusing means the session is bound by practices it was never
        # shown, which is the failure shape 3 exists to end, and it is
        # strictly worse than a file that is longer than intended. The gate
        # that refuses is build_views' own CLI, on the tracked block
        # (practice: fail-gracefully -- keep going, never look complete).
        block, _tokens, _count = bv.build_loader_block(
            extra, source_levels=levels,
            block_dir=_repo / OUT_DIR, repo_root=_repo,
            budget_tokens=e.tokens)
        head += [
            f'> **Over budget: this block is ~{e.tokens} tokens against a '
            f'declared ceiling of {e.budget}.** It is written anyway, because '
            f'a session bound by practices it was never shown is worse than a '
            f'long file. Raise the `{OUT_DIR}/{OUT_NAME}` ceiling in '
            f'`tools/session_load_budgets.json` if this is the size it should '
            f'be, or demote a resident practice in the source it came from --'
            f' but do NOT raise `resident_block_tokens`, which is a different '
            f'surface.', '']
    head += [block, '']
    head += _how_to_read_one(extra, levels, _repo)
    return '\n'.join(head)


def _how_to_read_one(extra, levels, repo):
    """-> lines telling the session how to load one of these practices.

    The block above ends with the loader's standing instruction, which says
    `python3 tools/precedent_show.py SLUG`. That command reads THIS repo's
    practices/, and not one practice in this file lives there -- that is the
    whole reason the file exists -- so in a public repo, and in every practice
    set, it answers `unknown slug` for all of them. Measured 2026-09-14: a
    session in this repository ran the instruction for ten slugs from this
    file and got ten refusals, then found the sources by hand. The tool has
    had `--repo DIR` all along; nothing told the reader to use it.

    One line per source, derived from where each practice's file actually
    sits (practices/<slug>.md, so the source root is two levels up), never
    from a path typed here. A consuming repo that materializes every source
    into its own practices/ never reaches this: its tracked block carries
    the practices and this file is not written.
    """
    roots = {}
    for fm, _sections, path in extra:
        slug = (fm.get('slug') or path.stem).strip()
        root = path.resolve().parent.parent
        roots.setdefault(root, [levels.get(slug, '?'), 0])
        roots[root][1] += 1
    if not roots:
        return []
    lines = ['## Reading one of these in full', '',
             'None of the practices above lives in this repository\'s '
             '`practices/`, so the standing instruction\'s bare '
             '`python3 tools/precedent_show.py SLUG` reports an unknown slug '
             'for every one of them. Add `--repo` naming the source that '
             'holds it (`--detail`, `--why` and `--story` work the same way):',
             '']
    for root, (level, n) in sorted(roots.items(), key=lambda kv: (kv[1][0], str(kv[0]))):
        lines.append(f'- `python3 tools/precedent_show.py SLUG --repo {root}` '
                     f'-- the {level} source ({n} practice(s) above)')
    lines.append('')
    return lines


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

    for _kind, n in notes:
        print(f'precedent session practices: {n}', file=sys.stderr)

    if check_only:
        # Count only the UNRESOLVED ones. Counting every note reported a
        # working deferral as a failure -- the same conflation the two
        # headings above had.
        n_bad = sum(1 for kind, _n in notes if kind == 'unresolved')
        print(f'{len(extra)} practice(s) from non-universal sources would be '
              f'written; {n_bad} source(s) unresolved.')
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
