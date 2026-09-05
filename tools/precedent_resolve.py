#!/usr/bin/env python3
"""precedent_resolve.py — resolve the four sources into one set of practices
(PRACTICE_ENGINE_PLAN.md, "Source — Who a Practice Belongs To" and
"Precedence, and the One Case Where the Individual Does Not Win").

A practice's LEVEL is not a field. It is implied by which repository the file
lives in, "so it cannot drift from reality" — universal in Precedent, team in
one private repo per team, individual in one private repo per person,
repo-local in the consuming repo's own tree. This tool is what turns "up to
four repositories" into "the practices in force here".

WHO DECLARES WHICH SOURCE, AND WHY THAT SPLIT IS A PRIVACY BOUNDARY RATHER
THAN A CONVENIENCE.

  The CONSUMER REPO declares universal, its team set, and its own repo-local
  set, in a tracked config file (precedent.json). Everyone working there
  gets those, and everyone working there can already read them.

  THE PERSON declares their own individual set in their USER-LEVEL config,
  outside any shared repo (~/.config/precedent/config.json, or wherever
  PRECEDENT_USER_CONFIG points). If a project repo named someone's individual
  set it would leak that set's existence and location to everyone on the
  team, and their sessions would try to fetch a repository they cannot read.

  So two people working in the same repo resolve DIFFERENT sets, each seeing
  their own personal practices and neither seeing the other's. That falls out
  of where the declaration lives; it is not a rule anyone has to remember.

PRECEDENCE is team > repo-local > individual > universal, by slug (changed
2026-09-03 from the phase-3 individual > team > universal order — see
spec/SOURCES.md for the reasoning). A team's rules bind everyone in it, so
they are the strongest -- closest to actual law for that group. Universal
covers every Precedent user in the world, so by design it is the lowest
common denominator and the weakest. An individual's own practices sit in
between: more binding than a rule meant for the whole world, less binding
than what a person's own team requires of them. Repo-local sits alongside
that same ladder, between individual and team, since it speaks to the actual
working reality of one specific repo rather than a person's general style --
but nothing here is fixed forever: any practice at any level can still be
reordered relative to one slug via `overrides:`, or protected from every
level above it via `severity: blocking` (see below). This is a property of
the resolver, not a rule written down and hoped to be read.

THE ONE CASE PRECEDENCE ALONE DOES NOT DECIDE. A practice at any level below
the top of PRECEDENCE (currently: repo-local, individual, or universal) may
be marked `severity: blocking`, which means no source ranked above it can
override it by ordinary precedence -- only a same-level `overrides:` still
can. This is for the rare case where a lower-ranked practice must hold
regardless of what a higher-ranked source happens to say: a universal
information-leak guard a team must not be able to quietly turn off for
itself, say. This is the difference between a practice about HOW SOMETHING
IS DONE and one about WHAT MUST NEVER HAPPEN.

DEGRADING GRACEFULLY IS PART OF THE CONTRACT, not an error path. A fresh
cloud session with no persistent home directory has no local individual set.
When a declared source is missing, the resolver runs on what it has and SAYS
SO — it never silently pretends personal practices were applied. A missing
source is reported on stderr and in `--json` under "missing"; only a
malformed source, or two practices at the same level claiming one slug, is
fatal.

Run:
  python3 tools/precedent_resolve.py                 # resolve, human-readable
  python3 tools/precedent_resolve.py --json          # the resolved set as data
  python3 tools/precedent_resolve.py --repo DIR      # resolve for another repo
  python3 tools/precedent_resolve.py --explain SLUG  # how one slug resolved
  python3 tools/precedent_resolve.py --strict        # a missing source is fatal
Exit: 0 on a resolved set, 1 on a conflict, a malformed source, or --strict
with a source missing.
"""
import json, os, pathlib, posixpath, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import build_views as bv

REPO_CONFIG = 'precedent.json'
USER_CONFIG_ENV = 'PRECEDENT_USER_CONFIG'
DEFAULT_USER_CONFIG = pathlib.Path.home() / '.config' / 'precedent' / 'config.json'

# The project-committed path a session-start hook that bootstraps a
# privately-scoped individual source lives at, by convention (INSTALL.md
# step 9, spec/BOOTSTRAP_NEW_SOURCES.md, the
# individual-source-bootstrap.sh.template this repo ships). Fixed rather
# than configurable: the self-heal below has to find it without first
# resolving a config that might be exactly what's missing.
INDIVIDUAL_BOOTSTRAP_HOOK = '.claude/hooks/precedent-individual-bootstrap.sh'

# Deliberately smaller than precedent_source_bootstrap.py's own CLI
# defaults (6 retries / 2s): the hook itself is the first line of defense
# and can afford to spend ~12s once at session start. This is the second
# line, invoked lazily from inside an ordinary resolve -- every extra
# second here is latency added to a session that just asked "what
# practices are in force", not to a one-time session-start cost.
SELF_HEAL_RETRIES = 2
SELF_HEAL_RETRY_DELAY = 1.0


def _self_heal_individual_source(repo_root):
    """practice: session-bootstrap -- "config absent" and "no individual
    set" are not the same fact, and treating them as the same fact is
    exactly the bug two independent adopters hit (see
    tools/precedent_source_bootstrap.py's module docstring for the
    incident). If a hook that would populate the user config exists in
    this project, in a session that could plausibly still be racing its
    own `add_repo` calls, try it once, synchronously, before concluding
    the individual source isn't available.

    Deliberately narrow: only fires when (a) CLAUDE_CODE_REMOTE=true --
    the race this exists for is specific to a hosted session's per-session
    git access, never a local machine's persistent $HOME -- and (b) the
    project actually ships the conventional hook. Never raises: a self-heal
    attempt that itself fails is exactly the "missing source" case this
    function was trying to avoid misreporting, not a new failure mode."""
    if os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
        return
    hook = repo_root / INDIVIDUAL_BOOTSTRAP_HOOK
    if not hook.is_file():
        return
    try:
        subprocess.run(['bash', str(hook)], cwd=str(repo_root),
                       capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        pass

# HIGHEST PRECEDENCE FIRST -- read this tuple left to right as strongest to
# weakest. (Changed 2026-09-03: this used to be listed lowest-first, weakest
# to strongest, which reads backwards to an English speaker scanning a
# left-to-right list -- team > repo-local > individual > universal is the
# actual precedence order, matching how it is written and spoken everywhere
# else in this codebase and its docs.)
#
# The resolver still needs to WALK sources lowest-precedence-first internally
# (a later source simply replaces what an earlier one put in place -- see
# resolve() below), so every place that turns a level into a walk position
# reads this tuple in reverse: `_precedence_rank()` gives the weakest level
# rank 0, not `PRECEDENCE` itself.
PRECEDENCE = ('team', 'repo-local', 'individual', 'universal')


def _precedence_rank(level):
    """0 = weakest (walked first), higher = stronger (walked later, wins on a
    shared slug). The one place PRECEDENCE's highest-first order gets
    inverted back into a walk order -- everything else should call this
    rather than re-deriving the inversion locally."""
    return len(PRECEDENCE) - 1 - PRECEDENCE.index(level)

# A practice that is not active is resolvable by slug -- so `supersedes:`
# still points somewhere real -- but is not in force.
IN_FORCE_STATUS = 'active'


class ResolveError(Exception):
    """A source that cannot be resolved at all, as opposed to one that is
    merely absent. Raised rather than sys.exit()ed so the verification
    harness can call this module in-process without an uncaught SystemExit
    taking the whole run down (the same fix phase 2 made for build_views)."""


def _read_json(path, what):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ResolveError(f"{what} at {path} is not valid JSON ({e}). A config the "
                           f"resolver cannot read is not an empty config.")


def load_config(repo, user_config=None):
    """-> list of {level, name, path}, lowest precedence first.

    The repo config may name universal, team, and repo-local sources. An
    individual source declared in a SHARED repo is refused by name, because
    that is the privacy boundary above, and a mistake that is silent here is
    a mistake nobody finds. A repo-local source's `path` must be EXACTLY
    "local" -- not the bare repo root (`"."`), and not some other
    subdirectory name a repo happened to pick. This used to be only a
    recommended convention (any path inside the repo passed validation) and
    two real, reproduced bugs are what closed that gap, not a style
    preference: (1) `path: "."` puts repo-local's own hand-authored
    practices/ in the exact same place tools/precedent_materialize.py's
    resolved output goes when a repo materializes into its own root --
    materializing a `path: "."` repo-local source into that same repo's own
    root silently overwrote the hand-authored source file the moment
    another source won resolution on a shared slug, with no trace left that
    it had ever held different content; a 2026-09-03 deep-check audit found
    a second, worse case surviving the first fix too (materialize()'s own
    prior output gets read back on the NEXT run as if this source had
    authored it). (2) two dependent repos that both installed Precedent
    picked two different subdirectory names for the same thing (`local/`
    in one, a bare `practices/` with no repo-local source declared at all
    in the other) -- structurally fine on its own, since the second repo
    simply had no repo-local practices yet, but it meant "where do this
    repo's own rules live" had no single answer a session could carry from
    one Precedent repo to the next, and the next repo to actually need one
    was free to pick a THIRD name. Fixing the name to "local" removes that
    degree of freedom: every repo-local source, in every repo, lives at
    `local/practices/`, so the answer travels.

    tools/precedent_materialize.py's `_self_referential_sources` remains
    as a separate, level-agnostic backstop (a UNIVERSAL source can
    legitimately sit at `path: "."` too, e.g. this repo's own
    self-hosted precedent.json) -- this validation prevents repo-local
    specifically from ever being declared at a colliding or inconsistent
    path in the first place, rather than relying on materialize() to catch
    it after the fact."""
    repo_root = pathlib.Path(repo).resolve()
    sources = []
    repo_cfg_path = repo_root / REPO_CONFIG
    if repo_cfg_path.exists():
        cfg = _read_json(repo_cfg_path, 'the repository config')
        for entry in cfg.get('sources', []):
            level = entry.get('level')
            if level == 'individual':
                raise ResolveError(
                    f"{repo_cfg_path} declares an individual source "
                    f"({entry.get('name')!r}). A shared repository may only name "
                    f"sources everyone in it can read -- naming an individual set "
                    f"here leaks its existence and location to the whole team, and "
                    f"every other person's session would try to fetch a repository "
                    f"they cannot read. Declare it in your user-level config "
                    f"instead ({DEFAULT_USER_CONFIG}).")
            if level not in PRECEDENCE:
                raise ResolveError(
                    f"{repo_cfg_path}: source {entry.get('name')!r} has level "
                    f"{level!r}; expected one of {', '.join(PRECEDENCE)}.")
            # Compare the NORMALIZED path, not the raw string: "local/",
            # "./local" and "local" all name the identical directory, and a
            # strict `!= 'local'` on the raw JSON value refused the first
            # two as if they were a different, non-compliant path -- a real
            # bug found testing this rule, not a hypothetical one.
            raw_path = entry.get('path')
            normalized_path = (posixpath.normpath(raw_path)
                                if isinstance(raw_path, str) else raw_path)
            if level == 'repo-local' and normalized_path != 'local':
                raise ResolveError(
                    f"{repo_cfg_path} declares a repo-local source "
                    f"({entry.get('name')!r}) at path {entry.get('path')!r}. "
                    f"A repo-local source's `path` must resolve to exactly "
                    f"\"local\" (holding local/practices/) -- not the bare "
                    f"repo root (\".\") and not any other subdirectory "
                    f"name. This is a fixed convention, not a per-repo "
                    f"choice: it is what "
                    f"keeps repo-local's own hand-authored practices/ "
                    f"physically separate from tools/precedent_materialize.py's "
                    f"output directory (a `path: \".\"` repo-local source has "
                    f"silently lost its own hand-authored content to that "
                    f"tool before), and it is what lets a session that has "
                    f"seen one Precedent repo's repo-local practices find "
                    f"another's without re-deriving the name each time.")
            entry_path = (repo_root / entry['path']).resolve()
            sources.append({'level': level, 'name': entry.get('name', level),
                            'path': str(entry_path)})

    user_cfg_path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(USER_CONFIG_ENV, str(DEFAULT_USER_CONFIG))).expanduser()
    if not user_cfg_path.exists():
        # practice: session-bootstrap -- a hook that hasn't run yet (lost its
        # race against this session's own `add_repo` calls) looks identical,
        # from here, to "this person has no individual set". Try once to
        # close that gap before reporting the latter.
        _self_heal_individual_source(repo_root)
    if user_cfg_path.exists():
        cfg = _read_json(user_cfg_path, 'the user config')
        ind = cfg.get('individual')
        if ind:
            sources.append({'level': 'individual',
                            'name': ind.get('name', 'precedent-individual'),
                            'path': str(pathlib.Path(ind['path']).expanduser())})
    sources.sort(key=lambda s: _precedence_rank(s['level']))
    return sources


def load_source(source):
    """-> ({slug: practice}, missing_reason or None). A source directory holds
    its practices in practices/, the same layout Precedent itself uses."""
    d = pathlib.Path(source['path']) / 'practices'
    if not d.is_dir():
        return {}, f"{source['path']} has no practices/ directory"
    out = {}
    for f in sorted(d.glob('*.md')):
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError as e:
            raise ResolveError(f"{source['name']}: {e}")
        slug = fm.get('slug', f.stem)
        if slug in out:
            raise ResolveError(
                f"{source['name']}: two practices claim the slug {slug!r} "
                f"({out[slug]['file']} and {f}). Slugs are identities; the "
                f"resolver cannot choose between two at the same level.")
        out[slug] = {'slug': slug, 'level': source['level'],
                     'source': source['name'], 'file': str(f), 'fm': fm,
                     'sections': sections}
    return out, None


def resolve(sources):
    """-> {'practices': {slug: practice}, 'shadowed': [...], 'blocked': [...],
           'missing': [...], 'retired': [...]}

    Sources are walked lowest precedence first, so a later source simply
    replaces what an earlier one put in place -- except where the practice it
    would replace is `severity: blocking`, which no source ranked above it
    can override by precedence alone (see _is_blocking)."""
    by_source, missing = [], []
    for s in sources:
        loaded, why = load_source(s)
        if why:
            missing.append({'level': s['level'], 'name': s['name'], 'reason': why})
            continue
        by_source.append((s, loaded))

    resolved, shadowed, blocked, retired = {}, [], [], []
    # Tracks, per precedence level, which `overrides:` target has already
    # been claimed by a practice at that same level. Two practices at the
    # SAME level naming the same target are a collision the plan requires
    # to fail loudly (PRACTICE_ENGINE_PLAN.md, "Precedence, and the One Case
    # Where the Individual Does Not Win": "the resolver fails loudly if two
    # same-level practices claim one slug"). Without this, the second
    # same-level practice to process finds its target already deleted from
    # `resolved` by the first -- `resolved.get(ov)` comes back None, the
    # `if prior_ov is not None:` guard below is skipped entirely, and the
    # second practice's override intent vanishes with no error, no shadow
    # entry, and no trace in `--explain` for either practice. Keyed by level
    # rather than by source, since the collision is about two practices the
    # resolver cannot order relative to each other -- there is no precedence
    # between them to fall back on -- regardless of which source(s) at that
    # level they came from.
    override_claims_by_level = {}
    for _s, loaded in by_source:                      # lowest precedence first
        claims = override_claims_by_level.setdefault(_s['level'], {})
        for slug, practice in sorted(loaded.items()):
            if bv._json_str(practice['fm'].get('status', 'active')) != IN_FORCE_STATUS:
                retired.append(practice)
                continue
            # A practice replaces the same slug from a lower source, and may
            # additionally name a differently-named lower practice in
            # `overrides:`.
            ov = bv._json_str(practice['fm'].get('overrides', 'null'))
            has_override = bool(ov) and ov != 'null' and ov != slug

            # Check the practice's OWN slug first. If a blocking prior holds
            # it, this practice never enters `resolved` at all -- so it must
            # not be allowed to act on `overrides:` either. The two used to
            # be processed as independent targets in one loop: an own-slug
            # block set `own_slug_refused` but the loop had already moved on
            # to the `overrides:` target, deleting and "shadowing" it even
            # though the practice that supposedly did the shadowing was never
            # actually activated. Ordering this as own-slug-first, with an
            # early return on refusal, makes that combination impossible
            # rather than merely untested.
            prior_own = resolved.get(slug)
            if prior_own is not None and _is_blocking(prior_own):
                blocked.append({'slug': slug, 'kept': prior_own, 'refused': practice})
                continue

            if has_override:
                prior_claim = claims.get(ov)
                if prior_claim is not None:
                    raise ResolveError(
                        f"{practice['source']} ({practice['slug']!r}) and "
                        f"{prior_claim['source']} ({prior_claim['slug']!r}) are "
                        f"both {_s['level']}-level practices that name "
                        f"`overrides: {ov}`. Two same-level practices cannot "
                        f"both claim one slug -- pick one, or point one of "
                        f"them at a different target.")
                claims[ov] = practice

                prior_ov = resolved.get(ov)
                if prior_ov is not None:
                    if _is_blocking(prior_ov):
                        blocked.append({'slug': ov, 'kept': prior_ov, 'refused': practice})
                    else:
                        shadowed.append({'slug': ov, 'shadowed': prior_ov, 'by': practice})
                        del resolved[ov]

            if prior_own is not None and not _is_blocking(prior_own):
                shadowed.append({'slug': slug, 'shadowed': prior_own, 'by': practice})
            resolved[slug] = practice
    return {'practices': resolved, 'shadowed': shadowed, 'blocked': blocked,
            'missing': missing, 'retired': retired}


def _is_blocking(practice):
    """`severity: blocking` is meaningful for any level except the very top
    of PRECEDENCE -- there is nothing ranked above the top level, so nothing
    for it to need protection from. Deriving this from PRECEDENCE (rather
    than hardcoding the two non-top level names, which is what this used to
    do) means a future reordering of PRECEDENCE does not silently leave a
    level's `blocking` marking inert or wrongly honored."""
    return (bv._json_str(practice['fm'].get('severity', 'default')) == 'blocking'
            and practice['level'] != PRECEDENCE[0])


def resident_stats(res):
    """The combined resident block across EVERY resolved source, using the
    same word*1.3 approximation build_views.py uses for its own hard cap.

    WHY THIS HAS TO LIVE HERE AND NOT JUST IN build_views.py. The single-repo
    cap (RESIDENT_BUDGET_TOKENS in build_views.py) only ever sees this
    repo's own practices/ directory -- it was built before a second or third
    source existed to combine with. `spec/PRIVATE_SETS_BRIEF.md` flagged the
    gap explicitly and asked the session populating the private sets to
    report back a combined figure "so a Precedent session can build the
    cross-source cap" -- nothing ever did. A team set marking six practices
    resident and an individual set marking three, on top of this repo's own
    six, pushes a real resolved session's context well past the 2,000-token
    budget with nothing objecting, because no single source's build ever
    sees the whole picture. This closes that: it sums `## Rule` text across
    every `tier: resident` practice in the RESOLVED set, whichever source
    contributed it, against the same budget."""
    resident = [p for p in res['practices'].values()
                if bv._json_str(p['fm'].get('tier', 'on-demand')) == 'resident']
    resident.sort(key=lambda p: p['slug'])
    text = '\n\n'.join(
        f"**{p['slug']}.** {p['sections'].get('rule', '').strip()}"
        for p in resident)
    tokens = bv._approx_tokens(text)
    return {
        'tokens': tokens,
        'budget': bv.RESIDENT_BUDGET_TOKENS,
        'over_budget': tokens > bv.RESIDENT_BUDGET_TOKENS,
        'practices': [{'slug': p['slug'], 'level': p['level'],
                       'source': p['source']} for p in resident],
    }


def _report(res, sources, out=sys.stdout):
    counts = {}
    for p in res['practices'].values():
        counts[p['level']] = counts.get(p['level'], 0) + 1
    print(f"resolved {len(res['practices'])} practice(s) from "
          f"{len(sources) - len(res['missing'])} source(s): "
          # PRECEDENCE is already highest-first, so this prints strongest to
          # weakest with no reversal needed -- iterating it directly used to
          # print weakest-to-strongest here, back when the tuple itself was
          # lowest-first and this call compensated with reversed().
          + ', '.join(f"{counts.get(l, 0)} {l}" for l in PRECEDENCE), file=out)
    for s in res['shadowed']:
        print(f"  overridden: {s['slug']} -- {s['by']['level']} "
              f"({s['by']['source']}) replaces {s['shadowed']['level']} "
              f"({s['shadowed']['source']})", file=out)
    for b in res['blocked']:
        print(f"  NOT overridden: {b['slug']} -- {b['kept']['level']} "
              f"({b['kept']['source']}) is severity: blocking, so the "
              f"{b['refused']['level']} practice does not replace it", file=out)
    for r in res['retired']:
        print(f"  not in force: {r['slug']} ({r['source']}) is status: "
              f"{bv._json_str(r['fm'].get('status'))}", file=out)
    rstats = resident_stats(res)
    if rstats['practices']:
        who = ', '.join(f"{p['slug']} ({p['level']})" for p in rstats['practices'])
        detail = f"{len(rstats['practices'])} practice(s): {who}"
    else:
        detail = "no resident practices"
    print(f"resident block across all sources: ~{rstats['tokens']} of "
          f"{rstats['budget']} token budget ({detail})", file=out)
    if rstats['over_budget']:
        print(f"OVER BUDGET: the combined resident block is ~{rstats['tokens']} "
              f"tokens against a {rstats['budget']}-token cap -- demote or "
              f"retire a resident practice in one of the sources above before "
              f"this set is usable at session start.", file=out)


def main():
    args = sys.argv[1:]
    known = {'--json', '--repo', '--explain', '--strict', '--user-config'}
    repo, explain, user_config = str(ROOT), None, None
    for flag, target in (('--repo', 'repo'), ('--explain', 'explain'),
                         ('--user-config', 'user_config')):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(f"precedent resolve FAIL: {flag} needs a value.")
            value = args[i + 1]
            args = args[:i] + args[i + 2:]
            if target == 'repo':
                repo = value
            elif target == 'explain':
                explain = value
            else:
                user_config = value
    unknown = [a for a in args if a.startswith('--') and a not in known]
    if unknown:
        sys.exit(f"precedent resolve FAIL: unknown option(s) {', '.join(unknown)} -- "
                 f"known options are {', '.join(sorted(known))}.")

    try:
        sources = load_config(repo, user_config)
        # NO sources at all is not an empty resolved set, it is an unconfigured
        # repository -- and "resolved 0 practices" printed with exit 0 is the
        # same confident all-clear from a check that never ran that this
        # project has now been bitten by three times.
        if not sources:
            sys.exit(
                f"precedent resolve FAIL: no practice sources are declared for "
                f"{repo}. A repository using Precedent declares its universal and "
                f"team sources in a tracked {REPO_CONFIG}; a person declares their "
                f"own individual set in their user-level config "
                f"({DEFAULT_USER_CONFIG}, or {USER_CONFIG_ENV}). Nothing was "
                f"resolved because nothing was asked for -- that is not an empty "
                f"answer, it is no question.")
        res = resolve(sources)
    except ResolveError as e:
        sys.exit(f"precedent resolve FAIL: {e}")

    # A missing source is reported, never silently absorbed: "personal
    # practices are missing" and "you have no personal practices" must not
    # look the same.
    for m in res['missing']:
        print(f"precedent resolve: the {m['level']} source {m['name']!r} is not "
              f"available ({m['reason']}). Running WITHOUT it -- the practices it "
              f"holds are not in force in this session.", file=sys.stderr)
    if res['missing'] and '--strict' in args:
        return 1

    if explain:
        return _explain(explain, res, sources)

    rstats = resident_stats(res)
    rc = 1 if (res['missing'] and '--strict' in args) else 0
    # OVER BUDGET is not gated behind --strict: PRACTICE_ENGINE_PLAN.md's
    # "The Resident Budget" is explicit that exceeding the cap "fails the
    # build outright... mechanically, not by discipline" for the single-repo
    # case; a resolved set that blows the budget across sources is the same
    # failure and gets the same default.
    if rstats['over_budget']:
        rc = 1

    if '--json' in args:
        rows = [{'slug': p['slug'], 'level': p['level'], 'source': p['source'],
                 'tier': bv._json_str(p['fm'].get('tier', 'on-demand')),
                 'severity': bv._json_str(p['fm'].get('severity', 'default'))}
                for p in res['practices'].values()]
        print(json.dumps({
            'sources': sources,
            'practices': sorted(rows, key=lambda r: r['slug']),
            'overridden': [{'slug': s['slug'], 'by': s['by']['level'],
                            'was': s['shadowed']['level']} for s in res['shadowed']],
            'blocked': [{'slug': b['slug'], 'kept': b['kept']['level'],
                         'refused': b['refused']['level']} for b in res['blocked']],
            'missing': res['missing'],
            'resident': rstats,
        }, indent=2, sort_keys=True))
        if rstats['over_budget']:
            print(f"precedent resolve FAIL: combined resident block is "
                  f"~{rstats['tokens']} tokens, over the {rstats['budget']}-"
                  f"token cross-source cap.", file=sys.stderr)
        return rc
    _report(res, sources)
    return rc


def _explain(slug, res, sources):
    p = res['practices'].get(slug)
    if p:
        print(f"{slug}: in force from the {p['level']} source "
              f"({p['source']}), {p['file']}")
    for s in res['shadowed']:
        # Match on BOTH ends: `--explain` on the practice that did the
        # overriding is the more natural question, and matching only the
        # target slug answered it with silence.
        if s['by']['slug'] == slug:
            print(f"  overrides the {s['shadowed']['level']} practice "
                  f"{s['shadowed']['slug']!r} at {s['shadowed']['file']}")
        elif s['slug'] == slug:
            print(f"  the {s['by']['level']} practice {s['by']['slug']!r} at "
                  f"{s['by']['file']} replaced this one; it is not in force")
    for b in res['blocked']:
        if b['slug'] == slug:
            print(f"  a {b['refused']['level']} practice at {b['refused']['file']} "
                  f"tried to override this and was refused: the "
                  f"{b['kept']['level']} practice is severity: blocking")
    if not p and not any(b['slug'] == slug for b in res['blocked']) \
            and not any(s['slug'] == slug for s in res['shadowed']):
        print(f"precedent resolve: no practice with slug {slug!r} in the resolved "
              f"set ({len(res['practices'])} practices from "
              f"{len(sources)} source(s)).")
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
