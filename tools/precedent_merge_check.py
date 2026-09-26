#!/usr/bin/env python3
"""precedent_merge_check.py -- run the push check on a pull request before
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
the pull request's head. The tier is the base branch's (precedent_branches.py):
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

HERE = pathlib.Path(__file__).resolve().parent
TOOL_CANDIDATES = ('tools/precedent_push_check.py',
                   'process/upstream/tools/precedent_push_check.py')
RECORD = 'precedent-push-check.json'
TAIL_LINES = 60


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


def resolve_pull(root, number):
    """-> (sha, bases, what) for pull request `number`, fetched into a
    private ref namespace, or (None, [], why) when it cannot be. `bases` is
    every branch on origin whose tip is the test merge's first parent --
    more than one when branches sit at the same commit, which is exactly
    when guessing one of them would be wrong (AGENTS.md's merge-target rule
    was born of two branches at one commit)."""
    ns = f'refs/precedent-merge-check/{number}'
    head = subprocess.run(['git', '-C', str(root), 'fetch', '-q', 'origin',
                           f'+refs/pull/{number}/head:{ns}/head'],
                          capture_output=True, text=True)
    if head.returncode != 0:
        return None, [], (f'could not fetch pull request #{number} from '
                          f'origin: {head.stderr.strip()[:300]}')
    merged = subprocess.run(['git', '-C', str(root), 'fetch', '-q', 'origin',
                             f'+refs/pull/{number}/merge:{ns}/merge'],
                            capture_output=True, text=True)
    if merged.returncode != 0:
        sha = git(root, 'rev-parse', f'{ns}/head')
        return sha, [], 'its head (GitHub has no test merge for it)'
    sha = git(root, 'rev-parse', f'{ns}/merge')
    base_tip = git(root, 'rev-parse', f'{ns}/merge^1')
    return sha, branches_at(root, base_tip), 'the merge GitHub would make'


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


def run_in_worktree(root, sha, tier, tool_rel):
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
        p = subprocess.run([sys.executable, tool_rel, '--gate', '--tier', tier],
                           cwd=wt, capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr
    finally:
        subprocess.run(['git', '-C', str(root), 'worktree', 'remove', '--force',
                        str(wt)], capture_output=True, text=True)
        shutil.rmtree(tmp, ignore_errors=True)
        subprocess.run(['git', '-C', str(root), 'worktree', 'prune'],
                       capture_output=True, text=True)


def pull_head(owner, repo, number, timeout=20):
    """-> (head branch, head repository 'owner/name') of pull request
    `number`, from GitHub's API, or (None, None) when it cannot be read --
    no network, no credential where one is needed. A GH_TOKEN or
    GITHUB_TOKEN is sent when set; a cloud session's proxy supplies one
    itself."""
    import urllib.request
    import os
    headers = {'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{number}'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers),
                                    timeout=timeout) as r:
            data = json.load(r)
        return data['head']['ref'], (data['head'].get('repo') or {}).get('full_name')
    except Exception:                                          # noqa: BLE001
        return None, None


def tier_source_refusal(head_ref, head_repo, owner, repo, tiers):
    """-> None, or why a pull request must not be merged: it comes FROM a
    tier branch of this same repository, and merging it lets GitHub's
    auto-delete remove that branch (2026-09-26: a pull request from staging
    into main was merged and staging was deleted). A fork's branch of the
    same name is somebody else's and is not refused."""
    if not head_ref or head_ref not in tiers:
        return None
    if head_repo and head_repo.lower() != f'{owner}/{repo}'.lower():
        return None
    from datetime import date
    copy = f'to-main-{date.today().isoformat()}'
    return (f'this pull request comes FROM {head_ref}, a tier branch. When it '
            f'is merged, GitHub\'s "automatically delete head branches" '
            f'deletes {head_ref} -- which is how staging disappeared on '
            f'2026-09-26. Open it from a throwaway copy instead:\n'
            f'  git push origin origin/{head_ref}:refs/heads/{copy}\n'
            f'then a pull request from {copy} into the same base, and close '
            f'this one. GitHub deletes the copy; {head_ref} stays.')


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
    head_ref, head_repo = pull_head(owner, repo, number)
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
        sha, bases, what = resolve_pull(root, number)
        if sha is None:
            print(f'precedent_merge_check: {what}')
            return 2
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
        rc, out = run_in_worktree(root, sha, tier, tool_rel)
    finally:
        _cleanup_refs(root, number)
    tail = out.rstrip().splitlines()[-TAIL_LINES:]
    print('\n'.join(tail))
    if rc == 0:
        return 0
    return 1 if rc == 1 else 2


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
