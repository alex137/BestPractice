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
merge rules, which this tool has no way to know. The unattended path is the
scheduled workflow the source templates now ship, which runs in the source
repo itself where its own rules apply.

A SECOND THING THIS COVERS, AND WHY IT IS THE SAME TOOL (added
2026-09-09). A source set also carries its own session hooks -- the
freshness guard and the commit-identity backstop -- installed by
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
SOURCE_BRANCH = 'precedent-beta-v01'   # kept in step with precedent_vendor_engine.SOURCE_BRANCH
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
            if s.get('level') in ('team', 'individual') and s.get('path'):
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
    for name in _bootstrap.SESSION_HOOKS:
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
    at the canonical path, or a set with no wiring at all. A hook declared
    somewhere else is the set's own arrangement and is reported, not
    overwritten."""
    return [m for m in (entry.get('hooks') or {}).get('missing', [])
            if 'will not guess' not in m]


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
    return True, ', '.join(str(pathlib.Path(w).relative_to(repo))
                           for w in written)


def _run(cmd, cwd):
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


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
    # Regenerate the views: a refreshed generator that has not been re-run
    # leaves the repo's committed AGENTS.md/MAP.md describing the OLD
    # engine's output, which its own --check would then fail on. The
    # engine bump and its output have to land together.
    ok, out = _run([sys.executable, 'tools/build_views.py'], repo)
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
                        f'has not been re-run fails the repo\'s own --check.'], repo)
    steps.append(('commit', ok, out))
    return steps


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
                          'not an error anybody sees, so these were off silently.']):
                ok, out = _run(step, e['repo'])
                print(f"  {'ok ' if ok else 'FAIL'} {step[1]}: "
                      f"{out.splitlines()[-1] if out else ''}")
                if not ok:
                    failed = True
                    break

    for e in stale:
        e['tip'] = tip
        print(f"\n--- {_label(e['repo'])}")
        for name, ok, out in apply_to(e, commit='--commit' in argv):
            print(f"  {'ok ' if ok else 'FAIL'} {name}: {out.splitlines()[-1] if out else ''}")
            failed = failed or not ok
    print("\nprecedent_refresh_sources: applied. Review each repo's diff, then "
          "push and open a pull request there -- this tool never publishes.")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
