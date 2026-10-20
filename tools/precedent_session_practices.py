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
the file on stdout, where a SessionStart hook's output becomes context.
`--quiet` prints none of it, for a hook that emits the file itself.

SPOKEN COMMANDS FIRST, AND SMALL (2026-10-04, the review of the above). A
session opened above several repos gets every repo's start-up output joined
and cut at a cap, and with five sets attached the ladder lines came after
the cut. So the file OPENS with one line per practice here that defines a
spoken command: its words, its slug and its one-line clause, under
SPOKEN_HEAD. A session-start runner lifts those blocks to the front of
everything it hands over (precedent_run_session_hooks.py).

AND ONLY THERE (2026-10-08, a reduction pass). Until then the block was
printed ahead of the file, and the file's occasion index listed every one
of those practices again, so a session paid for each command twice. A
consuming repository's session file went over its ceiling on exactly that.
Now the block is the file's first section, the file's occasion index leaves
those practices out (build_views.build_loader_block's omit_commands), and
the file is printed once. The tracked AGENTS.md has no such list, so its
own index still carries them. Because the block is part of the file, the
share of it a brought set accounts for is charged to the person's brought
budget, like the rest of that set (brought_share renders through render()).

Run:
  python3 tools/precedent_session_practices.py            # write the file and print it
  python3 tools/precedent_session_practices.py --quiet    # write it, print nothing
  python3 tools/precedent_session_practices.py --check    # report, write nothing
  python3 tools/precedent_session_practices.py --repo DIR
  python3 tools/precedent_session_practices.py --keep-if-incomplete
        # when a declared source does not resolve, keep the file already
        # there and mark it stale rather than write one with less in it

--keep-if-incomplete is what precedent_resolve._self_heal_stale_render
passes. That heal runs on every load_config(), from read-only checks
(build_views.py --check among them) included, and on 2026-10-17 it replaced a
complete 3-day-old file in an isolated clone with no sibling checkouts by one
listing every source as "did NOT resolve". A check that only reads must not
leave a session with fewer rules than it had; the old render, marked STALE on
its first line and left with its old modification time so the next heal still
re-renders it once the sources resolve, is the better guess.
"""
import collections
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

# The line --keep-if-incomplete puts at the top of a render it kept. One
# line, replaced rather than added to on a second kept run.
STALE_MARK = '> **STALE:** '


def keep_stale(target, unresolved):
    """Mark the render at `target` stale instead of rewriting it, because
    `unresolved` (the notes naming sources that did not resolve) would leave
    it with less. -> True when kept. Its modification time is put back, so
    it still reads as stale and the next heal re-renders it once the
    sources resolve."""
    try:
        st = target.stat()
        lines = target.read_text(encoding='utf-8').splitlines()
    except OSError:
        return False
    if not lines:
        return False
    try:
        import precedent_time
        when = precedent_time.from_unix(st.st_mtime, target.parent.parent
                                        ).strftime('%Y-%m-%d %H:%M %z')
    except Exception:                                        # noqa: BLE001
        when = 'earlier'
    mark = (f'{STALE_MARK}rendered {when}, kept because a re-render could not '
            f'resolve ' + '; '.join(n.split(' did NOT resolve')[0] for n in unresolved)
            + '. Its practices may be out of date; run '
            'python3 tools/precedent_session_practices.py once they resolve.')
    body = [ln for ln in lines if not ln.startswith(STALE_MARK)]
    # After the GENERATED comment, so the file still opens with it.
    at = 1 if body and body[0].startswith('<!--') else 0
    body[at:at] = [mark]
    tmp = target.with_name(f'.{target.name}.{os.getpid()}.tmp')
    try:
        tmp.write_text('\n'.join(body) + '\n', encoding='utf-8')
        os.replace(tmp, target)
        os.utime(target, (st.st_atime, st.st_mtime))
    except OSError:
        return False
    return True


# WHICH LEVELS THIS FILE CARRIES: exactly the ones a public repo's tracked
# loader block leaves out, which is build_views.PRIVATE_LEVELS -- imported
# rather than restated, because the two answering differently is the whole
# failure mode. Restating it as `everything except universal` was wrong
# within hours: build_views began rendering repo-local into the block too,
# and this file would have duplicated it into every session.


def collect(repo, skip_brought=False, skip_individual=False):
    """-> (extra_practices, levels, notes). `skip_brought` leaves out the
    sets the person brings, for measuring what bringing them costs
    (brought_share); `skip_individual` leaves out the person's own
    individual set too, for individual_share. `extra_practices` is in
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
    if skip_individual:
        sources = [s for s in sources if s.get('level') != 'individual']

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

    # THE SAVED COPY OF THE PERSON'S OWN SET (2026-10-19, Part 4 of the
    # copied-in shared sets plan). In a private repository practices/ holds
    # it, and the tracked block does not carry it. When the person's set did
    # not attach this session and the copy is theirs, it binds them from
    # here, last known good, and the first reply says so in one line. For
    # anyone else it is never read (precedent_audience.saved_copy_state).
    saved_extra = []
    try:
        if pa is not None and pa.saved_copy_in_use(repo):
            saved = pa.saved_copy_state(repo)[1]
            have = set(res['practices'])
            for fm, sections, f in bv.load_practices(
                    pathlib.Path(repo) / 'practices', announce=False):
                slug = fm.get('slug')
                if slug in saved['slugs'] and slug not in have:
                    saved_extra.append((slug, (fm, sections, pathlib.Path(f))))
            notes.append(('saved', pa.saved_copy_notice(repo)))
        elif pa is not None:
            state, _sv, why = pa.saved_copy_state(repo)
            if state == 'unknown':
                notes.append(('unresolved', f'the saved copy of an individual '
                              f'set in practices/ was not loaded: {why}'))
    except Exception as e:                                   # noqa: BLE001
        notes.append(('unresolved', f'the saved copy of an individual set '
                      f'could not be read: {e}'))

    if not deferred and not (_owner_only and _is_owner) and not saved_extra:
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
    for slug, triple in saved_extra:
        extra.append(triple)
        levels[slug] = 'individual'
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
    ]
    # THE SPOKEN COMMANDS ARE THE FIRST SECTION, ahead of the intro, so
    # whatever cuts the start-up output short, they come before the cut;
    # and the occasion index below leaves those practices out
    # (omit_commands), so each command is paid for once (AND ONLY THERE,
    # in the module docstring).
    spoken = spoken_block(extra)
    if spoken:
        head += [spoken.rstrip('\n'), '']
    head += [intro, '']
    unresolved = [n for kind, n in notes if kind == 'unresolved']
    deferred_notes = [n for kind, n in notes if kind == 'deferred']
    # The saved copy is in use: the person hears it in the first reply.
    head += [f'**Say this in one line of your first reply:** {n}.'
             for kind, n in notes if kind == 'saved' and n]
    if any(kind == 'saved' and n for kind, n in notes):
        head += ['']
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
        #
        # "Resolved" means READABLE: its practices could be loaded. Whether
        # this session can push to that repository is the ACCESS list
        # precedent_access_check.py prints at session start, where HANDOFF
        # marks one readable here but not pushable -- which, beside a bare
        # "resolved", read as a contradiction (reported by a consuming
        # repository, 2026-10-13). So the line names what it means and
        # points at the list that answers the other question.
        head += ['Every source this repository declares resolved for reading, '
                 'so its practices are below. Whether this session can also '
                 'push to each one is the ACCESS list printed at session '
                 'start: HANDOFF there means readable here, not pushable.', '']
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
            budget += brought_budget(repo, INDIVIDUAL_BUDGET_KEY)[0] or 0
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
            extra, include_code_owners=True, source_levels=levels,
            block_dir=_repo / OUT_DIR, repo_root=_repo,
            budget_tokens=budget, carried=carried, regen_comment=False,
            omit_commands=True)
    except bv.ResidentBudgetExceeded as e:
        # OVER BUDGET STILL WRITES, loudly. This runs from a session-start
        # hook: refusing means the session is bound by practices it was never
        # shown, which is the failure shape 3 exists to end, and it is
        # strictly worse than a file that is longer than intended. The gate
        # that refuses is build_views' own CLI, on the tracked block
        # (practice: fail-gracefully -- keep going, never look complete).
        block, _tokens, _count = bv.build_loader_block(
            extra, include_code_owners=True, source_levels=levels,
            block_dir=_repo / OUT_DIR, repo_root=_repo,
            budget_tokens=e.tokens, carried=carried, regen_comment=False,
            omit_commands=True)
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


# THE PERSON'S OWN INDIVIDUAL SET HAS A BUDGET OF ITS OWN TOO (Morgan,
# 2026-10-20, strength: decided: "7 option 1"). Its rules reach every
# repository the person works in, and no repository can shorten them, so
# when the set declares `individual_set_tokens` its share of this file is
# held to that, not to each repository's ceiling. 2026-10-20, a voice
# repository: ~1,176 of ~1,510 tokens were the individual set, against a
# 400-token ceiling, and every session start there failed for it.
# Undeclared, the share stays charged to the repository, as before.
INDIVIDUAL_BUDGET_KEY = 'individual_set_tokens'


def brought_budget(repo=None, key=BROUGHT_BUDGET_KEY):
    """-> (tokens or None, individual set path or None): the budget the
    person's individual set declares under `key`: for the sets it brings
    (BROUGHT_BUDGET_KEY), or for itself (INDIVIDUAL_BUDGET_KEY)."""
    try:
        sources = pr.load_config(repo or str(_ENGINE_DIR.parent))
    except Exception:                                        # noqa: BLE001
        return None, None
    ind = next((s for s in sources if pr.declared_level(s) == 'individual'), None)
    if not ind:
        return None, None
    try:
        man = json.loads((pathlib.Path(ind['path']) / pr.SOURCE_MANIFEST)
                         .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None, ind['path']
    v = man.get(key) if isinstance(man, dict) else None
    return (v if isinstance(v, int) else None), ind['path']


def _brought_renders(repo):
    """-> (full tokens, bare tokens, [names]): this file rendered now by this
    engine, with and without the sets the person brings. (None, None, names)
    when nothing is brought or either rendering fails."""
    try:
        names = [s['name'] for s in pr.load_config(repo) if s.get('brought')]
    except Exception:                                        # noqa: BLE001
        return None, None, []
    if not names:
        return None, None, []
    import contextlib, io
    try:
        # The renders' own notes were already printed by the real run.
        with contextlib.redirect_stderr(io.StringIO()):
            full = render(*collect(repo), repo=repo)
            bare = render(*collect(repo, skip_brought=True), repo=repo)
    except Exception:                                        # noqa: BLE001
        return None, None, names
    return bv._approx_tokens(full), bv._approx_tokens(bare), names


def brought_share(repo=None):
    """-> (tokens, [names]): how much of this file the sets the person
    brings account for, measured as the file rendered with them minus the
    file rendered without them -- so a rule of the person's own that needs
    the ladder counts as part of bringing it. (0, []) when nothing is
    brought or either rendering fails."""
    full, bare, names = _brought_renders(str(repo or _ENGINE_DIR.parent))
    if full is None:
        return 0, names
    return max(0, full - bare), names


def individual_share(repo):
    """-> tokens of the repository's charge (charged_to_repo) that the
    person's own individual set accounts for: the file rendered without the
    brought sets, less the file rendered without the individual set as well.
    0 when either rendering fails.

    WHY (2026-10-20). A consuming repository's ceiling for this file was
    seeded at 400 from a render whose own part measured 312; ten days later
    the session check failed every session start at ~1,510, and its remedy
    said to reduce the repository. ~1,200 of that was the person's own
    individual set -- rules the repository does not hold and cannot shorten.
    The check now says how much is whose, so the reduction goes where the
    text is, or the person decides to raise the repository's ceiling."""
    import contextlib, io
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            with_ind = render(*collect(repo, skip_brought=True), repo=repo)
            without = render(*collect(repo, skip_brought=True,
                                      skip_individual=True), repo=repo)
    except Exception:                                        # noqa: BLE001
        return 0
    return max(0, bv._approx_tokens(with_ind) - bv._approx_tokens(without))


def charged_to_repo(repo, n):
    """-> (tokens charged to the repository's ceiling, brought share, [names],
    the person's budget or None) for a session file measuring `n`.

    THE ONE DEFINITION of what the repository's ceiling for this file pays:
    the file less the share of the sets the person brings, which their own
    `brought_sets_tokens` holds (BROUGHT_BUDGET_KEY). Every reader of that
    ceiling -- the full check, the session check, the headroom and target
    notices, and the seed that writes the ceiling -- takes it from here, so
    a repository's ceiling never moves because of who works in it.
    2026-10-08, a consuming repository: the headroom notice and the target
    line charged the brought sets to the repository while the check did
    not, and the person re-measured the ceiling by hand.

    With no budget declared the share stays charged to the repository, as
    it was before the budget existed (Morgan, 2026-10-03, strength:
    assented), and the share is returned so a caller can say so.

    The charge is the file rendered NOW without the brought sets, never `n`
    less the share. `n` is read off the file on disk, which the last session
    start wrote -- with whatever engine was vendored then -- while the share
    is rendered by this one, so subtracting one from the other charged the
    repository for the difference between two engines. 2026-10-09, a
    consuming repository's Update Vendors: the file on disk measured 1,366
    and this engine's render 1,176, so a repository whose own part was 312
    was charged 502 against a ceiling of 400, and the update warned that the
    next Debut would refuse it."""
    try:
        full, bare, names = _brought_renders(str(repo))
        share = max(0, full - bare) if full is not None else 0
        budget = brought_budget(repo)[0] if share else None
    except Exception:                                        # noqa: BLE001
        return n, 0, [], None
    charged = n if (not share or budget is None) else bare
    # The individual set's share, when it declares a budget of its own
    # (INDIVIDUAL_BUDGET_KEY); individual_charge says whether it is over.
    ind, ind_budget = individual_charge(repo)
    if ind_budget is not None:
        charged = max(0, charged - ind)
    return charged, share, names, budget


def individual_charge(repo):
    """-> (the individual set's share of this file, its declared budget or
    None). The share is measured only when a budget is declared: (0, None)
    otherwise, and the share stays the repository's to pay."""
    try:
        ind_budget = brought_budget(repo, INDIVIDUAL_BUDGET_KEY)[0]
    except Exception:                                        # noqa: BLE001
        return 0, None
    if ind_budget is None:
        return 0, None
    return individual_share(str(repo)), ind_budget


def spoken_block(extra):
    """-> the spoken-commands block for `extra`, or '' when none of them
    defines a command: SPOKEN_HEAD, then one line per practice --
    `"Drop it" -> park-it: mark the item `parked` now; never raise it
    unprompted again`."""
    lines = []
    # An addition (`adds_to:`) loads with its base through precedent_show.py,
    # so the base's line only says how many there are here, never a line
    # each (Morgan, 2026-10-09).
    n_added = collections.Counter(bv.adds_to(fm) for fm, _s, _f in extra
                                  if bv.adds_to(fm))
    for fm, sections, f in extra:
        # The same test build_loader_block(omit_commands=True) uses to leave
        # a practice out of the index, so nothing falls out of both.
        words = bv.command_phrases(fm)
        if not words:
            continue
        slug = bv._json_str(fm.get('slug', '')) or f.stem
        clause = bv._index_clause(fm, sections)
        n = n_added.get(slug, 0)
        marker = f' (+ {n} addition{"s" if n != 1 else ""} here)' if n else ''
        lines.append(', '.join(f'"{w}"' for w in words)
                     + f' -> {slug}: {clause}{marker}')
    if not lines:
        return ''
    return '\n'.join([SPOKEN_HEAD] + [f'- {l}' for l in sorted(lines)]) + '\n'


def deliver_ships(repo, extra):
    """Deliver the `ships:` files and wire the `hooks:` of the practices this
    file carries, untracked (precedent_materialize.deliver_session_ships says
    how). The sync delivers a tracked set's; nothing delivered these until
    2026-10-13, when a repository given the writing set by the person's
    individual set had neither tools/create_word_doc.py, which a practice
    here tells every session to run, nor the hook another one needs
    (practice: practice-carries-its-files). Never fatal: this runs at
    session start (practice: fail-gracefully)."""
    try:
        import precedent_materialize as pm
    except ImportError:
        # Said plainly, not as a traceback's last line (2026-10-17: a set's
        # session printed "No module named 'precedent_materialize'").
        print('precedent session practices: this repository\'s engine does '
              'not carry tools/precedent_materialize.py, so the files and hooks '
              'the practices in force here ship were not set up. Update '
              'Vendors brings it.', file=sys.stderr)
        return None
    try:
        r = pm.deliver_session_ships(repo, [(fm, f) for fm, _s, f in extra])
    except Exception as e:                                   # noqa: BLE001
        print(f'precedent session practices: the files the practices below '
              f'ship were not delivered ({type(e).__name__}: {e})',
              file=sys.stderr)
        return None
    for n in r['notes']:
        print(f'precedent session practices: {n}', file=sys.stderr)
    if r['delivered'] or r['removed']:
        print(f'precedent session practices: '
              + '; '.join(filter(None, [
                  r['delivered'] and 'delivered ' + ', '.join(r['delivered']),
                  r['removed'] and 'removed ' + ', '.join(r['removed'])]))
              + ' -- files a set this repository does not track ships, kept '
              'out of git by .git/info/exclude', file=sys.stderr)
    if r['left']:
        print(f'precedent session practices: left as they are, not this '
              f'tool\'s copies or edited since: {", ".join(r["left"])}',
              file=sys.stderr)
    return r


def own_practices(repo):
    """-> a practice set's own practices in force, in collect()'s shape, so
    the session file registers their `hooks:` too; [] anywhere else. In a
    consuming repository the sync registers them in process/practice_hooks.json;
    a set has no sync, so until 2026-10-17 a set's own hooks never ran in a
    session rooted in it."""
    root = pathlib.Path(repo)
    if not bv.repo_is_practice_source(root) or not (root / 'practices').is_dir():
        return []
    try:
        return bv.load_practices(root / 'practices', announce=False)
    except Exception:                                        # noqa: BLE001
        return []


def attach_first(repo):
    """-> the block that opens a session whose practice sources did not all
    load: the add_repo call for each, before anything else, or '' when every
    one is here. On 2026-10-16 the line saying so sat in the middle of the
    session-start output, the session did all its work without the set, and
    the rule that set carries went quiet; a push is refused until it loads
    (precedent_hooks.unloaded_sources), so this says it where it is read."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_hooks
        missing = precedent_hooks.unloaded_sources(pathlib.Path(repo).resolve())
    except Exception:                                        # noqa: BLE001
        return ''
    if not missing:
        return ''
    rows = '\n'.join(f'  - {name}: '
                     + (f'add_repo owner="{w.split("/")[0]}" repo="{w.split("/")[1]}" '
                        f'access="read"' if w else 'add_repo (owner not known here)')
                     for name, w in missing)
    return ('BEFORE ANY OTHER WORK: these practice sources did not load, so their '
            'rules are not in force in this session and every push is refused '
            'until they are. Attach each, silently, then clone it where '
            '`python3 tools/precedent_session_check.py` says:\n' + rows + '\n')


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
    # Nothing is printed ahead of the file any more: it opens with the spoken
    # commands, and its head carries the code-owners note, so printing either
    # separately put it in front of the session twice (AND ONLY THERE above).
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

    unresolved = [n for kind, n in notes if kind == 'unresolved']
    target = pathlib.Path(repo) / OUT_DIR / OUT_NAME
    if ('--keep-if-incomplete' in args and unresolved and target.is_file()
            and keep_stale(target, unresolved)):
        print(f'precedent session practices: kept {OUT_DIR}/{OUT_NAME} as it '
              f'was, marked STALE, rather than rewrite it from a source set '
              f'missing a member.', file=sys.stderr)
        return 0

    lead = attach_first(repo)
    if lead:
        print(lead)
    for _kind, _n in notes:
        if _kind == 'saved' and _n:
            print(f'Say this in one line of your first reply: {_n}.')
    try:
        for line in getattr(pr, 'off_base_notes', lambda _r: [])(repo):
            print(line)
    except Exception:                                        # noqa: BLE001
        pass  # a notice; never what stops a session starting
    deliver_ships(repo, extra + own_practices(repo))
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
        # Still printed: the file could not be kept, and the session can
        # still be shown what it would have said.
        if extra and not quiet:
            print(text)
        return 0

    if not extra and not quiet:
        # Nothing else to print, and a code owner's practices were left out:
        # say why once, at session start (Morgan, 2026-10-05).
        for _kind, _n in notes:
            if _kind == 'hidden' and _n:
                print(_n)
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
            # Once, whole: it opens with the spoken commands. --quiet is for
            # a hook that emits the file itself (precedent-universal-
            # catalogue.sh), where printing them too would say them twice.
            print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
