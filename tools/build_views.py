#!/usr/bin/env python3
"""This file, GLOSSARY.md, and AGENTS.md's loader block — generated views

build_views.py — phase-2 generated views (PRACTICE_ENGINE_PLAN.md,
Sequence row 2: "make AGENTS.md, MAP.md, GLOSSARY.md and the index
generated"). Regenerates:

  - the loader block inside AGENTS.md, between the
    <!-- BEGIN GENERATED: precedent-loader --> / <!-- END GENERATED -->
    markers: the resident block (## Rule of every tier: resident practice),
    the occasion index (on-demand practices grouped by occasion), and the
    standing instruction. This is "the one generated file containing
    exactly three things" from "How an Agent Knows Which Practices to
    Load" -- AGENTS.md carries it because AGENTS.md is what a session
    already loads at start, rather than inventing a second file sessions
    would need to be told to also read.
  - MAP.md, in full (a generated file, not hand-authored).
  - GLOSSARY.md, in full, built from every practice's `defines:` field.

Hand-editing any of these three fails the check: rerun this script and diff
against the committed tree; any difference is a check failure (wired into
tools/verify_harness.py).

The resident block has a hard token ceiling (see RESIDENT_BUDGET_TOKENS
below, and PRACTICE_ENGINE_PLAN.md's "The Resident Budget" -- "target ~2,000
tokens, hard-capped"). Token count is approximated as words * 1.3 (no
tokenizer dependency; see (practice: computed-numbers-in-scripts), computed
numbers live in scripts -- this IS that script, not a number restated by
hand elsewhere). Exceeding the
cap fails the build outright: adding a resident practice must cost demoting
or retiring another, mechanically, not by discipline.

Run:
  python3 tools/build_views.py             # write AGENTS.md/MAP.md/GLOSSARY.md
  python3 tools/build_views.py --check      # regenerate to memory, diff against
                                             # the committed files, exit 1 on any diff
  python3 tools/build_views.py --agents-only [--check]
      # write (or check) only AGENTS.md's loader block. MAP.md and
      # GLOSSARY.md's content is specific to how THIS repo is laid out
      # (render_map_md()'s engine table, its "this repo is
      # BestPractice itself" prose); a shared or individual source repo
      # vendoring this same file for its own practices/ catalogue wants
      # the resident-block/occasion-index mechanism, not those two.
  python3 tools/build_views.py --views-only [--check]
      # write (or check) MAP.md, GLOSSARY.md and WHERE_THINGS_ARE.md, never
      # AGENTS.md -- what a repository using Precedent runs, since its
      # loader block is precedent_sync_views.py's to write
  python3 tools/build_views.py --repo DIR [--agents-only] [--check]
      # operate on DIR's practices/AGENTS.md/MAP.md/GLOSSARY.md instead of
      # this repo's own -- --repo defaults to this script's own parent
      # directory when omitted. The "## The engine" table inside MAP.md
      # still always lists the tools sitting beside THIS SCRIPT, regardless
      # of --repo: that table describes the engine's own code inventory,
      # not the target repo's content, the same "sibling files travel with
      # the script, not with --repo" rule sibling-module imports follow.
"""
import collections, json, os, pathlib, re, subprocess, sys

# _ENGINE_DIR (where this file itself lives) is only ever used for the
# sibling-module import and the MAP.md "## The engine" listing below --
# both describe the engine's own code, which travels with wherever this
# script physically is, never with --repo. ROOT is which repo's CONTENT
# (practices/, AGENTS.md, MAP.md, GLOSSARY.md) to read and (re)generate; it
# defaults to the engine's own parent directory but is overridable with
# --repo in main() -- see precedent_show.py for the fuller rationale, and
# precedent_sync_views.py's own docstring for the trap this avoids
# (computing ROOT from `__file__` alone breaks the moment this script is
# relocated or vendored somewhere other than <repo>/tools/whatever.py).
_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = _ENGINE_DIR.parent  # unchanged default when --repo is omitted
PRACTICES_DIR = ROOT / 'practices'
AGENTS_MD = ROOT / 'AGENTS.md'
MAP_MD = ROOT / 'MAP.md'
GLOSSARY_MD = ROOT / 'GLOSSARY.md'

# The views this script writes IN FULL, from practices/ alone. Nothing
# hand-authored survives in either, so a dirty copy of one in a source clone
# is the engine's own output and may be discarded --
# precedent_refresh_sources.engine_owned_paths reads this rather than
# repeating the names, and is the reason the tuple is declared at all.
#
# AGENTS.md IS DELIBERATELY NOT HERE. Only its loader block is generated;
# the rest is somebody's prose, and a modified AGENTS.md is far more likely
# to be a person mid-edit than a stale render. Discarding that would be
# exactly the mistake engine_owned_paths' own docstring says it must never
# make, so AGENTS.md stays a person's file for that purpose.
FULLY_GENERATED_VIEWS = ('MAP.md', 'GLOSSARY.md')


def is_generated_view(path):
    """True when `path` is missing or carries this tool's own
    `generated_by: tools/build_views.py` header -- the only MAP.md or
    GLOSSARY.md it may write. An adopter's hand-made map is theirs: the plain
    form used to replace it with this repository's own
    (todo-2026-09-21-pass-1-install-and-update-findings, finding 1), and a
    consumer whose map IS generated still needs it kept current after a sync
    removes practices (a consumer's report, 2026-10-03)."""
    try:
        head = pathlib.Path(path).read_text(encoding='utf-8')[:2000]
    except FileNotFoundError:
        return True
    except (OSError, UnicodeDecodeError):
        return False
    return bool(GENERATED_BY_RE.match(head))


# The header render_map_md / render_glossary_md write (generated_label), read
# back: front matter whose generated_by names this tool, quoted or not. The
# one definition -- precedent_update.generated_full_views asks this too.
GENERATED_BY_RE = re.compile(
    r'\A---\n(?:.*\n)*?generated_by:\s*["\']?tools/build_views\.py', re.M)

sys.path.insert(0, str(_ENGINE_DIR))
import split_practices as sp
import summary_text  # a withdrawn reason is a summary: links out before the cut

BEGIN_MARKER = '<!-- BEGIN GENERATED: precedent-loader -->'
END_MARKER = '<!-- END GENERATED -->'

# code-cites-practice: session-load-budget -- one registry holds every
# always-loaded ceiling, so the resident cap is not spelled twice. The literal
# is the fallback for a vendored copy that arrived without the registry, and
# is the value the registry was created with.
def _budget(key, default):
    f = pathlib.Path(__file__).resolve().parent / 'session_load_budgets.json'
    try:
        v = json.loads(f.read_text(encoding='utf-8')).get(key)
    except (OSError, ValueError, AttributeError):
        return default
    return v if isinstance(v, int) else default


RESIDENT_BUDGET_TOKENS = _budget('resident_block_tokens', 2000)
# code-cites-practice: session-load-budget -- the generated occasion index
# grew unbudgeted to 29% of AGENTS.md; see OccasionIndexBudgetExceeded.
# The 4000 fallback is what a consumer without its own registry row gets, and
# nobody decided it (practice: constants-are-risk-inputs) -- registered in
# session_load_budgets.json's _occasion_index_fallback_comment.
OCCASION_INDEX_BUDGET_TOKENS = _budget('occasion_index_tokens', 4000)
# code-cites-practice: session-load-budget -- EACH SOURCE'S SHARE of every
# consumer's occasion index (Morgan, 2026-09-29: the universal share,
# strength: assented; one per set and a consumer cap that is their sum,
# strength: decided). A consumer's index carries every source it declares
# under one cap, and no consumer can shrink a source's part of it. So each
# source declares its own allowance -- `occasion_share_tokens` in its own
# precedent-source.json, the file a consumer already reads to identify it --
# and is held to it when it builds itself; a consumer's cap is the sum of
# the allowances of the sources it declares. Whichever source grows is
# caught where it grows.
REPO_LOCAL_OCCASION_TOKENS = _budget('repo_local_occasion_tokens', 400)


def surface_budget(name, default):
    """The declared ceiling for ONE named surface in session_load_budgets.json.

    RESIDENT_BUDGET_TOKENS above is the ceiling for the resident block of the
    TRACKED loader block -- the one in AGENTS.md. It is not the ceiling for
    every file this renderer is asked to build, and treating it as one is the
    bug this exists to fix: .precedent/SESSION_PRACTICES.md carries a
    different set of practices, is untracked, and has its own entry in the
    same registry. Applying AGENTS.md's allocation to it made the untracked
    file unbuildable in two real practice sets on 2026-09-13 -- 1,396 tokens
    of universal residents against a 425- and a 550-token cap that were never
    about them (practice: registry-source-of-truth -- one registry, read the
    row you mean).
    """
    f = pathlib.Path(__file__).resolve().parent / 'session_load_budgets.json'
    try:
        row = (json.loads(f.read_text(encoding='utf-8'))
               .get('surfaces', {}).get(name, {}))
    except (OSError, ValueError, AttributeError):
        return default
    v = row.get('ceiling')
    return v if isinstance(v, int) else default


class ResidentBudgetExceeded(Exception):
    """The resident block is over its surface's declared ceiling.

    RAISED rather than sys.exit()ed, which is what it did until 2026-09-13.
    Exiting is right for the tracked block -- build_views' own CLI is a gate,
    and over budget means the commit does not happen -- and wrong for every
    other caller: precedent_session_practices.py runs from a SessionStart
    hook, so an exit there means the session gets no practices at all rather
    than a file that is a bit long. The gate keeps exiting, at the one place
    that is a gate; everyone else decides for themselves
    (practice: fail-gracefully).
    """

    def __init__(self, tokens, budget):
        self.tokens, self.budget = tokens, budget
        super().__init__(f'resident block is ~{tokens} tokens, over the '
                         f'{budget}-token hard cap')
def occasion_share(practices):
    """-> tokens of the occasion index these practices render ALONE, measured
    with the same renderer and the same estimate as the whole index. Given a
    source's own catalogue, it is that source's share of every consumer's
    index."""
    block, _t, _n = build_loader_block(practices, occasion_budget_tokens=None,
                                       budget_tokens=10 ** 9)
    if '## Occasion index' not in block:
        return 0
    idx = block.split('## Occasion index', 1)[1].split('```')[1]
    return _approx_tokens(idx)


universal_occasion_share = occasion_share      # the name it was added under


def own_occasion_allowance(root):
    """-> the `occasion_share_tokens` a source declares in its own
    precedent-source.json, or None (not a source, or none declared)."""
    f = pathlib.Path(root) / 'precedent-source.json'
    try:
        v = json.loads(f.read_text(encoding='utf-8')).get('occasion_share_tokens')
    except (OSError, ValueError, AttributeError):
        return None
    return v if isinstance(v, int) else None


def derived_occasion_cap(root, sources=None):
    """-> (cap, why) for a repository with no occasion_index_tokens of its own:
    the sum of every declared source's allowance plus its repo-local
    allowance (repo_local_occasion_tokens, 400 unless its registry says
    otherwise).

    A SOURCE THAT DECLARES NO ALLOWANCE YET counts at its current measured
    share (Morgan, 2026-09-29: "ANY change to the mechanics of how it works
    must take into account updates/upgrades/migrations"). Allowances arrive
    unevenly -- a set clone not yet pulled, a vendored universal tree an
    older Update Vendors wrote without its precedent-source.json -- and a
    repository mid-migration must build exactly as it did before, not be
    refused by a cap it has half of. Such a source is uncapped until it
    declares one, and `why` names it. -> (None, why) only when the sources
    cannot be read at all, and the single fallback applies."""
    try:
        # A copy of this file can run with no resolver beside it (a consumer
        # fixture, a partial vendor); then the old single cap applies.
        import precedent_resolve as _pr
        if sources is None:
            sources = _pr.load_config(str(root))
    except (Exception, SystemExit) as e:                    # noqa: BLE001
        return None, f'the declared sources could not be read ({e})'
    total, parts = 0, []
    for src in sources:
        if _pr.normalize_level(src.get('level')) == 'repo-local':
            total += REPO_LOCAL_OCCASION_TOKENS
            parts.append(f'repo-local {REPO_LOCAL_OCCASION_TOKENS}')
            continue
        try:
            m = _pr.read_source_manifest(src['path']) or {}
        except Exception:                                   # noqa: BLE001
            m = {}
        v = m.get('occasion_share_tokens')
        if not isinstance(v, int):
            pdir = pathlib.Path(src['path']) / 'practices'
            v = occasion_share(load_practices(pdir, announce=False)) \
                if pdir.is_dir() else 0
            parts.append(f"{src.get('name')} ~{v} measured (it declares no "
                         f"occasion_share_tokens yet, so it is not capped)")
        else:
            parts.append(f"{src.get('name')} {v}")
        total += v
    return (total, ' + '.join(parts)) if parts else (None, 'no sources declared')


def occasion_cap(root):
    """-> (cap, why): this repository's own occasion_index_tokens when its
    registry declares one (a decision it took), else the sum of the
    allowances of the sources whose practices THIS block carries, else the
    single fallback.

    THE SUM COVERS WHAT THE BLOCK CARRIES, NOTHING ELSE. The first version
    (2026-09-29, same day) summed every declared source. A practice set
    declares universal and defers it -- its tracked block carries its own
    catalogue only -- so its cap was universal's allowance, a number about
    a catalogue the block does not hold, and its own catalogue counted for
    nothing. Where universal was cloned beside it that was a large, loose
    cap and nothing showed; in GitHub's test, with no clone, universal
    measured 0 and a freshly bootstrapped set was refused at a 0-token cap.
    So: the sources sources_for_tracked_block() keeps, plus this repo's own
    catalogue when the repo is itself a source that none of them already is.

    A SOURCE REPO THAT DECLARES NO ALLOWANCE YET keeps the old single
    fallback (practice: vendor-rollout-disclosed, question 3): a set made
    before allowances existed, or by a bootstrap that does not write one,
    builds as it always did."""
    f = pathlib.Path(__file__).resolve().parent / 'session_load_budgets.json'
    try:
        explicit = json.loads(f.read_text(encoding='utf-8')).get('occasion_index_tokens')
    except (OSError, ValueError, AttributeError):
        explicit = None
    if isinstance(explicit, int):
        return explicit, 'occasion_index_tokens in tools/session_load_budgets.json'
    return block_occasion_cap(root)


def block_occasion_cap(root):
    """-> (cap, why) from the sources this repo's block carries, as
    occasion_cap() describes; the part of it no registry overrides."""
    root = pathlib.Path(root)
    try:
        sys.path.insert(0, str(_ENGINE_DIR))
        import precedent_resolve as _pr
        carried, _deferred, _notes = sources_for_tracked_block(
            root, _pr.load_config(str(root)))
    except (Exception, SystemExit) as e:                    # noqa: BLE001
        return (OCCASION_INDEX_BUDGET_TOKENS,
                f'the fallback (the declared sources could not be read: {e})')
    total, parts = 0, []
    if (root / 'precedent-source.json').is_file() and not any(
            _same_repository(s['path'], root) for s in carried):
        own = own_occasion_allowance(root)
        if own is None:
            return (OCCASION_INDEX_BUDGET_TOKENS,
                    'the fallback (this source declares no '
                    'occasion_share_tokens in precedent-source.json yet)')
        total, parts = own, [f'this source {own}']
    if carried:
        cap, why = derived_occasion_cap(root, carried)
        if cap is not None:
            total += cap
            parts.append(why)
    if not parts:
        return OCCASION_INDEX_BUDGET_TOKENS, 'the fallback (no sources declared)'
    return total, f"the sum of its sources' allowances: {' + '.join(parts)}"


def effective_budgets(root):
    """-> {key: tokens or None} for every budget in force in `root`, each read
    through the SAME function that enforces it -- never from the JSON field
    alone. None means uncapped.

    code-cites-practice: session-load-budget

    WHY (2026-09-29). A session made precedent-individual's session-file
    ceiling a computed sum, and the number in force went from 5,200 to 6,200
    while the `ceiling` field in the registry never moved. A check reading
    that field would have passed it. Reading the number the engine actually
    uses means a new formula, a new fallback, a newly declared source or a
    removed allowance all show up here exactly as an edited number does.
    precedent_check.py's budget-within-approval compares this against the
    person's approvals. A new place the engine takes a budget from belongs
    in this function, or that check cannot see it.

    Keys: resident_block_tokens; occasion_index (this repo's occasion cap,
    left out when the sources it sums cannot be read here, since a fallback
    measured in CI is not the cap in force); occasion_share_tokens (this
    repo's allowance in its consumers, when it is a source); and per surface
    surfaces/<name> (its ceiling), surfaces/<name>/target and
    surfaces/<name>/hard_ceiling."""
    root = pathlib.Path(root)
    out = {'resident_block_tokens': RESIDENT_BUDGET_TOKENS}
    cap, why = occasion_cap(root)
    if 'could not be read' not in why:
        out['occasion_index'] = cap
    if (root / 'precedent-source.json').is_file():
        out['occasion_share_tokens'] = own_occasion_allowance(root)
    f = _ENGINE_DIR / 'session_load_budgets.json'
    try:
        surfaces = json.loads(f.read_text(encoding='utf-8')).get('surfaces') or {}
    except (OSError, ValueError, AttributeError):
        surfaces = {}
    for name, row in sorted(surfaces.items()):
        if name.startswith('_') or not isinstance(row, dict):
            continue
        v = surface_budget(name, None)
        if isinstance(v, int):
            out[f'surfaces/{name}'] = v
        for k in ('target', 'hard_ceiling'):
            if isinstance(row.get(k), int):
                out[f'surfaces/{name}/{k}'] = row[k]
    return out


class OccasionIndexBudgetExceeded(Exception):
    """The generated occasion index is over its declared ceiling.

    code-cites-practice: session-load-budget

    WHY THIS EXISTS, and why the resident cap alone was not enough. The
    resident block has been capped since phase 2; the occasion index never
    was. Measured 2026-09-14: the index had grown every single day -- 1,136
    tokens on 08-31, 2,753 on 09-11, 3,377 on 09-14, about 160 a day over the
    fortnight -- which is 29% of AGENTS.md accruing with nobody deciding it.
    Four times in two days the file crossed its ceiling and a session that
    had come to do something else paid a reduction pass, trimming PROSE to
    make room for generated text it was not allowed to touch.

    Capped so the cost lands on the session ADDING a practice, at the moment
    it adds one, as a decision about the thing that actually grew.

    Raised, never exited, for the same reason as ResidentBudgetExceeded above:
    build_views' own CLI is a gate and exits, but precedent_session_practices
    runs from a SessionStart hook, where exiting means the session gets no
    practices at all (practice: fail-gracefully).

    WHAT A SESSION SHOULD DO when it fires -- and the order matters, because
    the cheap move is not the obvious one:

      1. Give the new practice a REAL `applies_to` glob or a `gates:` entry
         and drop its `occasion:`. It then loads when it is relevant instead
         of in every session, which is usually what was wanted anyway.
      2. Shorten `index_clause` on the practices whose lines are longest.
      3. Only then ask the person to raise the ceiling, which is a decision
         they take on purpose with the reason recorded in the registry.

    Never drop an `occasion:` from a practice whose `applies_to` is `["**"]`
    and which declares no gate: that glob matches everything and therefore
    routes nothing, so the index is its ONLY channel and dropping the line
    un-routes the rule silently. 33 of 113 active practices were in exactly
    that position when this cap landed.
    """

    def __init__(self, tokens, budget):
        self.tokens, self.budget = tokens, budget
        super().__init__(
            f'the generated occasion index is ~{tokens} tokens, over the '
            f'{budget}-token cap. Give a practice a real applies_to glob or '
            f'a gate and drop its occasion: (never one whose applies_to is '
            f'["**"] with no gate -- the index is its only channel), or '
            f'shorten the longest index_clause values. Raising '
            f'occasion_index_tokens in tools/session_load_budgets.json is a '
            f'decision for the person, with the reason recorded there.')


WORD_RE = re.compile(r"\S+")


def _approx_tokens(text):
    return int(len(WORD_RE.findall(text)) * 1.3)


# A practice that is not active is still resolvable BY SLUG -- so a
# `supersedes:` reference points somewhere real -- but it is not in force, and
# nothing that presents the catalogue as current may show it. Defined here,
# in the lower-level module, and imported by precedent_resolve as
# bv.IN_FORCE_STATUS, so the loader and the resolver cannot disagree about
# what "in force" means. (precedent_resolve imports this module, never the
# other way round -- putting the constant there would be a cycle.)
# The levels whose practice text is private. A public repo's tracked loader
# block must not carry them (see _sources_for_block), and
# tools/precedent_session_practices.py renders exactly this complement into
# an untracked file instead -- one definition, so the two cannot disagree
# about which practices a public repo's session is otherwise never shown.
PRIVATE_LEVELS = ('shared', 'team', 'individual')


_VISIBILITY_WARNED = set()


def visibility_is_declared(root):
    """True when precedent.json states `visibility` outright, either way.

    repo_is_public() collapses "declared public" and "not declared at all"
    into one answer, deliberately -- undeclared has to fail safe. But the two
    differ where it matters most: a repo that DECLARED public is choosing to
    withhold private practice text, while one that merely never declared is
    having that chosen for it, and if it is actually private the choice
    silently deletes practices it wanted. Callers that are about to remove
    something need to tell those apart."""
    try:
        return json.loads(
            (pathlib.Path(root) / 'precedent.json').read_text(
                encoding='utf-8')).get('visibility') in ('public', 'private')
    except (ValueError, OSError):
        return False


def repo_is_public(root):
    """Whether this repo's tracked files are a publication.

    Public means the tracked loader block and the materialized practices/
    tree are publications, so private sources are excluded from both -- and
    it is therefore also the signal that something else has to carry them,
    which is what the standing instruction's pointer and
    precedent_session_practices.py are for.

    AN UNDECLARED `visibility` COUNTS AS PUBLIC, which reverses this
    function's original default, and the reversal is the whole point. The
    two ways of being wrong are not symmetric:

      declared private, actually public -> a private source's practice TEXT
        is committed into a world-readable repo, permanently, and no later
        edit takes it back.
      declared public, actually private -> a few practices do not
        materialize. Visible immediately, fixed by one line.

    The old default was the first of those, justified in precedent.json's
    own comment as "a repo that omits this field publishes nothing by
    accident". The opposite is true: omitting it is exactly how a public
    repo publishes by accident. Found 2026-09-07 in a real public consumer
    that had never declared the field and carried 10 individual-level and
    40 shared-level practices in its tracked tree, one of them a person's name
    and email address.

    Silence would be its own failure here -- a degraded path that does not
    announce itself is worse than the crash, because the crash at least
    tells someone -- so the undeclared case says what it assumed and how to
    state the truth, once per root per process."""
    try:
        declared = json.loads(
            (pathlib.Path(root) / 'precedent.json').read_text(
                encoding='utf-8')).get('visibility')
    except (ValueError, OSError):
        return False              # no config at all: not a Precedent repo
    if declared == 'public':
        return True
    if declared == 'private':
        return False
    key = str(pathlib.Path(root).resolve())
    if key not in _VISIBILITY_WARNED:
        _VISIBILITY_WARNED.add(key)
        # TWO WORDINGS, because the two situations are not equally bad.
        # A config with no non-universal sources loses nothing to the
        # public assumption -- there is no private text to exclude, and the
        # notice is genuinely informational. A config that declares team or
        # individual sources AND omits `visibility` has no plausible
        # correct reading: it went to the trouble of wiring sources whose
        # entire content this run is about to drop. The old single NOTICE
        # covered both in the same informational register, and a real
        # install read straight past it while receiving 89 practices
        # instead of 121, with three shared sets bound to nothing
        # (2026-09-10). Say WHICH sources are being dropped, and say that
        # the install is not doing its job.
        dropped = []
        try:
            for src in (json.loads(
                    (pathlib.Path(root) / 'precedent.json').read_text(
                        encoding='utf-8')).get('sources') or []):
                if src.get('level') in PRIVATE_LEVELS:
                    dropped.append(f"{src.get('level')}:{src.get('name')}")
        except (ValueError, OSError, AttributeError, TypeError):
            dropped = []
        if dropped:
            print(f"build_views WARNING: {root}/precedent.json declares "
                  f"{len(dropped)} non-universal source(s) -- "
                  f"{', '.join(dropped)} -- and no `visibility`. An "
                  f"undeclared visibility is read as PUBLIC, which excludes "
                  f"every one of those sources' practice text from the "
                  f"materialized tree and the tracked loader block. Those "
                  f"sources are, for this run, wired to nothing. If this "
                  f"repo is private -- which is the only reading under "
                  f"which declaring them makes sense -- add "
                  f"\"visibility\": \"private\" to that file. If it is "
                  f"genuinely public, declare \"public\" so the exclusion "
                  f"is a choice rather than a default.", file=sys.stderr)
        else:
            print(f"build_views NOTICE: {root}/precedent.json declares no "
                  f"`visibility`, so this run assumes PUBLIC and excludes "
                  f"team- and individual-level sources from anything tracked. "
                  f"That is the safe assumption, not a guess worth trusting: "
                  f"declare \"visibility\": \"private\" to carry them, or "
                  f"\"public\" to make this explicit.", file=sys.stderr)
    return True


IN_FORCE_STATUS = 'active'

# THE TWO WAYS A PRACTICE STOPS APPLYING HERE ARE NOT THE SAME THING, and
# collapsing them into one word is what let a live rule be dropped
# (2026-09-06; see spec/PRACTICE_FORMAT.md "Status" and this repo's
# practices/mistakes-become-rules.md).
#
#   deduplicated  The COPY here is redundant. The rule itself is fully in
#                 force, from somewhere else -- another source's practice,
#                 or the engine. `in_force_at:` says where, and the check
#                 resolves it. This is the common, cheap, verifiable path.
#   retired       Nobody wants this rule anywhere. `in_force_at: none`,
#                 plus a Story line saying why. Rare and deliberate.
#
# The distinction exists because "retire" invites the question "does
# something similar exist?", which is answerable by reading two files and
# feeling that they rhyme -- and that is exactly how a routine check was
# dropped on the authority of an unrelated occasional one. "Deduplicate"
# cannot be answered by resemblance: it forces the only question that
# matters, which is what the surviving copy is and whether it resolves in
# force.
DEDUPLICATED_STATUS = 'deduplicated'
RETIRED_STATUS = 'retired'

# Every status this engine recognizes. A practice carrying anything else is
# a typo or a newer engine's vocabulary, and is reported rather than
# silently treated as one of these (see verify_harness.py's
# check_status_contract) -- but it is still NOT IN FORCE, because
# `is_in_force` tests for `active` rather than testing against this list.
# Failing closed is the only safe direction: a status nobody here
# understands must never be loaded as if it were current.
KNOWN_STATUSES = (IN_FORCE_STATUS, DEDUPLICATED_STATUS, RETIRED_STATUS)


def practice_status(fm):
    """A practice's declared status, decoded, defaulting to in-force.

    `status:` is written unquoted in every practice file this repo has, but
    it is a frontmatter string like any other and a hand-authored one may
    arrive quoted -- so it goes through _json_str rather than being read
    raw. Two tools used to compare `fm.get('status') == 'retired'` directly
    and would have missed both a quoted value and, once this vocabulary
    landed, every `deduplicated` practice."""
    return _json_str(fm.get('status', IN_FORCE_STATUS)) or IN_FORCE_STATUS


def is_in_force(fm):
    """Whether this practice's rule applies here, now.

    The one predicate every loading channel must use. It is deliberately
    `== IN_FORCE_STATUS` and not `not in (DEDUPLICATED_STATUS,
    RETIRED_STATUS)`: an unrecognized status fails closed."""
    return practice_status(fm) == IN_FORCE_STATUS


# `in_force_at:` takes a slug, or one of these two literals.
IN_FORCE_AT_ENGINE = 'engine'    # absorbed into the mechanism; no practice to load
IN_FORCE_AT_NOWHERE = 'none'     # in force nowhere -- the retirement case


def status_contract_violation(fm, sections=None, slug_in_force=None):
    """-> a message naming what is wrong with this practice's `status:` /
    `in_force_at:` pair, or None when the pair is sound.

    WHY THE PAIR IS CHECKED AND NOT JUST THE STATUS. `status:` alone records
    that a rule stopped applying here but never whether anything replaced it,
    so "deduplicated safely" and "dropped and forgotten" were indistinguishable
    to every check in the system -- the forwarding address existed only as
    English prose in `## Story`, which no tool reads. That is the gap a live
    rule fell through on 2026-09-06.

    `slug_in_force` is a callable (slug) -> bool, INJECTED rather than
    imported. The real answer comes from precedent_resolve.resolve() against
    the actually-declared sources, and precedent_resolve imports this module,
    so reaching for it here would be a cycle. Passing None checks the SHAPE
    only -- that a forwarding address is present and well-formed -- and
    deliberately does not check that it resolves, which is the entire point
    of the field. A caller that can resolve must pass the callable; one that
    cannot must say so rather than reporting a shape check as the real one."""
    status = practice_status(fm)
    target = _json_str(fm.get('in_force_at', '')) or ''

    if status not in KNOWN_STATUSES:
        return (f"status: {status!r} is not a status this engine knows "
                f"({', '.join(KNOWN_STATUSES)}). It is treated as not in "
                f"force, which may not be what was meant.")

    if status == IN_FORCE_STATUS:
        if target:
            return (f"status: active carries in_force_at: {target!r}. A rule "
                    f"in force HERE has no forwarding address; one of the two "
                    f"is wrong.")
        return None

    if not target:
        return (f"status: {status} with no in_force_at:. Not optional on "
                f"anything that is not active -- it is what tells a "
                f"deduplication apart from a rule dropped and forgotten.")

    if status == DEDUPLICATED_STATUS:
        if target == IN_FORCE_AT_NOWHERE:
            return (f"status: deduplicated with in_force_at: none. "
                    f"Deduplicated means the rule IS in force, elsewhere; if "
                    f"it is in force nowhere, that is status: retired, and "
                    f"needs the evidence retirement needs.")
        if target == IN_FORCE_AT_ENGINE:
            return None
        if slug_in_force is None:
            return None          # shape is sound; resolution not checked here
        if not slug_in_force(target):
            return (f"status: deduplicated names in_force_at: {target!r}, but "
                    f"that slug does not resolve IN FORCE against the declared "
                    f"sources. A surviving copy that is itself dropped, "
                    f"shadowed or unreachable is not a surviving copy -- this "
                    f"is the deduplication that silently loses a rule.")
        return None

    # status == RETIRED_STATUS
    if target != IN_FORCE_AT_NOWHERE:
        return (f"status: retired with in_force_at: {target!r}. Retired means "
                f"the rule is wanted nowhere, so the only legal value is "
                f"'none'. If the rule survives at {target!r}, this is "
                f"status: deduplicated.")
    story = (sections or {}).get('story', '').strip()
    if not story:
        return ("status: retired with an empty ## Story. Retirement is the "
                "rare, deliberate case and is the one status no mechanism can "
                "verify for you, so it must say in prose why nobody wants "
                "this rule anywhere.")
    return None


def load_practices(practices_dir=None, in_force_only=True, announce=True):
    """Every practice file in the directory, minus the ones not in force.

    WHY THE FILTER EXISTS (2026-09-06). This function read every *.md and
    returned it, and this module never looked at `status:` anywhere -- so a
    retired practice went on being emitted into the AGENTS.md loader block,
    MAP.md and GLOSSARY.md exactly like an active one. Retirement was
    cosmetic for the one channel that decides what a session actually loads.

    Invisible in BestPractice, whose own catalogue has no retired practice.
    Found 2026-09-06 in a private shared set with three of them -- all three
    were listed in the AGENTS.md its own README calls "what a session
    actually loads", months after retirement, including one retired that
    same day. precedent_resolve.py had this right all along and prints
    `not in force: <slug> ... is status: retired`; the generated views did
    not, so the two channels disagreed and only the quieter one was read.

    A dropped practice is announced rather than silently skipped -- a
    retirement that vanishes without a word is the same silence in a
    smaller place.

    `announce=False` is for a caller that loads the same catalogue many
    times in one run and reports what is in force itself (the very deep
    check loaded it once per source per section, and printed this roster
    about 120 times a run, 2026-09-28). The default is unchanged."""
    practices_dir = practices_dir if practices_dir is not None else PRACTICES_DIR
    out, dropped = [], []
    for f in sorted(practices_dir.glob('*.md')):
        fm, sections = sp._read_practice_file(f)
        status = practice_status(fm)
        if in_force_only and not is_in_force(fm):
            dropped.append((fm.get('slug', f.stem), status))
            continue
        out.append((fm, sections, f))
    for slug, status in (dropped if announce else ()):
        print(f"build_views: {slug} is status: {status}, so it is not in "
              f"force and is left out of the generated views.", file=sys.stderr)
    return out


def _json_list(raw):
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []


def _json_str(raw):
    """`occasion:` is a JSON string LITERAL in frontmatter, quotes and all,
    so it has to be decoded, not de-quoted. This was `raw.strip('"')`, which
    leaves the backslashes in an escaped occasion: the one practice whose
    occasion contains quotes rendered in the resident block every session
    reads as `When naming what \\"run the checks\\" means in a repo:`."""
    raw = (raw or '').strip()
    if raw.startswith('"'):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return raw.strip('"')


# Relocated here 2026-09-15 from precedent_materialize.py, which declared
# the same constant and predicate and reached back into this module (as
# `pr.bv._json_str`) to decode `scope:` -- so this module always had
# everything the predicate needed except the two lines themselves. That
# split cost more than tidiness: precedent_materialize.py applies the
# filter to what it writes into a consumer's materialized tree, but
# loader_practices() below resolves the identical multi-source set a
# SECOND time, independently, for the AGENTS.md loader block -- and had no
# copy of the predicate to apply it with. A practice whose occasion can
# only ever fire inside the engine's own repository (auditing the loader,
# the routing table, the harness adapter tree) still reached a
# 2+-source consumer's generated block, disagreeing permanently with what
# precedent_sync_views.py actually produces for the same repo (practice:
# session-load-budget). See the `scope` field: spec/PRACTICE_FORMAT.md.
ENGINE_DEV_SCOPE = 'engine-dev'
ANY_ADOPTER_SCOPE = 'any-adopter'

# The two legal values, in one place, so the harness check added 2026-09-22
# does not carry a second literal copy of them that can drift from the one
# the predicate below actually compares against.
SCOPE_VALUES = (ANY_ADOPTER_SCOPE, ENGINE_DEV_SCOPE)


def _is_engine_dev_scoped(fm):
    return _json_str(fm.get('scope', '')) == ENGINE_DEV_SCOPE


def scope_violation(fm, repo_local=False):
    """Why this practice's `scope:` is not one of its legal values, or None.

    ABSENT IS LEGAL and means `any-adopter` (spec/PRACTICE_FORMAT.md). Note
    that `scope: null` never reaches here as a value at all: the one null
    policy in split_practices.parse_frontmatter_fields drops a `null` field
    on the floor, for every field in both formats, so `scope: null` and no
    `scope:` line are the same input to every consumer in the engine. That
    is why this cannot be the check that catches a practice somebody MEANT
    to scope and did not -- nothing downstream can tell the two apart. The
    spec's own named list is what catches that, in verify_harness.py.

    `repo_local` flags the redundancy the spec asks for: `local/practices/`
    never travels to another repo by a different mechanism entirely, so a
    repo-local practice declaring `engine-dev` is stating a filter that
    cannot do anything, and reads as a scope decision somebody made."""
    raw = _json_str(fm.get('scope', ''))
    if not raw:
        return None
    if raw not in SCOPE_VALUES:
        return (f'scope: {raw!r} is not one of {SCOPE_VALUES} '
                f'(absent means {ANY_ADOPTER_SCOPE})')
    if repo_local and raw == ENGINE_DEV_SCOPE:
        return ('a repo-local practice declares scope: engine-dev, which can '
                'change nothing -- local/practices/ never travels to another '
                'repo by a different mechanism entirely')
    return None


# `ships:` -- the files a practice owns besides its `checked_by` script and
# that script's test, which travel on their own (spec/PRACTICE_FORMAT.md,
# "ships"). Parsed and validated HERE, once, because four tools ask the same
# question of the same field: precedent_materialize.py delivers the files,
# precedent_check.py's practice-carries-its-files holds a source to them,
# precedent_consumer_shape.py keeps them in its consumer-shaped copy, and
# precedent_move.py refuses a move that would leave one behind. Four parsers
# would disagree about a malformed entry the first time somebody wrote one
# (practice: registry-source-of-truth).
SHIPS_FIELD = 'ships'
# Destinations another mechanism already owns. A shipped file there would be
# overwritten on the next run of that mechanism, or overwrite its output.
_SHIPS_MANAGED_PREFIXES = ('practices/', 'tools/checks/')
_SHIPS_RESERVED_PATHS = ('MANIFEST.json', 'AGENTS.md', 'CLAUDE.md',
                         'precedent.json', 'tools/ENGINE_MANIFEST.json')
_SHIPS_RESERVED_BASENAMES = ('settings.json', 'settings.local.json')


def ships_paths(fm):
    """-> the `ships:` list as strings, [] when absent or null.

    Raises ValueError when the field is present and is not a JSON list of
    strings -- a declaration nobody can read is not the same as no
    declaration, and treating it as empty would ship nothing and say
    nothing."""
    raw = fm.get(SHIPS_FIELD)
    if raw is None or str(raw).strip() in ('', 'null'):
        return []
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        raise ValueError(f'`{SHIPS_FIELD}:` is not a JSON list: {raw!r}')
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError(f'`{SHIPS_FIELD}:` must be a JSON list of path '
                         f'strings, got {raw!r}')
    return value


def _engine_tool_paths():
    """{'tools/<name>'} for every file the vendoring engine installs, of
    either kind -- asked of precedent_vendor_engine.py, the one place that
    answers it. Empty when it cannot be imported, which only weakens the
    one refusal below that uses it."""
    try:
        import precedent_vendor_engine as pve
    except Exception:                               # practice: fail-gracefully
        return set()
    names = set(getattr(pve, 'ENGINE_FILES', ())) | set(
        getattr(pve, 'CONSUMER_ENGINE_FILES', ()))
    return {f'tools/{n}' for n in names}


def ship_path_problem(path):
    """Why `path` cannot be a `ships:` entry, or None when it can.

    A shipped file lands at the same relative path in every consuming
    repository, so every refusal here is about a path that would reach
    outside that repository, or into a file some other mechanism owns."""
    if not path or path != path.strip():
        return 'is empty or carries surrounding whitespace'
    p = pathlib.PurePosixPath(path)
    if path.startswith('/') or p.is_absolute():
        return 'is an absolute path'
    if '..' in p.parts:
        return 'walks above the repository with ".."'
    if any(c in path for c in '*?[]{}'):
        return ('is a glob -- `ships:` names concrete files, so a consumer '
                'receives exactly what the source declared')
    norm = p.as_posix()
    if norm.startswith(_SHIPS_MANAGED_PREFIXES):
        return ('is under practices/ or tools/checks/, which travel already '
                '-- the practice file, its checked_by script and its test '
                'need no declaration')
    if norm in _SHIPS_RESERVED_PATHS or p.name in _SHIPS_RESERVED_BASENAMES:
        return 'is a file every repository keeps its own copy of'
    if norm in _engine_tool_paths():
        return ('is an engine file, which precedent_vendor_engine.py installs '
                'in every repository already')
    return None


# A handful of practices carry a non-canonical rule-opening label kept as
# literal content by split_practices.py (e.g. "**The practice.**" -- see its
# _label_to_section: only the exact canonical words rule/why/install get
# stripped at split time, so a real authored label like this one stays in
# the Rule text on purpose, since the plan's no-invented-content rule means
# split_practices.py cannot silently drop or reword it). Fine when the full
# Rule is loaded via precedent_show, but it adds no information in a
# one-line index entry -- stripped here for DISPLAY ONLY, in this generated
# summary line; the underlying practice file and everything precedent_show
# and precedent_paths return is untouched.
_GENERIC_RULE_LABEL_RE = re.compile(r'^\*\*(?:The practice)\.?\*\*\s*')
_SENTENCE_END_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9(\[])')


INDEX_CLAUSE_MAX = 80


def _index_clause(fm, sections):
    """The one-line routing entry a session actually decides on.

    This used to be derived: the first sentence of the Rule, truncated at 90
    characters. 86% of the 46 entries came out cut off mid-thought, and one
    ended on a dangling colon -- a routing table whose rows do not finish
    their sentence. The plan's own worked example is not a derived first
    sentence at all, it is a written clause:

        document-references-are-links — references are links; ≈ not ~
        trim-prose                    — trim after any substantial edit

    So the clause is authored, in `index_clause:`, and verify_harness.py
    requires one on every on-demand practice. This is metadata for a
    generated view, not practice text: the no-invented-content rule governs
    Rule/Why/Story/Install, which this never touches. Derivation stays as a
    fallback so a newly added practice renders before its clause is written,
    rather than silently rendering nothing."""
    written = _json_str(fm.get('index_clause', ''))
    if written:
        return written
    return _occasion_clause(sections.get('rule', ''))


_INDEX_CLAUSE_LINE_RE = re.compile(r'^index_clause:.*$', re.M)


def over_long_index_clauses(practices, root):
    """-> [(path, length)] for each on-demand practice this repo AUTHORS whose
    index_clause is over INDEX_CLAUSE_MAX and was written or changed since
    the base branch.

    WHY THE GENERATOR REFUSES, and not only the test suite (2026-09-26). A
    session extended chief-of-staff's clause to 81 characters, ran this tool,
    and got the 81 characters rendered into the occasion index without a
    word. The limit was a constant here and a sentence in
    spec/PRACTICE_FORMAT.md, and nothing put it in front of the writer at
    the moment of writing. Only verify_harness.py compared the two, and a
    push to pre-staging does not run it, so the next session to run the full
    check inherited the failure. A model cannot count characters by eye
    either, so the limit has to be measured by the tool the writer already
    runs (practice: checkable-gets-checked).

    WHY ONLY A CHANGED CLAUSE, IN A REPO THAT WROTE IT. The practice sets
    were never held to the limit and carry longer clauses already; this
    runs in them at every session start, where refusing an old clause would
    stop the refresh over text nobody touched that day. A consumer's
    practices/ is materialized from other sources, so a clause there is
    never its own to shorten. What is refused is the case this exists for:
    a clause somebody in THIS repo just wrote or edited."""
    # Authors its practices: a practice set (its manifest says kind
    # 'source'), or a repo that declares itself a source at `.` -- the
    # universal catalogue, this engine's own repo. Anything else is not
    # refused, a copied engine with no manifest included.
    try:
        kind = json.loads((root / 'tools' / 'ENGINE_MANIFEST.json')
                          .read_text(encoding='utf-8')).get('kind')
    except (OSError, ValueError):
        kind = None
    try:
        cfg = json.loads((root / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        cfg = {}
    declares_itself = any(
        isinstance(src, dict) and str(src.get('path') or '').strip() in ('.', './')
        and src.get('level') != 'repo-local'
        for src in cfg.get('sources') or [])
    if kind != 'source' and not declares_itself:
        return []
    base = cfg.get('base_branch') or 'main'
    ref = f'origin/{base}'
    if subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', '-q',
                       ref], capture_output=True).returncode != 0:
        ref = 'HEAD'
    out = []
    for fm, _sections, f in practices:
        # Only an on-demand clause is rendered, in the occasion index; the
        # harness asks the same of the same set.
        if fm.get('tier') != 'on-demand':
            continue
        clause = _json_str(fm.get('index_clause', ''))
        if len(clause) <= INDEX_CLAUSE_MAX:
            continue
        try:
            rel = pathlib.Path(f).resolve().relative_to(root.resolve())
            now = _INDEX_CLAUSE_LINE_RE.search(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            out.append((f, len(clause)))
            continue
        was = subprocess.run(['git', '-C', str(root), 'show',
                              f'{ref}:{rel.as_posix()}'],
                             capture_output=True, text=True)
        before = (_INDEX_CLAUSE_LINE_RE.search(was.stdout)
                  if was.returncode == 0 else None)
        if not (now and before and now.group(0) == before.group(0)):
            out.append((f, len(clause)))
    return out


def _occasion_clause(rule_text, max_len=90):
    """First sentence of a practice's Rule, collapsed to one line, for the
    occasion index. Joins the whole first paragraph (not just its first
    *wrapped* line -- markdown files wrap prose at ~80 columns, so a rule
    text's first physical line is very often mid-sentence) before looking
    for a sentence boundary."""
    first_para = rule_text.strip().split('\n\n', 1)[0]
    first_para = ' '.join(first_para.split())  # collapse internal line wraps
    first_para = _GENERIC_RULE_LABEL_RE.sub('', first_para)
    clause = _SENTENCE_END_RE.split(first_para, maxsplit=1)[0]
    if len(clause) > max_len:
        clause = clause[:max_len - 3].rstrip() + '...'
    return clause


# practice: cite-the-incident -- 2026-09-06, precedent-team-tms. That set
# deleted its bootstrap placeholder, leaving one resident practice and no
# on-demand ones, and the block it generated told every session to consult
# an occasion index that rendered as an empty ``` ``` box and to run four
# `precedent_gate.py` commands, ALL FOUR of which exit with FAIL there
# because no practice in that set registers a gate. Reproduced against
# fixtures in all three shapes (resident-only, on-demand-only, and a set
# with no practices at all): the three sections and the four gate names
# were emitted unconditionally, so the block described the engine's
# channels rather than the ones this source actually fills. A standing
# instruction that names a command which fails is worse than no standing
# instruction, because it teaches the session that the block is decorative.
# code-cites-practice: session-load-budget -- the occasion index is loaded in
# full by every session, so a line that routes nothing is paid for every turn.
INDEX_REQUIRED_FIELD = 'index_required'


def _routes_by_path(fm):
    """True when `applies_to` names REAL paths, so precedent_paths.py fires.

    A bare `["**"]` matches everything and therefore routes nothing -- it is
    the signature of a practice that has no file trigger at all, not of one
    that applies everywhere usefully."""
    globs = _json_list(fm.get('applies_to', '')) or []
    return bool(globs) and globs != ['**']


def index_is_redundant(fm):
    """True when this practice reaches a session WITHOUT costing an index line.

    THE RULE. A practice is routed if a real `applies_to` glob fires on the
    files its occasion is about, or a `gates:` entry fires at the moment its
    occasion describes. Either way the index line is a second copy of a
    channel that already works, and every session pays for it in tokens
    before it does any work.

    THE EXCEPTION, and it is the whole reason this is not a one-liner. Neither
    channel can fire on something a PERSON SAYS. A file glob needs a file; a
    gate needs a moment, and the moments are merge/review/push/reply -- all of
    which arrive at the END of the work the phrase was supposed to redirect.
    `Go merge` is the worked example: it must be understood in the incoming
    message, and the reply gate does not fire until the turn is already over.
    That practice's own history is the citation (practice: cite-the-incident)
    -- while its definition sat in a private set a session could not read, one
    went and asked what the phrase meant, generating the exact interruption the
    phrase exists to prevent. The index is the ONLY channel for a spoken
    trigger, so a spoken trigger is never dropped from it.

    A practice declares that by carrying `index_required: true`, or by
    defining a `command:`, which is a spoken trigger by construction.
    tools/precedent_check.py's `index-required-is-declared` reads occasion
    text for the shapes a spoken trigger takes and fails any practice that
    looks like one without the field -- so the judgment is made once, by a
    person, in the practice file, rather than re-guessed by a regex here."""
    if fm.get('command') not in (None, '', 'null'):
        return False
    if _json_str(fm.get(INDEX_REQUIRED_FIELD, '')).lower() == 'true' \
       or str(fm.get(INDEX_REQUIRED_FIELD, '')).strip().lower() in ('true', '"true"'):
        return False
    gates = _json_list(fm.get('gates', '')) or []
    return _routes_by_path(fm) or bool(gates)


def _live_gates(practices):
    """Gate names to advertise: in the engine's own closed vocabulary AND
    holding at least one in-force practice in THIS source.

    Both halves are load-bearing. The vocabulary is what
    precedent_gate.py will accept at all (it lives beside the engine, not
    under --repo, deliberately -- see that script's own SCOPE comment), and
    a practice naming a gate outside it is refused as unknown. Having a
    practice registered is what makes the gate print anything: an empty
    gate is refused by name, on purpose, so advertising one guarantees a
    failing command."""
    scope = _ENGINE_DIR / 'routing_scope.json'
    if not scope.is_file():
        # Same graceful degradation as precedent_gate.gate_vocabulary(): a
        # partial vendor can leave this file out, and that must not take
        # the whole view build down. With no vocabulary readable, advertise
        # nothing rather than guess -- an omitted sentence costs a session
        # one channel; a wrong one costs it a failing command.
        return []
    try:
        vocab = json.loads(scope.read_text(encoding='utf-8')).get('gates', {})
    except (ValueError, OSError):
        return []
    live = set()
    for fm, _sections, _f in practices:
        for g in json.loads(fm.get('gates', '[]') or '[]'):
            if g in vocab and not g.startswith('_'):
                live.add(g)
    # Vocabulary order, not sorted(): routing_scope.json lists the gates
    # along the arc of a piece of work (merge, review, push, reply), and
    # JSON object order survives the parse. Sorting alphabetically is just
    # as deterministic and throws that away for nothing.
    return [g for g in vocab if g in live]


def _gate_moment(vocab_description):
    """The short moment phrase for one gate, taken from the vocabulary's
    own description rather than hand-written here. The descriptions carry a
    qualifier after a comma or an em-dash ("reviewing work, or a review
    finding a defect"; "before pushing -- the pre-push hook") that reads as
    a run-on inside a comma-joined list, so the phrase stops at whichever
    comes first. Derived, not hardcoded: the sentence this feeds used to
    name all four moments as fixed prose, which is exactly how it came to
    claim gates the source did not have."""
    phrase = re.split(r' — |, ', vocab_description, maxsplit=1)[0]
    return phrase.strip()


# ---- placing a resident Rule's relative links (practice: cite-the-incident)
#
# A resident practice's ## Rule is copied VERBATIM into the loader block, and
# that block lands in AGENTS.md at the repository ROOT. The Rule was written
# in practices/, one directory down, so a sibling citation legal there --
# `[audience-register](audience-register.md)` -- resolves to nothing from the
# root and lands in a consuming repo as a hard doc_lint BROKEN RELATIVE LINK,
# inside a generated region no session in that repo is allowed to edit.
#
# Reported 2026-09-11 from a consuming repo taking a vendor update: an
# individual set's new practice carried the only link in the whole resident
# block and failed that repo's doc gate on an otherwise-clean update. It was
# patched at the source by dropping the markup, which holds by convention
# only -- the next resident practice to carry a link breaks every consuming
# repo the same way.
#
# WHAT IS NOT DONE HERE, and it is the constraint that shapes the rest:
# precedent_materialize.py's _rewrite_links may not mint an absolute URL
# naming a private repository, because a consuming repo can be public and a
# disclosure cannot be taken back. Neither may this. So every placement here
# is a REPO-RELATIVE path or nothing: a link whose destination cannot be
# reached from the block's own directory without escaping the repository is
# left exactly as its author wrote it, and said out loud on stderr rather
# than quietly mangled (practice: fail-gracefully).
_RULE_LINK_RE = re.compile(r'(\]\()([^)\s]+?)((?:\s+"[^"]*")?\))')
# A link written inside backticks or a fenced block is a VALUE being
# documented, not a reference -- doc_lint skips both for the same reason, and
# rewriting one would edit the prose of a rule this file is only supposed to
# relay. A `## Rule` showing a reader what a link looks like is exactly the
# kind of practice that would carry one.
_CODE_SPAN_RE = re.compile(r'`[^`]*`')
_FENCE_RE = re.compile(r'^\s*(?:```|~~~)', re.MULTILINE)


def _literal_spans(text):
    """[(start, end)] of every region of `text` that is code rather than
    prose -- fenced blocks and inline code spans. A link inside one is a
    value being shown, not a reference to repoint."""
    spans, fences = [], [m.start() for m in _FENCE_RE.finditer(text)]
    for i in range(0, len(fences) - 1, 2):
        end = text.find('\n', fences[i + 1])
        spans.append((fences[i], len(text) if end < 0 else end))
    if len(fences) % 2:                   # an unclosed fence runs to the end
        spans.append((fences[-1], len(text)))
    for m in _CODE_SPAN_RE.finditer(text):
        if not any(a <= m.start() < b for a, b in spans):
            spans.append((m.start(), m.end()))
    return spans


def _within(path, root):
    """Whether `path` is `root` or sits under it. Both already resolved."""
    return path == root or root in path.parents


def placed_practice_file(repo_root, slug, source_file, planned=()):
    """-> the path a practice's Rule links are placed relative to.

    THE ONE PLACE THAT ANSWERS "where does this practice live, for the
    purpose of repointing its links". Two callers render AGENTS.md's loader
    block -- this module for `--repo DIR --check`, and
    precedent_sync_views.py for the install step -- and they used to answer
    it differently: sync_views passed the MATERIALIZED path
    (`<repo>/practices/<slug>.md`), this module passed the SOURCE clone's
    (`<repo>/precedent/universal/practices/<slug>.md`). Both exist on disk
    in a consuming repo, so neither was reported unplaceable; they simply
    rendered a sibling citation two different ways, and
    `generated-artifact-provenance` then reported an AGENTS.md the
    documented install step had just written as hand-edited, with no state
    of the repo able to satisfy it. Found 2026-09-21, after eight merges
    red; the fix is one function, not two that agree.

    The materialized path wins wherever the run has it: it is inside the
    repo the block lands in, so the link works for a reader with no source
    clone at all. `planned` covers the run that is ABOUT to write it --
    materialize() empties practices/ before refilling it, so asking the
    disk mid-run answers a question about the previous run
    (_place_rule_links carries the same argument for the same reason).
    Where neither holds -- an engine-dev practice withheld from the tree, a
    source that materializes nothing -- the source path is returned
    unchanged and _place_rule_links makes its own call about it."""
    placed = pathlib.Path(repo_root) / 'practices' / f'{slug}.md'
    if placed.exists() or f'practices/{slug}.md' in planned:
        return placed
    return pathlib.Path(source_file)


def _place_rule_links(text, practice_file, block_dir, repo_root=None,
                      planned=()):
    """-> (rewritten Rule text, [unplaceable link targets]).

    `block_dir` is the directory the rendered block will live in -- the repo
    root for AGENTS.md, `.precedent/` for the session-practices file -- which
    is what a relative link in the block is resolved against. It is NOT the
    practice file's own directory, and that difference IS the bug.

    `repo_root` is the tree a placed link may not leave, and it is a separate
    argument BECAUSE the two differ: a block rendered into `.precedent/`
    legitimately links `../practices/x.md`, so "the relative path starts with
    .." is not the test. Leaving the repository is.

    `planned` is every repo-relative path the surrounding run will have
    written by the time anyone reads the block -- materialize() empties and
    refills practices/ and tools/checks/, so asking the DISK mid-run answers
    a question about the previous run. precedent_materialize._rewrite_links
    carries the same argument for the same reason, and records what asking
    the disk instead cost it.
    """
    unplaced = []
    src_dir = pathlib.Path(practice_file).resolve().parent
    block_dir = pathlib.Path(block_dir).resolve()
    repo_root = (pathlib.Path(repo_root).resolve()
                 if repo_root is not None else block_dir)
    literal = _literal_spans(text)

    def sub(m):
        open_paren, target, close = m.groups()
        if any(a <= m.start() < b for a, b in literal):
            return m.group(0)
        if target.startswith(('http://', 'https://', 'mailto:', '#')):
            return m.group(0)
        bare, sep, frag = target.partition('#')
        if not bare:                      # a bare #fragment resolves against
            return m.group(0)             # the rendered document, not a file
        dest = (src_dir / bare).resolve()
        # "Cannot place confidently" has exactly two shapes, and both are
        # left alone rather than guessed at. The destination not existing
        # means the rewrite would invent a path; the destination sitting
        # outside the repository means the practice file lives in a source
        # clone somewhere else on this disk (a shared or individual set), where
        # no relative link reaches it, an absolute one would name a private
        # repository, and a machine-specific `../../../home/...` would be
        # wrong for every other reader.
        if not _within(dest, repo_root):
            unplaced.append(target)
            return m.group(0)
        in_repo = os.path.relpath(dest, repo_root).replace(os.sep, '/')
        if not (dest.exists() or in_repo in planned):
            unplaced.append(target)
            return m.group(0)
        try:
            rel = os.path.relpath(dest, block_dir).replace(os.sep, '/')
        except ValueError:                # different drive, on Windows
            unplaced.append(target)
            return m.group(0)
        if rel == bare:
            return m.group(0)
        return f'{open_paren}{rel}{sep}{frag}{close}'

    return _RULE_LINK_RE.sub(sub, text), unplaced


def build_loader_block(practices, source_levels=None, defers_sources=False,
                       block_dir=None, repo_root=None, planned=(),
                       budget_tokens=None, occasion_budget_tokens=None,
                       carried=None, regen_comment=True):
    """practices: (fm, sections, file) triples, exactly as load_practices()
    returns for this repo's own single-source catalogue. source_levels:
    optional {slug: level} for a caller resolving MULTIPLE sources (e.g.
    tools/precedent_materialize.py's output, walked by a consuming repo's
    own precedent_sync_views.py) -- purely cosmetic, breaking the header's
    practice count out by level, so the generated block discloses
    provenance at a glance rather than only in MANIFEST.json. Omitting it
    (the default) renders byte-identical to before this parameter existed,
    which is what keeps this repo's own single-source generation unchanged.

    block_dir: the directory the rendered block will be written into, which
    is what a relative link inside it resolves against -- the repo root for
    AGENTS.md (the default), `<repo>/.precedent` for the session-practices
    file. repo_root: the tree those links may not leave, defaulting to
    block_dir -- they differ only where the block is written below the repo
    root. planned: repo-relative paths this run will have written by the
    time the block is read. A resident Rule's relative links are repointed
    for all three; see _place_rule_links.

    carried: text the reader already has loaded -- the session-practices
    file passes its repo's tracked AGENTS.md. A standing-instruction
    sentence, or the omitted-index note, that appears in it word for word
    is left out here, because the session reads both files and a second
    copy of a sentence is tokens that teach nothing (practice:
    session-load-budget). Only a word-for-word
    match drops text, so a repo whose AGENTS.md lacks one keeps it. None
    (the default, and AGENTS.md's own render) drops nothing.

    regen_comment=False leaves out the "Regenerate with build_views.py"
    comment, which is true only of a block build_views writes into a tracked
    file -- the session-practices file is rebuilt by its own tool every
    session and has nothing to hand-edit or --check."""
    # Resolved, so the warning below names a path a reader can act on: a
    # caller passing `--repo .` otherwise produced "cannot be placed
    # relative to .", which says nothing.
    block_dir = (pathlib.Path(block_dir) if block_dir is not None else ROOT).resolve()
    repo_root = (pathlib.Path(repo_root).resolve()
                 if repo_root is not None else block_dir)
    resident = [(fm, sections, f) for fm, sections, f in practices
                if fm.get('tier') == 'resident']
    resident.sort(key=lambda t: t[0]['slug'])

    placed = []
    for fm, sections, f in resident:
        rule, unplaced = _place_rule_links(
            sections.get('rule', '').strip(), f, block_dir, repo_root,
            planned)
        for target in unplaced:
            # Loud, and never fatal: the session-practices file legitimately
            # renders practices that live outside this repository, where no
            # relative link can reach and an absolute one would name a
            # private repository. A dead relative link is the smaller
            # failure, and saying so is what keeps it from being silent.
            print(f"build_views: {fm['slug']}'s Rule links {target!r}, which "
                  f"cannot be placed relative to {block_dir} -- it is left as "
                  f"written and will not resolve from the rendered block. "
                  f"Make it an absolute upstream URL in the practice file, or "
                  f"drop the markup.", file=sys.stderr)
        placed.append((fm, sections, rule))

    # Back to (fm, sections) pairs: everything below counts and groups the
    # resident set and has no use for the file, while `placed` carries the
    # text that actually goes in the block.
    resident = [(fm, sections) for fm, sections, _f in resident]
    resident_text = '\n\n'.join(
        f"**{fm['slug']}.** {rule}" for fm, _sections, rule in placed
    )
    budget = (RESIDENT_BUDGET_TOKENS if budget_tokens is None
              else budget_tokens)
    token_count = _approx_tokens(resident_text)
    if token_count > budget:
        raise ResidentBudgetExceeded(token_count, budget)

    on_demand = [(fm, sections) for fm, sections, _f in practices if fm.get('tier') == 'on-demand']
    by_occasion = collections.defaultdict(list)
    routed_out = []
    for fm, sections in on_demand:
        occasion = _json_str(fm.get('occasion', ''))
        if not occasion:
            continue
        if index_is_redundant(fm):
            routed_out.append(fm['slug'])
            continue
        by_occasion[occasion].append((fm['slug'], _index_clause(fm, sections)))

    index_lines = []
    for occasion in sorted(by_occasion):
        index_lines.append(f"When {occasion}:")
        for slug, clause in sorted(by_occasion[occasion]):
            index_lines.append(f"  {slug} — {clause}")
    omitted_note = (
        "(More on-demand practices are not listed here: one whose "
        "applies_to names real paths, or which declares a gate, is "
        "reached by those channels instead -- `precedent_paths.py FILE` "
        "and `precedent_gate.py MOMENT`. A trigger a PERSON SAYS cannot "
        "be reached that way and is always listed above. "
        "`precedent_show.py --index-omitted` names the omitted ones.)")
    if routed_out and not _is_carried(omitted_note, carried):
        # Say what is NOT here, and how to reach it. A session that cannot see
        # the omission reads a short index as the whole catalogue.
        index_lines.append('')
        # Deliberately no COUNT here. The count would be a second computation
        # of the same set, made from a practice list this function was handed
        # and printed for a reader who will go run the tool -- which resolves
        # the set again, its own way. The two disagreed by three on the first
        # build (2026-09-14, this repo's local/practices/ counted by one and
        # not the other), which is the shape of drift that makes a reader
        # stop believing generated text. One source of truth: the flag.
        index_lines.append(omitted_note)
    index_text = '\n'.join(index_lines)
    # The generated half of what every session loads is capped too, not just
    # the resident block (practice: session-load-budget) -- but ONLY for a
    # caller that asks, which is the opposite default from the resident cap
    # above, and deliberately.
    #
    # The resident block is a CURATED set of about ten practices and does not
    # grow when a repo resolves more sources, so one number binds every
    # caller. The occasion index is every on-demand practice in force, so a
    # consumer resolving four sources legitimately has a far bigger one than
    # this repository's own catalogue. Enforcing this repo's number there
    # refuses a consumer's correct block: precedent_sync_views.py crashed on
    # exactly that in the harness's four-source consumer fixture, 2026-09-14,
    # within an hour of the cap landing.
    #
    # So the gate passes its budget explicitly (see the CLI below) and nobody
    # else is capped by a number that was never about them.
    if occasion_budget_tokens is not None:
        occ_tokens = _approx_tokens(index_text)
        if occ_tokens > occasion_budget_tokens:
            raise OccasionIndexBudgetExceeded(occ_tokens, occasion_budget_tokens)

    lines = [BEGIN_MARKER, '']
    # The command named here has to EXIST in the repo this block is being
    # written into. It used to name tools/verify_harness.py's regeneration
    # check, which is deliberately not vendored into a source set
    # (precedent_vendor_engine.py says so in as many words), so the one
    # line telling a session the block was protected was false in every
    # private set -- and it is the line a session reads INSTEAD of
    # checking. Measured 2026-09-11 in an individual set: MAP.md sat three
    # practices stale under a header saying a guard was failing the build
    # on exactly that. `build_views.py --check` is this same file, so it
    # exists wherever this block does (practice: cite-the-incident,
    # TODO.md's loader-comment-names-an-unvendored-check).
    # `Source:` is the half a session reading this block actually needs
    # (practice: generated-edit-goes-upstream). "Regenerate with" alone tells
    # a session how its edit gets destroyed; it does not say where to put the
    # change instead, so the honest-looking next move is to edit the block
    # anyway. Named as a directory rather than one file because the block is
    # built from every resolved source's practices/, not just this repo's.
    # Kept to one clause on purpose: this line is in every session's context
    # before its first turn, so it is spent against AGENTS.md's declared
    # ceiling (practice: session-load-budget) and the long version of the
    # argument belongs in the practice file, not here.
    if regen_comment:
        lines.append(f"<!-- Regenerate with: python3 tools/build_views.py -- do not hand-edit "
                     f"this block; `python3 tools/build_views.py --check` exits non-zero on "
                     f"drift. Source: practices/ -- edit the practice file, never this "
                     f"block. -->")
        lines.append('')
    count_detail = f"{len(resident)} of {len(practices)} practices"
    if source_levels and resident:
        # Levels of the RESIDENT set specifically (not all `practices`) --
        # this sits right after "X of Y practices", so a reader's natural
        # reading is "the breakdown of X", not of the larger Y. Breaking
        # down Y instead once rendered "1 of 4 practices (1 individual, 1
        # repo-local, 1 team, 1 universal)" for a fixture with exactly ONE
        # resident practice -- readable as four resident practices, one per
        # level, which was never true.
        by_level = collections.Counter(source_levels.get(fm['slug'], '?')
                                        for fm, _s in resident)
        count_detail += ' (' + ', '.join(f"{by_level[l]} {l}" for l in
                                          sorted(by_level) if by_level[l]) + ')'
    # Every section below is emitted ONLY if this source actually fills the
    # channel it describes. See _live_gates' own note for the incident: a
    # block that names an empty channel sends the session to a command that
    # fails, and the honest rendering of "this source has nothing here" is
    # silence, not an empty heading.
    if resident:
        lines.append(f"## Resident block (~{token_count} of {budget} token budget, "
                     f"{count_detail})")
        lines.append('')
        # SAY WHEN THIS TREE IS MACHINE-DEPENDENT, and only then.
        #
        # An INDIVIDUAL source resolves through a user-level config, not
        # through this project's own precedent.json -- by design, decided
        # 2026-09-21: a person's own practices follow them into every
        # project they touch, which is the whole point of having them.
        # What was wrong was that it happened SILENTLY. The same install,
        # same commit, materialized 142 practices on one machine and 125
        # with HOME emptied, and the only way to find out was to diff two
        # trees. That difference masked a real one-line bug for a day.
        #
        # So the block discloses it where it is TRUE and stays byte-identical
        # where it is not: a repo with no individual practice in force (this
        # one, every public set, every CI checkout) renders exactly as
        # before. Whoever wants a rule in some repos and not others makes a
        # SHARED set and declares it per repo --
        # documentation/SHARED_PRACTICE_SETS.md.
        _individual = sorted(slug for slug, lvl in (source_levels or {}).items()
                             if lvl == 'individual')
        if _individual:
            lines.append(
                f"**{len(_individual)} of the practices in this generated "
                f"tree came from an INDIVIDUAL source**, which resolves through this machine's "
                f"user-level config rather than through this repository's "
                f"own `precedent.json`. That is deliberate -- a person's own "
                f"practices follow them into every project they touch -- but "
                f"it means this generated tree is **machine-dependent**: the "
                f"same commit installed by somebody else resolves a "
                f"different set. A rule you want in SOME repositories and "
                f"not others belongs in a shared set you declare per "
                f"repository, not in your individual one.")
            lines.append('')
        lines.append(resident_text)
        lines.append('')
    if index_text:
        lines.append("## Occasion index")
        lines.append('')
        lines.append("```")
        lines.append(index_text)
        lines.append("```")
        lines.append('')

    instruction = []
    if index_text:
        instruction.append(
            "Before starting work of a kind named in the occasion index above, run "
            "`python3 tools/precedent_show.py SLUG` for each listed slug to load its Rule.")
    if on_demand:
        instruction.append(
            "When editing a file, `python3 tools/precedent_paths.py FILE` prints any "
            "on-demand practice whose `applies_to` matches it, without needing the index "
            "at all.")
    live_gates = _live_gates(practices)
    if live_gates:
        scope = _ENGINE_DIR / 'routing_scope.json'
        vocab = json.loads(scope.read_text(encoding='utf-8')).get('gates', {})
        moments = ', '.join(_gate_moment(vocab[g]) for g in live_gates)
        gate_run = (f"At a named moment — {moments} — run "
                    f"`python3 tools/precedent_gate.py {'|'.join(live_gates)}`")
        gate_why = ("some practices fire at a moment rather than in a file, "
                    "and no path glob reaches those.")
        gate_full = f"{gate_run}: {gate_why}"
        # Where the reader already has this sentence with a DIFFERENT gate
        # list, the list is the only news, so the why after the colon goes.
        # The same sentence whole is dropped below with the rest.
        if not _is_carried(gate_full, carried) and _is_carried(gate_why, carried):
            instruction.append(f"{gate_run}.")
        else:
            instruction.append(gate_full)
    # THE POINTER TO THE SESSION-TIME MULTI-SOURCE BLOCK, and why it is
    # conditional on `source_levels` being absent. When source_levels IS
    # given, this block was rendered from an already-resolved multi-source
    # set (a consuming repo's precedent_sync_views.py run over
    # precedent_materialize.py's output), so the shared and individual
    # practices are right here and a pointer elsewhere would be noise
    # pointing at a duplicate. When it is absent, this is a SINGLE-source
    # render -- this repo's own case -- and the other declared sources
    # reach the session only through the untracked file
    # tools/precedent_session_practices.py writes at session start, because
    # this repository is public and their text may not be committed
    # (practice: affordance-is-shared -- every single-source repo that
    # declares a private source has this same gap, not only Precedent's own).
    # `instruction and` matters: a source with NO practices must say so
    # rather than sprout a Standing instruction section whose only content
    # is a pointer to another file. Caught by the check that the loader
    # block advertises only the channels a source actually fills.
    #
    # THE CONDITION IS "DID ANYTHING GET DEFERRED", and it has been wrong
    # twice in the narrowing direction. First it tested `not source_levels`,
    # on the reasoning that a multi-source render already carries the team and
    # individual practices inline -- which stopped being true the moment a
    # public repo began rendering multi-source with the PRIVATE levels
    # deliberately excluded, and the pointer silently vanished from AGENTS.md.
    # It was then keyed off repo_is_public(), which is only ONE of the two
    # reasons sources_for_tracked_block() defers a source: a practice SET
    # defers the universal catalogue because committing it would be a second
    # copy of another repository's text, and a set is private, so
    # repo_is_public() was False and the pointer was suppressed in all four
    # sets. Measured 2026-09-14 in precedent-individual: the hook wrote
    # .precedent/SESSION_PRACTICES.md with universal's whole catalogue in it
    # and the standing instruction never told the session to read it, so a
    # session rooted in a practice set ran on that set's own practices alone.
    # Morgan named the cause: sessions open on a practice repo and "most of
    # the rules I want aren't loaded".
    #
    # So the caller now passes whether sources_for_tracked_block() actually
    # deferred anything, which is the question, and the two reasons cannot
    # drift apart from it again.
    #
    # And then it was too narrow a third time: a set a PERSON brings is
    # deferred too, but left out of defers_sources so a tracked file reads the
    # same whoever regenerates it -- so a consumer's block never pointed at
    # the file that carried the ladder's stage words, and a session there had
    # to search for "Debut" (2026-10-04). The sentence is conditional on the
    # file existing, so it is true in every repository and the same for every
    # person: it is always carried.
    if instruction:
        instruction.append(
            "If `.precedent/SESSION_PRACTICES.md` exists, read it too: it carries the "
            "practices in force from the other sources this repo declares, which are "
            "NOT in this block and bind work here exactly as these do. It is "
            "regenerated at session start and is deliberately untracked — never commit "
            "it or quote it into a pull request.")

    shown = [i for i in instruction if not _is_carried(i, carried)]
    if shown:
        lines.append("## Standing instruction")
        lines.append('')
        lines.append(' '.join(shown))
        lines.append('')

    if not resident and not index_text and not instruction:
        # Not an empty block: a bootstrapped source with no practices yet is
        # a normal state, and saying so beats leaving a reader to work out
        # whether the generator failed.
        lines.append("This source has no practices in force, so nothing loads from it. "
                     "Add one under `practices/` and regenerate this block.")
        lines.append('')
    lines.append(END_MARKER)
    return '\n'.join(lines), token_count, len(resident)


def _is_carried(text, carried):
    """Whether `text` appears word for word in `carried`, ignoring only how
    whitespace wraps -- a hand-wrapped AGENTS.md and a one-line generated
    sentence are the same words."""
    if not carried:
        return False
    return ' '.join(text.split()) in ' '.join(carried.split())


def repo_is_practice_source(root):
    """Whether this repo IS a practice set -- an individual or shared source --
    rather than a repo that consumes them.

    Read from tools/ENGINE_MANIFEST.json's `kind`, which
    precedent_vendor_engine.py writes as "source" when it vendors the engine
    into a set and "consumer" when it vendors into a consuming repo. That is
    the only durable signal a set carries about itself: precedent.json in a
    set declares no level and no kind, and the directory name is a
    convention a rename can break.

    Absent or unreadable manifest -> False, which keeps every pre-existing
    repo on the path it was already on.
    """
    mf = root / 'tools' / 'ENGINE_MANIFEST.json'
    try:
        return json.loads(mf.read_text()).get('kind') == 'source'
    except Exception:                                        # noqa: BLE001
        return False


def repo_is_consumer(root):
    """Whether this repo CONSUMES the practice sets: tools/ENGINE_MANIFEST.json
    says `kind: consumer`. BestPractice itself has no manifest and a practice
    set says `source`, so neither reads as one; an unreadable manifest is not
    one either."""
    mf = root / 'tools' / 'ENGINE_MANIFEST.json'
    try:
        return json.loads(mf.read_text()).get('kind') == 'consumer'
    except Exception:                                        # noqa: BLE001
        return False


def _same_repository(path, root):
    """Whether `path` and `root` are the same REPOSITORY, not merely the same
    directory.

    Path equality was the test until 2026-09-13 and it is not enough, for a
    reason this project already had written down: an individual source
    resolves through ~/.config/precedent/config.json, which names an absolute
    path, and that is routinely a SECOND clone rather than the checkout being
    edited (record/GOTCHAS.md's entry on it). So a session working IN an
    individual set, whose config named another clone of that same set, saw its
    own practices treated as somebody else's tree: deferred out of the tracked
    block and duplicated into .precedent/SESSION_PRACTICES.md, where they were
    already present from the block. Reported by that set on 2026-09-13 and
    reproduced here against two clones of one repository.

    Compares origin URLs, falling back to the resolved path when either side
    has no remote -- a fixture, a worktree, a directory that is not a git
    repository at all. Normalized for the differences that are not
    differences: a trailing .git, a trailing slash, and case, since a clone
    URL is routinely lowercased by the harness while the canonical spelling
    is not (record/GOTCHAS.md's entry on the lowercased clone URL).

    Only trusts the origin URL for a directory that is itself a repository
    ROOT. `git -C <dir> remote get-url origin` does not stop at `<dir>` --
    a git-tracked SUBDIRECTORY with no `.git` of its own (e.g. a vendored
    tree mirrored into a consumer's own history, not a submodule) makes git
    walk up to the ENCLOSING repository and answer with ITS origin. Without
    this check, a consumer's vendored source directory reads as though it
    were that source's own top-level checkout, which wrongly matches on the
    origin-URL comparison below (reported against a real vendored tree,
    2026-09-15).
    """
    path, root = pathlib.Path(path), pathlib.Path(root)
    if path.resolve() == root.resolve():
        return True

    def _is_repo_root(d):
        try:
            r = subprocess.run(['git', '-C', str(d), 'rev-parse', '--show-toplevel'],
                               capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return False
        if r.returncode != 0:
            return False
        try:
            return pathlib.Path(r.stdout.strip()).resolve() == pathlib.Path(d).resolve()
        except (OSError, ValueError):
            return False

    def _origin(d):
        if not _is_repo_root(d):
            return ''
        try:
            r = subprocess.run(['git', '-C', str(d), 'remote', 'get-url', 'origin'],
                               capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return ''
        if r.returncode != 0:
            return ''
        u = r.stdout.strip().rstrip('/').lower()
        return u[:-4] if u.endswith('.git') else u

    a, b = _origin(path), _origin(root)
    if a and a == b:
        return True
    # ONE CLONED FROM THE OTHER, which is what `git clone <local path>` makes
    # and what a person reproducing this by hand will produce. Its origin is a
    # filesystem path rather than a URL, so the comparison above cannot see it.
    for origin, other in ((a, root), (b, path)):
        if origin and not origin.startswith(('http', 'git@', 'ssh://')):
            try:
                if pathlib.Path(origin).resolve() == other.resolve():
                    return True
            except (OSError, ValueError):
                pass
    return False


def sources_for_tracked_block(root, declared):
    """Split declared sources into (tracked, deferred, notes).

    THE ONE PLACE that decides what a repo's COMMITTED loader block may
    carry. Both renderers read it -- this module for AGENTS.md, and
    precedent_session_practices.py for the untracked
    .precedent/SESSION_PRACTICES.md, which carries exactly what is deferred
    here. They are split across two files and must never disagree about the
    line between them, which is why the line is drawn once, here, and
    imported rather than restated. (The previous arrangement restated it as
    PRIVATE_LEVELS in both places, and the restatement was already wrong
    within hours once repo-local began rendering into the block.)

    TWO REASONS A SOURCE CANNOT GO IN THE TRACKED BLOCK, and they are
    different reasons with the same remedy:

    1. PUBLISHING SOMEONE'S PRIVATE TEXT. A public repo's tracked block is a
       publication, so a shared or individual source's clauses cannot be
       rendered into it. This is the original rule and repo_is_public()
       carries its full reasoning.

    2. COMMITTING A COPY OF ANOTHER REPOSITORY'S TEXT. A practice SET that
       declares the universal source is not publishing anything -- universal
       is already public -- but rendering it into the set's tracked block
       writes a second copy of universal's rule text into that set's git
       history, in four sets, which then has to be regenerated every time
       universal moves and is indistinguishable from current by reading it.
       That is exactly the shape spec/SOURCE_SET_PROSE_GAP.md costed and
       rejected as "shape 2". So a practice set's tracked block carries its
       OWN practices and nothing else, and everything it declares is
       deferred to the untracked file, where it is rebuilt from the source
       every session and cannot go stale.

    Case 2 is why this is not simply a level filter: the rule is about whose
    tree the text lives in, not what the level is called.
    """
    notes = []
    # A set a PERSON brings (spec/LADDER_OPT_IN_PLAN.md D2, D6) is never
    # rendered into a committed file, whatever the repository: it is in force
    # for that one person, so writing it into a tracked view would hand it to
    # everyone who works here -- and make the view differ by who regenerated
    # it last.
    brought = [s for s in declared if s.get('brought')]
    if brought:
        declared = [s for s in declared if not s.get('brought')]
        notes.append(
            f"{', '.join(s['name'] for s in brought)} deferred to "
            f".precedent/SESSION_PRACTICES.md -- brought by the person "
            f"working here, not declared by this repository")
    tracked, deferred, more = _split_declared(root, declared)
    return tracked, brought + deferred, notes + more


def _split_declared(root, declared):
    """sources_for_tracked_block's split of what the repository DECLARES."""
    notes = []
    if repo_is_practice_source(root):
        deferred = [s for s in declared if s['level'] != 'repo-local'
                    and not _same_repository(s['path'], root)]
        tracked = [s for s in declared if s not in deferred]
        if deferred:
            notes.append(
                f"{', '.join(s['name'] for s in deferred)} deferred to "
                f".precedent/SESSION_PRACTICES.md -- this repo is a practice "
                f"set, so committing another source's text here would be a "
                f"second copy of it")
        return tracked, deferred, notes
    if repo_is_public(root):
        deferred = [s for s in declared if s['level'] in PRIVATE_LEVELS]
        tracked = [s for s in declared if s['level'] not in PRIVATE_LEVELS]
        if deferred:
            notes.append(
                f"{', '.join(s['name'] + ' (' + s['level'] + ')' for s in deferred)} "
                f"excluded from the loader block -- this repo declares "
                f"visibility: public, and the block is a tracked file, so "
                f"rendering a private source into it would publish its "
                f"practice text")
        return tracked, deferred, notes
    return list(declared), [], notes


def defers_any_source(root):
    """True when this repo's TRACKED loader block cannot carry everything
    precedent.json declares, so the standing instruction has to point at
    .precedent/SESSION_PRACTICES.md instead.

    Asked of sources_for_tracked_block() rather than re-derived, because
    there are two unrelated reasons a source gets deferred and keying the
    pointer off either one alone has already suppressed it in a whole class
    of repository -- see the comment at the pointer itself in
    build_loader_block(). (practice: registry-source-of-truth -- the split is
    decided in one place; this only reads its answer.)

    Never raises: a config that will not load leaves the block to this repo's
    own practices, which is exactly the case where nothing was deferred
    (practice: fail-gracefully)."""
    config = root / 'precedent.json'
    if not config.is_file():
        return False
    try:
        sys.path.insert(0, str(_ENGINE_DIR))
        import precedent_resolve as _pr
        declared = _pr.load_config(root)
    except Exception as e:
        print(f"build_views NOTICE: could not read the declared sources "
              f"({e}), so the standing instruction cannot say whether any of "
              f"them is deferred to .precedent/SESSION_PRACTICES.md.",
              file=sys.stderr)
        return False
    _tracked, deferred, _notes = sources_for_tracked_block(root, declared)
    # Only what THIS REPOSITORY declares. A set the person brings is deferred
    # too, but reaches their session through the session-start hook, and a
    # tracked file must read the same whoever regenerates it: counting it
    # here wrote the pointer for a person who brings a set and not for one
    # who does not, so in a repository that uses Precedent build_views.py
    # and the view sync disagreed, and its full check failed for everyone
    # who brings one (found 2026-10-03, migrating a real consumer's copy).
    return any(not s.get('brought') for s in deferred)


def source_levels_from_manifest(root):
    """{slug: level} read back out of a consuming repo's MANIFEST.json, or
    None where there is no such file.

    WHY THIS EXISTS. precedent_sync_views.py renders the loader block with
    `source_levels=` (it has the resolution in hand), and this tool's own
    main() rendered it WITHOUT -- so the two wrote different header lines
    for the same catalogue ("6 of 61 practices (6 universal)" vs "6 of 61
    practices"). In a consuming repo, where both are documented commands,
    that is a permanent unresolvable flip-flop: session start runs
    precedent_sync_views.py, then `build_views.py --check` -- which
    generated-artifact-provenance runs on every precedent_check.py --
    reports the block as hand-edited or stale, forever, whichever ran
    last. MANIFEST.json is precedent_materialize.py's own record of which
    source produced each practice, so reading it here makes the two
    renderers agree by construction rather than by both remembering to
    pass the same argument. Absent in a single-source repo (Precedent
    itself), where there are no levels to break down and the header is
    unchanged."""
    manifest = root / 'MANIFEST.json'
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None
    levels = {e['slug']: e['level'] for e in data.get('practices', [])
              if 'slug' in e and 'level' in e}
    return levels or None


class _BlockNotVerifiable(Exception):
    """A declared source is unreachable, so the block cannot be judged."""


def loader_practices(root, own_practices):
    """-> (practices, source_levels) for the AGENTS.md loader block.

    THE BLOCK RENDERS EVERY SOURCE THE REPO DECLARES, not just its own
    catalogue. Precedent's own repo declares three -- universal (itself),
    a shared set, and a repo-local one -- and rendered ONLY the universal
    one, so 65 of 65 universal practices reached the block while 0 of 41
    team and 0 of 11 individual did. The config said they were in force,
    the resolver agreed, and the one artifact a session actually reads
    listed none of them: a rule nothing can load is not in force, it is
    filed. Measured 2026-09-06, fixed here at Morgan's direction.

    A consuming repo gets this through precedent_sync_views.py, which
    materializes every source into one practices/ tree and leaves a
    MANIFEST.json for source_levels_from_manifest() to read. Precedent
    itself cannot take that route: its practices/ IS the universal source
    (`path: "."`), and precedent_materialize.py refuses a self-referential
    source by name, since its output directory would be that source's only
    copy. So the sources are resolved IN MEMORY here instead -- the same
    resolver, the same precedence, nothing written to disk.

    PRIVATE SOURCES ARE EXCLUDED FROM A PUBLIC REPO'S BLOCK. The block is
    a tracked file; in a public repo, writing it publishes whatever it
    contains, permanently. Universal and repo-local sources are already
    public -- one is the repo itself, the other lives in its own tree. Team
    and individual sets are private repositories whose practice text has
    never been published, so rendering their clauses here is publication by
    another route: precedent_resolve.py already refuses to let a shared repo
    DECLARE an individual source, because "naming it here leaks its
    existence and location", and this is the same disclosure by a different
    door. Precedent's own repo is the public case, and
    decisions/2026-09-06-precedent-binds-itself.md rejected multi-source
    generated views THERE on exactly this ground. A repo says which it is
    with `"visibility": "public"` in precedent.json; absent that, nothing is
    excluded -- which is the right default, because the repos that most need
    the multi-source block are the private consumers.
    """
    config = root / 'precedent.json'
    if not config.is_file():
        return own_practices, source_levels_from_manifest(root)
    try:
        sys.path.insert(0, str(_ENGINE_DIR))
        import precedent_resolve as _pr
    except Exception as e:                       # keep going, and say so
        print(f"build_views NOTICE: precedent_resolve.py did not import "
              f"({e}); the loader block covers this repo's own practices/ "
              f"only, not the other sources precedent.json declares.",
              file=sys.stderr)
        return own_practices, source_levels_from_manifest(root)

    try:
        declared = _pr.load_config(root)
    except Exception as e:
        print(f"build_views NOTICE: {config} did not resolve ({e}); the "
              f"loader block covers this repo's own practices/ only.",
              file=sys.stderr)
        return own_practices, source_levels_from_manifest(root)

    # Exclude, keep going, and SAY so on stderr rather than silently.
    declared, _deferred, _notes = sources_for_tracked_block(root, declared)
    for n in _notes:
        print(f"build_views: {n}.", file=sys.stderr)

    # Only this repo's own source: nothing to merge, keep the old path.
    if len(declared) <= 1:
        return own_practices, source_levels_from_manifest(root)

    # A brought set is left out of the block but still counts for what is in
    # force (precedent_resolve.resolve's `context`).
    res = _pr.resolve(declared, context=[s for s in _deferred if s.get('brought')])
    if res['missing']:
        # A declared source that does not resolve HERE makes the block
        # unverifiable, not stale. A shared source is a sibling clone and an
        # individual source resolves through a private user-level config, so
        # neither exists in a bare CI checkout -- and the committed block was
        # built where they did. Regenerating without them and calling the
        # difference "drift" would fail every CI run and every fixture, on
        # evidence the environment could not have. Found the moment this
        # went multi-source, 2026-09-06: the harness's own temp-dir fixtures
        # reported the freshly-generated block as hand-edited.
        for m in res['missing']:
            print(f"build_views NOTICE: the {m['level']} source "
                  f"{m['name']!r} is not available ({m['reason']}).",
                  file=sys.stderr)
        print("build_views: NOT VERIFIABLE -- the loader block is built from "
              "sources this environment cannot reach, so it can be neither "
              "confirmed current nor reported stale here. Re-run where every "
              "declared source resolves.", file=sys.stderr)
        raise _BlockNotVerifiable()
    resolved = res['practices']
    # scope: engine-dev practices (very-deep-check, full-practice-audit,
    # routing-audit -- an occasion that can only ever fire inside the
    # engine's own repository) are withheld from a CONSUMER's materialized
    # tree by precedent_materialize.py's own _is_engine_dev_scoped filter.
    # This in-memory multi-source resolve is the same resolve() over the
    # same declared sources, for the repo whose AGENTS.md is actually being
    # written -- and every 2+-source repo takes it, this repo's own included
    # (it declares repo-local alongside universal, so `len(declared) > 1`
    # here is not by itself "is this a consumer"). What distinguishes them
    # is whether one of the declared sources' own content directory IS this
    # repo: only there does practices/ physically hold the engine-dev files,
    # and only there is the session actually able to run what they describe
    # (practice: session-load-budget). Filtering unconditionally would have
    # dropped all three from this repo's own occasion index the moment it
    # took this branch; not filtering at all is the bug this guards --
    # without it, a real consumer's AGENTS.md disagreed permanently with
    # what precedent_sync_views.py (materialize.py + build_views.py
    # --agents-only) actually produces for the same tree.
    if not any(s['level'] == 'universal' and _same_repository(s['path'], root)
               for s in declared):
        resolved = {slug: v for slug, v in resolved.items()
                    if not _is_engine_dev_scoped(v['fm'])}
    practices = [(v['fm'], v['sections'],
                  placed_practice_file(root, slug, v['file']))
                 for slug, v in resolved.items()]
    levels = {slug: v['level'] for slug, v in resolved.items()}
    return practices, levels


# Set by `--budgets`: a cap overrun exits non-zero instead of writing with
# a warning. The full check's loader-within-caps runs it; nothing else does.
STRICT_BUDGETS = False
BUDGETS_NOT_VERIFIED = 'build_views --budgets NOT VERIFIED'


def _over_cap_warning(msg):
    """Say that a loader cap is exceeded, and that it is allowed onto
    pre-staging but not staging (see render_agents_md)."""
    print(f"build_views WARNING: {msg} Written anyway: the quick check lets "
          f"it through, but the full check refuses it (loader-within-caps), "
          f"so bring it under the cap before it goes further. Tell the "
          f"person.", file=sys.stderr)


def render_agents_md(practices, agents_md=None, source_levels=None,
                     defers_sources=False, occasion_budget=None):
    """-> (text, stats), where stats is (resident_tokens, n_resident,
    n_total) FROM THE BLOCK THIS RETURNED -- not re-derived.

    The stats used to be discarded here and the caller recomputed them for
    its own summary line, from a different practice list: `main()` passed
    the single-source catalogue where the block itself had been built from
    the multi-source resolve. So the run reported "resident 7/69" while the
    file it had just written said "7 of 72", and neither number knew about
    the other (found 2026-09-07). Returning them removes the second
    computation rather than making two computations agree, which is the
    only version of this that cannot drift again."""
    agents_md = agents_md if agents_md is not None else AGENTS_MD
    original = agents_md.read_text(encoding='utf-8')
    # The block's links are relative to the file it lands IN, which is not
    # always this engine's own ROOT: `--repo DIR` renders another repo's
    # AGENTS.md, and a resident Rule's sibling citation has to be repointed
    # for that repo's root, not this one's.
    # OVER A CAP, THE BLOCK IS STILL WRITTEN, with a warning (Morgan,
    # 2026-09-30, strength: decided: "remove that limit for pre-staging and
    # instead just have it give the session user a warning, including
    # telling the user that it needs to be fixed before it can get onto
    # staging; but no change for the rules for staging"). This used to exit
    # here, so the block could not be regenerated, and the pre-staging
    # check then refused the push as "views not regenerated": branch after
    # branch stopped short of pre-staging on the same cap. The refusal now
    # belongs to the full check, which runs at the Debut: its
    # loader-within-caps check runs `build_views.py --budgets`, which is
    # the one caller still stopped here (STRICT_BUDGETS).
    resident_budget = None
    occ_budget = (occasion_budget if occasion_budget is not None
                  else OCCASION_INDEX_BUDGET_TOKENS)
    while True:
        try:
            block, tokens, n_resident = build_loader_block(
                practices, source_levels=source_levels,
                defers_sources=defers_sources, block_dir=agents_md.parent,
                budget_tokens=resident_budget, occasion_budget_tokens=occ_budget)
            break
        except OccasionIndexBudgetExceeded as e:
            msg = str(e)
            if STRICT_BUDGETS:
                sys.exit(f"build_views FAIL: {msg}")
            _over_cap_warning(msg)
            occ_budget = e.tokens
        except ResidentBudgetExceeded as e:
            msg = (f"resident block is ~{e.tokens} tokens, over the "
                   f"{e.budget}-token hard cap -- demote or retire a resident "
                   f"practice before adding another.")
            if STRICT_BUDGETS:
                sys.exit(f"build_views FAIL: {msg}")
            _over_cap_warning(msg)
            resident_budget = e.tokens
    if BEGIN_MARKER not in original or END_MARKER not in original:
        sys.exit(f"build_views FAIL: {agents_md} has no "
                 f"{BEGIN_MARKER} / {END_MARKER} markers to regenerate between.")
    pre = original[:original.index(BEGIN_MARKER)]
    post = original[original.index(END_MARKER) + len(END_MARKER):]
    return pre + block + post, (tokens, n_resident, len(practices))



def _upstream_doc_pointer():
    """The " see X for the format and Y for the design" tail of MAP.md's
    catalogue line -- only when those documents actually exist here.

    This ran unconditionally and named two of BestPractice's OWN documents,
    which no vendoree has. Nothing noticed while only BestPractice generated
    a MAP.md; the moment an engine refresh brought this generator to three
    practice sets (2026-09-06), each one generated a map with two broken
    relative links, and each one's own light check reported them -- findings
    against a file the repo did not write, naming files it is not supposed
    to have. A generator shared across repositories cannot assume the
    generating repo's own prose."""
    tail = []
    if (ROOT / 'spec' / 'PRACTICE_FORMAT.md').is_file():
        tail.append("[spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) for the format")
    if (ROOT / 'spec' / 'PRACTICE_ENGINE_PLAN.md').is_file():
        tail.append("[PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md)"
                    " for the design")
    return (" See " + " and ".join(tail) + ".") if tail else ""


def _withdrawn_reason(sections):
    """One line from a withdrawn practice's ## Story: the WHY, not the what.

    The reason is the load-bearing field, and it is the one thing history
    cannot hand back. Anyone can recover a rule's text from a file that was
    never deleted; nobody can recover the argument for dropping it once the
    person who made it has moved on. So this pulls the Story's first
    sentence rather than the Rule's.
    """
    # LOWERCASE key: _read_practice_file() normalises headings, so it is
    # 'story', not 'Story'. Getting this wrong reads as an ABSENT Story
    # rather than as a lookup miss -- the first run of this table accused
    # catalogue-carries-stories of letting an empty one through, on a
    # practice whose Story is one of the better ones in the catalogue.
    story = (sections or {}).get('story') or ''
    for para in story.split('\n\n'):
        para = ' '.join(para.split())
        # A BULLET is "- " or "* " -- with the space. Skipping a bare '*'
        # swallows every paragraph that opens in bold, which is how this
        # catalogue's Story sections conventionally open ("**Retired
        # 2026-09-07, by Morgan...**"). First run reported "no ## Story" for
        # a practice carrying an excellent one.
        if not para or para.startswith(('|', '#', '- ', '* ')):
            continue
        # Links out BEFORE looking for the sentence end or cutting at 400:
        # either cut can land inside one ("[e.g. Foo](x.md)" splits at its
        # own ". F"), and this row already links the practice file itself.
        para = summary_text.unlink(para)
        # First sentence, but never a fragment: a ". " inside "e.g." or a
        # version number would otherwise cut mid-thought.
        cut = para.find('. ')
        while 0 < cut < len(para) - 2 and not para[cut + 2].isupper():
            nxt = para.find('. ', cut + 1)
            if nxt == -1:
                break
            cut = nxt
        line = para[:cut + 1] if cut > 0 else para
        return line if len(line) <= 400 else summary_text.one_line(line, 397, '...')
    return ''


def _render_withdrawn(withdrawn):
    """The catalogue's own memory of what it stopped believing.

    WHY THIS EXISTS. A practice that is `retired` or `deduplicated` keeps its
    file -- the rule, the Story, the reasoning -- and the loader simply stops
    putting it in force. That was already true, and it was undiscoverable:
    the generated views list only what is in force, so the ONLY way to reach a
    withdrawn practice was to already know its slug. Morgan, 2026-09-07:
    "I could see us wanting to potentially re-evaluate and learn from deleted
    practices one day, not to mention, for the record."

    Deliberately DERIVED rather than a directory the files get moved into,
    which was the other option on the table. Moving them would break every
    sibling link between practice files -- they cite each other by bare
    filename, and those links travel into every consuming repo, where nobody
    can repoint them. It would also put the fact in two places at once (a
    path AND a status field) with nothing deciding which wins, and it would
    hide withdrawn rules from the grep a person doing prior-art research
    actually runs. A generated table costs none of that and goes stale only
    if the build stops running.
    """
    if not withdrawn:
        # Said, not omitted: an empty section and a missing section look the
        # same to a reader, and only one of them means "nothing has been
        # withdrawn".
        return [
            "## Withdrawn practices",
            '',
            "None. No practice in this catalogue has been retired or "
            "deduplicated yet -- when one is, its file stays and it is listed "
            "here.",
        ]
    lines = [
        "## Withdrawn practices",
        '',
        f"{len(withdrawn)} practice file(s) here are **not in force** and are "
        "left out of every table above. **The files are kept on purpose** -- a "
        "withdrawn rule and the argument against it are worth re-reading, and "
        "`retired` is not a synonym for deleted (that is "
        "`decommission-deletes-files`, and it is about mechanisms, not rules). "
        "Read one in full with `python3 tools/precedent_show.py SLUG`.",
        '',
        "| Practice | Status | Now in force at | Why it was withdrawn |",
        "|---|---|---|---|",
    ]
    for fm, sections, _f in sorted(withdrawn, key=lambda t: t[0].get('slug', '')):
        slug = _json_str(fm.get('slug', '')) or '?'
        status = practice_status(fm)
        target = _json_str(fm.get('in_force_at', '')) or ''
        if target in ('', 'none'):
            where = '— (nowhere)'
        elif target == 'engine':
            where = 'the engine'
        elif (pathlib.Path(_f).parent / f'{target}.md').is_file():
            where = f"[{target}](practices/{target}.md)"
        else:
            # THE SUCCESSOR USUALLY LIVES IN ANOTHER SOURCE, and linking it
            # as if it were local writes a broken relative link into a
            # generated file. `in_force_at:` names a slug, not a source, and
            # deduplication is precisely the case where a shared or individual
            # rule was dropped because a UNIVERSAL one already said it -- so
            # the successor is in a different repo by definition, more often
            # than not.
            #
            # Found 2026-09-08, the first time the withdrawn table (landed
            # that day) was regenerated in a shared set: `header-caps` names
            # `headline-capitalization`, which is universal, and the table
            # linked `practices/headline-capitalization.md` into a repo that
            # has no such file. The set then FAILED ITS OWN light-check on a
            # broken relative link, in a file it is told never to hand-edit
            # -- unfixable from inside that repo.
            #
            # Named, not linked: a reader can find the slug with
            # precedent_show, and a link that resolves to nothing is worse
            # than no link (practice: doc-references-are-links).
            where = (f"`{target}` — in another source; "
                     f"`python3 tools/precedent_show.py {target}`")
        # THE STORY'S LINKS ARE DROPPED, NOT REPOINTED. This lands in MAP.md
        # at the REPO ROOT, and a Story is written inside practices/, so a
        # sibling citation like `[x](x.md)` resolves to a root-level `x.md`
        # that does not exist. From 2026-09-21 this repointed them with
        # _place_rule_links (reported by a session auditing four practice
        # sets: one set's MAP.md carried a broken link to
        # reply-fits-one-screen.md that regenerating did not clear). Since
        # 2026-09-25 _withdrawn_reason() unlinks the sentence instead, before
        # its 400-character cut: a cut could still land inside a repointed
        # link, and the row's first cell already links the practice whose
        # Story this is (tools/summary_text.py says why every summary field
        # goes this way).
        _reason_raw = _withdrawn_reason(sections)
        reason = _reason_raw.replace('|', '\\|') or \
            '*(no ## Story -- catalogue-carries-stories should have caught this)*'
        lines.append(f"| [{slug}](practices/{slug}.md) | {status} | {where} | {reason} |")
    return lines


def _engine_scope_files():
    """-> the vendored engine's own *.py filenames sitting in `_ENGINE_DIR`,
    or None when `_ENGINE_DIR` IS the engine's home (no ENGINE_MANIFEST.json
    -- see repo_is_practice_source()'s own note: that file is the only
    durable signal a vendored copy carries about itself; its absence means
    every *.py here really is this project's own tooling, same as always).

    render_map_md()'s "every engine file is described" assertion used to
    run over every *.py sitting beside this script (`_ENGINE_DIR.glob`),
    which cannot tell the vendored engine apart from a CONSUMER's own local
    scripts living in that identical directory -- `tools/` in a consumer
    repo holds both, side by side, and the glob has no way to know which is
    which. Reported 2026-09-15: a vendor update made
    generated-artifact-provenance start running this in full mode for a
    real four-source consumer for the first time (previously only its
    AGENTS.md loader block was checked there), and it hard-exited on that
    consumer's own build_business_html.py, light_check.py,
    voice_pack_sync.py and report_automation_issue.py -- files this table
    was never responsible for describing; MAP.md's "## The engine" table
    documents the engine's own code inventory, and a repo's local tools are
    out of scope for it by definition. ENGINE_MANIFEST.json's own `files`
    list is what precedent_vendor_engine.py actually wrote into this
    directory for this install's `kind` (source or consumer), so reading it
    back is the authoritative answer rather than a second copy of
    ENGINE_FILES/CONSUMER_ENGINE_FILES that could drift from it."""
    mf = _ENGINE_DIR / 'ENGINE_MANIFEST.json'
    if not mf.is_file():
        return None
    try:
        files = json.loads(mf.read_text(encoding='utf-8')).get('files', [])
    except (OSError, ValueError):
        return None
    return {f for f in files if f.endswith('.py')}


def generated_label(generated_by, edit_instead, regenerate):
    """-> the frontmatter lines a wholly generated Markdown file opens with.

    WHY A LABEL AND NOT A COMMENT (Morgan, 2026-09-29, strength: assented).
    The hidden `<!-- GENERATED ... -->` comment never showed on GitHub, so a
    reader there had no sign the file was generated, and checks had to
    search the text for a phrase. GitHub renders frontmatter as a small
    table at the top of the page. The wording is his: "Generated by X.
    Don't edit here; edit Y instead, then run Z." -- true under both
    generated-artifact-provenance and derived-file-marker, and it says
    where the change belongs."""
    note = (f"Generated by {generated_by}. Don't edit here; edit "
            f"{edit_instead} instead, then run {regenerate}.")
    return ['---', f'generated_by: {generated_by}',
            f'edit_instead: "{edit_instead}"',
            'note: "' + note.replace('"', "'") + '"', '---']


# WHERE_THINGS_ARE.md AND AGENTS.md'S SHORT TABLE, FROM ONE SOURCE
# (spec/GENERATED_FILES_PLAN.md step 2; Morgan, 2026-10-03: generated files
# are never hand-edited, and a copy "should either cite the original instead
# of repeating it OR make sure they are kept in sync"). The short table was a
# hand copy of a dozen rows of the full one, and by then several read
# differently -- the full one still named the reply's closing section by its
# old name. Both render from where_things_are.json now; a repository without
# that file has neither, and nothing here touches it.
WHERE_SOURCE = 'where_things_are.json'
WHERE_PAGE = 'WHERE_THINGS_ARE.md'
QUICK_BEGIN = '<!-- BEGIN GENERATED: where-things-are -->'
QUICK_END = '<!-- END GENERATED: where-things-are -->'
_ROW_LINK = re.compile(r'\]\(([^)\s]+)\)')


def _where_source(root):
    """-> where_things_are.json's content, or None when the repository has
    none. Every relative link in a row must resolve, or the build stops
    naming each one: a row that sends a reader to a file that moved is the
    staleness this page exists to prevent."""
    path = pathlib.Path(root) / WHERE_SOURCE
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as e:
        sys.exit(f"build_views FAIL: {WHERE_SOURCE} is not valid JSON: {e}")
    broken = []
    for row in data.get('rows') or []:
        for cell in (row.get('looking_for', ''), row.get('go_to', '')):
            for target in _ROW_LINK.findall(cell):
                if re.match(r'[a-z]+:|#', target):
                    continue
                rel = target.split('#', 1)[0]
                if rel and not (pathlib.Path(root) / rel).exists():
                    broken.append(f"{row.get('looking_for', '')[:60]!r} -> {target}")
    if broken:
        sys.exit(f"build_views FAIL: {WHERE_SOURCE} links to paths that do not "
                 f"exist -- fix the row there, then run this again:\n  "
                 + '\n  '.join(broken))
    return data


def _where_row(row):
    return f"| {row['looking_for']} | {row['go_to']} |"


def render_where_things_are(data):
    """-> WHERE_THINGS_ARE.md: the label, the intro and every row."""
    lines = [*generated_label('tools/build_views.py', WHERE_SOURCE,
                              'python3 tools/build_views.py'),
             '', '# Where things are — the full index', '',
             *data.get('intro', []), '',
             '| Looking for… | Go to |', '|---|---|',
             *(_where_row(r) for r in data.get('rows') or [])]
    return '\n'.join(lines) + '\n'


def splice_quick_index(text, data):
    """-> `text` (AGENTS.md) with the rows marked `quick` written between
    QUICK_BEGIN and QUICK_END, in their `quick` order, and a last row
    pointing at the full page."""
    if QUICK_BEGIN not in text or QUICK_END not in text:
        sys.exit(f"build_views FAIL: {WHERE_SOURCE} exists but AGENTS.md has no "
                 f"{QUICK_BEGIN} / {QUICK_END} markers for its short table.")
    quick = sorted((r for r in data.get('rows') or [] if r.get('quick')),
                   key=lambda r: r['quick'])
    block = [QUICK_BEGIN, '| Looking for… | Go to |', '|---|---|',
             *(_where_row(r) for r in quick),
             f'| Anything else — the full index | [{WHERE_PAGE}]({WHERE_PAGE}) |',
             QUICK_END]
    pre = text[:text.index(QUICK_BEGIN)]
    post = text[text.index(QUICK_END) + len(QUICK_END):]
    return pre + '\n'.join(block) + post


# A REPOSITORY'S OWN SECTIONS (spec/GENERATED_FILES_PLAN.md step 5; Morgan,
# 2026-10-03: MAP.md and GLOSSARY.md are generated in every repository, and
# a repository that uses Precedent keeps what it wrote). What a repository
# says about itself -- its deliverables, who depends on it, its own names --
# lives in MAP.source.md and GLOSSARY.source.md, written by hand, and is
# copied into the generated view word for word, ahead of the sections
# generated from the catalogue and the engine. A repository with neither
# file gets the views exactly as before.
MAP_SOURCE = 'MAP.source.md'
GLOSSARY_SOURCE = 'GLOSSARY.source.md'

# THE SOURCE AS A DIRECTORY (Alex, 2026-10-04: "should we modify map.md to be
# a directory so we don't have so many collisions when multiple threads are
# running?"). A one-file source is edited by every branch that adds a row, so
# two branches adding rows to the same table conflict on merge, and the
# generated view conflicts after them. The same text may instead live in a
# directory beside it -- MAP.source/ for MAP.source.md, GLOSSARY.source/ for
# GLOSSARY.source.md -- one file per entry, so two branches that each add a
# row add two files and never meet. todo/ and gotchas/ solved the same
# collision the same way. The directory is assembled in name order:
#   - a top-level FILE is a block of text, copied as it is;
#   - a top-level DIRECTORY is a section: its _head.md (the heading, prose
#     and table header), then every other .md file in it as the rows that
#     follow with no blank line between them, then its _tail.md after a
#     blank line;
#   - blocks are separated by one blank line.
# Name entries with a numeric prefix with gaps (0010-, 0020-) so a new one
# can go between two others. `precedent_migrate_views.py --split` turns a
# one-file source into a directory, refusing any section it cannot split
# without changing a word. A repository may have the file or the directory,
# never both.
SOURCE_DIR_SUFFIX = '.source'
SECTION_HEAD = '_head.md'
SECTION_TAIL = '_tail.md'


def source_dir_name(name):
    """'MAP.source.md' -> 'MAP.source' (the directory form of a source)."""
    return name[:-len('.md')] if name.endswith('.md') else name


def own_source_path(root, name):
    """-> the path of a repository's own source for `name` (the file or its
    directory form), or None when it has neither. Both at once is refused:
    which one is the truth would be a guess."""
    root = pathlib.Path(root or ROOT)
    f, d = root / name, root / source_dir_name(name)
    if f.is_file() and d.is_dir():
        sys.exit(f"build_views FAIL: both {name} and {d.name}/ exist; keep one "
                 f"(precedent_migrate_views.py --split moves the file into the "
                 f"directory).")
    if f.is_file():
        return f
    if d.is_dir():
        return d
    return None


def has_own_source(root, name):
    """True when a repository has its own source for `name`, as a file or a
    directory -- what every 'is this view generated here?' test asks."""
    return own_source_path(root, name) is not None


def own_source_label(root, name):
    """-> how the generated label names the source: the file, or the
    directory with a trailing slash."""
    p = own_source_path(root, name)
    return f"{p.name}/" if p is not None and p.is_dir() else name


def _entries(d):
    return sorted((c for c in d.iterdir()
                   if not c.name.startswith('.') and (c.is_dir() or c.suffix == '.md')),
                  key=lambda c: c.name)


def _read_block(path):
    return path.read_text(encoding='utf-8').strip('\n')


def assemble_source_dir(d):
    """-> the text of a source directory, assembled by the rules above."""
    blocks = []
    for child in _entries(pathlib.Path(d)):
        if child.is_dir():
            files = [f for f in _entries(child) if f.is_file()]
            head = [f for f in files if f.name == SECTION_HEAD]
            tail = [f for f in files if f.name == SECTION_TAIL]
            rows = [f for f in files if f.name not in (SECTION_HEAD, SECTION_TAIL)]
            parts = [_read_block(head[0])] if head else []
            if rows:
                parts.append('\n'.join(_read_block(r) for r in rows))
            text = '\n'.join(p for p in parts if p)
            if tail:
                text = f"{text}\n\n{_read_block(tail[0])}" if text else _read_block(tail[0])
            if text:
                blocks.append(text)
        else:
            text = _read_block(child)
            if text:
                blocks.append(text)
    return '\n\n'.join(blocks)


def _own_source(root, name):
    """-> a repository's own hand-written section text, or None."""
    path = own_source_path(root, name)
    if path is None:
        return None
    if path.is_dir():
        return assemble_source_dir(path)
    return path.read_text(encoding='utf-8').rstrip('\n')


def _vendored_engine(root):
    """True when `root` carries a vendored copy of the engine -- a practice
    set or a repository that uses Precedent -- rather than being the
    engine's own repository. Only there may MAP.md introduce itself as
    Precedent's own map: until 2026-10-03 every generated map, in every set
    and consumer, opened with this repository's introduction."""
    root = pathlib.Path(root or ROOT)
    return any((root / d / 'ENGINE_MANIFEST.json').is_file()
               for d in ('tools', 'process/upstream/tools'))


def render_map_md(practices, withdrawn=(), root=None):
    by_tier = collections.Counter(fm.get('tier') for fm, _s, _f in practices)
    own = _own_source(root, MAP_SOURCE)
    # The label every generated file opens with (tools/generated_files.json
    # lists them all): visible as a small table on GitHub, read by
    # precedent_check.py's generated-files-registered (Morgan, 2026-09-29).
    head = ([*generated_label('tools/build_views.py',
                              f'{own_source_label(root, MAP_SOURCE)} and practices/*.md',
                              'python3 tools/build_views.py'), '', own, '']
            if own is not None else [
        *generated_label('tools/build_views.py', 'practices/*.md',
                         'python3 tools/build_views.py'),
        '',
        "# Repository map — where to find things",
        '',
        *([("This repository's map of the practice catalogue in force here and "
            "the engine's own code, generated, never hand-edited. What this "
            "repository says about itself goes in MAP.source.md, which this map "
            "then carries first.")]
          if _vendored_engine(root) else [
        "Precedent's own repo map (PRACTICE_ENGINE_PLAN.md, Sequence row 2: "
        '"make AGENTS.md, MAP.md, GLOSSARY.md and the index generated"). '
        "For the plan and format spec, see AGENTS.md's quick index instead — this file "
        "indexes the practice catalogue and the engine's own code, not the whole repo's prose."]),
        ''])
    lines = [
        *head,
        "## The practice catalogue",
        '',
        f"`practices/` holds {len(practices)} practice files "
        f"({by_tier.get('resident', 0)} resident, {by_tier.get('on-demand', 0)} on-demand). "
        "One file per practice." + _upstream_doc_pointer(),
        '',
        "| Practice | Tier | Occasion / scope |",
        "|---|---|---|",
    ]
    for fm, _sections, _f in sorted(practices, key=lambda t: t[0]['slug']):
        occasion = _json_str(fm.get('occasion', '""'))
        applies_to = _json_list(fm.get('applies_to', '[]'))
        scope = occasion if occasion else ', '.join(applies_to)
        lines.append(f"| [{fm['slug']}](practices/{fm['slug']}.md) | {fm.get('tier')} | {scope} |")
    lines += ['']
    lines += _render_withdrawn(withdrawn)
    lines += [
        '',
        "## The engine",
        '',
        "| Path | What it is |",
        "|---|---|",
    ]
    engine_scope = _engine_scope_files()
    engine_names = sorted(p.name for p in _ENGINE_DIR.glob('*.py'))
    if engine_scope is not None:
        engine_names = [n for n in engine_names if n in engine_scope]
    for name in engine_names:
        desc = tool_summary(_ENGINE_DIR / name)
        if not desc:
            # Every engine file is described, or the build stops: this table
            # once silently omitted over half of tools/, including
            # precedent_check.py and precedent_gate.py (a 2026-09-01 audit).
            sys.exit(f"build_views FAIL: tools/{name} has no module docstring "
                     f"to describe it in MAP.md. Give it one whose first line "
                     f"says what it is -- that line is its row in the map.")
        lines.append(f"| [tools/{name}](tools/{name}) | {desc} |")
    lines.append('')
    return '\n'.join(lines) + '\n'


def tool_summary(path):
    """-> the first line of a tool's own module docstring: what MAP.md's
    "## The engine" table says about it, or None when it has none.

    Read from the tool itself since 2026-10-03 (spec/GENERATED_FILES_PLAN.md
    step 1, Morgan: generated files are never hand-edited; a change goes
    into their sources). It used to be TOOLS_DESCRIPTIONS, a hand-typed
    table here: a second copy of what each tool already says about itself,
    edited by hand inside the generator. Each entry moved into its tool as
    that first line, word for word, so the map did not change. Parsed, never
    imported: a tool's imports are not this generator's business."""
    import ast
    try:
        doc = ast.get_docstring(ast.parse(pathlib.Path(path).read_text(encoding='utf-8')))
    except (OSError, SyntaxError, ValueError):
        return None
    first = (doc or '').strip().splitlines()
    return first[0].strip() if first and first[0].strip() else None


def render_glossary_md(practices, root=None):
    root = pathlib.Path(root) if root else ROOT
    terms = []
    for fm, _sections, _f in practices:
        raw = fm.get('defines', '[]')
        for term in _json_list(raw):
            terms.append((term, fm['slug']))
    terms.sort(key=lambda t: t[0].lower())
    own = _own_source(root, GLOSSARY_SOURCE)
    lines = [
        *generated_label('tools/build_views.py',
                         (f"{own_source_label(root, GLOSSARY_SOURCE)} and the defines: field of practices/*.md"
                          if own is not None else
                          "the defines: field of practices/*.md"),
                         'python3 tools/build_views.py'),
        '',
        *([own, '', "## Names the practices define"] if own is not None
          else ["# Canonical names"]),
        '',
        "Built from every practice's `defines:` frontmatter field -- the terms that "
        "practice owns (PRACTICE_ENGINE_PLAN.md, The Practice File). A term with no row "
        "here yet is simply a practice that hasn't had its `defines:` filled in; this is "
        "not the exhaustive vocabulary of the repo (that's the plan's own Vocabulary "
        "table), only what the practice catalogue itself has claimed so far.",
        '',
        "| Term | Defined in |",
        "|---|---|",
    ]
    if not terms:
        lines.append("| *(none yet)* | — |")
    else:
        for term, slug in terms:
            lines.append(f"| {term} | [{slug}](practices/{slug}.md) |")
    lines.append('')

    # ENGINE VOCABULARY, from its own registry (practice:
    # registry-source-of-truth). These are the words the MECHANISM is made
    # of -- `source`, `level`, `gate`, `slug` -- which no single practice
    # owns, so `defines:` has nowhere to put them and they went undefined
    # while being the most-used terms in the project. Measured 2026-09-08:
    # `source` 1152 uses, `gate` 709, `slug` 372, `level` 342, none defined.
    engine_terms = _engine_glossary_terms(root)
    if engine_terms:
        lines += [
            "## Engine vocabulary",
            '',
            "The words the mechanism itself is made of. No single practice "
            "owns these, so they cannot come from a `defines:` field -- they "
            "are declared in [tools/glossary_terms.json](tools/glossary_terms.json) "
            "and rendered here. **Everything above is a term some practice "
            "claimed; everything below is a term the engine needs you to "
            "know before any practice makes sense.**",
            '',
            "| Term | What it means | Where it is spelled out |",
            "|---|---|---|",
        ]
        for t in engine_terms:
            defn = t['definition'].replace('|', '\\|')
            lines.append(f"| **{t['term']}** | {defn} | "
                         f"{_travel_link(root, t.get('see', ''))} |")
        lines.append('')
    return '\n'.join(lines)


# WHERE A GLOSSARY ROW POINTS, IN A REPOSITORY THAT IS NOT THIS ONE.
# The registry names its targets as paths in the upstream tree
# (`practices/source-naming.md`, `spec/LOADER.md`), and this block is
# rendered into every source set's own GLOSSARY.md by its vendored copy of
# this file -- where `spec/` does not exist and most of `practices/` is a
# different catalogue. Emitted verbatim, those rows are eight dead links in
# a generated file nobody hand-edits, which is what a real shared set's own
# light check reported on 2026-09-11, immediately after a vendor update.
#
# So the same rule practice-links-travel already states for practice files:
# link it where it lives, and point at upstream when it does not travel.
# The upstream repository and branch come from the vendored engine's own
# ENGINE_MANIFEST.json -- the only file that knows where this copy came
# from -- and with no manifest and no local file the link markup is dropped
# rather than guessed at, leaving a backticked path that misleads nobody.
def _stays_home(root, see):
    """True when `see` is a file this repo keeps out of the catalogue copy
    it ships (tools/checkin.py's VENDORING_RULES), so a relative link to it
    from a shipped file is broken in every consumer (2026-10-01)."""
    if (pathlib.Path(root) / 'tools' / 'ENGINE_MANIFEST.json').is_file():
        return False          # a consumer or set receives the copy, ships none
    try:
        import checkin
        rule = checkin.vendoring_rule(see)
    except Exception:                                         # noqa: BLE001
        return False
    return bool(rule) and rule[1] is False


def _travel_link(root, see):
    if not see:
        return '—'
    root = pathlib.Path(root) if root else ROOT
    if (root / see).exists() and _stays_home(root, see):
        try:
            branch = json.loads((root / 'precedent.json').read_text(
                encoding='utf-8')).get('base_branch') or 'staging'
        except (OSError, ValueError):
            branch = 'staging'
        return f'[{see}](https://github.com/alex137/BestPractice/blob/{branch}/{see})'
    if (root / see).exists():
        return f'[{see}]({see})'
    try:
        man = json.loads((root / 'tools' / 'ENGINE_MANIFEST.json')
                         .read_text(encoding='utf-8'))
        repo = str(man.get('source_repo') or '').rstrip('/')
        branch = str(man.get('source_branch') or '')
    except (OSError, ValueError):
        repo = branch = ''
    if repo and branch:
        return f'[{see}]({repo}/blob/{branch}/{see})'
    return f'`{see}`'


def _engine_glossary_terms(root=None):
    """-> [dict] the engine-vocabulary rows, or [] when the registry is
    absent.

    It IS vendored (precedent_vendor_engine.ENGINE_FILES), so the normal
    case is present. Absent means a vendored engine older than 2026-09-08,
    when the file was added -- and a glossary that refused to build there
    would break the adopter who is furthest behind, which is the one least
    able to fix it (practice: fail-gracefully)."""
    reg = (pathlib.Path(root) if root else ROOT) / 'tools' / 'glossary_terms.json'
    if not reg.is_file():
        return []
    try:
        data = json.loads(reg.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    return [t for t in data.get('terms', [])
            if t.get('term') and t.get('definition')]


def main():
    argv = sys.argv[1:]
    repo = None
    if '--repo' in argv:
        i = argv.index('--repo')
        if i + 1 >= len(argv):
            sys.exit("build_views FAIL: --repo needs a value.")
        repo = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    root = pathlib.Path(repo).resolve() if repo else ROOT
    # A run from inside a different repo reads THIS repo, silently -- say so
    # (precedent_which_repo.py; gotcha-2026-09-29). Warn only; never fatal.
    if repo is None:
        try:
            import precedent_which_repo
            precedent_which_repo.warn_if_elsewhere(ROOT, 'build_views.py',
                                                   repo_flag=True)
        except Exception:                                    # noqa: BLE001
            pass
    practices_dir = root / 'practices'
    agents_md = root / 'AGENTS.md'
    map_md = root / 'MAP.md'
    glossary_md = root / 'GLOSSARY.md'
    # Graceful degradation, not a crash: the loader block is written INTO an
    # existing AGENTS.md, between markers the install step puts there. A
    # repo that has not instantiated it yet (INSTALL.md sec.0 step 4 /
    # sec.1 step 2) used to get a bare FileNotFoundError from deep inside
    # the renderer, which reads as the generator being broken rather than
    # as one install step not done.
    if not agents_md.is_file():
        sys.exit(f"build_views FAIL: {agents_md} does not exist. Instantiate "
                 f"it from templates/AGENTS.md.loader.template (or "
                 f"templates/AGENTS.md.template on the classic layout), "
                 f"keeping its BEGIN/END GENERATED markers, then re-run.")

    check = '--check' in argv
    # --agents-only: regenerate just AGENTS.md's loader block (resident
    # block, occasion index, standing instruction), skip MAP.md and
    # GLOSSARY.md. render_map_md()'s engine table and "this repo
    # is BestPractice itself" prose are specific to this repo; a team or
    # individual source repo vendoring this same engine for its OWN
    # catalogue (practice: layered-practice-packs -- every level needs the
    # same resident/occasion-index treatment universal already gets, not
    # just a hand-written README describing the practice list in prose)
    # wants only the loader-block mechanism, not BestPractice's own MAP/
    # GLOSSARY conventions.
    agents_only = '--agents-only' in argv
    # --views-only: MAP.md, GLOSSARY.md and WHERE_THINGS_ARE.md, never
    # AGENTS.md. In a repository that uses Precedent the loader block is the
    # view sync's to write (precedent_sync_views.py renders it across every
    # source); rebuilding the views must not rewrite it from practices/
    # alone. Found 2026-10-03 migrating a real consumer: a full run here
    # left AGENTS.md different from a fresh sync.
    views_only = '--views-only' in argv
    global STRICT_BUDGETS
    STRICT_BUDGETS = '--budgets' in argv
    practices = load_practices(practices_dir)
    too_long = over_long_index_clauses(practices, root)
    if too_long:
        sys.exit('build_views FAIL: index_clause over the '
                 f'{INDEX_CLAUSE_MAX}-character limit -- shorten it:\n' +
                 '\n'.join(f'  {f.name}: {n} characters' for f, n in too_long))

    # MAP.md and GLOSSARY.md stay this repo's OWN catalogue -- they document
    # the set it publishes. Only the loader block covers every declared
    # source, because that block is what a session actually loads.
    try:
        block_practices, levels = loader_practices(root, practices)
    except _BlockNotVerifiable:
        # Exit 0: not verified is not a failure, and not a pass either --
        # the reason is already on stderr, in those words.
        if check:
            return 0
        # --budgets only reads, so it is --check's case, not a refused write
        # (2026-09-30: a consumer's GitHub test runs on a bare checkout with
        # no sibling practice sets, and failed loader-within-caps on the
        # write refusal below). It says it measured nothing, in words
        # precedent_check.py turns into COULD NOT VERIFY, never a pass.
        if STRICT_BUDGETS:
            print(BUDGETS_NOT_VERIFIED + ": a declared source is not "
                  "reachable here, so the loader block's caps were not measured")
            return 0
        sys.exit("build_views FAIL: refusing to WRITE a loader block from an "
                 "incomplete source set -- that would silently drop every "
                 "practice the unreachable sources contribute. Make them "
                 "resolvable, then re-run.")
    # Whatever the tracked block could not carry -- a private source in a
    # public repo, or another repository's catalogue in a practice set --
    # reaches the session only through the untracked file, so the standing
    # instruction has to point at it.
    _cap, _cap_why = occasion_cap(root)
    new_agents, (block_tokens, n_resident, n_total) = render_agents_md(
        block_practices, agents_md, source_levels=levels,
        defers_sources=defers_any_source(root), occasion_budget=_cap)
    _own = own_occasion_allowance(root)
    if _own is not None:
        share = occasion_share(practices)
        if share > _own:
            (sys.exit if STRICT_BUDGETS else _over_cap_warning)(
                f"{'build_views FAIL: ' if STRICT_BUDGETS else ''}"
                f"this source's share of every consumer's "
                f"occasion index is ~{share} tokens, over its {_own}-token "
                f"allowance (occasion_share_tokens in precedent-source.json). "
                f"A consumer carries this share, with every other source it "
                f"declares, under a cap that is the sum of their allowances, "
                f"and cannot shrink it. Give a file-bound practice a real "
                f"applies_to glob and drop its occasion:, or shorten the "
                f"longest index_clause values; raising the allowance is the "
                f"person's decision, with the reason recorded there.")
    if STRICT_BUDGETS:
        print("build_views --budgets OK: the resident block, the occasion "
              "index and this source's occasion share are within their caps")
        return 0
    where = _where_source(root)
    if where is not None:
        new_agents = splice_quick_index(new_agents, where)
    targets = [] if views_only else [(agents_md, new_agents)]
    if where is not None and not agents_only:
        targets.append((root / WHERE_PAGE, render_where_things_are(where)))
    if not agents_only:
        # Load a SECOND time without the in-force filter: load_practices()
        # drops withdrawn practices by design (that filter is what stopped a
        # retired rule being emitted into the loader block), so the only way
        # to list them is to ask for everything and subtract.
        _all = load_practices(practices_dir, in_force_only=False)
        _in_force = {id(t) for t in practices}
        withdrawn = [t for t in _all if not is_in_force(t[0])]
        for path, render in ((map_md, lambda: render_map_md(practices, withdrawn, root)),
                             (glossary_md, lambda: render_glossary_md(practices, root))):
            # A view whose own source file exists has been migrated: it is
            # generated from now on, whatever the file on disk says.
            src = MAP_SOURCE if path.name == 'MAP.md' else GLOSSARY_SOURCE
            # A views-only rebuild (a consumer's sync, migration or commit
            # backstop) keeps the views a repository has and never adds one
            # it lacks: a consumer whose glossary lives in docs/ got a root
            # GLOSSARY.md, untracked, every time its MAP.source.md changed
            # (2026-10-03). A consumer's --check judges the same set: one
            # whose glossary lives in docs/ failed every check on a root
            # GLOSSARY.md no rebuild of its own would ever write (2026-10-04,
            # a consumer's Update Vendors). Everywhere else a deleted view is
            # still drift -- BestPractice and a practice set write both.
            if (views_only or (check and repo_is_consumer(root))) \
                    and not path.exists() and not has_own_source(root, src):
                continue
            if is_generated_view(path) or has_own_source(root, src):
                targets.append((path, render()))
            else:
                print(f"build_views: {path.name} has no generated_by header, so "
                      f"it is this repository's own and is left alone.",
                      file=sys.stderr)

    if check:
        drift = []
        for path, new_text in targets:
            old_text = path.read_text(encoding='utf-8') if path.exists() else None
            if old_text != new_text:
                drift.append(path.name)
        if drift:
            print(f"build_views --check FAIL: hand-edited or stale, drifted from "
                  f"regeneration: {', '.join(drift)}")
            return 1
        print(f"build_views --check OK: {', '.join(p.name for p, _t in targets)} "
              f"all byte-identical to a fresh regeneration")
        return 0

    for path, new_text in targets:
        path.write_text(new_text, encoding='utf-8')
    wrote = ', '.join(p.name for p, _t in targets)
    # These three figures come from the block that was just written, not
    # from a second build -- see render_agents_md's docstring for the
    # mismatch that made this the only safe shape.
    print(f"build_views OK: wrote {wrote} (loader block regenerated, resident "
          f"{n_resident}/{n_total} practices, ~{block_tokens} tokens)")
    return 0


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/FOR_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
