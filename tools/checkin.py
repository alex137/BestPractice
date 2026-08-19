#!/usr/bin/env python3
"""checkin.py — drive the periodic check-in (INSTALL.md §4) mechanically.

Runs from a dependent repo (script lives at process/upstream/tools/). The
check-in loop — sync the vendored tree into a clone of the upstream repo,
land it there, then record the landed commit in the manifest — was performed
by hand several times and each pass repeated the same steps with the same
two failure modes: forgetting the scrub before content left the private
repo, and recording a hash that didn't actually match the tree that landed.
Per the convention-becomes-audit rule, the steps are now a tool; every
mutation it performs is gated by a check that fails loudly.

Four subcommands — update takes upstream changes IN, the other three drive
a check-in OUT:

  status <upstream-clone>   Compare the vendored tree against the clone's
                            working tree: list Added/Modified/Deleted files
                            (vendored perspective), show the manifest's
                            recorded upstream.commit vs the clone's HEAD.
                            Exit 1 if the trees differ (so it can gate).

  update <upstream-clone> [--force]
                            The INSTALL.md §2 direction: pull the clone's
                            default branch and mirror it into the vendored
                            tree. REFUSES if the vendored tree differs from
                            the recorded upstream.commit — that difference
                            is unexported local work the mirror would
                            silently clobber; export it first (§3/§4) or
                            pass --force to overwrite. (Origin: a session
                            hand-rolled this mirror with git archive | tar
                            — rsync is absent in hosted containers, as of
                            2026-08 — and a stale local default-branch ref
                            nearly mirrored an old tree; the tool pulls
                            fresh and guards the overwrite.)

  push <upstream-clone> [--force]
                            REFUSES if upstream's default branch has moved
                            past what the vendored tree was mirrored from —
                            the tree is then behind, and this mirror DELETES
                            files it lacks, so it would revert upstream work
                            (run `update` first). Then run the scrub/practice
                            audit — it must
                            pass, THIS is the gate that keeps proprietary
                            content out of the public repo — then mirror the
                            vendored tree into the clone's working tree
                            (deleting files that no longer exist upstream,
                            .git untouched). Committing, opening the PR, and
                            merging remain deliberate manual steps: the PR
                            review is the second scrub line.

  record <upstream-clone> [--note "..."]
                            After the upstream merge: pull the clone's
                            default branch, verify it is byte-identical to
                            the vendored tree (fail loudly if not — never
                            record a hash that doesn't match the tree), then
                            write the clone's HEAD hash into
                            process/manifest.json upstream.commit. Commit
                            the manifest change in the dependent repo
                            yourself.

Run:  python3 process/upstream/tools/checkin.py status ../BestPractice
      python3 process/upstream/tools/checkin.py update ../BestPractice
      python3 process/upstream/tools/checkin.py push   ../BestPractice
      python3 process/upstream/tools/checkin.py record ../BestPractice --note "PR #4"
"""
import datetime, filecmp, io, json, pathlib, shutil, subprocess, sys, tarfile, tempfile

HERE = pathlib.Path(__file__).resolve()
_top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=HERE.parent,
                      capture_output=True, text=True).stdout.strip()
ROOT = pathlib.Path(_top) if _top else HERE.parents[3]
UPSTREAM = ROOT / 'process' / 'upstream'
MANIFEST = ROOT / 'process' / 'manifest.json'


def _git(clone, *args):
    return subprocess.run(['git', '-C', str(clone)] + list(args),
                          capture_output=True, text=True).stdout.strip()


def _files(base):
    return {p.relative_to(base) for p in base.rglob('*')
            if p.is_file() and '.git' not in p.parts}


def _diff(clone):
    """(added, modified, deleted) of the vendored tree vs the clone tree."""
    ours, theirs = _files(UPSTREAM), _files(clone)
    added = sorted(ours - theirs)
    deleted = sorted(theirs - ours)
    modified = sorted(p for p in ours & theirs
                      if not filecmp.cmp(UPSTREAM / p, clone / p, shallow=False))
    return added, modified, deleted


def _manifest():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def _clone_or_die(arg):
    clone = pathlib.Path(arg).resolve()
    if not (clone / '.git').exists():
        sys.exit(f"checkin FAIL: {clone} is not a git clone")
    return clone


def status(clone):
    added, modified, deleted = _diff(clone)
    recorded = _manifest().get('upstream', {}).get('commit')
    head = _git(clone, 'rev-parse', 'HEAD')
    for p in added:
        print(f"  A {p}")
    for p in modified:
        print(f"  M {p}")
    for p in deleted:
        print(f"  D {p}")
    n = len(added) + len(modified) + len(deleted)
    print(f"vendored vs clone: {n} file(s) differ "
          f"({len(added)} added, {len(modified)} modified, {len(deleted)} deleted)")
    print(f"manifest upstream.commit: {recorded}")
    print(f"clone HEAD:               {head}"
          + ("  (== recorded)" if head == recorded else "  (!= recorded)"))
    return 1 if n else 0


def _stamp_synced_from(commit):
    """Record which upstream commit the vendored tree was last mirrored from.

    Distinct from upstream.commit, which record() writes only after verifying
    the vendored tree is byte-identical to what actually landed upstream. That
    invariant is deliberate and untouched; this field answers a different
    question -- "is the vendored tree current with upstream?" -- which push()
    needs and which upstream.commit cannot answer during the normal cycle,
    because it legitimately lags from update() until the merge is recorded.
    """
    path = ROOT / 'process' / 'manifest.json'
    m = json.loads(path.read_text(encoding='utf-8'))
    m.setdefault('upstream', {})['synced_from'] = commit
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n",
                    encoding='utf-8')


def _default_branch(clone):
    return (_git(clone, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD').rsplit('/', 1)[-1]
            or 'main')


def update(clone, force=False):
    """INSTALL.md §2 step 5: mirror the clone's freshly pulled default branch
    into the vendored tree, refusing to clobber unexported local work."""
    branch = _default_branch(clone)
    _git(clone, 'checkout', branch)
    _git(clone, 'pull', 'origin', branch)
    if not force:
        recorded = _manifest().get('upstream', {}).get('commit')
        if not recorded:
            sys.exit("checkin FAIL: no upstream.commit recorded in the manifest — "
                     "cannot tell local work from upstream drift; pass --force to mirror anyway")
        tar = subprocess.run(['git', '-C', str(clone), 'archive', recorded],
                             capture_output=True)
        if tar.returncode != 0:
            sys.exit(f"checkin FAIL: recorded commit {recorded[:12]} not found in the clone — "
                     f"fetch it there, or pass --force")
        with tempfile.TemporaryDirectory() as td:
            tarfile.open(fileobj=io.BytesIO(tar.stdout)).extractall(td)
            base = pathlib.Path(td)
            ours, theirs = _files(UPSTREAM), _files(base)
            drift = sorted(ours ^ theirs) + sorted(
                p for p in ours & theirs
                if not filecmp.cmp(UPSTREAM / p, base / p, shallow=False))
        if drift:
            for p in drift:
                print(f"  local change: {p}")
            sys.exit("checkin FAIL: vendored tree differs from the recorded upstream commit — "
                     "that is unexported work the mirror would clobber. Export it first "
                     "(INSTALL.md §3/§4) or pass --force to overwrite.")
    vendored_only, differing, clone_only = _diff(clone)
    if not (vendored_only or differing or clone_only):
        _stamp_synced_from(_git(clone, 'rev-parse', 'HEAD'))
        print(f"checkin update: vendored tree already identical to clone {branch} — nothing to do.")
        return 0
    for p in vendored_only:
        (UPSTREAM / p).unlink()
    for p in differing + clone_only:
        (UPSTREAM / p).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(clone / p, UPSTREAM / p)
    _stamp_synced_from(_git(clone, 'rev-parse', 'HEAD'))
    print(f"checkin update OK: mirrored {len(differing) + len(clone_only)} file(s), "
          f"deleted {len(vendored_only)} from the vendored tree (clone {branch} @ "
          f"{_git(clone, 'rev-parse', 'HEAD')[:12]})")
    print("next: propagate template changes into instantiated files (INSTALL.md §2),")
    print("      update manifest entries, then run:  checkin.py record " + str(clone))
    return 0


def push(clone, force=False):
    # Guard 1: the vendored tree must be CURRENT with upstream. This mirror
    # DELETES any file the vendored tree lacks, so pushing from a tree that is
    # behind silently reverts whatever upstream gained. Symmetric to update()'s
    # guard: that one refuses to clobber unexported LOCAL work, this one
    # refuses to clobber unimported UPSTREAM work.
    #
    # Origin (2026-08-12): a session's vendored tree was behind by two upstream
    # merges; a plain push would have reverted two practices, and it was caught
    # only by a human reading `status` output. In the same session the *other*
    # direction then bit as well -- an `update --force`, passed specifically to
    # bypass update()'s guard, silently reverted three unexported additions
    # including this function. Both directions of this mirror destroy work;
    # both now warn, and --force means what it says.
    if not force:
        up = _manifest().get('upstream', {})
        # synced_from is what update() mirrored; fall back to commit for a
        # manifest written before that field existed.
        base = up.get('synced_from') or up.get('commit')
        branch = _default_branch(clone)
        _git(clone, 'fetch', 'origin', branch)
        head = _git(clone, 'rev-parse', f'origin/{branch}')
        if base and head != base:
            sys.exit(
                f"checkin FAIL: upstream origin/{branch} is at {head[:12]} but "
                f"the vendored tree was last mirrored from {base[:12]} — it is "
                "behind, and this mirror DELETES files it does not have, so it "
                "would revert upstream work. Run `checkin.py update` first (it "
                "refuses if that would clobber unexported local work — export "
                "that, or `update --force` and RE-APPLY your additions on top, "
                "keeping a copy first), then push. `--force` overrides if you "
                "are certain the vendored tree is the intended upstream state.")

    # Guard 2: the scrub gates every export of content toward the public repo.
    audit = HERE.parent / 'practice_audit.py'
    if subprocess.run([sys.executable, str(audit)]).returncode != 0:
        sys.exit("checkin FAIL: practice_audit (scrub) failed — nothing was copied")
    added, modified, deleted = _diff(clone)
    if not (added or modified or deleted):
        print("checkin push: vendored tree and clone already identical — nothing to do.")
        return 0
    for p in deleted:
        (clone / p).unlink()
    for p in added + modified:
        (clone / p).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(UPSTREAM / p, clone / p)
    print(f"checkin push OK: mirrored {len(added) + len(modified)} file(s), "
          f"deleted {len(deleted)} into {clone}")
    print("next: commit there on a branch, open the PR (review = second scrub line),")
    print("      merge, pull the default branch, then run:  checkin.py record " + str(clone))
    return 0



def _dep_git(*args):
    return subprocess.run(['git', '-C', str(ROOT)] + list(args),
                          capture_output=True, text=True).stdout


def _carry_check(clone, accept_loss):
    """No pending vendored addition may vanish across a check-in cycle.

    The failure this kills (2026-08-19, real): the vendored tree carried
    other threads' committed additions; a sync session hand-merged upstream's
    copy over them, push mirrored the lossy result, and record's
    tree-identical verification then STAMPED the loss as the new truth --
    detection was luck (the erased thread's session happened to be open).
    The carry-all-pending rule (INSTALL sec.4 step 1) states the obligation;
    this check enforces it at the chokepoint every cycle must pass through.

    Mechanism: every line ADDED in the dependent repo's committed default-
    branch vendored tree relative to the recorded base must be present in
    the landed upstream tree (same file, or anywhere in the tree to tolerate
    moves). A deliberate removal needs --accept-loss, which prints exactly
    what is being let go.
    """
    base = _manifest().get('upstream', {}).get('commit')
    if not base:
        return
    _dep_git('fetch', 'origin')
    dep_branch = (_dep_git('symbolic-ref', '--short', 'refs/remotes/origin/HEAD').strip()
                  .rsplit('/', 1)[-1] or 'master')
    prefix = UPSTREAM.relative_to(ROOT).as_posix()
    names = _dep_git('ls-tree', '-r', '--name-only', f'origin/{dep_branch}', prefix).split()
    landed_all = None
    lost = []
    for name in names:
        rel = name[len(prefix) + 1:]
        committed = _dep_git('show', f'origin/{dep_branch}:{name}')
        base_txt = subprocess.run(['git', '-C', str(clone), 'show', f'{base}:{rel}'],
                                  capture_output=True, text=True).stdout
        pending = set(committed.splitlines()) - set(base_txt.splitlines())
        pending = {l for l in pending if len(l.strip()) > 3}
        if not pending:
            continue
        landed = (clone / rel).read_text(encoding='utf-8', errors='replace') \
            if (clone / rel).exists() else ''
        missing = {l for l in pending if l not in landed.splitlines()}
        if missing:
            if landed_all is None:
                landed_all = '\n'.join((clone / f).read_text(encoding='utf-8', errors='replace')
                                        for f in _files(clone) if (clone / f).suffix
                                        in ('.md', '.py', '.sh', '.json', '.yml', '.template'))
            missing = {l for l in missing if l not in landed_all}
        if missing:
            lost.append((rel, sorted(missing)))
    if not lost:
        return
    for rel, lines in lost:
        print(f"  LOST from {rel}:")
        for l in lines[:8]:
            print(f"    | {l}")
        if len(lines) > 8:
            print(f"    | ... and {len(lines) - 8} more line(s)")
    if accept_loss:
        print(f"carry check: {sum(len(l) for _, l in lost)} pending line(s) NOT in the landed "
              f"tree -- accepted deliberately (--accept-loss).")
        return
    sys.exit("checkin FAIL: pending vendored additions are MISSING from the landed upstream "
             "tree -- a check-in dropped committed content (the 2026-08-19 failure). Carry "
             "them in another PR and re-record, or pass --accept-loss if the removal is "
             "deliberate; nothing recorded.")

def record(clone, note, accept_loss=False):
    branch = _default_branch(clone)
    _git(clone, 'checkout', branch)
    _git(clone, 'pull', 'origin', branch)
    _carry_check(clone, accept_loss)
    added, modified, deleted = _diff(clone)
    if added or modified or deleted:
        for p in added + modified + deleted:
            print(f"  differs: {p}")
        sys.exit(f"checkin FAIL: clone {branch} is not identical to the vendored tree — "
                 f"merge/pull upstream first (or push the missing export); nothing recorded")
    head = _git(clone, 'rev-parse', 'HEAD')
    manifest = _manifest()
    old = manifest['upstream'].get('commit')
    manifest['upstream']['commit'] = head
    # record() has just verified the vendored tree is byte-identical to what
    # landed upstream -- which is STRONGER evidence of currency than the mirror
    # stamp update() writes. So advance synced_from too, or push()'s currency
    # guard reports a false positive on the very next export: the tree is
    # provably current while the stamp still points at the pre-merge commit.
    # (Found immediately after the guard shipped, by running the normal cycle
    # through to the end -- a reminder that a new gate is not done until the
    # whole loop has been walked with it in place.)
    manifest['upstream']['synced_from'] = head
    manifest['upstream']['_note'] = (
        f"commit = upstream hash last synced ({note or 'check-in'}, "
        f"recorded {datetime.date.today().isoformat()}; verified tree-identical).")
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf-8')
    print(f"checkin record OK: upstream.commit {old} -> {head}")
    print("next: commit process/manifest.json in this repo.")
    return 0


def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in ('status', 'update', 'push', 'record'):
        sys.exit(__doc__)
    clone = _clone_or_die(args[1])
    if args[0] == 'status':
        return status(clone)
    if args[0] == 'update':
        return update(clone, force='--force' in args)
    if args[0] == 'push':
        return push(clone, force='--force' in args)
    note = args[args.index('--note') + 1] if '--note' in args else ''
    return record(clone, note, accept_loss='--accept-loss' in sys.argv)


if __name__ == '__main__':
    sys.exit(main())
