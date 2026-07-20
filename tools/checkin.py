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

Three subcommands, in the order a check-in uses them:

  status <upstream-clone>   Compare the vendored tree against the clone's
                            working tree: list Added/Modified/Deleted files
                            (vendored perspective), show the manifest's
                            recorded upstream.commit vs the clone's HEAD.
                            Exit 1 if the trees differ (so it can gate).

  push <upstream-clone>     Run the scrub/practice audit first — it must
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
      python3 process/upstream/tools/checkin.py push   ../BestPractice
      python3 process/upstream/tools/checkin.py record ../BestPractice --note "PR #4"
"""
import datetime, filecmp, json, pathlib, shutil, subprocess, sys

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


def push(clone):
    # The scrub gates every export of content toward the public repo.
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


def record(clone, note):
    branch = (_git(clone, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD').rsplit('/', 1)[-1]
              or 'main')
    _git(clone, 'checkout', branch)
    _git(clone, 'pull', 'origin', branch)
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
    if len(args) < 2 or args[0] not in ('status', 'push', 'record'):
        sys.exit(__doc__)
    clone = _clone_or_die(args[1])
    if args[0] == 'status':
        return status(clone)
    if args[0] == 'push':
        return push(clone)
    note = args[args.index('--note') + 1] if '--note' in args else ''
    return record(clone, note)


if __name__ == '__main__':
    sys.exit(main())
