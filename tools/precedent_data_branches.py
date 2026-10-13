#!/usr/bin/env python3
"""Which branch holds each of the engine's long-lived data -- `data-<what>` in a repository on the ladder, the old `precedent-<what>` name everywhere else -- and the rename that moves a ladder repository onto the new names

precedent_data_branches.py -- the one place the engine's data branches are
named.

Some branches are not work at all: they hold data the engine keeps for a
repository, live for as long as the repository does, and are never merged.
Two are the engine's own:

    data-check-receipts   (was precedent-check-receipts)  which checks passed
                          on which tree, so no other checkout re-runs them
    data-promote-lock     (was precedent-promote-lock)    held while a
                          Promote or a landing check runs, so two never overlap

THE RULE (Morgan, 2026-10-11, strength: decided: "'data-' for permanent
branches is great and approved (maybe we also rename existing ones?) BUT
maybe this should be in 'ladder' only, because Alex might not want this and
we don't want to touch his"). A long-lived data branch starts `data-`, so a
branch list says at a glance which branches are live records and not
finished work -- but only where the ladder is in force. Everywhere else the
names stay as they were.

HOW A NAME IS CHOSEN, for one repository, in this order:

  1. origin has `data-<what>`: that, whoever is working. Once a repository
     has moved, every session in it reads and writes the same branch, on the
     ladder or not, so receipts and the lock stay shared between them.
  2. a ladder repository -- the ladder is in force for the person here
     (precedent_ladder) AND the repository has the ladder's tiers
     (precedent_branches.repo_has_tiers) -- writes `data-<what>`. If the old
     branch is there, the first write copies it: `data-<what>` is pushed at
     the old branch's tip, history and all, and the old branch is left
     exactly where it was (practice: never-delete-a-remote-branch). That is
     the rename of the existing ones Morgan asked about. Nothing reads the
     old branch after that, so the copy says so with the link that deletes
     it, and the branch-cleanup page lists it (2026-10-13).
  3. anything else: the old name. A repository without the ladder never
     gains a `data-` branch from here.

Reading never pushes: name() only looks, and in a ladder repository not
moved yet it still reads the old branch. The copy happens in
name_for_write(), which the two writers call -- the push check before it
publishes a receipt, Promote before it takes the lock.

A WINDOW ON AN OLDER ENGINE keeps writing the old name until its repository
takes this engine. For receipts that costs a re-run at most. For the lock,
the claim here also counts a fresh hold on the old branch as busy, so a
Promote on this engine never starts beside one on an older engine.

The coordination board and the result cache (lease_board.py,
result_cache.py) are libraries whose host names their branch; a ladder
repository's host names them `data-leases` and `data-result-cache`.

Run:
  python3 tools/precedent_data_branches.py              # each data branch here, and why
  python3 tools/precedent_data_branches.py --migrate    # copy old ones to data- now (ladder only)
"""
import argparse
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

PREFIX = 'data-'
# <what> -> the name it had before 2026-10-11.
LEGACY = {
    'check-receipts': 'precedent-check-receipts',
    'promote-lock': 'precedent-promote-lock',
}
RECEIPTS = 'check-receipts'
LOCK = 'promote-lock'


def new_name(what):
    return PREFIX + what


def legacy_name(what):
    return LEGACY[what]


def every_name():
    """-> both names of every data branch: what never-delete lists hold."""
    return sorted({n for w in LEGACY for n in (new_name(w), legacy_name(w))})


def is_data_branch(name):
    """True for any branch this convention marks as a live record."""
    name = str(name or '')
    return name.startswith(PREFIX) or name in LEGACY.values()


def _git(root, *args, timeout=60):
    try:
        return subprocess.run(['git', '-C', str(root), *args],
                              capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None


def remote_tip(root, branch):
    """-> the branch's commit on origin, '' when origin has no such branch,
    None when origin could not be asked."""
    r = _git(root, 'ls-remote', '--heads', 'origin', f'refs/heads/{branch}')
    if r is None or r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        sha, _, ref = line.partition('\t')
        if ref.strip() == f'refs/heads/{branch}':
            return sha.strip()
    return ''


def on_the_ladder(root):
    """True when this is a ladder repository for the person here: the ladder
    is in force and the repository has its tiers. False when either is
    missing, or cannot be read -- the old names are the safe answer."""
    sys.path.insert(0, str(HERE))
    try:
        import precedent_branches as pb
        return bool(pb.ladder_in_force(root)) and bool(pb.repo_has_tiers(root))
    except Exception:                                         # noqa: BLE001
        return False
    finally:
        sys.path.pop(0)


_CACHE = {}


def name(root, what, ladder=None, tip=remote_tip):
    """-> (branch, why) for reading `what` in `root`. Never pushes.
    `ladder` None means ask on_the_ladder; `tip` is remote_tip (a test
    passes its own). A ladder repository that still has only the old branch
    reads the old one: nothing has been copied yet."""
    key = (str(pathlib.Path(root).resolve()), what)
    if ladder is None and tip is remote_tip and key in _CACHE:
        return _CACHE[key]
    new, old = new_name(what), legacy_name(what)
    if tip(root, new):
        out = (new, f'origin has {new}')
    elif not (on_the_ladder(root) if ladder is None else ladder):
        out = (old, 'not a ladder repository, so the name it always had')
    elif tip(root, old):
        out = (old, f'a ladder repository not moved yet: the next write '
                    f'copies {old} to {new}')
    else:
        out = (new, 'a ladder repository')
    if ladder is None and tip is remote_tip:
        _CACHE[key] = out
    return out


def name_for_write(root, what, ladder=None, tip=remote_tip, say=None):
    """-> the branch to write `what` to. In a ladder repository that still
    has only the old branch, first pushes `data-<what>` at the old branch's
    tip; the old branch is left as it is. Never raises: a copy that fails is
    said, and the write goes to the old branch, as before."""
    new, old = new_name(what), legacy_name(what)
    if tip(root, new):
        return new
    if not (on_the_ladder(root) if ladder is None else ladder):
        return old
    old_tip = tip(root, old)
    if not old_tip:
        return new
    ok, err = copy_branch(root, old, old_tip, new)
    _CACHE.pop((str(pathlib.Path(root).resolve()), what), None)
    if ok:
        if say:
            url = _delete_link(root, old)
            say(f'{new} made from {old} (at {old_tip[:12]}). Nothing reads '
                f'{old} now -- {new} holds its whole history -- so it can be '
                f'deleted; it is left for you to delete'
                + (f': {url}' if url else '')
                + ' (the branch-cleanup page lists it too).')
        return new
    if say:
        say(f'NOTE: could not make {new} from {old} ({err[:160]}); '
            f'writing {old} as before.')
    return old


def _delete_link(root, branch):
    """-> GitHub's branch list filtered to `branch`, where its trash icon
    deletes it, or '' when origin is not on GitHub. The engine never deletes
    a remote branch itself (practice: never-delete-a-remote-branch); the
    link is how the person does (practice: branch-delete-links)."""
    try:
        sys.path.insert(0, str(HERE))
        import precedent_stale_branches as sb
        slug = sb._slug(root)
        return sb.link(*slug, branch) if slug else ''
    except Exception:                                         # noqa: BLE001
        return ''
    finally:
        sys.path.pop(0)


def copy_branch(root, old, old_tip, new):
    """Push origin's `old` (at `old_tip`) to a new branch `new` on origin.
    -> (ok, stderr). Never forced: a `new` that appeared meanwhile refuses."""
    f = _git(root, 'fetch', '-q', '--no-tags', 'origin', f'refs/heads/{old}')
    if f is None or f.returncode != 0:
        return False, (f.stderr.strip() if f else 'fetch timed out')
    # --no-verify: the pre-push hook is the push check, which judges work,
    # and this pushes none.
    p = _git(root, 'push', '-q', '--no-verify', 'origin',
             f'{old_tip}:refs/heads/{new}')
    if p is None:
        return False, 'push timed out'
    return p.returncode == 0, p.stderr.strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--repo', default='.', help='the checkout to ask about')
    ap.add_argument('--migrate', action='store_true',
                    help='in a ladder repository, copy each old branch to its data- name now')
    args = ap.parse_args(argv)
    root = pathlib.Path(args.repo).resolve()
    for what in LEGACY:
        if args.migrate:
            branch = name_for_write(root, what, say=print)
            print(f'{what}: {branch}')
        else:
            branch, why = name(root, what)
            print(f'{what}: {branch} ({why})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
