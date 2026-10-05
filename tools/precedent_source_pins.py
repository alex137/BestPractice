#!/usr/bin/env python3
"""Which commit of each live practice source a consumer's views were built
from, and reading a source at that commit.

THE PROBLEM THIS ANSWERS (2026-10-05, a consumer's push check). A consumer
declares shared sets that live beside it as clones (`../precedent-shared-
writing`). Its views check compared the committed views against whatever
branch that clone had checked out, and session start leaves the clone on
the set's `main`. The consumer's `pre-staging` takes a set's change as soon
as it is Booked into the set's own `pre-staging`, so between a set's Booked
and its Produce every push in every consumer was refused for "drift" in
files it never touched -- and the remedy the check printed, a plain sync,
would have rolled the Booked changes back. It happened twice in one session.

THE FIX IS A PIN, NOT A BETTER GUESS. Every sync records, in MANIFEST.json,
the commit it read each live source at (`sources[].commit`). The views
check then reads each source AT THAT COMMIT, from a throwaway worktree of
the clone, so its answer depends on neither the clone's checkout nor how
far the set has moved since. What the views check asks becomes one
question -- are the committed views what their recorded inputs produce? --
and a hand-edited generated file still fails it on every branch.

The two questions it used to blur are asked separately, each with a remedy
that cannot destroy work:

  * the rung (rung_refusals): a push to pre-staging, staging or main may
    carry a set only at a commit that set has itself landed on the same
    rung -- the consumer's main never carries what the set has not
    Produced. The remedy is to promote the set, never to sync.
  * freshness (newer_notes): the set has newer commits on the matching
    rung. Said, never refused.

And a write sync refuses to roll a source back (rollback_refusals): when
the clone does not contain the recorded commit, syncing from it would drop
what this repository already carries.

A MANIFEST WITHOUT PINS (written before this engine) gets its pin inferred:
the candidate commit -- the clone's own checkout, then the set's
pre-staging, staging and main -- whose practice files hash to what the
manifest recorded taking (`source_sha256_16`). The first sync after Update
Vendors writes real pins.

A source inside the consuming repository (a vendored universal copy, a
repo-local `local/`) is read from the working tree, as always: it is
committed with the views it produces, so nothing can move under it.
"""
import contextlib
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile

PRE_STAGING, STAGING, MAIN = 'pre-staging', 'staging', 'main'
# A consumer branch reads a set at the same rung; a set without that rung
# falls back to the next one up, ending at main.
RUNGS = (PRE_STAGING, STAGING, MAIN)
FETCH_TIMEOUT = 60
# What a sync reads from a set, for saying whether a newer commit matters.
SYNCED_PATHS = ('practices', 'tools', 'bootstrap', 'precedent-source.json')


def _git(path, *args, timeout=None):
    try:
        return subprocess.run(['git', '-C', str(path), *args],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, '', 'timed out')


def _out(path, *args, timeout=None):
    r = _git(path, *args, timeout=timeout)
    return r.stdout.strip() if r.returncode == 0 else ''


def head_commit(path):
    """-> the commit checked out at `path` when `path` is the top of a git
    work tree, else None (a plain directory, or a subdirectory of some
    other repository, has no commit of its own to pin)."""
    path = pathlib.Path(path)
    top = _out(path, 'rev-parse', '--show-toplevel')
    if not top or pathlib.Path(top).resolve() != path.resolve():
        return None
    return _out(path, 'rev-parse', '--verify', '--quiet', 'HEAD') or None


def is_dirty(path):
    """True when a file a sync reads from this source has uncommitted
    changes. Only those count: session start refreshes a set's vendored
    engine (tools/ENGINE_MANIFEST.json names those files) and its generated
    MAP.md in the working tree, and a consumer's sync reads neither -- were
    they counted, no set clone in a session would ever be pinned."""
    engine = set()
    try:
        m = json.loads((pathlib.Path(path) / 'tools' / 'ENGINE_MANIFEST.json')
                       .read_text(encoding='utf-8'))
        engine = {f'tools/{f}' for f in m.get('files') or []}
    except (OSError, ValueError, AttributeError):
        pass
    engine.add('tools/ENGINE_MANIFEST.json')
    r = _git(path, 'status', '--porcelain', '-z', '--untracked-files=no')
    if r.returncode != 0:
        return True
    for entry in r.stdout.split('\0'):
        rel = entry[3:]
        if len(entry) < 4 or rel in engine:
            continue
        if rel == 'precedent-source.json' or \
                rel.startswith(('practices/', 'bootstrap/', 'tools/')):
            return True
    return False


def has_commit(path, sha):
    return _git(path, 'cat-file', '-e', f'{sha}^{{commit}}').returncode == 0


def ensure_commit(path, sha):
    """-> True when `sha` is (now) in the clone at `path`. A clone made
    before the commit existed, or a shallow one, lacks it: fetch it by id,
    then the rung branches, which carry every commit a sync can have
    pinned once the work is Booked."""
    if has_commit(path, sha):
        return True
    _git(path, 'fetch', '-q', 'origin', sha, timeout=FETCH_TIMEOUT)
    if has_commit(path, sha):
        return True
    _git(path, 'fetch', '-q', 'origin', *RUNGS, timeout=FETCH_TIMEOUT)
    return has_commit(path, sha)


def is_ancestor(path, older, newer):
    return _git(path, 'merge-base', '--is-ancestor', older,
                newer).returncode == 0


def _inside(path, repo):
    try:
        pathlib.Path(path).resolve().relative_to(pathlib.Path(repo).resolve())
        return True
    except ValueError:
        return False


def live(sources, repo):
    """-> the sources a sync reads from outside `repo`, from a git checkout
    of their own: the ones whose content can move under the views."""
    return [s for s in sources
            if not _inside(s['path'], repo) and head_commit(s['path'])]


def _manifest(repo):
    try:
        return json.loads((pathlib.Path(repo) / 'MANIFEST.json')
                          .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def recorded(repo):
    """-> {source name: commit} as the repository's MANIFEST.json records
    them; {} for a manifest written before pins existed."""
    return {e['name']: e['commit']
            for e in _manifest(repo).get('sources') or []
            if isinstance(e, dict) and e.get('name') and e.get('commit')}


def rung_for(branch):
    """-> the rung a consumer branch reads its sets at, or None for a
    working branch (it is built on pre-staging, so its notes use that;
    nothing is refused on it -- trying a set's unbooked work in a consumer
    is what a working branch is for)."""
    if branch in RUNGS:
        return branch
    if branch == 'precedent-beta-v01':          # staging before its rename
        return STAGING
    return None


def rung_ref(path, rung):
    """-> (ref, branch) of the set's own branch for `rung`, falling back up
    the ladder to main; (None, None) when the clone knows none of them."""
    for b in RUNGS[RUNGS.index(rung):]:
        ref = f'refs/remotes/origin/{b}'
        if _git(path, 'rev-parse', '--verify', '--quiet', ref).returncode == 0:
            return f'origin/{b}', b
    return None, None


# How far back a pin is looked for when a manifest records none.
INFER_DEPTH = 300


def _practice_hashes_at(path, commit, cache=None):
    """-> {sha256_16} of every practices/*.md at `commit`, or of the files
    on disk when commit is None. `cache` maps blob id -> hash, so walking
    history hashes each distinct file version once."""
    out = set()
    if commit is None:
        for f in (pathlib.Path(path) / 'practices').glob('*.md'):
            out.add(hashlib.sha256(f.read_bytes()).hexdigest()[:16])
        return out
    cache = {} if cache is None else cache
    for line in _out(path, 'ls-tree', commit, 'practices/').splitlines():
        meta, _tab, name = line.partition('\t')
        parts = meta.split()
        if len(parts) != 3 or parts[1] != 'blob' or not name.endswith('.md'):
            continue
        blob = parts[2]
        if blob not in cache:
            r = subprocess.run(['git', '-C', str(path), 'cat-file', 'blob',
                                blob], capture_output=True)
            cache[blob] = (hashlib.sha256(r.stdout).hexdigest()[:16]
                           if r.returncode == 0 else None)
        out.add(cache[blob])
    return out


def inferred(repo, source):
    """-> (commit, ref) for a source the manifest pins no commit for: the
    first candidate whose practice files hash to everything the manifest
    recorded taking from it -- the clone's checkout, each rung's tip, then
    the rungs' recent history, newest first. (None, None) when none does,
    or the manifest records nothing to match on."""
    want = {p['source_sha256_16'] for p in _manifest(repo).get('practices') or []
            if isinstance(p, dict) and p.get('source') == source['name']
            and p.get('source_sha256_16')}
    if not want:
        return None, None
    path = source['path']
    if want <= _practice_hashes_at(path, None):
        return head_commit(path), 'its checkout'
    cache = {}
    refs = [f'origin/{r}' for r in RUNGS
            if _out(path, 'rev-parse', '--verify', '--quiet', f'origin/{r}')]
    for ref in refs:
        sha = _out(path, 'rev-parse', ref)
        if want <= _practice_hashes_at(path, sha, cache):
            return sha, ref
    if refs:
        for sha in _out(path, 'rev-list', f'--max-count={INFER_DEPTH}',
                        *refs, '--', *SYNCED_PATHS).splitlines():
            if want <= _practice_hashes_at(path, sha, cache):
                return sha, f'a commit on {"/".join(refs)}'
    return None, None


def pins(repo, sources):
    """-> {name: {'commit', 'how'}} for every live source: the recorded
    commit, else an inferred one. A live source with neither is absent."""
    rec = recorded(repo)
    out = {}
    for s in live(sources, repo):
        if s['name'] in rec:
            out[s['name']] = {'commit': rec[s['name']], 'how': 'recorded'}
            continue
        sha, ref = inferred(repo, s)
        if sha:
            out[s['name']] = {'commit': sha, 'how': f'matched {ref}'}
    return out


@contextlib.contextmanager
def at_pins(sources, pinned):
    """Yield (sources, notes): `sources` with each pinned live source's
    path swapped for a detached worktree of its clone at the pinned commit.
    A source already checked out, clean, at its pin is read in place. A pin
    the clone cannot produce, even after a fetch, is read from the clone as
    it stands, and said. The worktrees are removed on the way out."""
    made, notes, out = [], [], []
    try:
        for s in sources:
            pin = (pinned.get(s['name']) or {}).get('commit')
            path = s['path']
            if not pin or (head_commit(path) == pin and not is_dirty(path)):
                out.append(s)
                continue
            if not ensure_commit(path, pin):
                notes.append(f"{s['name']}: the commit this repository's views "
                             f"were built from, {pin[:10]}, is not in the clone "
                             f"at {path} and could not be fetched -- checked "
                             f"against the clone as it stands instead")
                out.append(s)
                continue
            tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"pin-{s['name']}-"))
            wt = tmp / pathlib.Path(path).name
            r = _git(path, 'worktree', 'add', '-q', '--detach', str(wt), pin)
            if r.returncode != 0:
                shutil.rmtree(tmp, ignore_errors=True)
                notes.append(f"{s['name']}: could not read it at {pin[:10]} "
                             f"({r.stderr.strip() or 'git worktree add failed'})"
                             f" -- checked against the clone as it stands")
                out.append(s)
                continue
            made.append((path, wt, tmp))
            # `clone_path` is what MANIFEST.json records as the source's
            # path: the worktree is gone the moment this returns.
            out.append({**s, 'path': str(wt), 'clone_path': path})
        yield out, notes
    finally:
        for path, wt, tmp in made:
            _git(path, 'worktree', 'remove', '--force', str(wt))
            shutil.rmtree(tmp, ignore_errors=True)
            _git(path, 'worktree', 'prune')


def checkouts(repo, sources):
    """-> {name: {'commit', 'how'}}: each live source at the commit its
    clone has checked out -- what a WRITE sync reads. Through at_pins, so a
    clone whose synced files carry uncommitted changes is read at that
    commit, without them: what a repository commits as its views has to be
    something every other checkout can reproduce."""
    return {s['name']: {'commit': head_commit(s['path']), 'how': 'checkout'}
            for s in live(sources, repo)}


def rollback_refusals(repo, sources, pinned=None):
    """-> [refusal] for a WRITE sync: each live source whose clone does not
    contain the commit this repository already carries it at. Syncing from
    that clone would drop the commits between them from this repository's
    views -- the remedy the old views check printed, which rolled Booked
    changes back (practice: repair-cannot-discard-work)."""
    pinned = pins(repo, sources) if pinned is None else pinned
    out = []
    for s in live(sources, repo):
        pin = (pinned.get(s['name']) or {}).get('commit')
        head = head_commit(s['path'])
        if not pin or pin == head:
            continue
        if not ensure_commit(s['path'], pin):
            continue                        # cannot tell; nothing to refuse on
        if is_ancestor(s['path'], pin, head):
            continue                        # the clone is ahead: a step forward
        branch = _out(s['path'], 'rev-parse', '--abbrev-ref', 'HEAD')
        holder = next((f'origin/{b}' for b in RUNGS
                       if _git(s['path'], 'rev-parse', '--verify', '--quiet',
                               f'refs/remotes/origin/{b}').returncode == 0
                       and is_ancestor(s['path'], pin, f'origin/{b}')), None)
        where = (f"Check the clone out where it is: git -C {s['path']} "
                 f"checkout --detach {holder}" if holder else
                 f"Check the clone out at a branch that contains {pin[:10]}")
        out.append(
            f"{s['name']}: this repository carries it at {pin[:10]}, and the "
            f"clone at {s['path']} ({'detached' if branch == 'HEAD' else branch}"
            f", {head[:10]}) does not contain that commit. Syncing from it "
            f"would roll those changes back out of this repository. {where}, "
            f"then sync again; --allow-rollback if dropping them is what you "
            f"mean.")
    return out


def landed(path, pin, rung):
    """True when `pin` is on the set's `rung` or any rung above it. Above
    counts: a set's main carries the pull-request merge commits that its
    pre-staging never gets, and what reached main has passed every rung
    below it."""
    for b in RUNGS[RUNGS.index(rung):]:
        ref = f'refs/remotes/origin/{b}'
        if _git(path, 'rev-parse', '--verify', '--quiet', ref).returncode == 0 \
                and is_ancestor(path, pin, ref):
            return True
    return False


def rung_refusals(repo, sources, branch, pinned=None):
    """-> [refusal] for a push to `branch`: each live source carried at a
    commit that source has not landed on the same rung itself. Nothing on a
    working branch."""
    rung = rung_for(branch)
    if rung is None:
        return []
    pinned = pins(repo, sources) if pinned is None else pinned
    out = []
    for s in live(sources, repo):
        pin = (pinned.get(s['name']) or {}).get('commit')
        if not pin or not ensure_commit(s['path'], pin):
            continue
        ref, at = rung_ref(s['path'], rung)
        if ref is None:
            continue
        if landed(s['path'], pin, rung):
            continue
        # The remote-tracking refs may simply be old: fetch, then ask again.
        _git(s['path'], 'fetch', '-q', 'origin', *RUNGS, timeout=FETCH_TIMEOUT)
        if landed(s['path'], pin, rung):
            continue
        below = RUNGS[RUNGS.index(at) - 1] if RUNGS.index(at) else None
        step = {PRE_STAGING: 'Book', STAGING: 'Debut', MAIN: 'Produce'}[at]
        out.append(
            f"{s['name']}: this push puts {branch} on {s['name']} at "
            f"{pin[:10]}, which {s['name']}'s own {at} does not have yet. "
            f"{step} it in {s['name']} first"
            + (f" ({below} into {at})" if below else '')
            + f", then push again. Do not sync to get past this: a sync from "
            f"the set's {at} would take those changes back out.")
    return out


def newer_notes(repo, sources, branch, pinned=None):
    """-> [note] for each live source whose matching rung has commits this
    repository has not taken yet. Never a refusal: taking them is a
    decision, and the views are consistent without them."""
    rung = rung_for(branch) or PRE_STAGING
    pinned = pins(repo, sources) if pinned is None else pinned
    out = []
    for s in live(sources, repo):
        pin = (pinned.get(s['name']) or {}).get('commit')
        if not pin or not has_commit(s['path'], pin):
            continue
        ref, _at = rung_ref(s['path'], rung)
        if ref is None:
            continue
        if is_ancestor(s['path'], ref, pin):
            continue                        # this repository is at or past it
        changed = _out(s['path'], 'diff', '--name-only', pin, ref, '--',
                       *SYNCED_PATHS).splitlines()
        if changed:
            out.append(f"{s['name']}: its {ref} differs from what this "
                       f"repository took in {len(changed)} file(s) a sync "
                       f"reads; a sync from there takes them")
    return out


def main(argv):
    """`--repo DIR [--branch B]`: print each live source's pin, how it was
    found, and what the rung and freshness checks say."""
    import sys
    if '--help' in argv or '-h' in argv:
        print(__doc__)
        return 0
    import precedent_resolve as pr
    repo = argv[argv.index('--repo') + 1] if '--repo' in argv else '.'
    branch = argv[argv.index('--branch') + 1] if '--branch' in argv else \
        _out(repo, 'rev-parse', '--abbrev-ref', 'HEAD')
    sources = [s for s in pr.load_config(repo) if not s.get('brought')]
    pinned = pins(repo, sources)
    for s in live(sources, repo):
        p = pinned.get(s['name'])
        print(f"{s['name']}: " + (f"{p['commit'][:10]} ({p['how']})" if p
                                  else 'no pin, and none could be inferred'))
    for line in (rung_refusals(repo, sources, branch, pinned)
                 + newer_notes(repo, sources, branch, pinned)):
        print(f'  {line}')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
