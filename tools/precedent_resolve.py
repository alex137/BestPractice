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

  The CONSUMER REPO declares universal, its shared set, and its own repo-local
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

PRECEDENCE is shared > repo-local > individual > universal, by slug (changed
2026-09-03 from the phase-3 individual > shared > universal order — see
spec/SOURCES.md for the reasoning). A team's rules bind everyone in it, so
they are the strongest -- closest to actual law for that group. Universal
covers every Precedent user in the world, so by design it is the lowest
common denominator and the weakest. An individual's own practices sit in
between: more binding than a rule meant for the whole world, less binding
than what a person's own team requires of them. Repo-local sits alongside
that same ladder, between individual and shared, since it speaks to the actual
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
  python3 tools/precedent_resolve.py --strict        # a missing source, or a
                                                      # deduplication pointing
                                                      # IN FORCE NOWHERE, is fatal
Exit: 0 on a resolved set, 1 on a conflict, a malformed source, --strict with
a source missing or a dangling deduplication, or the resident budget over cap.
"""
import json, os, pathlib, posixpath, re, subprocess, sys, time

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

def _scratch_copy_of(repo_root):
    """-> the checkout `repo_root` was copied from, when its `origin` is
    another directory on this disk (a path or a file:// URL), else None.

    NO SELF-REPAIR BESIDE A SCRATCH COPY (2026-09-30). A test or tool that
    copies a checkout with `git clone <path>` and resolves from the copy --
    precedent-shared-repo-maintenance's trailer test does, to judge a clone
    that resolves no working-style set -- had the repairs below clone every
    declared source beside the copy, in /tmp, in a hosted session. The
    copy then resolved exactly what the test set out to exclude, and failed
    on untouched pre-staging. A checkout a person works in, attached or the
    project itself, has a remote for its origin; a copy of a checkout on
    this disk does not, and the sources it declares belong to the checkout
    it was copied from. The directory it sits in is not the test: the
    repairs' own tests run from temporary fixtures, and a copy made beside
    the real checkout is still a copy."""
    try:
        r = subprocess.run(['git', '-C', str(repo_root), 'remote', 'get-url',
                            'origin'], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    url = r.stdout.strip() if r.returncode == 0 else ''
    if url.startswith('file://'):
        url = url[len('file://'):]
    if not url or '://' in url or re.match(r'^[\w.-]+@[\w.-]+:', url):
        return None
    return url if pathlib.Path(url).expanduser().exists() else None


def _self_heal_individual_source(repo_root):
    """practice: session-bootstrap -- "config absent" and "no individual
    set" are not the same fact, and treating them as the same fact is
    exactly the bug two independent adopters hit (see
    tools/precedent_source_bootstrap.py's module docstring for the
    incident, and its 2026-09-06 correction for why THIS function -- not
    a retry loop inside the hook itself -- is the thing that actually
    closes it). A `SessionStart` hook runs entirely to completion before
    the agent's own turn starts, so on a genuinely fresh session it is
    GUARANTEED to run before `add_repo` can have been called even once --
    not a race it might win, one it structurally cannot. By the time
    anything calls this function, though, the agent's own turn (and its
    `add_repo` call, per the standing session-start instruction) has
    already happened -- so a single re-invocation of the project's hook,
    here, now has the access it needed the first time and should succeed
    on this one attempt.

    Deliberately narrow: only fires when (a) CLAUDE_CODE_REMOTE=true --
    this is specific to a hosted session's per-session git access, never a
    local machine's persistent $HOME -- and (b) the project actually ships
    the conventional hook. Never raises: a self-heal attempt that itself
    fails is exactly the "missing source" case this function was trying to
    avoid misreporting, not a new failure mode.

    Returns WHICH of those happened -- 'attempted', 'not-remote' or
    'no-hook' -- because the caller cannot otherwise tell a self-heal that
    ran and found nothing from one that never ran at all, and those are
    different answers to "do you have an individual set?" (2026-09-06: this
    returned None either way, and the difference was the whole reason a real
    rule went looked-for and not found.)"""
    if os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
        return 'not-remote'
    if _scratch_copy_of(repo_root):
        return 'scratch-copy'
    # A config named on purpose OUTSIDE $HOME belongs to somebody other than
    # the person whose home the hook works in: the hook clones and syncs
    # under $HOME. Running it anyway reached past the named person to the
    # real one -- every test fixture that named a config of its own put this
    # machine's individual clone back on its pinned branch (2026-10-02,
    # found as a branch that kept moving mid-session). An absent config
    # named there is a definite "none", as on a local machine. A fixture
    # that moves $HOME with its config is still healed, in its own home.
    named = os.environ.get(USER_CONFIG_ENV)
    if named:
        home = pathlib.Path.home().resolve()
        where = pathlib.Path(named).expanduser().resolve()
        if where != home and home not in where.parents:
            return 'not-remote'
    hook = repo_root / INDIVIDUAL_BOOTSTRAP_HOOK
    if not hook.is_file():
        return 'no-hook'
    # The project dir is passed on because this runs from a shell tool call,
    # which carries no project-dir variable, and the bootstrap needs one to
    # find a clone the attach tool already put beside the project -- without
    # it, this self-heal is what cloned the individual set a second time
    # (precedent_source_bootstrap.attach_workspace, 2026-09-28).
    env = dict(os.environ)
    env.setdefault('PRECEDENT_PROJECT_DIR', str(repo_root))
    try:
        subprocess.run(['bash', str(hook)], cwd=str(repo_root),
                       capture_output=True, timeout=60, env=env)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return 'attempted'

def _self_heal_universal_source(repo_root):
    """practice: session-bootstrap -- the mirror-image gap to
    _self_heal_individual_source above, for a SOURCE-kind repo (an
    individual or shared practice set) that declares the universal source
    (BestPractice) in its own precedent.json.

    NO TIMING RACE HERE, unlike the individual case: BestPractice is
    PUBLIC, so cloning it needs no token and no wait for this session's own
    `add_repo` call to have happened. What is actually missing is any
    non-SessionStart path that ever attempts the clone at all.
    bootstrap/precedent-universal-catalogue.sh does it, but only at
    SessionStart -- and a practice set opened as one of several repos in a
    session, attached alongside others rather than as the session's own
    primary project, never runs a SessionStart hook that is not its own
    (this repo's own record/GOTCHA.md g15/g17). A session reaching this
    set's declared universal source through the engine's ordinary tools
    (precedent_check.py, precedent_paths.py,
    precedent_session_practices.py -- all of which run through load_config
    below) would otherwise see it declared and simply absent, forever, with
    nothing left to try -- the same silence the individual-source heal
    above exists to break for the private case.

    Deliberately narrow, same as the function above: only fires when the
    repo actually ships tools/precedent_source_bootstrap.py (a source set
    whose engine predates ENGINE_FILES picking it up has neither the tool
    nor the gap this closes). Never raises: a failed clone here is reported
    by the ordinary 'missing source' path load_config's caller already has,
    not a new failure mode."""
    tool = repo_root / 'tools' / 'precedent_source_bootstrap.py'
    if not tool.is_file():
        return 'no-tool'
    if _scratch_copy_of(repo_root):
        return 'scratch-copy'
    try:
        # -B: this tool runs INSIDE repo_root, and its own _credential_args()
        # imports precedent_source_credentials from ITS directory (repo_root/
        # tools) -- on a repo_root that is a just-bootstrapped set, that
        # write lands inside the set and reads as bootstrap drift in every
        # audit afterwards, same as the build_views.py subprocess
        # precedent_bootstrap_source.py already runs with -B for the same
        # reason.
        subprocess.run([sys.executable, '-B', str(tool), '--sources-from',
                        str(repo_root)], cwd=str(repo_root),
                       capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return 'attempted'


def _stale_render_hours(repo_root):
    """-> the age, in hours, past which .precedent/SESSION_PRACTICES.md
    counts as stale rather than merely old -- read from THIS repo's own
    `stale_render_hours` (precedent.json), or the engine default (1) when
    the key is absent or malformed.

    ITS OWN KEY, DELIBERATELY SEPARATE FROM `stale_checkout_hours`
    (.claude/hooks/freshness-guard.sh's threshold for how old a git
    CHECKOUT may be). Until 2026-09-18 this function borrowed that key
    outright -- same name, same 24h fallback -- reasoning that a threshold
    nobody decided is doctrine (practice: constants-are-risk-inputs) and a
    declared number beats a second hardcoded one. That reasoning held for
    reuse, not for the number itself: checkout staleness and render
    staleness are different questions with different failure shapes.
    Stale checkout is LOUD -- freshness-guard prints a banner a person acts
    on -- so tolerating it for up to a day, as Morgan's own 24h reasoning
    argues ("an hour behind, not much changed; a few days behind, a lot
    probably did"), is a reasonable place to draw that line. Stale render
    is SILENT by design -- the self-heal has no banner, because a session
    should never notice it ran -- which is exactly what let the
    2026-09-18 incident stay undetected for a full day: nothing was
    watching for it at all. A silent failure mode wants a much shorter
    leash than a loud one, so this now has its own key and its own
    default -- 1 hour, not 24 -- rather than continuing to inherit an
    answer measured for a different question.
    spec/SESSION_PRACTICES_RENDER_SELF_HEAL.md has the fuller comparison
    of the two cases and the reasoning behind the number.
    Never raises: an unreadable or absent precedent.json is the ordinary
    case for a repo with no declared threshold, not a failure."""
    try:
        cfg = json.loads((repo_root / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return 1
    hours = cfg.get('stale_render_hours')
    return hours if isinstance(hours, int) and hours > 0 else 1


def _ref_mtime(clone):
    """-> the mtime of the ref a clone has checked out, or None. Read off the
    filesystem, never from git: this runs on every load_config(), so it must
    cost a stat or two. A pull or a checkout rewrites that ref (or HEAD
    itself); a packed ref falls back to packed-refs. Follows a `.git` FILE
    (a worktree or submodule) to its gitdir."""
    try:
        git = pathlib.Path(clone) / '.git'
        if git.is_file():
            line = git.read_text(encoding='utf-8').strip()
            if not line.startswith('gitdir:'):
                return None
            git = (pathlib.Path(clone) / line[len('gitdir:'):].strip()).resolve()
        head = git / 'HEAD'
        stamps = [head.stat().st_mtime]
        text = head.read_text(encoding='utf-8').strip()
        if text.startswith('ref:'):
            ref = text[4:].strip()
            common = git
            cfile = git / 'commondir'
            if cfile.is_file():
                common = (git / cfile.read_text(encoding='utf-8').strip()).resolve()
            loose = common / ref
            packed = common / 'packed-refs'
            if loose.is_file():
                stamps.append(loose.stat().st_mtime)
            elif packed.is_file():
                stamps.append(packed.stat().st_mtime)
        return max(stamps)
    except (OSError, ValueError):
        return None


def _render_older_than_sources(repo_root, rendered_at):
    """-> the declared source whose checkout moved after the render was
    written, or None. The render is built FROM those checkouts, so one that
    moved since makes it stale however young it is (2026-10-02: a resume
    fast-forwarded the shared sets an individual set reads, its render stayed
    as it was, and the reply gate reported a session load about 300 tokens
    over what a rebuild measured). Read off declared_source_paths(), which
    never clones or fetches."""
    try:
        declared = declared_source_paths(repo_root)
    except Exception:                                       # noqa: BLE001
        return None
    # A stamp from the future is ignored, not trusted: a clone unpacked with
    # future mtimes, or a clock that stepped back, would otherwise read as
    # "moved after the render" on every call and re-render forever.
    now = time.time() + 60
    for path, _level, name, note in declared:
        if note or not path:
            continue
        moved = _ref_mtime(path)
        if moved is not None and rendered_at < moved <= now:
            return name
    return None


# Set in the environment of the renderer _self_heal_stale_render spawns, so
# the renderer's own load_config() never spawns a second one.
SELF_HEAL_RENDER_ENV = 'PRECEDENT_SELF_HEAL_RENDER'


def _self_heal_stale_render(repo_root):
    """practice: session-bootstrap -- the other half of the render gap
    _self_heal_universal_source above does not close. That function fires
    only when a declared universal source's CLONE is entirely missing, and
    even then it only clones -- it never re-renders
    .precedent/SESSION_PRACTICES.md, the file precedent_session_practices.py
    writes and that AGENTS.md tells every session to read. The 2026-09-18
    incident this closes had every clone present the whole session; the
    render was simply a day stale, so `entry_path / 'practices'` was always
    True and the clone-heal never fired -- see
    spec/SESSION_PRACTICES_RENDER_SELF_HEAL.md (Shape C, the shape this
    implements) for the fuller account.

    Fires when the rendered file is ABSENT, older than
    _stale_render_hours() above, or older than a checkout it was rendered
    from (_render_older_than_sources, 2026-10-02). Judged from mtimes ON DISK,
    never from session state: there is no reliable in-session signal for
    whether SessionStart actually ran (CLAUDE_PROJECT_DIR being unset
    proves nothing either way, per tools/precedent_session_check.py's own
    docstring).

    Deliberately narrow, same shape as _self_heal_universal_source above:
    only fires when the repo actually ships
    tools/precedent_session_practices.py (a source set whose engine
    predates this addition simply doesn't get it, rather than failing).
    Never raises: a failed render here is reported by whatever ordinary
    path the caller already has for a missing or stale
    SESSION_PRACTICES.md, not a new failure mode."""
    # NEVER FROM INSIDE ITS OWN RENDER. precedent_session_practices.py calls
    # load_config(), which lands here, which ran precedent_session_practices.py
    # again -- and that child's load_config() ran here again, before any
    # render had been written to read as fresh. Every level of the recursion
    # spawned the next, and nothing bounded it but the 60-second timeout:
    # a single bootstrap of a new set stood up over two thousand renderers
    # in a few seconds (2026-09-19, found the first time the harness's
    # bootstrap-drift check actually ran after this heal landed; the
    # session-wide OOM kills recorded the day before were the same fork
    # bomb, seen from the memory cgroup). The child is told it IS the heal,
    # and a process told that does not start another.
    if os.environ.get(SELF_HEAL_RENDER_ENV):
        return 'nested'
    tool = repo_root / 'tools' / 'precedent_session_practices.py'
    if not tool.is_file():
        return 'no-tool'
    target = repo_root / '.precedent' / 'SESSION_PRACTICES.md'
    if target.is_file():
        try:
            rendered_at = target.stat().st_mtime
            age_hours = (time.time() - rendered_at) / 3600
        except OSError:
            rendered_at = age_hours = None
        if age_hours is not None and age_hours < _stale_render_hours(repo_root) \
                and _render_older_than_sources(repo_root, rendered_at) is None:
            return 'fresh'
    try:
        subprocess.run([sys.executable, str(tool), '--repo', str(repo_root)],
                       cwd=str(repo_root), capture_output=True, timeout=60,
                       env=dict(os.environ, **{SELF_HEAL_RENDER_ENV: '1'}))
    except (OSError, subprocess.TimeoutExpired):
        pass
    return 'attempted'

# HIGHEST PRECEDENCE FIRST -- read this tuple left to right as strongest to
# weakest. (Changed 2026-09-03: this used to be listed lowest-first, weakest
# to strongest, which reads backwards to an English speaker scanning a
# left-to-right list -- shared > repo-local > individual > universal is the
# actual precedence order, matching how it is written and spoken everywhere
# else in this codebase and its docs.)
#
# The resolver still needs to WALK sources lowest-precedence-first internally
# (a later source simply replaces what an earlier one put in place -- see
# resolve() below), so every place that turns a level into a walk position
# reads this tuple in reverse: `_precedence_rank()` gives the weakest level
# rank 0, not `PRECEDENCE` itself.
PRECEDENCE = ('shared', 'repo-local', 'individual', 'universal')

# `shared` is the level of any practice set a repository declares beside
# the universal one and its own local/ -- a team's house rules, a subject
# system (a filing pipeline, a presentation kit), a code style. It was
# called `team` until 2026-09-18, when the first subject set to be built
# showed that "team" named one kind of shared set and excluded the rest
# (Morgan approved the change; relayed by Alex). The old word still reads:
# a declaration saying `team` resolves as `shared`, so no existing
# precedent.json breaks. New declarations say `shared`.
LEVEL_ALIASES = {'team': 'shared'}
# The levels whose sources are private by default -- never vendored into a
# public tree, never named in one except by the name their consumer
# declares. Read by the leak gate, the views and the gate.
PRIVATE_LEVELS = ('shared', 'individual')


def normalize_level(level):
    """The canonical level for a declared one: `team` -> `shared`; anything
    else unchanged (an unknown level is refused where it is read)."""
    return LEVEL_ALIASES.get(level, level)


def _precedence_rank(level):
    """0 = weakest (walked first), higher = stronger (walked later, wins on a
    shared slug). The one place PRECEDENCE's highest-first order gets
    inverted back into a walk order -- everything else should call this
    rather than re-deriving the inversion locally."""
    return len(PRECEDENCE) - 1 - PRECEDENCE.index(level)

# practice: source-naming -- a source's NAME is chosen once by its author,
# recorded in the source's own manifest (SOURCE_MANIFEST below) and declared
# verbatim by every consumer; the REPOSITORY may be called anything. Only
# two names are fixed: the universal set is `precedent` (it is the product)
# and a repo-local source is `local` (it is a directory, like its path).
# Until 2026-09-18 a shared set's name was fixed to `precedent-team-<slug>`
# and an individual's to `precedent-individual`, and the machinery keyed on
# those shapes -- the clone URL, the leak gate's path rules, the level. A
# name was doing work that belongs in a file: the first subject set to be
# built could not be called what its author called it. Identity now lives
# in the manifest, and the shape a name must have is only what a slug
# needs to be a path segment and a manifest key. See spec/SOURCE_NAMING.md.
SOURCE_NAME_SHAPE = {
    'universal':  (re.compile(r'^precedent$'), 'precedent'),
    'repo-local': (re.compile(r'^local$'), 'local'),
}
# A shared or individual source: lowercase, digits and single hyphens, so it
# is a clone directory, a manifest key and a path segment the leak gate can
# match whole. Nothing else about it is prescribed.
SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
# Every person's own set defaults to this name when their config names none;
# it is a default, not a requirement.
DEFAULT_INDIVIDUAL_NAME = 'precedent-individual'
# The file a source carries at its root to say what it is: {"name", "level",
# "visibility", "subject", "code"}. A consumer declares the name; the
# resolver checks the clone at that path calls itself the same thing.
SOURCE_MANIFEST = 'precedent-source.json'


def check_source_name(level, name, where):
    """Raise ResolveError unless `name` is a name a source may carry at its
    level: the two fixed names for universal and repo-local, a slug for the
    rest. Shared with tools/precedent_check.py so the engine and the gate
    cannot disagree about what the convention is."""
    level = normalize_level(level)
    shape = SOURCE_NAME_SHAPE.get(level)
    if shape is not None:
        pattern, expected = shape
        if isinstance(name, str) and pattern.match(name):
            return
        raise ResolveError(
            f"{where}: the {level} source named {name!r} is not the name its "
            f"level fixes -- expected {expected}. The universal set is the "
            f"product and a repo-local source is a directory, so neither is "
            f"named per repository. See spec/SOURCE_NAMING.md.")
    if isinstance(name, str) and SLUG_RE.match(name):
        return
    raise ResolveError(
        f"{where}: the {level} source named {name!r} is not a slug (lowercase "
        f"letters, digits and single hyphens). A source's name is chosen once "
        f"by its author and written into its {SOURCE_MANIFEST}; the "
        f"repository may be called anything, but the name is a clone "
        f"directory, a manifest key and a path segment, so it has to be "
        f"spellable as one. See spec/SOURCE_NAMING.md.")


def read_source_manifest(path):
    """-> the source's own manifest (dict) or None when it carries none.
    Malformed JSON is a ResolveError: a manifest the resolver cannot read is
    not an absent one."""
    f = pathlib.Path(path) / SOURCE_MANIFEST
    if not f.is_file():
        return None
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise ResolveError(f"{f} is not valid JSON ({e}).")
    if not isinstance(data, dict):
        raise ResolveError(f"{f} must hold a JSON object.")
    return data


def check_source_manifest(source):
    """The identity check that replaced the name-shape check: when the clone
    at a declared path carries a manifest, its name and level must be the
    ones the consumer declared. A mismatch is the wrong repository at that
    path -- a typo in `path`, a stale clone, a rename nobody finished -- and
    it is refused, because materializing from it would attribute every
    check to a name the source itself does not answer to. A clone with no
    manifest is accepted as declared (sets predating 2026-09-18 carry none).
    Returns the manifest, or None."""
    m = read_source_manifest(source['path'])
    if m is None:
        return None
    declared_name, declared_level = source['name'], normalize_level(source['level'])
    own_name = m.get('name')
    own_level = normalize_level(m.get('level'))
    if own_name and own_name != declared_name:
        raise ResolveError(
            f"the source at {source['path']} calls itself {own_name!r} in its "
            f"{SOURCE_MANIFEST}, but this repository declares it as "
            f"{declared_name!r}. A consumer declares a source by the name the "
            f"source gives itself; fix the declaration, or the path if the "
            f"clone is the wrong repository.")
    if own_level and own_level != declared_level:
        raise ResolveError(
            f"the source at {source['path']} says it is a {own_level} source in "
            f"its {SOURCE_MANIFEST}, but this repository declares it as "
            f"{declared_level}.")
    return m


def warn_name_matches_path(level, name, path, where):
    """Warn -- never refuse -- when a source's clone directory looks like it
    was MEANT to carry the source's name and does not.

    Refusing is wrong here and was considered: a continuous integration
    checkout, a git worktree, and a vendored universal copy at
    `process/upstream` all legitimately put a conforming source in a
    differently-named directory.

    Warning on every mismatch is wrong too, and that is the narrower point.
    The first version did, and it fired on perfectly correct fixtures and
    checkouts whose directory is simply named something else ('shared-set',
    'ind', a temporary directory) -- noise on legitimate work, which is the
    fastest way to teach a reader to ignore a warning. So it fires only when
    the directory basename already carries the `precedent-` prefix: that is a
    directory someone meant to name after a source, and a mismatch there is a
    typo or a half-finished rename, not a deliberate choice."""
    base = posixpath.basename(posixpath.normpath(str(path).replace('\\', '/')))
    if level in ('universal', 'repo-local') or not base or base in ('.', '..'):
        return
    if not base.startswith('precedent-'):
        return
    if base != name:
        print(f"precedent resolve: {where} declares the {level} source "
              f"{name!r} at a path whose directory is {base!r}. That resolves "
              f"fine here, but the two disagreeing is usually a typo -- the "
              f"clone directory should carry the source's own name.",
              file=sys.stderr)


# A practice that is not active is resolvable by slug -- so `supersedes:`
# still points somewhere real -- but is not in force. Re-exported from
# build_views rather than defined twice: this module and the generated views
# disagreed about it for months (build_views never read `status:` at all, so
# it emitted retired practices into the loader block while this file
# correctly reported them not in force), and one definition is what stops
# that recurring.
IN_FORCE_STATUS = bv.IN_FORCE_STATUS


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


# Set by every load_config() call: None when an individual source WAS
# declared (its own fate is then reported through `missing` like any other
# source), otherwise the finding from _diagnose_no_individual below. Module
# state because load_config returns a plain list of sources that a dozen
# callers unpack positionally, and widening that return type to carry one
# diagnosis would be a worse trade than this.
INDIVIDUAL_STATUS = None


def _diagnose_no_individual(why, heal, user_cfg_path, repo_root):
    """-> {'certain', 'code', 'message'} for a session that resolved NO
    individual source.

    `certain` is the whole point. "You have no individual practices" and
    "this session could not find out whether you have any" are different
    answers, and until 2026-09-06 both came out as the same silence: nothing
    was appended to `sources`, so nothing reached the `missing` report, so
    the run printed a confident resolved-set summary that simply had no
    individual level in it. That is the exact failure the report loop's own
    comment says must not happen ("'personal practices are missing' and 'you
    have no personal practices' must not look the same") -- it was enforced
    for declared sources and unenforced for this one.

    The incident: a rule Morgan believed was in his individual set went
    unapplied, and every diagnostic in the repository agreed there was
    nothing to apply. Nothing was wrong with the individual set; this
    session simply had no way to reach it and never said so."""
    if why == 'config-declares-none':
        return {'certain': True, 'code': why,
                'message': (f"{user_cfg_path} exists and declares no "
                            f"individual source. No individual practices are "
                            f"in force, and that is a definite answer.")}
    # No evidence anywhere that this person has an individual set (no token,
    # base URL, repo name or clone): nothing could have fetched one, so a
    # missing set is a definite "none" where it would otherwise be unknown.
    # The reasoning, and the one case it gives up, are in
    # precedent_source_credentials.individual_signals. A tree vendored before
    # that module existed keeps the old, uncertain answer.
    try:
        from precedent_source_credentials import individual_signals
    except ImportError:
        individual_signals = None
    if (heal in ('no-hook', 'attempted') and individual_signals is not None
            and not individual_signals()):
        return {'certain': True, 'code': 'no-individual-signal',
                'message': ("nothing in this environment points to an "
                            "individual set (no token, base URL, repo name "
                            "or clone), so no individual practices are in "
                            "force; set PRECEDENT_INDIVIDUAL_REPO if you have "
                            "one")}
    if heal == 'scratch-copy':
        return {'certain': False, 'code': 'scratch-copy',
                'message': (
                    f"no individual source resolved in {repo_root}, a copy of "
                    f"{_scratch_copy_of(repo_root)} on this disk, and none was "
                    f"fetched beside it: a copy's sources belong to the "
                    f"checkout it was copied from. Treat this as unknown here, "
                    f"not as 'none'.")}
    if heal == 'no-hook':
        return {'certain': False, 'code': 'no-bootstrap-hook',
                'message': (
                    f"no individual source resolved, and this session could "
                    f"not find out whether you have one. {user_cfg_path} does "
                    f"not exist, and the self-heal that would create it did "
                    f"not run: this project ships no "
                    f"{INDIVIDUAL_BOOTSTRAP_HOOK}. On a hosted session that "
                    f"hook is the ONLY route to a private individual set, so "
                    f"treat this as unknown, not as 'none'. Instantiate it "
                    f"with `python3 tools/precedent_bootstrap_source.py "
                    f"--write-session-hook` (see spec/BOOTSTRAP_NEW_SOURCES.md), "
                    f"or point {USER_CONFIG_ENV} at a config yourself.")}
    if heal == 'attempted':
        return {'certain': False, 'code': 'bootstrap-hook-failed',
                'message': (
                    f"no individual source resolved. {INDIVIDUAL_BOOTSTRAP_HOOK} "
                    f"ran and did not produce {user_cfg_path}, which usually "
                    f"means its clone could not be fetched (a private "
                    f"repository this session was never granted). Treat this "
                    f"as unknown rather than 'none': run the hook by hand to "
                    f"see its error.")}
    # Not a hosted session: $HOME is this person's own persistent machine, so
    # an absent user config really is an absent individual set.
    return {'certain': True, 'code': 'no-config-file',
            'message': (f"{user_cfg_path} does not exist, so no individual "
                        f"practices are in force. On a local machine that is "
                        f"a definite answer; declare one there to change it.")}


def _main_checkout(repo_root):
    """-> the main checkout of `repo_root` when it is a LINKED git worktree,
    else None.

    A relative source path (`../precedent-shared-writing`) names a sibling
    of the repository as it really lives. The engine checks a commit in a
    throwaway worktree under the system temp directory -- the merge check,
    Promote's batch, the push check's base -- and from there no sibling
    exists: every declared set read as missing, and a practice in force in
    the repository (a set's revert exemption, 2026-09-29) read as not in
    force, so the merge check refused a pull request the checkout itself
    passed. Git records where a worktree's main checkout is; a relative path
    that does not resolve beside the worktree is resolved beside that."""
    def rev(arg):
        r = subprocess.run(['git', '-C', str(repo_root), 'rev-parse', arg],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ''
    common, own = rev('--git-common-dir'), rev('--git-dir')
    if not common or not own:
        return None
    common_p = pathlib.Path(common) if pathlib.Path(common).is_absolute() \
        else repo_root / common
    own_p = pathlib.Path(own) if pathlib.Path(own).is_absolute() \
        else repo_root / own
    if common_p.resolve() == own_p.resolve() or common_p.name != '.git':
        return None
    return common_p.resolve().parent


def _declared_path(repo_root, raw):
    """-> the directory a declared source `path` names, resolved the one way
    every reader resolves it: variables and ~ expanded, a relative path taken
    from the repo root, and -- in a linked worktree where it is not there --
    from the main checkout instead."""
    entry_path = pathlib.Path(os.path.expandvars(str(raw))).expanduser()
    relative = not entry_path.is_absolute()
    entry_path = (entry_path if not relative else repo_root / entry_path).resolve()
    if relative and not entry_path.exists():
        main = _main_checkout(repo_root)
        if main is not None and (main / raw).exists():
            entry_path = (main / raw).resolve()
    return entry_path


# SETS A PERSON BRINGS (spec/LADDER_OPT_IN_PLAN.md D2, 2026-10-02).
#
# A repository declares the shared sets everyone working in it reads. A
# PERSON may want more than that -- a working method of their own team, say
# -- without putting it on everyone else in every repository they touch. So
# the individual set's own precedent-source.json may list `brings`: shared
# sets that load wherever that person works, at the shared level, cloned
# beside the individual set. Nobody else's session ever sees them, and they
# are never rendered into a committed file (build_views defers them, D6).
#
# Each entry is {"name": <slug>, "repo_url": <full URL>}. A full URL, not a
# bare name: a teammate who brings somebody else's set would otherwise look
# for it under their own account.
#
# A set may say what it PROVIDES (`provides` in its own
# precedent-source.json). One capability is named today, "ladder": the
# five-stage working method. PRECEDENT_NO_LADDERS=1 drops every source that
# provides it, so a person on the ladder can start a session that sees what
# a person off it sees (D13) -- before the session reads anything, which is
# the only point at which leaving text out of a session is possible.
NO_LADDERS_ENV = 'PRECEDENT_NO_LADDERS'
LADDER_CAPABILITY = 'ladder'


# For a test fixture of the tier machinery itself -- Promote, promote_only,
# a pre-staging landing -- whose person brings no set: treat the ladder as
# in force. Never set in a session; PRECEDENT_NO_LADDERS wins over it.
ASSUME_LADDER_ENV = 'PRECEDENT_ASSUME_LADDER'


def assume_ladder():
    return os.environ.get(ASSUME_LADDER_ENV, '').strip() == '1'


def no_ladders():
    """True when this session was started with the ladder switched off."""
    return os.environ.get(NO_LADDERS_ENV, '').strip().lower() not in (
        '', '0', 'false', 'no', 'off')


def source_provides(path):
    """-> the capabilities a source's own precedent-source.json declares, as
    a set of strings; empty when it declares none or cannot be read."""
    try:
        man = json.loads((pathlib.Path(path) / SOURCE_MANIFEST).read_text(
            encoding='utf-8'))
    except (OSError, ValueError):
        return set()
    got = man.get('provides') if isinstance(man, dict) else None
    return {str(x) for x in got} if isinstance(got, list) else set()


# What a `brings` URL may look like. Anything else -- above all a string that
# starts with "-", which git would read as an option to `git clone` rather
# than a repository -- is skipped, never handed to git.
_BRING_URL_RE = re.compile(r'^(?:(?:https?|ssh|git|file)://[^\s]+|git@[^\s:]+:[^\s]+)$')


def brought_sources(individual_path, warn=True):
    """-> [{'level': 'shared', 'name', 'path', 'repo', 'brought': True}] for
    every set the individual set at `individual_path` brings, at the path it
    is cloned to: beside the individual set, named for the set. Entries that
    are not a dict with a valid slug name and a repo_url are skipped, with a
    one-line note on stderr: a typo in one person's file must not take every
    session of theirs down."""
    if not individual_path:
        return []
    ind = pathlib.Path(individual_path).expanduser()
    try:
        man = json.loads((ind / SOURCE_MANIFEST).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    raw = man.get('brings') if isinstance(man, dict) else None
    if not isinstance(raw, list):
        return []
    out, seen = [], set()
    for item in raw:
        name = item.get('name') if isinstance(item, dict) else None
        url = item.get('repo_url') if isinstance(item, dict) else None
        target = (ind.resolve().parent / name).resolve() \
            if isinstance(name, str) and SLUG_RE.match(name or '') else None
        if not isinstance(name, str) or not SLUG_RE.match(name or '') \
                or not isinstance(url, str) or not _BRING_URL_RE.match(url.strip()) \
                or name in seen or target == ind.resolve():
            if warn:
                print(f"precedent resolve: {ind / SOURCE_MANIFEST} has a "
                      f"`brings` entry that is not {{\"name\": <slug>, "
                      f"\"repo_url\": <url>}}, or that names this set "
                      f"itself ({item!r}); it is skipped.",
                      file=sys.stderr)
            continue
        seen.add(name)
        out.append({'level': 'shared', 'name': name,
                    'path': str((ind.resolve().parent / name)),
                    'repo': url.strip(), 'brought': True})
    return out


def declared_source_paths(repo, user_config=None):
    """-> [(path, level, name, note)] for every practice source this repo and
    this person DECLARE, at the paths load_config() resolves -- without
    load_config()'s self-heal, validation or anything else that can clone,
    fetch or write. For a hook that must be fast and never change the disk:
    the freshness guard checks exactly the clones the loader reads, so a
    stale second copy elsewhere cannot pass for the live one (2026-09-30).

    `note` is '' for a clone that is there, or why it cannot be checked (not
    cloned yet, no user config): the caller says so in one line and never
    blocks on it. The repo itself and its repo-local source are left out:
    they are this checkout, which is checked as the project."""
    repo_root = pathlib.Path(repo).resolve()
    out = []
    try:
        cfg = json.loads((repo_root / REPO_CONFIG).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        cfg = {}
    for entry in (cfg.get('sources') if isinstance(cfg, dict) else None) or []:
        if not isinstance(entry, dict) or not entry.get('path'):
            continue
        level = normalize_level(entry.get('level'))
        if level in ('repo-local', 'individual'):
            continue
        path = _declared_path(repo_root, entry['path'])
        if path == repo_root:
            continue
        note = '' if (path / '.git').exists() else 'not cloned here yet'
        out.append((str(path), level, entry.get('name') or level, note))
    user_cfg_path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(USER_CONFIG_ENV, str(DEFAULT_USER_CONFIG))).expanduser()
    try:
        ind = json.loads(user_cfg_path.read_text(encoding='utf-8')).get('individual')
    except (OSError, ValueError, AttributeError):
        ind = None
        out.append(('', 'individual', DEFAULT_INDIVIDUAL_NAME,
                    f'no readable {user_cfg_path}, so the individual set is not known here'))
    if isinstance(ind, dict) and ind.get('path'):
        path = pathlib.Path(ind['path']).expanduser().resolve()
        if path != repo_root:
            note = '' if (path / '.git').exists() else 'not cloned here yet'
            out.append((str(path), 'individual',
                        ind.get('name') or DEFAULT_INDIVIDUAL_NAME, note))
        have = {pathlib.Path(p).resolve() for p, *_ in out if p}
        for b in brought_sources(path, warn=False):
            bp = pathlib.Path(b['path']).resolve()
            if bp == repo_root or bp in have:
                continue
            if no_ladders() and LADDER_CAPABILITY in source_provides(bp):
                continue
            note = '' if (bp / '.git').exists() else 'not cloned here yet'
            out.append((str(bp), 'shared', b['name'], note))
    return out


def _base_branch_of(path):
    """-> the branch a source clone is checked against: its own precedent.json
    base_branch, else main."""
    try:
        base = json.loads((pathlib.Path(path) / REPO_CONFIG).read_text(
            encoding='utf-8')).get('base_branch')
    except (OSError, ValueError, AttributeError):
        base = None
    return base if isinstance(base, str) and base.strip() else 'main'


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
            level = normalize_level(entry.get('level'))
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
            # practice: source-naming
            check_source_name(level, entry.get('name'), str(repo_cfg_path))
            warn_name_matches_path(level, entry.get('name'), entry['path'],
                                   str(repo_cfg_path))
            # Expand `~` and `$HOME` before joining. A source set declaring
            # the universal source cannot write a relative path that is
            # correct everywhere: an individual set is cloned to
            # $HOME/precedent-individual, and $HOME is /root on some
            # containers and /home/user on others, while the shared sets and
            # the consuming repo sit side by side. So "../BestPractice"
            # resolves from a shared set and names nothing from an individual
            # one. Same reasoning, and the same remedy, as
            # PRECEDENT_FRESHNESS_ALSO's "write the path as ~/name, never
            # spelled out". An already-relative path is unaffected: expansion
            # is a no-op on it, and the join still happens against repo_root.
            # practice: upstream-fix
            entry_path = _declared_path(repo_root, entry['path'])
            # practice: session-bootstrap -- a universal source declared but
            # not yet on disk (never cloned, because the SessionStart hook
            # that clones it never ran for this session -- see
            # _self_heal_universal_source above) gets one clone attempt now,
            # before load_source() reports it missing. A path that already
            # has a practices/ dir is left alone: this never re-clones or
            # refreshes an existing checkout, only creates an absent one.
            if level == 'universal' and not (entry_path / 'practices').is_dir():
                _self_heal_universal_source(repo_root)
            src = {'level': level, 'name': entry.get('name', level),
                   'path': str(entry_path)}
            # Where the source is cloned from, when that is not `<base
            # url>/<name>`: a bare repository name (joined to the base URL,
            # so a public consumer still names no account) or a full URL
            # (a private consumer only -- the leak gate's repo-reference
            # rule reads a public tree for exactly this). Optional; absent
            # means the repository is called what the source is.
            if entry.get('repo'):
                src['repo'] = str(entry['repo']).strip()
            sources.append(src)

    user_cfg_path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(USER_CONFIG_ENV, str(DEFAULT_USER_CONFIG))).expanduser()
    def _individual_entry():
        """The declared individual source, or None -- and None means
        'not usable from here', not merely 'the file is absent'.

        The three ways a too-early hook leaves this broken are distinct
        states on disk and used to be treated as one: no config file at
        all, a config file the hook created before it could write an
        `individual` entry, and an entry whose declared clone directory
        the hook never managed to create. Only the first triggered the
        self-heal, so a hook that got half-way through -- which is what a
        hook killed part-way by a failing `git clone` actually leaves --
        was reported as 'this person has no individual set' forever."""
        if not user_cfg_path.exists():
            return None, False, 'no-config-file'
        cfg = _read_json(user_cfg_path, 'the user config')
        ind = cfg.get('individual')
        if not ind or not ind.get('path'):
            return None, False, 'config-declares-none'
        path = pathlib.Path(ind['path']).expanduser()
        entry = {'level': 'individual',
                 'name': ind.get('name', DEFAULT_INDIVIDUAL_NAME),
                 'path': str(path)}
        if ind.get('repo_url'):
            entry['repo'] = str(ind['repo_url']).strip()
        return entry, (path / 'practices').is_dir(), 'declared'

    entry, usable, why = _individual_entry()
    heal = None
    if not usable:
        # practice: session-bootstrap -- a hook that ran too early to have
        # this session's own `add_repo` access yet (guaranteed on a fresh
        # session, not just possible) looks identical, from here, to "this
        # person has no individual set". Try once, now that the agent's own
        # turn (and its add_repo call) has actually happened, before
        # reporting the latter.
        heal = _self_heal_individual_source(repo_root)
        entry, usable, why = _individual_entry()
    # A DECLARED-but-unusable source is still appended: load_source() then
    # reports the real reason ("<path> has no practices/ directory") instead
    # of the source vanishing, which would be the same silence the self-heal
    # exists to break. Only a person who declared nothing gets no entry --
    # and THAT case is now diagnosed rather than passed over: see
    # _diagnose_no_individual, and INDIVIDUAL_STATUS for how it is reported.
    global INDIVIDUAL_STATUS
    INDIVIDUAL_STATUS = (None if entry is not None
                         else _diagnose_no_individual(why, heal, user_cfg_path,
                                                      repo_root))
    if INDIVIDUAL_STATUS and INDIVIDUAL_STATUS['certain'] is False:
        print(f"precedent resolve: {INDIVIDUAL_STATUS['message']}",
              file=sys.stderr)
    if entry is not None:
        # practice: source-naming -- _individual_entry()'s own default is a
        # default; any slug is a name. It is checked here rather than
        # carried into a MANIFEST.json that could never match it.
        check_source_name('individual', entry['name'], str(user_cfg_path))
        warn_name_matches_path('individual', entry['name'], entry['path'],
                               str(user_cfg_path))
        sources.append(entry)
        if usable:
            have = {s['name'] for s in sources}
            for b in brought_sources(entry['path']):
                # A repository that already declares the set wins: it is the
                # same set, and the repository's declaration is the one
                # everybody there reads.
                if b['name'] in have:
                    continue
                if pathlib.Path(b['path']).resolve() == repo_root:
                    continue
                sources.append(b)
    if no_ladders():
        # D13: everything that provides the ladder leaves the session,
        # wherever it was declared.
        sources = [s for s in sources
                   if LADDER_CAPABILITY not in source_provides(s['path'])]
    sources.sort(key=lambda s: _precedence_rank(s['level']))
    # practice: session-bootstrap -- every load_config() caller (_check,
    # _paths, _show, _gate) is a chance to notice the rendered catalogue is
    # stale, not just a missing clone (_self_heal_universal_source above
    # only ever catches the latter). Only when this repo actually declares
    # something to render for: a bare load_config() call against a repo
    # with no sources has nothing SESSION_PRACTICES.md would carry.
    if sources:
        _self_heal_stale_render(repo_root)
    return sources


# IDENTITY MOVED OUT, AND IS RE-EXPORTED HERE (2026-09-10, the same day it
# landed). declared_identity() answers a question about a PERSON; everything
# else in this file answers one about a CATALOGUE. This module is
# CONSUMER_ENGINE_FILES-only on purpose -- a practice set resolves no
# catalogue -- but a practice set is precisely the repo that HAS an
# identity.json, so leaving the resolution here made
# `precedent-individual`'s own commit-author and buenos-aires-dates checks
# report SKIPPED inside the set they belong to. See
# tools/precedent_identity.py's own docstring for the whole reasoning.
#
# Re-exported rather than merely moved: a consuming repo that already calls
# precedent_resolve.declared_identity() keeps working, and there is one
# implementation behind both names.
from precedent_identity import (                                # noqa: F401
    NoDeclaredIdentity,
    declared_identity,
)


def mirrored_prefixes(repo):
    """-> tuple of repo-relative POSIX prefixes ("precedent/universal/",
    "process/upstream/") whose contents this repo MIRRORS from somewhere
    else, and therefore may not edit.

    THE ONE PLACE THIS QUESTION GETS ANSWERED, and why it moved here
    (2026-09-10). Several checks need it -- anything that scans prose and
    would otherwise report findings inside a vendored copy of somebody
    else's catalogue -- and each of them derived it privately from
    `process/manifest.json`'s `upstream.vendored_at`. That file is §1's
    bookkeeping. INSTALL.md §0 step 5 says outright to SKIP it, so in a §0
    install every one of those checks silently lost its exclusion and put
    the vendored catalogue back in scope. A real §0 install's run reported
    dozens of findings inside Precedent's own historical prose -- "states
    34 practices, but practices currently holds 121" -- none of them
    actionable, because editing a mirror is forbidden and the next sync
    would overwrite it anyway. The downstream workaround was to write a
    `process/manifest.json` carrying nothing but an `upstream` block,
    purely to feed a signal.

    `precedent.json` is the authority that EXISTS in exactly the repos
    `process/manifest.json` is missing from, so its declared source paths
    are read here alongside the manifest, and neither file is required.

    WHAT IS AND IS NOT A MIRROR. A declared source whose path resolves
    inside this repo is a vendored copy of another repo's catalogue: a
    mirror. Deliberately excluded from that:

      * the repo root itself -- a SOURCE SET declares `path: "."`, and its
        own `practices/` tree is hand-authored, not mirrored. Treating it
        as a mirror would blind every check inside a practice set to that
        set's own content.
      * `local/` -- the repo-local source is this repo's own practices, by
        the same reasoning (load_config refuses any other path for it).
      * a source resolving OUTSIDE this repo -- a live sibling clone is not
        in this repo's tree at all, so nothing here can report on it.

    The materialized `practices/` tree is also NOT listed, on purpose. It
    is generated, but it is where a consuming repo's practices actually
    live and where several checks are supposed to look; excluding it would
    trade unactionable findings for missing ones.

    Never raises: a caller is a check that must degrade to "exclude
    nothing" rather than take a run down. An empty tuple is a valid,
    meaningful answer -- it is what a source set and a fresh repo return."""
    repo_root = pathlib.Path(repo).resolve()
    prefixes = set()

    def _add(candidate):
        try:
            resolved = pathlib.Path(candidate)
            if not resolved.is_absolute():
                resolved = (repo_root / resolved)
            resolved = resolved.resolve()
            rel = resolved.relative_to(repo_root).as_posix()
        except (ValueError, OSError):
            return                      # outside this repo, or unreadable
        if rel in ('', '.', 'local'):
            return                      # this repo's own, hand-authored
        prefixes.add(rel.rstrip('/') + '/')

    # SIGNAL 1: §1's own bookkeeping, which is what every private copy of
    # this logic read, and which a §0 install does not have.
    try:
        manifest = json.loads(
            (repo_root / 'process' / 'manifest.json').read_text(
                encoding='utf-8'))
        vendored_at = (manifest.get('upstream') or {}).get('vendored_at')
        if vendored_at:
            _add(vendored_at)
    except (ValueError, OSError, AttributeError, TypeError):
        pass

    # SIGNAL 2: the classic §1 layout, whether or not a manifest says so --
    # a repo with the tree and no manifest is a half-finished install, not
    # a repo that owns that tree.
    if (repo_root / 'process' / 'upstream').is_dir():
        _add('process/upstream')

    # SIGNAL 3: every source this repo VENDORS, read off precedent.json.
    # load_config() is deliberately not used: it resolves the individual
    # source, which can self-heal by running a hook and cloning a repo --
    # far too much machinery for a caller that only wants to know which of
    # its own directories are copies.
    try:
        declared = json.loads(
            (repo_root / 'precedent.json').read_text(
                encoding='utf-8')).get('sources') or []
        for entry in declared:
            path = (entry or {}).get('path')
            if path:
                _add(path)
    except (ValueError, OSError, AttributeError, TypeError):
        pass

    return tuple(sorted(prefixes))


class NotBindingError(Exception):
    """A `not_binding` declaration that is itself malformed. Raised rather
    than tolerated: an exemption mechanism that silently ignores its own bad
    entries is a way to opt out of a rule by typo."""


def load_not_binding(repo, user_config=None):
    """-> {slug: reason} for practices this repo declares are IN FORCE at
    their source but do NOT bind this repository.

    WHY THIS VOCABULARY EXISTS (2026-09-06, closing TODO's
    `unreachable-practices`). Of 114 practices in force in Precedent's own
    repo, 43 were reachable by no loading channel at all -- and running the
    source-supplied checks against the tree showed the answer is not "turn
    them all on": some pass, some report real findings, and some report
    things this repo cannot act on because THE PRACTICE IS ABOUT A DIFFERENT
    KIND OF REPOSITORY (one a single person authors alone, or a practice
    set's own shipped content). The system had no way to say "in force at
    this level, does not bind this repo", so silence was doing that job --
    which is why a forgotten rule and a deliberately-inapplicable one looked
    identical.

    WHY IT IS DECLARED BY THE CONSUMING REPO, not by the practice. Whether a
    rule binds is a property of the PAIR, not of the rule: `commit-author`
    binds a repo one person authors alone and not one with many
    contributors, and the practice cannot know which repos it will reach.
    The repo knows why a rule does not bind it; the practice does not.

    WHY EVERY ENTRY NEEDS A WRITTEN REASON. An exemption list is a way to
    opt out of rules, so the guard has to be that opting out is *visible and
    argued*, never merely declared. A reasonless entry is refused, a stale
    entry (naming a slug nothing puts in force) is reported by the caller,
    and `severity: blocking` cannot be exempted at all -- the same rule the
    resolver already applies to precedence, for the same reason: a blocking
    practice is precisely the one no downstream declaration may switch off.

    This is NOT a way to silence a rule that is merely inconvenient. The
    reason is read by people, and the audit that reads it is
    practices/full-practice-audit.md."""
    repo_root = pathlib.Path(repo).resolve()
    out = {}
    cfg_path = repo_root / REPO_CONFIG
    if not cfg_path.exists():
        return out
    cfg = _read_json(cfg_path, 'the repository config')
    raw = cfg.get('not_binding', [])
    if not isinstance(raw, list):
        raise NotBindingError(
            f"{cfg_path}: `not_binding` must be a list of "
            f"{{slug, reason}} objects, got {type(raw).__name__}.")
    for entry in raw:
        if not isinstance(entry, dict):
            raise NotBindingError(
                f"{cfg_path}: every `not_binding` entry must be an object "
                f"with `slug` and `reason`, got {entry!r}.")
        slug = entry.get('slug')
        reason = (entry.get('reason') or '').strip()
        if not slug:
            raise NotBindingError(
                f"{cfg_path}: a `not_binding` entry has no `slug`: {entry!r}.")
        if not reason:
            raise NotBindingError(
                f"{cfg_path}: `not_binding` entry {slug!r} has no `reason`. "
                f"An exemption without a stated reason is the same silence "
                f"this mechanism exists to replace -- say why the rule does "
                f"not bind this repository.")
        out[slug] = reason
    return out


def load_source(source):
    """-> ({slug: practice}, missing_reason or None). A source directory holds
    its practices in practices/, the same layout Precedent itself uses."""
    d = pathlib.Path(source['path']) / 'practices'
    if not d.is_dir():
        return {}, f"{source['path']} has no practices/ directory"
    # practice: source-naming -- identity is read off the source, never
    # inferred from its name.
    source['manifest'] = check_source_manifest(source)
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


def _requires(fm):
    """-> the capabilities a practice's `requires:` names, as a set."""
    raw = fm.get('requires')
    if raw in (None, '', 'null', '[]'):
        return set()
    try:
        got = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        got = [raw]
    if isinstance(got, str):
        got = [got]
    return {str(x).strip() for x in got or [] if str(x).strip()}


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
    # `requires` (spec/LADDER_OPT_IN_PLAN.md D11, 2026-10-02): a practice
    # that names a capability is in force only while a source in force
    # provides it -- a person's own "for me, the ladder" rule goes quiet in
    # a session started with PRECEDENT_NO_LADDERS, which load_config has
    # already applied to `sources`. Left out, not retired: nothing about the
    # practice is stale, the session simply does not have what it needs.
    provided = set()
    for _s, _loaded in by_source:
        provided |= source_provides(_s['path'])
    for _s, loaded in by_source:                      # lowest precedence first
        claims = override_claims_by_level.setdefault(_s['level'], {})
        for slug, practice in sorted(loaded.items()):
            if bv._json_str(practice['fm'].get('status', 'active')) != IN_FORCE_STATUS:
                retired.append(practice)
                continue
            needs = _requires(practice['fm'])
            if needs and not needs <= provided:
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
                # Two DIFFERENT sources at the SAME level claiming one slug
                # is not a precedence question -- there is no precedence
                # between them to fall back on, so the winner would be
                # whichever the config happens to list second. The plan
                # says this fails loudly ("the resolver fails loudly if two
                # same-level practices claim one slug"), and until
                # 2026-09-06 it did not: two shared sources with a shared
                # slug resolved silently to the later one, reported only as
                # an `overridden:` notice on stderr that reads exactly like
                # a legitimate higher-level override. load_source() already
                # refuses this WITHIN one source; this is the same rule
                # across sources at one level.
                if prior_own['level'] == practice['level']:
                    raise ResolveError(
                        f"{practice['source']} and {prior_own['source']} are "
                        f"both {practice['level']}-level sources and both "
                        f"define the practice {slug!r} "
                        f"({practice['file']} and {prior_own['file']}). Slugs "
                        f"are identities; nothing orders two sources at the "
                        f"same level, so there is no answer to which one "
                        f"wins -- rename one of them, retire one, or move "
                        f"one to a different level.")
                shadowed.append({'slug': slug, 'shadowed': prior_own, 'by': practice})
            resolved[slug] = practice
    # A non-active practice's forwarding address, checked against what this
    # resolution actually put in force -- the callable build_views'
    # status_contract_violation asks for and, until 2026-09-14, only the
    # harness ever passed. Every set and consumer ran the shape check alone,
    # so `in_force_at:` naming a slug that resolved nowhere was reported by
    # nothing they could run (practice: verify-postcondition). This is the
    # state a rule is in when it was withdrawn at one level and the landing
    # at the other never reached this repo: a copy-and-delete, a destination
    # set not declared here, or a universal landing this consumer has not
    # taken yet.
    # Deduplicated ones only: a retirement's own contract (a Story saying
    # why nobody wants the rule) is the publishing set's to keep, and its
    # own check reports it there; repeating it into every consumer's sync
    # would be noise nobody downstream can act on.
    # The forwarding address is followed, not just looked up: a
    # deduplication may name a slug that is itself a deduplicated stub one
    # level down. Renaming go-merge to go-update on 2026-09-26 left a
    # universal `go-merge` stub forwarding to `go-update`, and an individual
    # set's own `go-merge`, deduplicated against the universal one, read IN
    # FORCE NOWHERE in every consumer -- the rule was live the whole time,
    # one hop further on.
    dangling = []
    for practice in retired:
        if bv.practice_status(practice['fm']) != bv.DEDUPLICATED_STATUS:
            continue
        msg = bv.status_contract_violation(
            practice['fm'], practice.get('sections'),
            slug_in_force=lambda s: follow_in_force_at(s, resolved, retired) is not None)
        if msg:
            entry = {'slug': practice['slug'], 'source': practice['source'],
                     'level': practice['level'], 'file': practice['file'],
                     'why': msg}
            # A universal copy withdrawn ON PURPOSE to a set this repo does
            # not declare is not "the deduplication that silently loses a
            # rule": precedent_move.py wrote down where it went and that the
            # reach loss was accepted. Said as that, so a reader can act on
            # it (declare the set) instead of hunting a bug. Still reported
            # -- the rule does not bind here, and whether that is fine is
            # this repo's call.
            gone = withdrawn_from_universal(practice.get('sections'))
            if gone:
                entry.update(withdrawn_on=gone[0], withdrawn_to=gone[1],
                             why=(f"withdrawn from universal on {gone[0]}; in "
                                  f"force in `{gone[1]}` -- declare that set "
                                  f"to keep it"))
            dangling.append(entry)
    return {'practices': resolved, 'shadowed': shadowed, 'blocked': blocked,
            'missing': missing, 'retired': retired, 'dangling': dangling}


# The Story line tools/precedent_move.py appends when it withdraws a
# universal practice with --accept-reach-loss: "Withdrawn from universal on
# <date>, deliberately, with --accept-reach-loss[ (approved by X)]:
# deduplicated here; the rule is in force only from the <level> set `<set>`
# now." Read back rather than stored as a new frontmatter field: a field
# would change the practice-file format every set and consumer vendors, and
# this sentence is already on every such stub.
_WITHDRAWN_RE = re.compile(
    r'Withdrawn from universal on (\d{4}-\d\d-\d\d)\b.*?'
    r'in force only from the \w+ set `([^`]+)`', re.S)


def withdrawn_from_universal(sections):
    """-> (date, set name) when a deduplicated stub's ## Story records a
    deliberate withdrawal from universal, else None. The LAST such line
    wins, the way the latest Story line is the current record."""
    story = (sections or {}).get('story') or ''
    found = _WITHDRAWN_RE.findall(story)
    return tuple(found[-1]) if found else None


def follow_in_force_at(slug, resolved, retired):
    """-> the slug IN FORCE that `slug` ends on once every deduplication's
    `in_force_at:` is followed, or None when the chain ends nowhere.

    `resolved` is resolve()'s {slug: practice} in force; `retired` its list
    of non-active practices. A slug in force is its own answer. Otherwise
    every DEDUPLICATED practice claiming that slug -- more than one source
    can carry the same stub, and a set's copy can name the very slug it
    carries -- is a hop to its own target. Stops on a slug already seen, so
    a cycle (a -> b -> a, or a set's `go-merge` naming `go-merge`) ends in
    None rather than a hang; `engine` and `none` are not slugs and end a
    branch of the walk."""
    hops = {}
    for practice in retired:
        if bv.practice_status(practice['fm']) != bv.DEDUPLICATED_STATUS:
            continue
        target = bv._json_str(practice['fm'].get('in_force_at', '')) or ''
        if target and target not in (bv.IN_FORCE_AT_ENGINE, bv.IN_FORCE_AT_NOWHERE):
            hops.setdefault(practice['slug'], []).append(target)
    seen, queue = set(), [slug]
    while queue:
        s = queue.pop(0)
        if s in seen:
            continue
        seen.add(s)
        if s in resolved:
            return s
        queue.extend(hops.get(s, ()))
    return None


def forwarding_map(res):
    """-> {slug: live slug} for every deduplicated slug not itself in force
    whose `in_force_at:` chain ends on a slug that is. What a link to a
    renamed or deduplicated practice's file should point at instead
    (precedent_materialize._rewrite_links), since a consumer materializes
    only practices in force and never the stub the link names."""
    resolved, retired = res['practices'], res.get('retired', [])
    out = {}
    for practice in retired:
        slug = practice['slug']
        if slug in resolved or slug in out:
            continue
        if bv.practice_status(practice['fm']) != bv.DEDUPLICATED_STATUS:
            continue
        live = follow_in_force_at(slug, resolved, retired)
        if live is not None:
            out[slug] = live
    return out


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
    cross-source cap" -- nothing ever did. A shared set marking six practices
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
    for d in res.get('dangling', ()):
        print(f"  IN FORCE NOWHERE: {d['slug']} ({d['source']}) -- {d['why']}",
              file=out)
    if res.get('dangling'):
        print(f"  {len(res['dangling'])} deduplication(s) unreachable from "
              f"here -- rerun with --strict to fail on this", file=out)
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
    known = {'--json', '--repo', '--explain', '--strict', '--user-config',
             '--declared-paths'}
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
    if '--declared-paths' in args:
        # One line per declared source: path, base branch, level, name, and
        # why it cannot be checked ('' when it can). Never clones, fetches or
        # writes -- the freshness guard runs this on every session.
        for path, level, name, note in declared_source_paths(repo, user_config):
            base = _base_branch_of(path) if path and not note else ''
            print('\t'.join((path, base, level, name, note)))
        return 0

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
                f"shared sources in a tracked {REPO_CONFIG}; a person declares their "
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
    if (res['missing'] or res.get('dangling')) and '--strict' in args:
        return 1

    if explain:
        return _explain(explain, res, sources)

    rstats = resident_stats(res)
    # A dedup pointing IN FORCE NOWHERE is real exposure -- a rule someone
    # believes is still binding is reachable by nobody, for this repo -- but
    # it is a PRE-EXISTING condition every consumer inherited silently, not
    # something this run caused. Flipping the default exit code for it would
    # turn every consumer's next `--check` red with no warning. --strict is
    # the same opt-in already used for a missing source, for the same
    # reason; the count above makes it visible either way.
    rc = 1 if ((res['missing'] or res.get('dangling')) and '--strict' in args) else 0
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
            'dangling': [{'slug': d['slug'], 'source': d['source'],
                          'why': d['why'],
                          **({'withdrawn_to': d['withdrawn_to']}
                             if d.get('withdrawn_to') else {})}
                         for d in res.get('dangling', ())],
            # None when an individual source was declared (its fate is then
            # in 'missing' like any other source's). Otherwise says whether
            # "no individual practices" is a finding or merely a silence.
            'individual_status': INDIVIDUAL_STATUS,
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
