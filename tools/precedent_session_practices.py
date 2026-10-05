#!/usr/bin/env python3
"""Writes the shared/individual/repo-local practices in force into an untracked .precedent/ file at session start, since this repo is public and their text may not be committed

precedent_session_practices.py — write the practices in force from EVERY
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
resolved set into it would publish private shared and individual practice
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

PRINTED AS WELL AS WRITTEN (2026-10-04). A file on disk is not in a
session's context (gotcha-2026-09-20-a-sessionstart-hook-writing-a-file-is-
not-the-session-loadi). A practice set's own hook,
precedent-universal-catalogue.sh, hands the file back as context, but a
consumer's session-start hook only ran this tool, so a set the person brings
-- the ladder's stage words, among them -- reached a consumer's session as an
unread file, and "Debut" had to be searched for. So the write also prints
the block on stdout, where a SessionStart hook's output becomes context.
`--quiet` prints only the spoken commands (below), for a hook that emits
the file itself.

SPOKEN COMMANDS FIRST, AND SMALL (2026-10-04, the review of the above). A
session opened above several repos gets every repo's start-up output joined
and cut at a cap, and with five sets attached the ladder lines came after
the cut. So before anything else -- with --quiet too -- this prints one line
per practice here that defines a spoken command: its words, its slug and its
one-line clause, under SPOKEN_HEAD. A session-start runner lifts those
blocks to the front of everything it hands over (precedent_run_session_hooks.py).

Run:
  python3 tools/precedent_session_practices.py            # write the file and print it
  python3 tools/precedent_session_practices.py --quiet    # write it, print the spoken commands
  python3 tools/precedent_session_practices.py --check    # report, write nothing
  python3 tools/precedent_session_practices.py --repo DIR
"""
import json
import os
import pathlib
import sys

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))
import build_views as bv            # noqa: E402
import precedent_resolve as pr      # noqa: E402

OUT_DIR = '.precedent'
OUT_NAME = 'SESSION_PRACTICES.md'
# The first line of the spoken-commands block, which is this line and the
# `- ` lines right after it. precedent_run_session_hooks.py finds it by this.
SPOKEN_HEAD = ('Spoken commands in force here that AGENTS.md does not carry '
               '(load one with: python3 tools/precedent_show.py SLUG):')

# WHICH LEVELS THIS FILE CARRIES: exactly the ones a public repo's tracked
# loader block leaves out, which is build_views.PRIVATE_LEVELS -- imported
# rather than restated, because the two answering differently is the whole
# failure mode. Restating it as `everything except universal` was wrong
# within hours: build_views began rendering repo-local into the block too,
# and this file would have duplicated it into every session.


def collect(repo, skip_brought=False):
    """-> (extra_practices, levels, notes). `skip_brought` leaves out the
    sets the person brings, for measuring what bringing them costs
    (brought_share). `extra_practices` is in
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
    if skip_brought:
        sources = [s for s in sources if not s.get('brought')]

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

    # CODE OWNERS ONLY (Morgan, 2026-10-05). The tracked block never carries
    # a practice marked `visible_to: code-owners`, since it reads the same for
    # everyone; this file is per session, so it carries them to a code owner
    # from EVERY source, and leaves them out for anyone else, saying why.
    try:
        import precedent_audience as pa
        _owner_only = {slug for slug, p in res['practices'].items()
                       if pa.for_code_owners(p['fm'])}
        _is_owner, _ = pa.is_code_owner(repo)
    except Exception:                                        # noqa: BLE001
        pa, _owner_only, _is_owner = None, set(), False
    if _owner_only and not _is_owner:
        notes.append(('hidden', pa.hidden_notice(repo, sorted(_owner_only))))

    if not deferred and not (_owner_only and _is_owner):
        notes.append((
            'deferred',
            'every source this repo declares is already carried by its '
            'tracked loader block, so there is nothing for this file to add.'))
        return [], {}, notes

    extra, levels = [], {}
    for slug, p in sorted(res['practices'].items()):
        if slug in _owner_only:
            if not _is_owner:
                continue
        elif not _from_deferred_source(p, deferred_paths):
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
    # private repo. The intro carries the reason, once; the header comment
    # below only says never to commit it.
    #
    # EVERY LINE OF WRAPPING HERE IS PAID BY EVERY SESSION, in a file with its
    # own ceiling in tools/session_load_budgets.json. On 2026-09-24 a set went
    # over its ceiling when universal promoted one practice to resident, and
    # ~380 of the tokens that pushed it over were this wrapper: a header
    # comment written for people, a section restating the intro's reason, and
    # a standing instruction and index note the tracked AGENTS.md already
    # carried word for word. Keep new wrapping to what a session acts on
    # (practice: session-load-budget).
    source_set = bool(repo) and bv.repo_is_practice_source(pathlib.Path(repo))
    if source_set:
        intro = (
            "These are **in addition to** this set's own practices in "
            "[AGENTS.md](../AGENTS.md) and bind work here exactly as those "
            "do. Their text belongs to the sources it came from, so a "
            "committed copy here goes stale.")
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
        intro = (
            "These are **in addition to** the universal catalogue in "
            "[AGENTS.md](../AGENTS.md) and bind work here exactly as it "
            "does. Their text belongs to sources that move on their own, so "
            "a committed copy here goes stale.")
        title = ('# Practices in force here from the team, individual and '
                 'repo-local sources')
    else:
        intro = (
            "These are **in addition to** the universal catalogue in "
            "[AGENTS.md](../AGENTS.md) and bind work here exactly as it "
            "does. They are not in it because this repository is public and "
            "their text is not.")
        title = ('# Practices in force here from the team, individual and '
                 'repo-local sources')
    head = [
        '<!-- GENERATED by tools/precedent_session_practices.py. Never '
        'commit it. -->',
        '',
        title,
        '',
        intro,
        '',
    ]
    unresolved = [n for kind, n in notes if kind == 'unresolved']
    deferred_notes = [n for kind, n in notes if kind == 'deferred']
    # One line, kept short: every session pays for it.
    head += [n for kind, n in notes if kind == 'hidden' and n]
    if any(kind == 'hidden' and n for kind, n in notes):
        head += ['']
    if unresolved:
        head += ['## Sources that did not resolve this session', '',
                 'These are missing, and their practices are NOT below.', '']
        head += [f'- {n}' for n in unresolved]
        head += ['']
    if not extra:
        head += ['## Nothing to add', '',
                 'No source resolved that the tracked loader block does not '
                 'already carry, so this session is bound by that block alone. '
                 'If you expected a source here, a note says why it is '
                 'missing.',
                 '']
        head += [f'- {n}' for n in deferred_notes]
        return '\n'.join(head)
    if deferred_notes:
        # ONE LINE, not a section. The deferral notes' reasons are the
        # intro's; what the reader still needs is that these sources
        # RESOLVED, as against the heading above for the ones that did not.
        head += ['Every source this repository declares resolved.', '']
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
    # ...plus the person's own budget for the sets they bring, when they
    # bring any (BROUGHT_BUDGET_KEY): their share is not the repo's to pay.
    if repo:
        try:
            if any(s.get('brought') for s in pr.load_config(str(repo))):
                budget += brought_budget(repo)[0] or 0
        except Exception:                                    # noqa: BLE001
            pass
    # The tracked AGENTS.md is loaded every session alongside this file, so a
    # standing-instruction sentence or index note it already carries word for
    # word is left out of this one (build_loader_block's `carried`).
    try:
        carried = (_repo / 'AGENTS.md').read_text(encoding='utf-8')
    except OSError:
        carried = None
    try:
        block, _tokens, _count = bv.build_loader_block(
            extra, source_levels=levels,
            block_dir=_repo / OUT_DIR, repo_root=_repo,
            budget_tokens=budget, carried=carried, regen_comment=False)
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
            budget_tokens=e.tokens, carried=carried, regen_comment=False)
        head += [
            f'> **Over budget: this block is ~{e.tokens} tokens against a '
            f'declared ceiling of {e.budget}.** It is written anyway, because '
            f'a session bound by practices it was never shown is worse than a '
            f'long file. Tell the person, and bring it down: demote or trim a '
            f'resident practice in the source it came from. Never raise any '
            f'ceiling to clear this without the person\'s own words for that '
            f'raise (practice: session-load-budget).', '']
    head += [block, '']
    # A "Reading one of these in full" section used to follow, one
    # `precedent_show.py SLUG --repo <source>` line per source, because
    # the bare command read only this repo's practices/ and refused every
    # slug here. precedent_show.py looks the slug up through the declared
    # sources itself since 2026-09-30, so the standing instruction's bare
    # command works and the section, ~120 tokens every session, is
    # retired (a Reduction pass, Morgan, 2026-09-30).
    return '\n'.join(head)


# How the over-target warning below begins. The cap checks measure the file
# without it (without_target_warning): it is written BECAUSE the file is
# over its target, so counting it against the ceiling made the warning
# itself the thing that broke the ceiling. precedent-individual, 2026-09-30:
# 5,155 tokens without it, 5,211 with it, against a 5,200 ceiling -- every
# Promote there refused on a file only the warning had pushed over.
TARGET_WARNING_MARK = '> **SESSION LOAD OVER TARGET:'


def without_target_warning(text):
    """-> `text` without the over-target warning _with_target_warning adds
    (and the blank line before it): the file as its content measures."""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.startswith(TARGET_WARNING_MARK):
            start = i - 1 if i and not lines[i - 1].strip() else i
            return '\n'.join(lines[:start] + lines[i + 1:])
    return text


def _with_target_warning(repo, text, brought=0):
    """-> `text` with a warning under its title when the file is over the
    `target` its registry entry declares, else `text` unchanged.

    code-cites-practice: session-load-budget

    This file is loaded into every session, so the warning is too: over
    target, every session is told to bring it down (Morgan, 2026-09-29,
    strength: decided).
    """
    try:
        reg = json.loads((pathlib.Path(repo) / 'tools' /
                          'session_load_budgets.json').read_text(encoding='utf-8'))
        target = (reg.get('surfaces') or {}).get(f'{OUT_DIR}/{OUT_NAME}', {}).get('target')
    except (OSError, ValueError, AttributeError):
        return text
    if not isinstance(target, int):
        return text
    # The repo's part only: `brought`, the share of `text` the sets the
    # person brings account for, has its own budget (brought_share; main
    # measures it once for the file it writes).
    n = bv._approx_tokens(text) - brought
    lines = text.split('\n')
    at = next((i for i, l in enumerate(lines) if l.startswith('# ')), None)
    if n <= target or at is None:
        return text
    warning = (f'{TARGET_WARNING_MARK} this file is ~{n:,} tokens, over '
               f'its {target:,}-token target.** Say so to the person in your '
               f'first reply and offer a Reduction pass (practice: '
               f'reduction-pass). Never raise the target or the ceiling '
               f'without their own words for it.')
    return '\n'.join(lines[:at + 1] + ['', warning] + lines[at + 1:])


# THE SETS A PERSON BRINGS HAVE A BUDGET OF THEIR OWN (Morgan, 2026-10-03,
# strength: assented). Bringing the ladder is one person's choice, so its
# cost is charged to a budget in that person's individual set
# (`brought_sets_tokens` in its precedent-source.json), not to the ceiling a
# repository declared for everyone who works in it. A consumer rehearsal
# found the ladder put two repositories' session files over their ceilings,
# which refused every push there.
BROUGHT_BUDGET_KEY = 'brought_sets_tokens'


def brought_budget(repo=None):
    """-> (tokens or None, individual set path or None): the budget the
    person's individual set declares for the sets it brings."""
    try:
        sources = pr.load_config(repo or str(_ENGINE_DIR.parent))
    except Exception:                                        # noqa: BLE001
        return None, None
    ind = next((s for s in sources if s.get('level') == 'individual'), None)
    if not ind:
        return None, None
    try:
        man = json.loads((pathlib.Path(ind['path']) / pr.SOURCE_MANIFEST)
                         .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None, ind['path']
    v = man.get(BROUGHT_BUDGET_KEY) if isinstance(man, dict) else None
    return (v if isinstance(v, int) else None), ind['path']


def brought_share(repo=None):
    """-> (tokens, [names]): how much of this file the sets the person
    brings account for, measured as the file rendered with them minus the
    file rendered without them -- so a rule of the person's own that needs
    the ladder counts as part of bringing it. (0, []) when nothing is
    brought or either rendering fails."""
    repo = str(repo or _ENGINE_DIR.parent)
    try:
        names = [s['name'] for s in pr.load_config(repo) if s.get('brought')]
    except Exception:                                        # noqa: BLE001
        return 0, []
    if not names:
        return 0, []
    import contextlib, io
    try:
        # The renders' own notes were already printed by the real run.
        with contextlib.redirect_stderr(io.StringIO()):
            full = render(*collect(repo), repo=repo)
            bare = render(*collect(repo, skip_brought=True), repo=repo)
    except Exception:                                        # noqa: BLE001
        return 0, names
    return max(0, bv._approx_tokens(full) - bv._approx_tokens(bare)), names


def spoken_block(extra):
    """-> the spoken-commands block for `extra`, or '' when none of them
    defines a command: SPOKEN_HEAD, then one line per practice --
    `"Debut" -> debut: stage 4: pre-staging into staging, full checks`."""
    import precedent_vocabulary as voc
    lines = []
    for fm, sections, f in extra:
        try:
            words = list(voc._commands_in(fm))
        except (ValueError, AttributeError):
            continue
        if not words:
            continue
        slug = bv._json_str(fm.get('slug', '')) or f.stem
        clause = bv._index_clause(fm, sections)
        lines.append(', '.join(f'"{w}"' for w in words) + f' -> {slug}: {clause}')
    if not lines:
        return ''
    return '\n'.join([SPOKEN_HEAD] + [f'- {l}' for l in sorted(lines)]) + '\n'


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
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
    quiet = '--quiet' in args

    extra, levels, notes = collect(repo)
    if not check_only:
        # First, and with --quiet too: whatever cuts the start-up output
        # short, these lines come before it (SPOKEN COMMANDS FIRST above).
        try:
            spoken = spoken_block(extra)
        except Exception as e:                               # noqa: BLE001
            spoken = ''
            print(f'precedent session practices: could not list the spoken '
                  f'commands ({type(e).__name__}: {e})', file=sys.stderr)
        if spoken:
            print(spoken)
        # Said once, at session start, beside the commands: why the
        # code-owners-only practices are not here (Morgan, 2026-10-05).
        for _kind, _n in notes:
            if _kind == 'hidden' and _n:
                print(_n)
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

    text = _with_target_warning(repo, text, brought=brought_share(repo)[0])
    out_dir = pathlib.Path(repo) / OUT_DIR
    try:
        out_dir.mkdir(exist_ok=True)
        # Written whole, then renamed into place: a hook that reads the file
        # while another hook rewrites it never reads half of it.
        tmp = out_dir / f'.{OUT_NAME}.{os.getpid()}.tmp'
        tmp.write_text(text, encoding='utf-8')
        os.replace(tmp, out_dir / OUT_NAME)
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
        if not quiet:
            # On stdout, so it is in the session's context, not just on disk.
            print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
