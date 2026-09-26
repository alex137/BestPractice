#!/usr/bin/env python3
"""precedent_refresh_sources.py -- find the practice-set sources attached to
this session and tell whether their vendored engine is out of date; with
--apply, bring them up to date.

WHY THIS EXISTS, AND THE INCIDENT THAT PRODUCED IT (practice:
cite-the-incident). A source set -- someone's own precedent-individual, a
team's precedent-team-* -- vendors this repo's engine as tracked files.
Nothing told anyone when that copy went stale. On 2026-09-06 two real sets
sat at ef8b5d09 while this branch moved more than two hundred commits past
it, and both were generating a loader block with a defect fixed upstream
days earlier (a standing instruction advertising four gate commands, all
four of which failed there). It surfaced only because a session happened to
have a BestPractice clone attached and happened to run `status` by hand.

The asymmetry that made this possible is worth stating plainly, because it
is the thing this tool closes. A CONSUMER repo vendors process/upstream/ as
tracked files, and its bootstrap runs a freshness check at session start --
so "your copy is behind" reaches a person without anyone deciding to look.
A SOURCE set had neither: `precedent_vendor_engine.py status` needs a local
clone of this repo to compare against, and a fresh session has no reason to
have one.

This runs from THIS repo's own checkout, which by definition IS that clone.
Every session working here already has, on disk, exactly what a source set
needs to answer the question -- so the check costs nothing and needs no
network beyond what is already fetched.

WHAT IT DELIBERATELY DOES NOT DO. It never pushes and never opens a pull
request. `--apply` refreshes the vendored files and regenerates the views,
and `--commit` will commit that on a branch in the target repo; publishing
it stays a person's (or a session's) explicit act, per that repo's own
merge rules, which this tool has no way to know.

THERE IS NO UNATTENDED PATH, AND THAT IS THE DECISION (2026-09-14). This
paragraph used to end by naming one -- "the scheduled workflow the source
templates now ship" -- which was wrong twice over: the templates never
shipped one (added 2026-09-06, pulled the same day), and as of 2026-09-14
no repository runs a scheduled engine refresh at all. Morgan, in his own
words: "I think that engine-refresh.yml is now doing an automatic update
weekly. Let's stop that. No weekly updates. I had that weeks ago, but we're
not doing that anymore; this is now really complex and deserves hand
attention and issues come up every time and I'm on it every day anyway."
The replacement channel is a person saying "Update Vendors" in a session
(practices/vendor-update-runbook.md). So this tool's report, and the
session-start line it prints, are the whole notification story -- if
nobody is looking, nothing tells anybody.

CLARIFIED 2026-09-15: the paragraph above was about the WEEKLY, unattended
workflow specifically, not about a session's own bootstrap applying this
tool's report to its own working tree. Morgan: "my objection was to the
WEEKLY updates that were automatic; I never objected to START OF SESSION
checks that are automatic, I LOVE THAT." (strength: decided).
`.claude/hooks/session-start.sh` now calls this with `--apply`
unconditionally, every session, for the reason its own comment gives: a
session working from a BestPractice checkout already has everything this
tool needs, so applying costs nothing further and closes the round trip
every earlier session had to make by hand (notice STALE, then run
--apply). This is still not the retired mechanism -- it runs once, inside
a session someone is sitting in, against that session's own working tree,
and it still never commits or pushes on its own; --commit remains a
separate, explicit flag. The dirty-tree check in the stale loop below
(added the same day) is what keeps this from being the auto-apply that
would have made 2026-09-14's decision moot: a source with its own
uncommitted changes is left alone rather than silently overwritten.

A SECOND THING THIS COVERS, AND WHY IT IS THE SAME TOOL (added
2026-09-09). A source set also carries its own session hooks -- the
freshness guard, the commit-identity backstop, and since 2026-09-13 the
individual-source bootstrap that makes the person's own practice set
resolve there at all -- installed by
tools/precedent_bootstrap_source.py when the set is created. Sets created
BEFORE that existed never got them, and nothing has ever repaired one:
there was an install path and no refresh path, which is the same asymmetry
this tool was built to close for the vendored engine, one directory over.
Found on 2026-09-09 in a real individual source: a .claude/settings.json
present, .claude/hooks/ absent entirely, every session there running with
its guards off and nothing saying so.

Hooks are checked and repaired INDEPENDENTLY of engine staleness, because
they are independent: a set can be current at the tip and still have no
hooks at all, which is precisely the state that was found. An existing
settings.json is never rewritten -- if it wires something this tool does
not recognise, that is reported for a person to read, not resolved by
guesswork.

Run:
  python3 tools/precedent_refresh_sources.py                 # report
  python3 tools/precedent_refresh_sources.py --check         # exit 1 if any stale
  python3 tools/precedent_refresh_sources.py --apply         # refresh + regenerate
  python3 tools/precedent_refresh_sources.py --apply --commit
  python3 tools/precedent_refresh_sources.py --path ../other-set
Exit: 0 always, except --check with a stale source, or a malformed manifest.
"""
import json, os, pathlib, re, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_resolve

# The hook installer, imported rather than reimplemented: settings.json's
# payload and the hook list have exactly one definition, in the tool that
# creates a source set, and this one repairs what that one installs. A
# second copy here would drift, and the drift would be invisible -- both
# copies would keep producing a settings.json that looked right.
# Neither module is in precedent_vendor_engine.ENGINE_FILES, so both run
# only from a BestPractice checkout, where this import always resolves.
# The pin's own answer for which branch a source belongs on, imported rather
# than restated: a report that disagreed with the tool that does the pinning
# would be worse than no report at all.
try:
    import precedent_source_bootstrap as _srcboot
except Exception:
    _srcboot = None

try:
    import precedent_bootstrap_source as _bootstrap
except Exception as exc:            # reported below, never raised: a hook
    _bootstrap = None               # problem must not take down the engine
    _bootstrap_err = f'{type(exc).__name__}: {exc}'   # staleness report
else:
    _bootstrap_err = None

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE_BRANCH = 'main'   # kept in step with precedent_vendor_engine.SOURCE_BRANCH
MANIFEST = 'tools/ENGINE_MANIFEST.json'


def _git(*args, cwd=None):
    """(ok, stdout). Never raises, and NEVER returns stdout on a non-zero
    exit -- `git rev-parse <missing-ref>` exits 1 but PRINTS the ref name it
    was asked for, which a caller that only reads stdout will happily carry
    forward as if it were a commit hash. That exact bug reached CI in this
    repo on 2026-09-06 (see AGENTS.md's gotchas section); returning the
    exit code alongside the text is what makes it unrepeatable here."""
    try:
        r = subprocess.run(['git', *args], cwd=str(cwd or ROOT),
                           capture_output=True, text=True)
    except OSError as exc:
        return False, str(exc)
    return r.returncode == 0, (r.stdout or r.stderr).strip()


def session_trailer():
    """-> the session-trailer line for a commit THIS TOOL authors.

    practice: session-trailer -- a commit carrying no trailer at all is the
    "forgotten" case that practice exists to make distinguishable from
    "considered and skipped", and every set this tool commits into runs
    check_session_trailer.py over its own history. Until 2026-09-14 both
    commit sites below wrote a message with no trailer of any kind, so every
    --commit run produced a commit its own target repo's check then refused:
    a four-set refresh that day landed four violations at once, each of which
    had to be rewritten by hand before it could be pushed. A tool that writes
    a commit the repo will reject is not a convenience.

    This tool has no chat session of its own to link, so the default is the
    practice's own explicit opt-out form rather than silence.
    PRECEDENT_SESSION_URL lets a session that DOES have a link hand it over,
    and then the commit carries the real thing.
    """
    url = (os.environ.get('PRECEDENT_SESSION_URL') or '').strip()
    if url:
        return f'Session: {url}'
    return 'Session: none available (tools/precedent_refresh_sources.py)'


def head_commit():
    """This checkout's own tip for SOURCE_BRANCH -- what a source set that
    refreshed right now would end up recording.

    Prefers the remote-tracking ref over local HEAD: a session working on a
    feature branch here has a HEAD that is not what anyone would vendor, and
    recording a feature-branch commit into a source set's manifest would
    make its provenance name a commit that may never reach the branch."""
    ok, out = _git('rev-parse', '--verify', '--quiet', f'origin/{SOURCE_BRANCH}')
    if ok and out:
        return out, f'origin/{SOURCE_BRANCH}'
    ok, out = _git('rev-parse', '--verify', '--quiet', SOURCE_BRANCH)
    if ok and out:
        return out, SOURCE_BRANCH
    return None, None


def declared_paths():
    """Where the sources in force here actually live, per the configs that
    decide it -- this repo's own precedent.json for team sources, and the
    user-level config for the individual one.

    Siblings alone are not enough, and finding that out is what added this.
    A person's individual set is cloned to wherever their user-level config
    names ($HOME/precedent-individual, by the convention the individual
    set's own bootstrap hook uses) -- which is nowhere near this checkout's
    parent directory. Scanning only siblings would have reported on a copy
    that happened to be attached to a session while silently ignoring the
    one their sessions actually load."""
    out = []
    try:
        for s in precedent_resolve.load_config(ROOT):
            if s.get('level') in ('shared', 'team', 'individual') and s.get('path'):
                out.append(pathlib.Path(s['path']).expanduser().resolve())
    except Exception:
        # Any config problem is precedent_resolve's to report, loudly, in
        # its own run. Here it must not take down an advisory check that
        # still has siblings to look at.
        pass
    return out


def candidate_dirs(extra_paths=()):
    """Directories that might hold a source set: this checkout's siblings,
    plus anything named explicitly.

    Siblings, because that is where an attached repo actually lands -- a
    session with several repos attached gets them side by side under one
    parent. Not a filesystem-wide search: a wide walk would be slow, would
    reach into places nobody asked about, and would turn an unrelated repo
    that happens to vendor this engine into something this tool reports on."""
    seen, out = set(), []
    for p in [*(pathlib.Path(x).expanduser().resolve() for x in extra_paths),
              *declared_paths(),
              *sorted(ROOT.parent.iterdir())]:
        if p == ROOT or not p.is_dir() or p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def _label(repo):
    """A path, not a basename. Two different clones of one set legitimately
    coexist -- a session-attached copy beside this checkout, and the one a
    person's user config actually points at under $HOME -- and they can be
    at different commits. Printing just the directory name rendered them as
    two identical-looking lines with different verdicts."""
    try:
        return '~/' + str(repo.relative_to(pathlib.Path.home()))
    except ValueError:
        return str(repo)


def read_manifest(repo):
    path = repo / MANIFEST
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        return {'_error': str(exc)}


def survey(extra_paths=()):
    """-> (tip, [{repo, kind, recorded, stale, error}]). One entry per repo
    that actually carries a vendored engine; everything else is not this
    tool's business and is silently skipped."""
    tip, tip_ref = head_commit()
    found = []
    for repo in candidate_dirs(extra_paths):
        man = read_manifest(repo)
        if man is None:
            continue
        if '_error' in man:
            found.append({'repo': repo, 'kind': '?', 'recorded': None,
                          'stale': None, 'error': f"unreadable {MANIFEST}: {man['_error']}"})
            continue
        recorded = str(man.get('source_commit') or '')
        # A '+dirty' suffix means the vendored bytes came from a working
        # tree, not a commit (precedent_vendor_engine.seed writes it that
        # way on purpose). It can never equal a real hash, so it always
        # reads as stale -- which is the honest answer: nobody can tell what
        # those bytes are.
        stale = None if not tip else (recorded != tip)
        found.append({'repo': repo, 'kind': man.get('kind', '?'),
                      'recorded': recorded, 'stale': stale, 'error': None,
                      'hooks': hook_state(repo),
                      'branch': branch_state(repo)})
    return tip, tip_ref, found


def engine_owned_paths(repo):
    """-> set of repo-relative paths this clone's own manifest says the
    ENGINE writes, plus the manifest itself.

    The three lists are keyed differently and that is not a detail: `files`
    are bare names under `tools/`, `hook_files` bare names under
    `.claude/hooks/`, and `ci_workflow_files` are already repo-relative.
    Getting one of those prefixes wrong would make a person's real edit look
    like engine output, which is the one mistake this function must never
    make, so each is joined explicitly rather than by a shared rule.

    The manifest is not listed in `files` -- it is what does the listing --
    but the refresh rewrites it on every run, so it belongs here.

    SO DO THE FULLY GENERATED VIEWS, added 2026-09-22. `build_views.py`
    rewrites MAP.md and GLOSSARY.md in every source clone on every refresh,
    from `practices/` alone, and they are in none of the three manifest
    lists -- `files` are bare names under `tools/`, and a generated view at
    the repo root is not one. So every refreshed clone carried a modified
    MAP.md that read as somebody's uncommitted edit, which skipped the
    refresh and, from 2026-09-22, made the container scanner call the
    container unsafe on every reply. The names come from build_views.py
    itself rather than being repeated here; AGENTS.md is deliberately not
    among them, because only its loader block is generated and the rest is
    a person's prose (that file's own note says why)."""
    man = read_manifest(repo)
    if not man or '_error' in man:
        return set()
    owned = {f'{MANIFEST}'}
    for name in man.get('files') or []:
        owned.add(f'tools/{name}')
    for name in man.get('hook_files') or []:
        owned.add(f'.claude/hooks/{name}')
    for name in man.get('ci_workflow_files') or []:
        owned.add(str(name))
    # Lazily, and never fatally: a vendored engine that arrived without
    # build_views.py still classifies everything the manifest names
    # (practice: fail-gracefully). The literal is that module's own tuple,
    # kept here only as the fallback.
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import build_views as _bv
        views = _bv.FULLY_GENERATED_VIEWS
    except Exception:                                         # noqa: BLE001
        views = ('MAP.md', 'GLOSSARY.md')
    owned.update(views)
    # AND THE ENGINE'S OWN CURRENT FILE LISTS, added 2026-09-22 -- because
    # everything above is read from the DESTINATION's manifest, which is a
    # snapshot of the last refresh and therefore lags the engine by exactly
    # one refresh for any newly added file. That lag is not an edge case: it
    # is the guaranteed state of every clone between "a file is added to
    # ENGINE_FILES upstream" and "this clone refreshes again", and the
    # refresh is the very thing the misclassification skips. So the lag
    # sustains itself.
    #
    # WHAT IT COST, measured the same day. `precedent_container_safe.py` was
    # added to ENGINE_FILES on 2026-09-21 and written into
    # `precedent-individual`. Its manifest did not name it, so classify_dirt
    # called it a person's untracked work, the container scanner called the
    # container unsafe, and the archive gate went red on every single reply
    # -- about a file byte-identical to one already tracked and pushed in
    # BestPractice, which could not have been lost by anything.
    #
    # The clause above already states the principle: "the manifest is a
    # DECLARATION of what the engine writes, not a listing of what is
    # tracked". This finishes it. The engine's own lists are the same
    # declaration one level up and they do not lag, so a name in them is the
    # engine's whether this clone's manifest has caught up or not. It is the
    # identical test precedent_vendor_engine._untracked_engine_files already
    # applies from the other side -- it calls such a file "a hand-copy
    # dropped in beside the vendored engine" and says `refresh` is its fix.
    # Both halves existed; they did not share the set.
    #
    # SCOPED, and the scoping is what keeps this safe: read_manifest above
    # has already returned for a repo that vendors no engine, so a repo with
    # its own tools/ and no manifest can never have a file of its own
    # reclassified as engine output by this. Within a repo that DOES vendor,
    # a file carrying an engine file's name either is one or is the hand-drop
    # that check exists to catch -- and both want `refresh`, not a person's
    # attention as lost work.
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_vendor_engine as _ve
        for name in set(_ve.ENGINE_FILES) | set(_ve.CONSUMER_ENGINE_FILES):
            owned.add(f'tools/{name}')
    except Exception:                                         # noqa: BLE001
        pass          # fail-gracefully: the manifest half still classifies
    return owned


def classify_dirt(repo):
    """-> (engine_dirt, other_dirt), each a sorted list of repo-relative paths.

    THE LOOP THIS EXISTS TO BREAK, measured 2026-09-21 across four sources
    that were 17 to 34 commits behind their own origin. The refresh writes
    engine files into a source clone and deliberately never commits them --
    `this tool never publishes`. The clone is then dirty, so the next
    session's `git pull --ff-only` refuses to run and the dirty-guard below
    skips. Nothing exited non-zero and the closing line read `applied.`
    either way, so four sources drifted for weeks while every run reported
    success. Every dirty path in all four was engine output nobody had
    hand-edited.

    The guard is right and stays. Its own comment says what it is for -- a
    person's uncommitted edit mid-review -- and it simply could not tell that
    from the tool's own output, so the tool's output disarmed the tool.

    A rename or a deletion is NOT engine dirt even when the path is owned:
    the engine rewrites files in place, so anything else in the status
    porcelain is a person moving things around and is left well alone.

    AN UNTRACKED OWNED PATH IS, since 2026-09-22. `M` alone was the test,
    and a NEWLY vendored engine file does not arrive modified -- it arrives
    as `??`, because the clone has never tracked it. Adding one file to
    ENGINE_FILES upstream therefore made three source clones read as
    carrying somebody's uncommitted work, which skipped their refresh and
    made the archive gate red on every reply. The manifest is a
    DECLARATION of what the engine writes, not a listing of what is
    tracked, so a path it names is the engine's whether git has seen it
    before or not -- and that manifest's own `_note` tells people never to
    hand-write a file it lists."""
    ok, out = _git('status', '--porcelain', cwd=repo)
    if not ok:
        return [], []
    owned = engine_owned_paths(repo)
    engine, other = [], []
    # NOT a fixed-width slice of the porcelain line. `_git` strips its whole
    # output, so the FIRST line loses the leading space of a ` M path` status
    # and every later line keeps it -- slicing `line[3:]` then ate a
    # character off exactly one path per repo, silently, and that path
    # stopped matching the owned set. Caught by running this against the
    # four real clones before wiring it to anything.
    for line in out.splitlines():
        m = re.match(r'^\s*([A-Z?!]{1,2}|[A-Z?!] )\s+(.*)$', line)
        if not m:
            continue
        code, path = m.group(1).strip(), m.group(2).strip()
        if ' -> ' in path:                       # a rename; never ours
            other.append(path)
            continue
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        is_engine = code in ('M', '??') and path in owned
        (engine if is_engine else other).append(path)
    return sorted(engine), sorted(other)


def discard_engine_dirt(repo, paths):
    """Put the engine's own output back the way the last commit had it.
    -> (ok, note-on-failure).

    TWO KINDS, and `git checkout --` only handles one. A tracked file that
    the engine rewrote is restored. An untracked one it has never seen --
    a newly vendored engine file, the case classify_dirt was widened for --
    makes `checkout --` fail outright with "did not match any file(s) known
    to git", which would have turned a working refresh into a refusal. It is
    REMOVED instead: the refresh that immediately follows make_current
    rewrites every path in this set, so the file is back, from upstream,
    within the same run."""
    if not paths:
        return True, ''
    ok, listed = _git('ls-files', '--', *paths, cwd=repo)
    tracked = set(listed.splitlines()) if ok else set(paths)
    restore = [p for p in paths if p in tracked]
    remove = [p for p in paths if p not in tracked]
    if restore:
        ok, out = _git('checkout', '--', *restore, cwd=repo)
        if not ok:
            return False, f'could not discard engine output: {out}'
    for rel in remove:
        try:
            (pathlib.Path(repo) / rel).unlink()
        except OSError as exc:
            return False, f'could not remove engine output {rel}: {exc}'
    return True, ''


def make_current(repo, branch):
    """Bring one source clone's working tree to origin/<branch>.

    -> (ok, note). Discards engine dirt first, because `pull --ff-only`
    refuses to run over it and the refresh about to follow rewrites every
    one of those files anyway. A person's own dirt is never touched: the
    caller has already refused in that case.

    DIVERGENCE IS NOT REPAIRED HERE, on purpose. A clone carrying its own
    unpushed commits needs a person -- rebasing or resetting someone's work
    to get a vendoring tool unstuck is exactly the trade this whole loop was
    made of. It is reported and left alone."""
    ok, _ = _git('fetch', '--quiet', 'origin', branch, cwd=repo)
    if not ok:
        return False, f'could not fetch origin/{branch}'
    ok, counts = _git('rev-list', '--left-right', '--count',
                      f'origin/{branch}...HEAD', cwd=repo)
    if ok and counts:
        parts = counts.split()
        if len(parts) == 2 and parts[1] != '0':
            return False, (f'{parts[1]} local commit(s) not on origin/{branch} '
                           f'({parts[0]} behind) -- a person has to resolve this; '
                           f'nothing was changed')
        if len(parts) == 2 and parts[0] == '0':
            return True, 'already current'
    engine, _other = classify_dirt(repo)
    if engine:
        ok, note = discard_engine_dirt(repo, engine)
        if not ok:
            return False, note
    ok, out = _git('merge', '--ff-only', f'origin/{branch}', cwd=repo)
    if not ok:
        return False, out.splitlines()[-1] if out else 'ff-only merge refused'
    # practice: verify-postcondition -- the state wanted is "this working
    # tree is at origin/<branch>", never "the command said ok".
    ok_h, head = _git('rev-parse', 'HEAD', cwd=repo)
    ok_o, want = _git('rev-parse', f'origin/{branch}', cwd=repo)
    if not (ok_h and ok_o and head and head == want):
        return False, (f'merge reported success but HEAD is {head[:12] or "?"} '
                       f'and origin/{branch} is {want[:12] or "?"}')
    note = f'now at origin/{branch} {head[:12]}'
    if engine:
        note += f' (discarded {len(engine)} file(s) of engine output)'
    return True, note


def _declared_base_branch(root):
    """The branch a source set's work is measured against, as DECLARED in
    its own precedent.json `base_branch` -- not inferred from origin/HEAD.

    Same helper, same reasoning, as doc_lint.py's: origin/HEAD answers "what
    does GitHub show first", and every caller here means "what lineage does
    this work belong to". This repo is itself the standing counterexample --
    its default branch is main and its work is on precedent-beta-v01 -- and
    wiring a source set's freshness guard to the wrong one of those makes it
    compare against a lineage that set never touches, silently. Returns None
    when undeclared or unreadable, so the caller falls back rather than
    breaking (practice: fail-gracefully). Enforced by precedent_check.py's
    `declared-base-branch`."""
    try:
        v = json.loads((pathlib.Path(root) / 'precedent.json')
                       .read_text(encoding='utf-8')).get('base_branch')
        return v if isinstance(v, str) and v.strip() else None
    except Exception:
        return None


def _default_branch(repo):
    """The base branch freshness-guard.sh gets wired to compare against.

    Declaration first, inference second, `main` last -- and `main` is a
    fallback, not an answer. Both git calls are consulted for their EXIT
    CODE as well as their text, per the _git() note above."""
    declared = _declared_base_branch(repo)
    if declared:
        return declared
    ok, out = _git('symbolic-ref', '--quiet', 'refs/remotes/origin/HEAD', cwd=repo)
    if ok and out.startswith('refs/remotes/origin/'):
        return out.rsplit('/', 1)[-1]
    ok, out = _git('rev-parse', '--abbrev-ref', 'HEAD', cwd=repo)
    if ok and out and out != 'HEAD':
        return out
    return 'main'


HOOK_TOKEN_RE = re.compile(r'\$\{?CLAUDE_PROJECT_DIR\}?/(\S+)')


def _declared_hooks(repo):
    """{hook name -> [paths it is declared at]}, read out of every
    settings*.json the set carries.

    WHY THIS RESOLVES PATHS INSTEAD OF LOOKING IN .claude/hooks/ (2026-09-09,
    and this cost a wrong diagnosis before it cost anything else). A source
    set is free to keep its hooks somewhere else and point settings.json
    there: the individual set does exactly that, wiring four hooks under its
    own tracked bootstrap/ directory precisely so there is one copy and
    nothing to drift from it. An earlier version of this function looked for
    the two file names under .claude/hooks/, found neither, and would have
    reported a perfectly healthy set as having its guards off -- then
    "repaired" it by installing the second copy that set's own comment
    exists to prevent. **The absence of .claude/hooks/ is not evidence of a
    missing hook.** Only the declared path can answer that."""
    out = {}
    for s in sorted((repo / '.claude').glob('settings*.json')):
        try:
            payload = json.loads(s.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        for entries in (payload.get('hooks') or {}).values():
            for entry in entries if isinstance(entries, list) else []:
                for h in (entry.get('hooks') or []) if isinstance(entry, dict) else []:
                    cmd = h.get('command') if isinstance(h, dict) else None
                    if not isinstance(cmd, str):
                        continue
                    for m in HOOK_TOKEN_RE.finditer(cmd):
                        rel = m.group(1)
                        out.setdefault(pathlib.PurePath(rel).name, []).append(rel)
    return out


def branch_state(repo):
    """-> (current, expected) or None when it cannot be told.

    A source clone sitting on the wrong branch is a SILENT revert waiting to
    happen: everything that syncs from it reads an older tree and writes it
    over newer committed text, and every tool involved reports success. It
    was found on 2026-09-09 only because someone went looking by hand. The
    clone is pinned now (precedent_source_bootstrap.SOURCE_BRANCH_DEFAULT),
    which stops it happening again -- this says so out loud for the clones
    that are already wrong, since a pin only takes effect the next time
    something clones or pulls."""
    if _srcboot is None:
        return None
    ok, current = _git('rev-parse', '--abbrev-ref', 'HEAD', cwd=repo)
    if not ok or not current:
        return None
    return current, _srcboot.expected_branch(repo)


def hook_state(repo):
    """-> {'error', 'missing', 'unwired', 'has_settings'} for one source set.

    `missing` is what --apply may write: a session hook the set DECLARES at
    the canonical .claude/hooks/<name> and does not have, or has without the
    executable bit (which the bootstrap installer sets for the reason its own
    comment gives -- a hook that is not executable is a hook that silently
    never runs); plus, when the set has no settings*.json at all, both hooks
    and their wiring, which is the case _install_session_hooks was written
    for.

    `unwired` is a hook no settings*.json declares anywhere. It is reported
    and never repaired: a set may leave one out on purpose, and one of the
    five real sets does. Writing a file nothing declares would produce a
    hook that still never runs, plus a diff nobody asked for."""
    if _bootstrap is None:
        return {'error': _bootstrap_err, 'missing': [], 'unwired': [],
                'has_settings': False}
    settings = sorted((repo / '.claude').glob('settings*.json'))
    declared = _declared_hooks(repo)
    missing, unwired = [], []
    # ALL_SESSION_HOOKS, not SESSION_HOOKS: the individual-source bootstrap
    # is a session hook this tool has to report like the other two, and every
    # set that existed on 2026-09-13 is missing it. It lands in `unwired`
    # there rather than `missing`, which is the honest answer -- the file can
    # be written, and adding a command to somebody's existing settings.json
    # is still not this tool's call.
    for name in _bootstrap.ALL_SESSION_HOOKS:
        where = declared.get(name)
        if not where:
            if settings:
                unwired.append(name)
            else:
                # No settings at all: nothing is declared because nothing
                # has been installed, which is the state bootstrap creates
                # from and the one case worth writing wiring for.
                missing.append(f'{name} (no .claude/settings.json at all)')
            continue
        canonical = f'.claude/hooks/{name}'
        resolved = [(rel, repo / rel) for rel in where]
        if any(path.is_file() and os.access(path, os.X_OK)
               for _, path in resolved):
            continue
        for rel, path in resolved:
            if not path.is_file():
                what, fixable = 'absent', rel == canonical
            elif not os.access(path, os.X_OK):
                what, fixable = 'not executable', rel == canonical
            else:
                continue
            missing.append(f'{name} (declared at {rel}, {what})'
                           + ('' if fixable else ' — not under .claude/hooks/, '
                              'so this tool will not guess; fix it there'))
    return {'error': None, 'missing': missing, 'unwired': unwired,
            'has_settings': bool(settings)}


def _repairable(entry):
    """Only findings this tool can honestly act on: a hook the set declares
    at the canonical path, a set with no wiring at all, or a set missing the
    universal-catalogue wiring or its ignore line. A hook declared somewhere
    else is the set's own arrangement and is reported, not overwritten.

    THE LAST TWO WERE MISSING UNTIL 2026-09-13 and that is why a set already
    current got no repair: this list is what puts a set in front of
    repair_hooks() at all, and a set whose only problem was the missing
    wiring appeared in neither this list nor the stale one. It was invisible
    to the tool while being exactly what the tool had just been taught to
    fix.
    """
    found = [m for m in (entry.get('hooks') or {}).get('missing', [])
             if 'will not guess' not in m]
    repo = pathlib.Path(entry['repo'])
    if _bootstrap is not None:
        try:
            cmds = ' '.join(_bootstrap._wired_commands(repo))
            if (_bootstrap.UNIVERSAL_CATALOGUE_HOOK not in cmds
                    and 'precedent_session_practices.py' not in cmds):
                found.append(
                    f'{_bootstrap.UNIVERSAL_CATALOGUE_HOOK} is not wired into '
                    f'SessionStart, so none of the universal catalogue reaches '
                    f'a session rooted here')
            gi = repo / '.gitignore'
            body = gi.read_text(encoding='utf-8') if gi.is_file() else ''
            if not any(ln.strip() == '.precedent/' for ln in body.splitlines()):
                found.append(
                    '.gitignore does not ignore `.precedent/`, so the '
                    'session-start practices file is offered to the next '
                    '`git add -A`')
        except Exception:                                    # noqa: BLE001
            pass          # a set this cannot read is reported by the rows above
    return found


def repair_hooks(repo):
    """(ok, message). Writes the session hooks and, only when the set has no
    settings*.json at all, the wiring for them -- _install_session_hooks
    itself declines to overwrite an existing one."""
    if _bootstrap is None:
        return False, _bootstrap_err
    try:
        written = _bootstrap._install_session_hooks(repo, _default_branch(repo))
    except Exception as exc:        # a repair that fails must say so and
        return False, f'{type(exc).__name__}: {exc}'      # leave the rest
    # THE WIRING AND THE IGNORE LINE BELONG HERE, not in apply_to(). They were
    # in apply_to() for one afternoon and apply_to() runs over the STALE sets
    # only -- so a set that was already current got neither, silently, and a
    # session had to notice and call the engine functions by hand. Reported by
    # the set it happened in, 2026-09-13, along with the second half: wiring
    # and hook-INSTALL were on two different lists, so one --apply wired a
    # hook into SessionStart while leaving the file absent from
    # .claude/hooks/. That is a declared-but-missing hook, which the harness
    # reports as nothing at all (record/GOTCHAS.md's own entry on it) -- the
    # exact failure this tool exists to catch, shipped by the tool itself.
    #
    # Doing all three in one function is what makes them impossible to get
    # out of step: whatever set reaches this line gets the hook file, the
    # wiring that names it, and the ignore line, in that order.
    try:
        _bs = _bootstrap_source_module()
        gi, gi_changed = _bs.ensure_precedent_gitignore(pathlib.Path(repo))
        if gi_changed:
            written.append(gi)
        st, wired = _bs.ensure_hook_wired(pathlib.Path(repo),
                                          _bs.UNIVERSAL_CATALOGUE_HOOK)
        if wired:
            written.append(st)
    except Exception as exc:                                 # noqa: BLE001
        # Never fatal: the hooks above are written, and saying which half
        # could not be done beats losing both (practice: fail-gracefully).
        return True, (', '.join(str(pathlib.Path(w).relative_to(repo))
                                for w in written)
                      + f' -- but the wiring/ignore repair failed '
                        f'({type(exc).__name__}: {exc})')
    return True, ', '.join(str(pathlib.Path(w).relative_to(repo))
                           for w in written)


def _run(cmd, cwd):
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def _bootstrap_source_module():
    """This repo's own precedent_bootstrap_source, imported lazily.

    Lazily, and from THIS repo rather than the set's vendored copy, unlike
    apply_to()'s `refresh` subprocess: the ignore line is one constant, not
    something resolved against the engine directory it sits in, and a set
    whose vendored copy predates the helper is exactly the set that needs
    it."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_bootstrap_source as _bs
    return _bs


def apply_to(entry, commit=False, branch=None):
    """Refresh one source set, using ITS OWN vendored engine as a subprocess.

    Its own copy, not this repo's, on purpose: `refresh` resolves what to
    write from the engine directory it physically sits in, so running this
    repo's copy against another repo's tree would write the right bytes to
    the wrong place. It is also exactly the command a person runs by hand,
    so a failure here is a failure they can reproduce."""
    repo = entry['repo']
    steps = []
    ok, out = _run([sys.executable, 'tools/precedent_vendor_engine.py',
                    'refresh', str(ROOT)], repo)
    steps.append(('refresh', ok, out))
    if not ok:
        return steps
    # An EXISTING set gets the .precedent/ ignore line here, because
    # precedent_bootstrap_source.py only ever runs when a set is created and
    # every set that exists today was created before shape 3
    # (spec/SOURCE_SET_PROSE_GAP.md). Without it the untracked file the
    # refreshed engine starts writing is offered to the next `git add -A` in
    # that set -- which would commit universal's text into it, the one thing
    # shape 3 exists to avoid. Idempotent, so it is a no-op on every later
    # run. Same reasoning as repair_hooks(): there was an install path and no
    # repair path, and the sets that need it most are the ones the install
    # path can no longer reach.
    # Regenerate the views: a refreshed generator that has not been re-run
    # leaves the repo's committed AGENTS.md/MAP.md describing the OLD
    # engine's output, which its own --check would then fail on. The
    # engine bump and its output have to land together.
    # WHICH regenerator, and why it is not always build_views.py. A practice
    # SET's views ARE its own practices/, so build_views.py is the whole job
    # there. A CONSUMER's views are materialized from several sources first,
    # and its entry point for that is precedent_sync_views.py; running plain
    # build_views.py against one used to render MAP.md's "## The engine"
    # table over the consumer's whole tools/ directory, which holds the
    # consumer's OWN scripts alongside the vendored engine, and hard-fail
    # the moment one of them had no TOOLS_DESCRIPTIONS entry -- a script
    # this repo wrote can never have one for a script it has never seen.
    # Found 2026-09-14 against a real consumer, on
    # `tools/check_file_mention_links.py`: the refresh had already written
    # the new engine and then hard-failed before regenerating anything,
    # leaving exactly the engine-ahead-of-its-output state the comment above
    # exists to prevent. build_views.py's own table-building
    # (_engine_scope_files()) now scopes that assertion to the files
    # ENGINE_MANIFEST.json actually recorded as vendored here, so running it
    # against a consumer no longer hard-fails on the consumer's own
    # scripts -- but MAP.md and GLOSSARY.md are still not what a consumer's
    # views should be (see build_views.py's own --agents-only note), so the
    # routing below is unchanged.
    sync = repo / 'tools' / 'precedent_sync_views.py'
    if entry.get('kind') == 'consumer' and sync.is_file():
        cmd = [sys.executable, 'tools/precedent_sync_views.py', '--repo', '.']
    else:
        cmd = [sys.executable, 'tools/build_views.py']
    ok, out = _run(cmd, repo)
    steps.append(('build_views', ok, out))
    if not ok or not commit:
        return steps
    br = branch or 'precedent/engine-refresh'
    ok, out = _run(['git', 'checkout', '-B', br], repo)
    steps.append(('branch', ok, out))
    if not ok:
        return steps
    ok, out = _run(['git', 'add', '-A'], repo)
    if ok:
        ok, out = _run(['git', 'commit', '-m',
                        f'Refresh the vendored engine to BestPractice {entry["tip"][:12]}\n\n'
                        f'Generated by tools/precedent_refresh_sources.py from a\n'
                        f'BestPractice checkout. Vendored files and the regenerated\n'
                        f'views land together -- a refreshed generator whose output\n'
                        f'has not been re-run fails the repo\'s own --check.\n\n'
                        f'{session_trailer()}'], repo)
    steps.append(('commit', ok, out))
    return steps


def ensure_source_credentials(found):
    """Leave the credential helper in every attached source clone that has
    none, and -> the labels of the clones repaired.

    WHY THIS EXISTS SEPARATELY FROM THE BOOTSTRAP TOOL (practice:
    cite-the-incident). precedent_source_bootstrap.py writes the helper on
    every sync it performs, which covers a clone it created and a clone it
    pulls. It cannot cover a clone NOTHING syncs, and at session start that
    is the ordinary state of an individual source: session-start.sh leaves it
    to precedent_resolve.py's self-heal, and a clone that looks usable never
    triggers one. A clone made by an engine older than that persist therefore
    stays credential-less for the life of the container, however many
    sessions run in it.

    Measured 2026-09-11: four private sources cloned at 11:00 by a
    pre-persist engine, the fix merged at 14:22, and a session at 15:49 --
    running the fixed code, with PRECEDENT_GIT_TOKEN set -- still met four
    clones that could not fetch. The freshness guard named
    `could not fetch origin/main` and refused every non-git tool call.

    This tool already walks every attached source at every session start,
    which makes it the one place that question gets asked for free. It writes
    no secret: the config records the environment variable's NAME (see
    precedent_source_credentials.persist_credential_helper). A clone that
    already has a helper is left alone, so this is idempotent and silent in
    the ordinary case."""
    try:
        import precedent_source_credentials as psc
    except ImportError:
        return []
    if not psc.have_token():
        return []
    repaired = []
    for entry in found:
        repo = entry.get('repo')
        if repo is None:
            continue
        # An EXISTING helper is never replaced. It may be somebody's own
        # credential manager, and a tool that overwrites one to install its
        # own is doing something nobody asked for.
        ok, existing = _git('config', '--get-all', 'credential.helper', cwd=repo)
        if ok and existing.strip():
            continue
        ok_url, url = _git('remote', 'get-url', 'origin', cwd=repo)
        if not ok_url:
            continue
        if psc.persist_credential_helper(repo, url):
            repaired.append(_label(repo))
    return repaired


def _credential_reminder():
    """A source set that is not attached at all cannot be stale, so this
    tool's own report is silent about it -- and "no attached source found"
    reads as "nothing to do" when it often means "the sources never
    resolved". Say which it is (practice: fail-gracefully -- never look
    complete)."""
    try:
        import precedent_source_credentials as psc
    except ImportError:
        return
    line = psc.remind(ROOT, prefix='precedent_refresh_sources')
    if line:
        print(line)


def main(argv):
    if '--help' in argv or '-h' in argv:
        print(__doc__)
        return 0
    extra = [argv[i + 1] for i, a in enumerate(argv) if a == '--path' and i + 1 < len(argv)]
    tip, tip_ref, found = survey(extra)

    if tip is None:
        # Not a failure: a shallow or partial clone may simply not have the
        # branch. Saying so beats reporting every source as up to date,
        # which is what a silent fallback to "no tip, nothing differs"
        # would have produced.
        print(f"precedent_refresh_sources: cannot resolve {SOURCE_BRANCH} in this "
              f"checkout, so nothing can be compared against it. "
              f"`git fetch origin {SOURCE_BRANCH}` and re-run.", file=sys.stderr)
        return 0

    _credential_reminder()
    for label in ensure_source_credentials(found):
        # Said out loud rather than repaired in silence: this is a clone that
        # every git command inside it was failing on, and the failure it was
        # producing (a freshness-guard block naming a branch that belongs to
        # a DIFFERENT repository) sends whoever reads it to the wrong place.
        print(f"precedent_refresh_sources: wrote the credential helper into "
              f"{label}, which had none -- git inside that clone could not "
              f"authenticate until now. It was cloned by an engine older than "
              f"the persist; nothing else was wrong with it.")
    if not found:
        print(f"precedent_refresh_sources: no attached practice-set source found "
              f"beside {ROOT} (looked for {MANIFEST}). Nothing to check.")
        return 0

    stale = [e for e in found if e['stale']]
    for e in found:
        if e['error']:
            print(f"  ?      {_label(e['repo'])}: {e['error']}")
        elif e['stale']:
            print(f"  STALE  {_label(e['repo'])} ({e['kind']}): has "
                  f"{e['recorded'][:12] or '(none)'}, {tip_ref} is {tip[:12]}")
        else:
            print(f"  ok     {_label(e['repo'])} ({e['kind']}): current at {tip[:12]}")
        # The hook line is printed for a CURRENT source too, and that is the
        # whole point: the set this was written for was current at the tip
        # and had no hooks at all. Reporting hooks only for stale sets would
        # have kept it invisible.
        b = e.get('branch')
        if b and b[0] != b[1]:
            print(f"         BRANCH on {b[0]} — expected {b[1]}. Everything "
                  f"that syncs from this clone is reading that tree; if it is "
                  f"behind, a sync writes the older text over newer committed "
                  f"text and reports success")
        h = e.get('hooks') or {}
        if h.get('error'):
            print(f"         hooks not checked: {h['error']}")
        elif h.get('missing'):
            print(f"         HOOKS  {', '.join(h['missing'])} — sessions in "
                  f"that set run with those guards off, silently")
        elif h.get('unwired'):
            print(f"         hooks present but no settings*.json wires "
                  f"{', '.join(h['unwired'])} — read that file yourself; "
                  f"this tool never rewrites one")

    hookbad = [e for e in found if _repairable(e)]
    if not stale and not hookbad:
        print(f"precedent_refresh_sources: {len(found)} attached source(s), all current.")
        return 0

    if '--apply' not in argv:
        if stale:
            print(f"\nprecedent_refresh_sources: {len(stale)} of {len(found)} attached "
                  f"source(s) are behind {tip_ref}.")
        if hookbad:
            print(f"precedent_refresh_sources: {len(hookbad)} of {len(found)} attached "
                  f"source(s) are missing session hooks.")
        print(f"Re-run with --apply to refresh and regenerate them (add --commit to "
              f"commit the result on a branch in each); publishing stays your call, "
              f"per each repo's own merge rules.")
        return 1 if '--check' in argv else 0

    failed = False
    skipped = []
    # Hooks first, and over every affected set rather than only the stale
    # ones: the two problems are independent (see the docstring), and a hook
    # repair on a stale set is then swept into that set's refresh commit
    # below instead of needing one of its own.
    for e in hookbad:
        print(f"\n--- {_label(e['repo'])}")
        ok, out = repair_hooks(e['repo'])
        print(f"  {'ok ' if ok else 'FAIL'} hooks: {out}")
        failed = failed or not ok
        if ok and '--commit' in argv and not e['stale']:
            br = 'precedent/restore-session-hooks'
            for step in (['git', 'checkout', '-B', br],
                         ['git', 'add', '-A', '.claude'],
                         ['git', 'commit', '-m',
                          'Restore the session hooks this set was created without\n\n'
                          'Written by tools/precedent_refresh_sources.py --apply from a\n'
                          'BestPractice checkout. A hook whose path does not exist is\n'
                          'not an error anybody sees, so these were off silently.\n\n'
                          + session_trailer()]):
                ok, out = _run(step, e['repo'])
                print(f"  {'ok ' if ok else 'FAIL'} {step[1]}: "
                      f"{out.splitlines()[-1] if out else ''}")
                if not ok:
                    failed = True
                    break

    for e in stale:
        e['tip'] = tip
        print(f"\n--- {_label(e['repo'])}")
        # practice: durable-fix -- session-start.sh now calls --apply
        # unconditionally, every session, so this guard is what keeps that
        # safe. Without it, a person's own uncommitted edit in this source
        # (a new practice file, a hand fix mid-review) would be sitting in
        # the same working tree that `refresh` and `build_views` write
        # into, and their diff would land tangled with a regenerated one
        # they never asked for -- indistinguishable after the fact from
        # having clobbered it outright.
        _engine_dirt, other_dirt = classify_dirt(e['repo'])
        if other_dirt:
            print(f"  SKIP refresh: uncommitted changes present in this "
                  f"source that the engine does not own "
                  f"({', '.join(other_dirt[:4])}"
                  f"{'...' if len(other_dirt) > 4 else ''}) -- commit or "
                  f"stash there, then re-run")
            skipped.append(_label(e['repo']))
            continue

        # MAKE IT CURRENT FIRST. The catalogue half of a vendor update is
        # read out of this working tree -- precedent_materialize.py has no
        # fetch in it at all -- so a clone that is behind silently puts an
        # older catalogue in force. Morgan, 2026-09-21 (strength: decided):
        # "would this force it to clone the most updated version first
        # thing? I think that's what we need."
        want = _declared_base_branch(e['repo']) or _default_branch(e['repo'])
        if want:
            ok_cur, note = make_current(e['repo'], want)
            print(f"  {'ok ' if ok_cur else 'FAIL'} current: {note}")
            if not ok_cur:
                skipped.append(_label(e['repo']))
                continue
        else:
            print(f"  SKIP refresh: cannot tell which branch this source "
                  f"belongs on, so it cannot be brought current -- declare "
                  f"base_branch in its precedent.json")
            skipped.append(_label(e['repo']))
            continue

        for name, ok, out in apply_to(e, commit='--commit' in argv):
            print(f"  {'ok ' if ok else 'FAIL'} {name}: {out.splitlines()[-1] if out else ''}")
            failed = failed or not ok

    # A SKIP IS NOT A SUCCESS. This line used to read `applied.` however many
    # sources had been declined, and the exit code ignored them entirely --
    # which is how four sources drifted 17 to 34 commits behind while every
    # session start reported success (todo-2026-09-21-refresh-output-blocks-
    # the-next-pull). practice: control-asserts-which-failure.
    if skipped:
        print(f"\nprecedent_refresh_sources: NOT APPLIED to "
              f"{len(skipped)} of {len(stale)} stale source(s): "
              f"{', '.join(skipped)}. Those clones stay behind, and the "
              f"catalogue in force is read from their working trees.")
    else:
        print("\nprecedent_refresh_sources: applied. Review each repo's diff, "
              "then push and open a pull request there -- this tool never "
              "publishes.")
    return 1 if (failed or skipped) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
