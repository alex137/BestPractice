#!/usr/bin/env python3
"""The push check on the merge GitHub would make, at its base branch's tier -- `merge-check-gate.sh` runs it before a pull request is merged through GitHub, a push no push gate sees, and again on the merge commit after it, reverting a merge that fails because the base moved in between

precedent_merge_check.py -- run the push check on a pull request before
it is merged through GitHub, since that merge is a push no local hook sees.

WHY THIS EXISTS (spec/BRANCH_TIERS_PLAN.md, "Three holes this has to
close", hole 1). The push gate checks what a session sends with `git push`.
A pull request merged with GitHub's merge tool lands on its base branch
without any local push at all, so nothing ran there. Before the branch tiers
that was safe by accident: the branch had already been fully checked when it
was pushed. Under the tiers a working branch gets only the basic check, so
without this a merge into staging or main would land work nobody fully
checked.

WHAT IT CHECKS. The commit GitHub would merge -- `refs/pull/N/merge`, the
test merge of the pull request into its base -- when GitHub has one, else
the pull request's head. The test merge counts only once its second parent
is the pull request's current head: right after a push GitHub still serves
the merge of the old head, so this waits briefly for the rebuilt one, and
judges the head itself, saying so, if it never comes. The tier is the base branch's (precedent_branches.py):
full for staging and main, the person's setting for anything else. The base
branch is read from that merge commit's first parent, matched against the
remote's branch tips; when it cannot be matched, the check is full.

It runs the repository's own precedent_push_check.py in a temporary
worktree of that commit, never in the session's checkout, so the session's
own uncommitted work is neither checked nor touched. A pass already recorded
for the same tree in the checkout is reused, so a branch fully checked
before its pull request was opened merges at once.

Run:
  precedent_merge_check.py --owner O --repo R --number N [--search DIR]...
  precedent_merge_check.py --head [--search DIR]   # `gh pr merge` with no
                                                   # number: the current branch
  precedent_merge_check.py --owner O --repo R --number N --landed SHA
      after the merge: the full check on the merge commit itself, and a
      revert when the base moved in the gap and what landed fails (landed())

Exit: 0 passed; 1 a check failed; 2 could not be run here (no checkout of
that repository, no push check in it, a fetch that failed) -- the hook
fails open on 2, loudly, the same contract every gate here keeps
(practice: fail-gracefully).
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
TOOL_CANDIDATES = ('tools/precedent_push_check.py',
                   'process/upstream/tools/precedent_push_check.py')
RECORD = 'precedent-push-check.json'
TAIL_LINES = 60
# GitHub rebuilds refs/pull/N/merge some time after the head moves, not with
# it. 2026-09-28, measured: a session pushed a fix to a pull request's head
# and merged at once; this judged the test merge of the OLD head, still
# carrying the bug, refused, and reported it as the merge GitHub would make.
# A minute later the merge ref had the new head as its second parent and the
# same merge passed. So the merge ref is judged only once its second parent
# is the pull request's current head, waited for up to this long.
MERGE_REF_WAIT_SECONDS = 90
MERGE_REF_POLL_SECONDS = 10
_sleep = time.sleep


def git(root, *args):
    p = subprocess.run(['git', '-C', str(root), *args],
                       capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def _origin_matches(root, owner, repo):
    url = git(root, 'remote', 'get-url', 'origin') or ''
    url = url.rstrip('/')
    if url.endswith('.git'):
        url = url[:-4]
    want = f'{owner}/{repo}'.lower()
    return url.lower().endswith('/' + want) or url.lower().endswith(':' + want)


def find_checkout(search, owner, repo):
    """The first git checkout among `search` and its siblings whose origin is
    owner/repo."""
    seen, candidates = set(), []
    for d in search:
        d = pathlib.Path(d).expanduser()
        top = git(d, 'rev-parse', '--show-toplevel')
        if top:
            candidates.append(pathlib.Path(top))
            d = pathlib.Path(top)
        if d.parent.is_dir():
            candidates.extend(sorted(p for p in d.parent.iterdir() if p.is_dir()))
    for c in candidates:
        if c in seen or not (c / '.git').exists():
            continue
        seen.add(c)
        if _origin_matches(c, owner, repo):
            return c
    return None


def push_check_tool(root):
    for rel in TOOL_CANDIDATES:
        if (root / rel).is_file():
            return rel
    return None


def branches_module():
    sys.path.insert(0, str(HERE))
    try:
        import precedent_branches
        return precedent_branches
    except ImportError:
        return None
    finally:
        sys.path.pop(0)


def resolve_pull(root, number, head_sha=None):
    """-> (sha, bases, what) for pull request `number`, fetched into a
    private ref namespace, or (None, [], why) when it cannot be. `bases` is
    every branch on origin whose tip is the test merge's first parent --
    more than one when branches sit at the same commit, which is exactly
    when guessing one of them would be wrong (AGENTS.md's merge-target rule
    was born of two branches at one commit).

    `head_sha` is the head GitHub reports for the pull request, when it
    could be read; without it, the fetched head ref. The test merge is used
    only once its second parent is that head (MERGE_REF_WAIT_SECONDS); if
    it never is, the head itself is judged and `what` says so."""
    ns = f'refs/precedent-merge-check/{number}'
    waited = 0
    while True:
        head = subprocess.run(['git', '-C', str(root), 'fetch', '-q', 'origin',
                               f'+refs/pull/{number}/head:{ns}/head'],
                              capture_output=True, text=True)
        if head.returncode != 0:
            return None, [], (f'could not fetch pull request #{number} from '
                              f'origin: {head.stderr.strip()[:300]}')
        fetched = git(root, 'rev-parse', f'{ns}/head')
        want = head_sha or fetched
        merged = subprocess.run(['git', '-C', str(root), 'fetch', '-q', 'origin',
                                 f'+refs/pull/{number}/merge:{ns}/merge'],
                                capture_output=True, text=True)
        if merged.returncode != 0 and fetched == want:
            return fetched, [], 'its head (GitHub has no test merge for it)'
        carried = (git(root, 'rev-parse', f'{ns}/merge^2')
                   if merged.returncode == 0 else None)
        if fetched == want and carried == want:
            sha = git(root, 'rev-parse', f'{ns}/merge')
            base_tip = git(root, 'rev-parse', f'{ns}/merge^1')
            return sha, branches_at(root, base_tip), 'the merge GitHub would make'
        if waited >= MERGE_REF_WAIT_SECONDS:
            break
        _sleep(MERGE_REF_POLL_SECONDS)
        waited += MERGE_REF_POLL_SECONDS
    if fetched != want:
        return None, [], (f'GitHub reports {want[:12]} as the head of pull '
                          f'request #{number}, but after {waited}s its head '
                          f'ref still reads {(fetched or "nothing")[:12]}, so '
                          f'nothing current could be checked. Wait a minute '
                          f'and merge again.')
    print(f'precedent_merge_check: after {waited}s GitHub\'s test merge of pull '
          f'request #{number} still carries the older head '
          f'{(carried or "none")[:12]}, not the current {want[:12]}, so it is '
          f'NOT judged -- the head itself is.', flush=True)
    return want, [], ('its current head, NOT merged with its base (the test '
                      'merge GitHub has is of an older head)')


def branches_at(root, tip):
    """Every branch on origin whose tip is `tip`."""
    out = []
    listing = git(root, 'ls-remote', '--heads', 'origin') or ''
    for line in listing.splitlines():
        sha, _, ref = line.partition('\t')
        if tip and sha == tip and ref.startswith('refs/heads/'):
            out.append(ref[len('refs/heads/'):])
    return out


def _cleanup_refs(root, number):
    for leaf in ('head', 'merge'):
        subprocess.run(['git', '-C', str(root), 'update-ref', '-d',
                        f'refs/precedent-merge-check/{number}/{leaf}'],
                       capture_output=True, text=True)


def run_in_worktree(root, sha, tier, tool_rel, extra=()):
    """-> (returncode, output). The push check, in a throwaway worktree of
    `sha`, carrying over the checkout's recorded pass so an already-checked
    tree is not checked twice."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-merge-check-'))
    wt = tmp / 'tree'
    try:
        add = subprocess.run(['git', '-C', str(root), 'worktree', 'add', '-q',
                              '--detach', str(wt), sha],
                             capture_output=True, text=True)
        if add.returncode != 0:
            return 2, f'could not make a worktree of {sha[:12]}: {add.stderr.strip()[:300]}'
        src = git(root, 'rev-parse', '--git-path', RECORD)
        dst = git(wt, 'rev-parse', '--git-path', RECORD)
        if src and dst:
            src_p = pathlib.Path(src) if pathlib.Path(src).is_absolute() else root / src
            dst_p = pathlib.Path(dst) if pathlib.Path(dst).is_absolute() else wt / dst
            if src_p.is_file():
                dst_p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_p, dst_p)
        p = subprocess.run([sys.executable, tool_rel, '--gate', '--tier', tier,
                            *extra], cwd=wt, capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr
    finally:
        subprocess.run(['git', '-C', str(root), 'worktree', 'remove', '--force',
                        str(wt)], capture_output=True, text=True)
        shutil.rmtree(tmp, ignore_errors=True)
        subprocess.run(['git', '-C', str(root), 'worktree', 'prune'],
                       capture_output=True, text=True)


def pull_head(owner, repo, number):
    """-> (head branch, head repository 'owner/name', base branch, head sha)
    of pull request `number`, or four Nones when it cannot be read -- no
    network, no credential where one is needed. One call, counted and cached
    by github_budget.py like every other call this engine makes."""
    sys.path.insert(0, str(HERE))
    try:
        import github_budget
    except ImportError:
        return None, None, None, None
    finally:
        sys.path.pop(0)
    data, err = github_budget.call(f'repos/{owner}/{repo}/pulls/{number}')
    if err or not isinstance(data, dict) or not isinstance(data.get('head'), dict):
        return None, None, None, None
    base = data.get('base') if isinstance(data.get('base'), dict) else {}
    return (data['head'].get('ref'), (data['head'].get('repo') or {}).get('full_name'),
            base.get('ref'), data['head'].get('sha'))


def choose_bases(declared_base, tip_bases):
    """-> the branch(es) a pull request's tier is judged by.

    The base GitHub declares, when it could be read. Only without it, every
    branch whose tip is the test merge's first parent, whose strictest
    decides. 2026-09-28: an update had just made pre-staging and staging at
    main's commit, so a pull request into pre-staging matched all three by
    tip, and the merge gate announced "main is a fully checked branch" --
    while the same call that reads the pull request's head had returned its
    real base all along, unread."""
    return [declared_base] if declared_base else list(tip_bases)


def tier_source_refusal(head_ref, head_repo, owner, repo, tiers):
    """-> None, or why a pull request must not be merged: it comes FROM a
    tier branch of this same repository, and merging it lets GitHub's
    GitHub's "Delete branch" button -- offered on every merged pull
    request's page for its source -- remove that branch (2026-09-26: a pull request from staging
    into main was merged and staging was deleted). A fork's branch of the
    same name is somebody else's and is not refused."""
    if not head_ref or head_ref not in tiers:
        return None
    if head_repo and head_repo.lower() != f'{owner}/{repo}'.lower():
        return None
    sys.path.insert(0, str(HERE))
    try:
        import precedent_branches
        copy = precedent_branches.promote_branch_name(
            HERE.parent, precedent_branches.COPY_SLUG, None) or 'to-main-copy'
    except Exception:                                          # noqa: BLE001
        copy = 'to-main-copy'
    finally:
        sys.path.pop(0)
    return (f'this pull request comes FROM {head_ref}, a tier branch. When it '
            f'is merged, its page offers to delete {head_ref} -- and staging '
            f'disappeared right after such a merge on 2026-09-26. Open it '
            f'from a throwaway copy instead:\n'
            f'  git push origin origin/{head_ref}:refs/heads/{copy}\n'
            f'then a pull request from {copy} into the same base, and close '
            f'this one. GitHub deletes the copy; {head_ref} stays.')


def pull_landed(owner, repo, number):
    """-> (merged, base branch, merge commit) of pull request `number` as
    GitHub reports it now, uncached -- before the merge the same field names
    the test merge. (None, None, None) when it cannot be read."""
    sys.path.insert(0, str(HERE))
    try:
        import github_budget
    except ImportError:
        return None, None, None
    finally:
        sys.path.pop(0)
    data, err = github_budget.call(f'repos/{owner}/{repo}/pulls/{number}',
                                   cache=False)
    if err or not isinstance(data, dict):
        return None, None, None
    base = data.get('base') if isinstance(data.get('base'), dict) else {}
    return bool(data.get('merged')), base.get('ref'), data.get('merge_commit_sha')


def revert_landing(root, base, sha, number, pb=None):
    """-> (done, what). Put `base` back to the tree it had just before merge
    commit `sha`, by a new commit on top of `sha` -- nothing is rewritten,
    and the pull request's branch still carries the work. Done only while
    `base` still points at `sha`: a base that moved on again is reported,
    never reverted over someone else's commit."""
    tip = None
    for line in (git(root, 'ls-remote', '--heads', 'origin', base) or '').splitlines():
        s, _, ref = line.partition('\t')
        if ref == f'refs/heads/{base}':
            tip = s
    if tip != sha:
        return False, (f'{base} has moved on to {(tip or "nothing")[:12]} since '
                       f'the merge, so it was NOT reverted')
    before = git(root, 'rev-parse', f'{sha}^1^{{tree}}')
    if not before:
        return False, f'the tree before {sha[:12]} could not be read'
    env = pb._merge_env(root) if pb and hasattr(pb, '_merge_env') else None
    made = subprocess.run(
        ['git', '-C', str(root), 'commit-tree', before, '-p', sha, '-m',
         f'Revert pull request #{number}: {base} moved while it merged, and '
         f'what landed failed its full check',
         '-m', 'precedent_merge_check.py --landed put the base back to the '
               'tree it had just before the merge. Nothing is lost: the pull '
               'request\'s branch still has the work. Merge the base into it, '
               'fix what the check found, and merge it again.'],
        capture_output=True, text=True, env=env)
    commit = made.stdout.strip()
    if made.returncode != 0 or not commit:
        return False, f'the revert commit could not be made: {made.stderr.strip()[:200]}'
    push = subprocess.run(['git', '-C', str(root), 'push', '-q', 'origin',
                           f'{commit}:refs/heads/{base}'],
                          capture_output=True, text=True)
    if push.returncode != 0:
        return False, f'the revert was refused: {push.stderr.strip()[:200]}'
    return True, f'{base} is back at the tree it had before the merge ({commit[:12]})'


def landed(argv, pb, search):
    """--landed [SHA]: after a merge through GitHub, check what actually
    landed, and undo it when it fails.

    WHY (2026-09-30). The merge gate checks the test merge, then frees the
    base's hold, and GitHub merges seconds later. A base that moved in those
    seconds gets a merge nobody checked. So once the merge is done this runs
    the full check on the merge commit itself. When nothing moved it is the
    tree the gate passed, and the recorded pass is reused at once. When the
    base moved, the check runs; if it fails, the merge is reverted
    (revert_landing), which puts the base back to the tree the other window
    had already landed."""
    owner, repo, number = (_arg(argv, '--owner'), _arg(argv, '--repo'),
                           _arg(argv, '--number'))
    if not (owner and repo and number and re.fullmatch(r'\d+', number)):
        print('precedent_merge_check: --landed needs --owner, --repo and a '
              'numeric --number.')
        return 2
    sha = _arg(argv, '--landed')
    sha = sha if sha and re.fullmatch(r'[0-9a-f]{40}', sha) else None
    merged, base, api_sha = pull_landed(owner, repo, number)
    if merged is False:
        return 0            # nothing landed: a refused or failed merge
    sha = sha or (api_sha if merged else None)
    if not sha:
        print(f'precedent_merge_check: could not tell which commit pull '
              f'request #{number} landed as, so what landed was NOT checked.')
        return 2
    root = find_checkout(search, owner, repo)
    if root is None:
        print(f'precedent_merge_check: no checkout of {owner}/{repo} here, so '
              f'what pull request #{number} landed was NOT checked.')
        return 2
    tool_rel = push_check_tool(root)
    if not tool_rel:
        return 2
    ns = f'refs/precedent-merge-check/{number}/landed'
    try:
        if base:
            subprocess.run(['git', '-C', str(root), 'fetch', '-q', 'origin',
                            f'+refs/heads/{base}:{ns}'], capture_output=True, text=True)
        if not git(root, 'cat-file', '-t', sha):
            subprocess.run(['git', '-C', str(root), 'fetch', '-q', 'origin', sha],
                           capture_output=True, text=True)
        if git(root, 'cat-file', '-t', sha) != 'commit':
            print(f'precedent_merge_check: the merge commit {sha[:12]} of pull '
                  f'request #{number} could not be fetched, so it was NOT checked.')
            return 2
        full = pb.full_branches(root) if pb else {'main', 'staging'}
        if not base:
            # Without GitHub's word: the fully checked branch at the merge,
            # else one whose history holds it (it may have moved on since).
            bases = [b for b in branches_at(root, sha) if b in full]
            for b in ([] if bases else sorted(full)):
                got = subprocess.run(['git', '-C', str(root), 'fetch', '-q',
                                      'origin', f'+refs/heads/{b}:{ns}'],
                                     capture_output=True, text=True)
                if got.returncode == 0 and subprocess.run(
                        ['git', '-C', str(root), 'merge-base', '--is-ancestor',
                         sha, ns], capture_output=True).returncode == 0:
                    bases = [b]
                    break
            base = bases[0] if bases else None
        if not base or base not in full:
            return 0        # a working branch: its basic check was the gate's
        rc, out = run_in_worktree(root, sha, 'full', tool_rel)
    finally:
        subprocess.run(['git', '-C', str(root), 'update-ref', '-d', ns],
                       capture_output=True, text=True)
    if rc == 0 and 'this exact tree already passed' in out:
        print(f'precedent_merge_check: pull request #{number} landed on {base} '
              f'as checked ({sha[:12]}).')
        return 0
    if rc == 0:
        print(f'precedent_merge_check: {base} MOVED while pull request '
              f'#{number} merged, so what landed ({sha[:12]}) was not what the '
              f'gate checked. It has now had its own full check, and passed.')
        return 0
    tail = '\n'.join(out.rstrip().splitlines()[-TAIL_LINES:])
    if rc != 1:
        print(f'precedent_merge_check: {base} MOVED while pull request '
              f'#{number} merged, and what landed ({sha[:12]}) could not be '
              f'checked here:\n{tail}')
        return 2
    done, what = revert_landing(root, base, sha, number, pb)
    print(f'precedent_merge_check: {base} MOVED while pull request #{number} '
          f'merged, and what landed ({sha[:12]}) FAILED its full check. '
          + (f'Reverted: {what}. The pull request\'s branch still has the '
             f'work: merge {base} into it, fix the finding, and merge again.'
             if done else f'{what}. Fix it on {base} now.')
          + f'\n{tail}')
    return 1


def _arg(argv, name):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1]
    return None


def main(argv):
    search = [a for i, a in enumerate(argv) if i and argv[i - 1] == '--search']
    search = search or [str(pathlib.Path.cwd())]
    pb = branches_module()

    if '--landed' in argv:
        return landed(argv, pb, search)

    # The No ladders test session merges nothing (precedent_ladder.py).
    try:
        sys.path.insert(0, str(HERE))
        import precedent_ladder
        refusal = precedent_ladder.test_session_refusal()
    except Exception:                                        # noqa: BLE001
        refusal = None
    if refusal:
        print(f'precedent_merge_check: {refusal}')
        return 1

    if '--head' in argv:
        root_s = git(search[0], 'rev-parse', '--show-toplevel')
        if not root_s:
            print(f'precedent_merge_check: {search[0]} is not a git checkout.')
            return 2
        root = pathlib.Path(root_s)
        tool_rel = push_check_tool(root)
        if not tool_rel:
            print(f'precedent_merge_check: {root} carries no push check.')
            return 2
        p = subprocess.run([sys.executable, tool_rel, '--gate', '--tier', 'full'],
                           cwd=root, capture_output=True, text=True)
        print(f'precedent_merge_check: the pull request of the current branch '
              f'of {root.name}, checked fully -- its base branch is not named '
              f'here.')
        print((p.stdout + p.stderr).rstrip())
        return 0 if p.returncode == 0 else (1 if p.returncode == 1 else 2)

    owner, repo, number = (_arg(argv, '--owner'), _arg(argv, '--repo'),
                           _arg(argv, '--number'))
    if not (owner and repo and number and re.fullmatch(r'\d+', number)):
        print('precedent_merge_check: needs --owner, --repo and a numeric '
              '--number, or --head.')
        return 2
    # A tier branch is never a pull request's source, whether or not this
    # machine can check the merge itself.
    if pb:
        root_guess = find_checkout(search, owner, repo)
        tiers = pb.tier_branches(root_guess) if root_guess else [
            pb.MAIN, pb.STAGING, pb.PRE_STAGING, pb.LEGACY_STAGING]
    else:
        tiers = ['main', 'staging', 'pre-staging', 'precedent-beta-v01']
    head_ref, head_repo, declared_base, head_sha = pull_head(owner, repo, number)
    why_not = tier_source_refusal(head_ref, head_repo, owner, repo, tiers)
    if why_not:
        print(f'precedent_merge_check: pull request #{number} of '
              f'{owner}/{repo} REFUSED -- {why_not}')
        return 1
    root = find_checkout(search, owner, repo)
    if root is None:
        print(f'precedent_merge_check: no checkout of {owner}/{repo} beside '
              f'{", ".join(search)}, so pull request #{number} could not be '
              f'checked here.')
        return 2
    tool_rel = push_check_tool(root)
    if not tool_rel:
        print(f'precedent_merge_check: {root} carries no push check, so there '
              f'is nothing to run.')
        return 2
    try:
        sha, bases, what = resolve_pull(root, number, head_sha)
        if sha is None:
            print(f'precedent_merge_check: {what}')
            return 2
        bases = choose_bases(declared_base, bases)
        refusal = getattr(pb, 'merge_refusal', None) if pb else None
        if refusal:
            heads = branches_at(root, git(root, 'rev-parse',
                                          f'refs/precedent-merge-check/{number}/head'))
            why_not = refusal(root, bases, heads)
            if why_not:
                print(f'precedent_merge_check: REFUSED pull request #{number} '
                      f'of {owner}/{repo} -- {why_not}')
                return 1
        if bases and pb:
            # Every branch at that commit could be the base; the strictest
            # of them decides.
            tiers = [pb.tier_for_branch(root, b) for b in bases]
            full = [t for t in tiers if t[0] == 'full']
            tier, why = full[0] if full else tiers[0]
        else:
            tier, why = 'full', ('the base branch could not be matched to a '
                                 'branch on origin, so it is checked fully')
        base = ' or '.join(bases) if bases else 'an unmatched base'
        print(f'precedent_merge_check: pull request #{number} of '
              f'{owner}/{repo} into {base} -- '
              f'{tier} check of {what} ({sha[:12]}); {why}.', flush=True)
        # A pull request into pre-staging is judged by the practice checks
        # on the files it changes (precedent_push_check.CHANGED_PRACTICE_CHECK).
        extra = ()
        if tier == 'basic' and pb and pb.PRE_STAGING in bases:
            extra = ('--changed-since', f'origin/{pb.PRE_STAGING}')
        # A fully checked base is held still while its merge is judged
        # (precedent_branches.hold_for_landing): a Promote or another landing
        # moving it now would make this pass stale before it is used.
        held = None
        hold = getattr(pb, 'hold_for_landing', None) if pb else None
        # Only where the tiers exist: a repository that never promotes has
        # no lock, and must not grow a branch because a merge was checked.
        if hold and tier == 'full' and bases \
                and set(bases) & set(pb.full_branches(root)) \
                and pb._remote_tip(root, pb.PRE_STAGING):
            state, info = hold(root, f'landing pull request #{number} into {base}')
            if state == 'busy':
                print(f'precedent_merge_check: REFUSED pull request #{number} '
                      f'of {owner}/{repo} for now -- {base} is being moved or '
                      f'checked by another window ({info}), so a check started '
                      f'now would be out of date before it finished. Merge '
                      f'again once that ends; a claim frees itself after '
                      f'{pb.LOCK_STALE_SECONDS // 60} minutes.')
                return 1
            if state == 'held':
                held = info
        try:
            rc, out = run_in_worktree(root, sha, tier, tool_rel, extra)
        finally:
            if held:
                pb.release_hold(root, held)
    finally:
        _cleanup_refs(root, number)
    tail = out.rstrip().splitlines()[-TAIL_LINES:]
    print('\n'.join(tail))
    if rc == 0:
        return 0
    return 1 if rc == 1 else 2


# THE MERGE GATE'S WORDS ARE WRITTEN HERE, NOT IN THE HOOK (2026-10-07), for
# the reason doc_lint.py's hook_reason gives: a reworded hook is a question
# for a person in every repository at its next Update Vendors, and a
# reworded tool is not. .claude/hooks/merge-check-gate.sh pipes the run's
# output back in with --hook-reason and passes on what comes out.
# The hook refuses the WHOLE command before any of it starts, so a commit
# or push chained in front of the merge did not happen either; a bare
# "REFUSED this merge" was read as covering only the last step
# (2026-10-03, 2026-10-05, the push gate's twin of this).
NOTHING_RAN = ('Nothing in the refused command ran -- not the merge, and not any step\n'
               'before it in the same command (a commit or a push included). Make those\n'
               'steps in a call of their own, check `git status`, then merge separately.')


def hook_reason(outcome, out):
    """-> the whole text the merge gate refuses or blocks with: '1' a check
    failed before the merge, '124' the hook's deadline killed the run,
    'landed-1' what the merge landed failed afterwards. None otherwise."""
    if outcome == 'landed-1':
        return f'What this merge landed failed its full check.\n\n{out.rstrip()}'
    if outcome == '1':
        why = ('A check failed on what this merge would land. Fix it on the\n'
               'branch and push, then merge.')
    elif outcome == '124':
        why = ('The checks did not finish within 14 minutes, so nothing was\n'
               'verified. Run the push check on the branch first -- a recorded pass for the\n'
               'same tree is reused -- then merge.')
    else:
        return None
    tail = '\n'.join(out.rstrip().splitlines()[-120:])
    return ('The merge check REFUSED this merge.\n\n'
            f'{NOTHING_RAN}\n\n{why}\n\n{tail}\n\n'
            'Nothing lets a merge past this, and nothing should: fix what it found on\n'
            'the branch, push, and merge again. If the check itself is wrong, fix the\n'
            'check where it lives.')


def _hook_reason_main(argv):
    """`--hook-reason OUTCOME`, the run's output on stdin: print the text,
    exit 0; exit 2 for an outcome this tool does not word."""
    i = argv.index('--hook-reason') + 1
    text = hook_reason(argv[i] if i < len(argv) else '', sys.stdin.read())
    if text is None:
        return 2
    print(text)
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    if '--hook-reason' in sys.argv[1:]:
        sys.exit(_hook_reason_main(sys.argv[1:]))
    sys.exit(main(sys.argv[1:]))
