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

Run:
  python3 tools/precedent_refresh_sources.py                 # report
  python3 tools/precedent_refresh_sources.py --check         # exit 1 if any stale
  python3 tools/precedent_refresh_sources.py --apply         # refresh + regenerate
  python3 tools/precedent_refresh_sources.py --apply --commit
  python3 tools/precedent_refresh_sources.py --path ../other-set
Exit: 0 always, except --check with a stale source, or a malformed manifest.
"""
import json, pathlib, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_resolve

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
                      'recorded': recorded, 'stale': stale, 'error': None})
    return tip, tip_ref, found


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

    if not stale:
        print(f"precedent_refresh_sources: {len(found)} attached source(s), all current.")
        return 0

    if '--apply' not in argv:
        print(f"\nprecedent_refresh_sources: {len(stale)} of {len(found)} attached "
              f"source(s) are behind {tip_ref}. Re-run with --apply to refresh and "
              f"regenerate them (add --commit to commit the result on a branch in "
              f"each); publishing stays your call, per each repo's own merge rules.")
        return 1 if '--check' in argv else 0

    failed = False
    for e in stale:
        e['tip'] = tip
        print(f"\n--- {_label(e['repo'])}")
        for name, ok, out in apply_to(e, commit='--commit' in argv):
            print(f"  {'ok ' if ok else 'FAIL'} {name}: {out.splitlines()[-1] if out else ''}")
            failed = failed or not ok
    print("\nprecedent_refresh_sources: refreshed. Review each repo's diff, then "
          "push and open a pull request there -- this tool never publishes.")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
