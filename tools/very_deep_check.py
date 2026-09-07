#!/usr/bin/env python3
"""very_deep_check.py -- the very deep check (practice: very-deep-check).

Enumerates this checkout's own scope -- its top-level documents plus every
active source's `practices/*.md` tree, resolved via
tools/precedent_resolve.py the same way ordinary loading is -- and hands the
invoking session a fixed checklist of drift categories to read that scope
against. On-demand only, invoked explicitly by a person; never wired into a
commit, push, or merge gate.

NOT `full_practice_audit.py` under another name. That tool asks, one
practice at a time, "is this specific Rule satisfied?" -- a closed question
against one document's own text. This one asks a question no single
practice's Rule can be checked against: does the repo's OWN WRITING, taken as
a set, still hold together? A contradiction between two documents or a
cross-reference gone stale is not a violation of any one practice's Rule; it
is a property of the documents together, which a per-practice sweep -- run
any number of times -- cannot see.

WHAT THIS TOOL DOES AND DOES NOT DO. It enumerates; it does not read or
judge. Enumerating requires no model judgment (it is a directory walk), so
it is done here, mechanically, the same reasoning `full_practice_audit.py`
gives for enumerating practices instead of leaving that to the session too.
Reading the enumerated scope for contradiction, staleness, repetition,
disproportion, formatting drift, self-application gaps, and backlog drift
is the part only a session can do -- see practices/very-deep-check.md's
Detail section for the fixed checklist, printed again at the end of this
tool's own output so it travels with the enumeration.

READ practices/very-deep-check.md's Why section before trusting this
mechanism's own reliability -- it has not been evaluated the way
full-practice-audit and routing-audit have.

A missing declared team or individual source FAILS this tool by default
(practice: very-deep-check) -- the ordinary loader degrades gracefully when
one is absent, which is right for routine loading but wrong here: a very
deep check that silently runs without a source it was told to check is not
a very deep check. Pass --allow-missing-sources for the rare case where
that is actually intended.

Also scans this checkout and every team/individual source that is its own
git checkout for branches, in BOTH directions. Fully merged and not yet
deleted (git merge-base --is-ancestor -- true regardless of whether
GitHub's own "merged" flag is set, which it is not for a repo that lands
PRs by direct push) is the cheap half. The half that costs more is the
other one: a branch that never landed and that nobody ever decided about.
Each of those is reported with what it is ahead by, when it last moved, and
how many of its commits have no patch-equivalent on the integration branch
(git cherry -- so a rebased or squash-merged branch is not mistaken for
unlanded work), plus a verdict to act on. Reported for the invoking session to cross-check
against each branch's PR history and report with a direct link, per
practice: very-deep-check and the branch-cleanup method
next-steps-after-commit (in a repo running that practice) already defines --
this offline scan has no GitHub access, so it can prove "merged" but never
"who opened this" or "which PR", the same limits practice: next-steps-after-
commit already lays out for that lookup.

FIRST, before it reads anything: every repo in force must be provably
current against its origin -- this checkout and every declared team or
individual source. Not provably current FAILS the run (--allow-stale for a
deliberately offline one). "Stale" and "cannot prove it isn't" are the same
verdict, because the failure mode is identical: a confident report that
current work is missing and fixed bugs are open. It verifies rather than
mutates; --freshen fast-forwards, and only a clean tree that is strictly
behind.

Run:
  python3 tools/very_deep_check.py [--repo PATH] [--user-config PATH]
      -- the scope to read, plus the checklist, as plain text.
  python3 tools/very_deep_check.py --json [--repo PATH] [--user-config PATH]
      -- the same enumeration as structured data.
  python3 tools/very_deep_check.py --target BRANCH
      -- override the checkout's own integration branch for the merge scan
      (e.g. "precedent-beta-v01" in this repo, while the sweep still
      defaults to "main" for every other source).
  python3 tools/very_deep_check.py --allow-missing-sources
      -- proceed even if a declared team/individual source isn't present.
  python3 tools/very_deep_check.py --skip-branch-scan
      -- enumerate and check sources only; skip the git merge scan.
  python3 tools/very_deep_check.py --freshen
      -- fast-forward any repo in force that is strictly behind on a clean
      tree, then proceed. Never touches a diverged or dirty one: there,
      fast-forwarding discards commits.
  python3 tools/very_deep_check.py --allow-stale
      -- run anyway on a tree that is not provably current. For a
      deliberately offline run only; every finding is then provisional.
Exit: 1 if any repo in force is not provably current (unless --allow-stale),
or if a declared team/individual source is missing (unless
--allow-missing-sources); 0 otherwise.
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_resolve as pr

FATAL_MISSING_LEVELS = ('team', 'individual')

# Top-level documents worth reading for coherence, if a given scope has them.
# Not every source will carry every name; only files that actually exist are
# reported. Deliberately a fixed, generic list rather than reflection over
# "every markdown file at the root" -- that would also sweep in one-off
# planning documents no session should be reading for whole-repo coherence.
CANDIDATE_DOCS = [
    "README.md", "AGENTS.md", "CLAUDE.md", "MAP.md", "GLOSSARY.md",
    "TODO.md", "GETTING_STARTED.md",
]

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import parse_check as pcheck  # noqa: E402
import precedent_bootstrap_source as bootstrap_source  # noqa: E402
import split_practices as sp  # noqa: E402

# The passes the invoking session actually works are read from the practice
# file's own `## Detail` section at run time, not kept as a second copy here.
# They used to be a CHECKLIST string literal in this file, which is a copy of
# practices/very-deep-check.md's Detail with nothing keeping the two in step
# -- exactly the "needless repetition" the check itself tells a session to
# report. One source, one code path (split_practices is the same parser
# precedent_show.py uses, so the section boundaries can't be read two ways).
PRACTICE_FILE = ROOT / 'practices' / 'very-deep-check.md'


def checklist(practice_file=None):
    """-> the practice's ## Detail section as text, or a pointer to it if the
    file isn't readable from here. Never raises: a tool that dies rather than
    printing its enumeration because a doc moved is worse than one that says
    where to look."""
    path = pathlib.Path(practice_file or PRACTICE_FILE)
    try:
        _fm, sections = sp._read_practice_file(path)
        body = (sections.get('detail') or '').strip()
    except Exception as exc:                                  # noqa: BLE001
        body = ''
        why = f'{type(exc).__name__}: {exc}'
    else:
        why = 'that section is empty'
    if body:
        return body
    return (f"(could not read the passes from {path} -- {why}. Read that "
            f"file's ## Detail section directly, or run "
            f"`python3 tools/precedent_show.py very-deep-check --detail`.)")


def _run_git(repo_dir, *args):
    try:
        r = subprocess.run(['git', '-C', str(repo_dir), *args],
                            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return 1, '', 'git unavailable or timed out'
    return r.returncode, r.stdout.strip(), r.stderr.strip()



# --- freshness gate (practice: very-deep-check) -------------------------
# The FIRST thing the check does, before it parses or reads a line, and a
# hard refusal rather than a warning.
#
# The incident this closes is in AGENTS.md's gotchas three times over: a
# session 366 commits behind concluded that files which had landed days
# earlier "did not exist", and the session-start guard that should have
# caught it was itself too old to contain the check. Warning was already
# tried and already failed -- by the time a stale session can act on a
# warning, it has been handed stale instructions and has no way to know it.
# A very deep check is the worst place for this: its whole product is
# judgment about what the repo says, so a stale tree does not degrade the
# result, it inverts it -- current work reads as missing, and fixed bugs
# read as open.
#
# Every repo in force, not just this checkout: the session-start guard runs
# for the session's PRIMARY repo only, so a sibling source attached with
# add_repo has never been freshness-checked at all (AGENTS.md, "A repo
# attached mid-session never runs its own SessionStart hook").
#
# It VERIFIES; it does not mutate, unless --freshen is passed and the tree
# is clean and strictly behind. A tool that pulls inside a clone handed to
# it is its own gotcha in that same section -- one silently moved a
# session's checkout onto another branch mid-session -- so there is no
# checkout, no pull, and nothing at all done to a diverged or dirty tree,
# where fast-forwarding would discard someone's commits.
FRESHNESS_CLEAN = ('current', 'ahead', 'no-remote', 'not-a-checkout')


def freshness(repo_dir, fetch=True):
    """-> {'status', 'branch', 'behind', 'ahead', 'remedy'}.

    status: not-a-checkout | no-remote | detached | no-upstream |
            fetch-failed | branch-not-on-origin | no-shared-history |
            behind | diverged | ahead | current. Everything outside FRESHNESS_CLEAN is a
    refusal: "cannot prove this is current" and "is known stale" are the
    same verdict here, because the failure mode is a confident wrong
    answer either way."""
    repo_dir = pathlib.Path(repo_dir)
    out = {'status': 'not-a-checkout', 'branch': None, 'behind': 0,
           'ahead': 0, 'remedy': None}
    if not (repo_dir / '.git').exists():
        return out
    rc, remotes, _ = _run_git(repo_dir, 'remote')
    if rc != 0 or 'origin' not in remotes.split():
        # Nothing to be behind. A fixture or a local-only clone is not stale.
        out['status'] = 'no-remote'
        return out
    rc, branch, _ = _run_git(repo_dir, 'rev-parse', '--abbrev-ref', 'HEAD')
    if rc != 0 or not branch or branch == 'HEAD':
        out['status'] = 'detached'
        out['remedy'] = 'git checkout <branch>  # HEAD is detached, so there is no upstream to compare against'
        return out
    out['branch'] = branch
    if fetch:
        # Bounded: --unshallow is blocked by some git policy hooks, and a
        # depth-limited fetch works on a shallow and a full clone alike.
        rc, _, err = _run_git(repo_dir, 'fetch', '--depth=500', 'origin', branch)
        if rc != 0:
            rc, _, err = _run_git(repo_dir, 'fetch', 'origin', branch)
        if rc != 0:
            # A failed fetch has two completely different causes with two
            # completely different remedies, and reporting the wrong one
            # sends the reader to debug a network that is fine. ls-remote
            # asks the server directly and ignores local refs entirely
            # (AGENTS.md's add_repo entry), so it separates them: if the
            # server answers and simply has no such branch, the branch was
            # never pushed.
            rc2, heads, _ = _run_git(repo_dir, 'ls-remote', '--heads', 'origin')
            if rc2 == 0:
                if f'refs/heads/{branch}' in heads:
                    out['status'] = 'no-upstream'
                    out['remedy'] = (
                        f"git -C {repo_dir} config --add remote.origin.fetch "
                        f"'+refs/heads/*:refs/remotes/origin/*'; "
                        f"git -C {repo_dir} fetch --depth=50 origin {branch}   "
                        f"# origin has {branch}; this clone's refspec does not "
                        f"fetch it")
                else:
                    out['status'] = 'branch-not-on-origin'
                    out['remedy'] = (
                        f'git -C {repo_dir} push -u origin {branch}   '
                        f'# or switch this source to its integration branch. '
                        f'origin has no {branch}: the network is fine, the '
                        f'branch is local-only, so nothing can say whether '
                        f'its content is current')
                return out
            out['status'] = 'fetch-failed'
            out['remedy'] = (f'git -C {repo_dir} fetch origin {branch}   '
                             f'# failed: {err.splitlines()[-1] if err else "no detail"}')
            return out
    # rev-parse --verify --quiet, never bare rev-parse: the bare form prints
    # the ref NAME it was asked for and exits non-zero, so a caller that
    # reads stdout binds a branch name where a hash belongs (AGENTS.md).
    rc, _, _ = _run_git(repo_dir, 'rev-parse', '--verify', '--quiet',
                        f'origin/{branch}')
    if rc != 0:
        out['status'] = 'no-upstream'
        out['remedy'] = (
            f"git -C {repo_dir} config --unset-all remote.origin.fetch; "
            f"git -C {repo_dir} config --add remote.origin.fetch "
            f"'+refs/heads/*:refs/remotes/origin/*'; "
            f"git -C {repo_dir} fetch --depth=50 origin {branch}   "
            f"# single-branch clone: origin/{branch} was never fetched")
        return out
    rc, counts, _ = _run_git(repo_dir, 'rev-list', '--left-right', '--count',
                             f'HEAD...origin/{branch}')
    if rc != 0 or len(counts.split()) != 2:
        # Do NOT report this as a rewritten branch. On a shallow clone the
        # real common ancestor can simply be outside the fetched depth, and
        # that false negative reads exactly like a force-push (AGENTS.md).
        out['status'] = 'no-shared-history'
        out['remedy'] = (f'git -C {repo_dir} fetch --depth=5000 origin {branch}   '
                         f'# cannot compare: either a shallow clone too shallow '
                         f'to reach the common ancestor, or a genuinely '
                         f'rewritten branch -- deepen first, then look')
        return out
    ahead, behind = (int(n) for n in counts.split())
    out['ahead'], out['behind'] = ahead, behind
    if behind and ahead:
        out['status'] = 'diverged'
        out['remedy'] = (f'git -C {repo_dir} merge origin/{branch}   '
                         f'# {ahead} local commit(s) here are NOT on origin -- '
                         f'never `checkout -B` or `reset --hard`, that discards them')
    elif behind:
        out['status'] = 'behind'
        out['remedy'] = (f'git -C {repo_dir} merge --ff-only origin/{branch}   '
                         f'# or re-run with --freshen')
    elif ahead:
        out['status'] = 'ahead'
    else:
        out['status'] = 'current'
    return out


def freshen(repo_dir, verdict):
    """Fast-forward one repo, ONLY when strictly behind on a clean tree.
    -> a fresh verdict. Refuses silently in every other state: a diverged
    branch fast-forwarded is someone's work deleted, and a dirty tree left
    half-merged is worse than a stale one left alone."""
    if verdict['status'] != 'behind':
        return verdict
    rc, dirty, _ = _run_git(repo_dir, 'status', '--porcelain')
    if rc != 0 or dirty:
        verdict = dict(verdict)
        verdict['remedy'] = (f'git -C {repo_dir} stash   # --freshen declined: '
                             f'the working tree is dirty, and a half-applied '
                             f'fast-forward is worse than a stale tree')
        return verdict
    rc, _, err = _run_git(repo_dir, 'merge', '--ff-only',
                          f"origin/{verdict['branch']}")
    if rc != 0:
        verdict = dict(verdict)
        verdict['remedy'] = f'--freshen failed: {err or "no detail"}'
        return verdict
    # verify-postcondition: re-read the state we wanted, rather than
    # trusting that the command reported success.
    return freshness(repo_dir, fetch=False)


def report_freshness(label, verdict, out=sys.stdout):
    """-> True if this repo is clean enough to read."""
    s = verdict['status']
    if s == 'not-a-checkout':
        return True
    if s in FRESHNESS_CLEAN:
        note = {'current': 'up to date with origin',
                'ahead': f"{verdict['ahead']} unpushed commit(s), nothing missing",
                'no-remote': 'no origin remote -- nothing to be behind'}[s]
        print(f"  OK: {label} ({verdict['branch'] or '-'}): {note}", file=out)
        return True
    detail = {'behind': f"{verdict['behind']} commit(s) BEHIND origin",
              'diverged': f"DIVERGED: {verdict['behind']} behind, "
                          f"{verdict['ahead']} ahead",
              'no-upstream': 'no origin/<branch> ref -- freshness unprovable',
              'fetch-failed': 'could not reach origin -- freshness unprovable',
              'branch-not-on-origin': 'this branch exists only locally -- '
                                      'freshness unprovable',
              'no-shared-history': 'cannot compare against origin',
              'detached': 'HEAD is detached'}[s]
    print(f"  STALE: {label} ({verdict['branch'] or '-'}): {detail}", file=out)
    print(f"     -> {verdict['remedy']}", file=out)
    return False


def _declared_base_branch(repo_dir):
    """The branch a repo DECLARES its work is measured against, in its own
    precedent.json `base_branch` -- not inferred from `origin/HEAD`.

    Those are two different questions with usually the same answer, which is
    why asking the wrong one survives so long. `origin/HEAD` answers "what
    does GitHub show first"; callers here mean "what lineage does this work
    belong to". They diverge the moment a repo pins its work to a branch
    that is not the configured default -- this repo's own
    `precedent-beta-v01` -- and then every inference is quietly wrong with
    nothing failing. Returns None when undeclared or unreadable, so callers
    fall back to the old inference rather than breaking (fail-gracefully).
    Enforced by precedent_check.py's `declared-base-branch`.
    """
    try:
        import json as _json, pathlib as _pathlib
        v = _json.loads((_pathlib.Path(repo_dir) / 'precedent.json')
                        .read_text(encoding='utf-8')).get('base_branch')
        return v if isinstance(v, str) and v.strip() else None
    except Exception:
        return None

def _default_remote_branch(repo_dir):
    """-> the short branch name origin/HEAD points at ('main', typically),
    or None if it can't be determined. `refs/remotes/origin/HEAD` is not set
    on every clone this tool will see -- reproduced directly on this repo's
    own sibling checkouts of precedent-team-maintainers and
    precedent-individual, both attached (not `git clone`d normally) without
    it, where `git symbolic-ref --short refs/remotes/origin/HEAD` just fails
    rather than degrading -- so fall back to checking for a same-named
    remote-tracking branch among the common default names before giving up."""
    rc, out, _ = _run_git(repo_dir, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD')
    if rc == 0 and '/' in out:
        return out.split('/', 1)[1]
    for candidate in ('main', 'master'):
        rc, _, _ = _run_git(repo_dir, 'rev-parse', '--verify', '--quiet', f'origin/{candidate}')
        if rc == 0:
            return candidate
    return None


def _unmerged_row(repo_dir, name, ref, target_ref, target):
    """-> the evidence a session needs to say MERGE or CLOSE about one
    branch that is not an ancestor of the integration branch.

    The ancestor test alone answers "can this be deleted safely", and
    answers nothing about the opposite risk: a branch whose work was meant
    to land and never did. Those need different evidence, so it is gathered
    here rather than left to the session to go and run by hand -- which, in
    practice, means per branch it does not run at all.

    `git cherry` is the load-bearing part. `merge-base --is-ancestor` reads
    commit identity, so a branch that was rebased or squash-merged onto the
    target reports as unmerged forever even though every line of it landed.
    `git cherry` compares patch-ids instead: a branch whose commits all show
    `-` is content-identical to work already on the target, which is a
    deletion candidate the ancestor test structurally cannot see. Only a `+`
    commit is genuinely unlanded work."""
    row = {'name': name, 'ahead': None, 'unique': None, 'last': None,
           'verdict': None}
    rc, out, _ = _run_git(repo_dir, 'rev-list', '--count', f'{target_ref}..{ref}')
    if rc == 0 and out.isdigit():
        row['ahead'] = int(out)
    rc, out, _ = _run_git(repo_dir, 'log', '-1', '--format=%cs', ref)
    if rc == 0 and out:
        row['last'] = out
    rc, out, _ = _run_git(repo_dir, 'cherry', target_ref, ref)
    if rc == 0:
        row['unique'] = sum(1 for ln in out.splitlines() if ln.startswith('+'))
    if row['unique'] is None:
        # Never guess here. On a shallow clone the patch comparison simply
        # cannot run, and a fabricated verdict is worse than none: this is
        # the branch someone might delete on it.
        row['verdict'] = (f'UNKNOWN -- patch comparison could not run here '
                          f'(shallow clone?). Deepen with `git fetch '
                          f'--depth=5000` and re-check before acting')
    elif row['unique'] == 0:
        row['verdict'] = (f'ALREADY LANDED as patches -- every commit has an '
                          f'equivalent on {target} (rebased or squash-merged '
                          f'in), so there is nothing to merge. Deletion '
                          f'candidate that the ancestor test cannot see')
    else:
        row['verdict'] = (f'CARRIES {row["unique"]} unlanded commit(s) -- '
                          f'decide, do not skip: merge it, or close it with '
                          f'the reason recorded')
    return row


def _fetch_all_heads(repo_dir):
    """-> (missing_heads, note). Widen a single-branch clone's refspec and
    fetch every head, then report which heads origin has that this clone
    still does not.

    The branch scan reads `refs/remotes/origin`, which holds only what was
    actually fetched. The harness clones single-branch (AGENTS.md's add_repo
    entry), and the freshness gate above fetches ONE branch, so without this
    the scan enumerates two or three refs on a repo that has forty -- and
    reports "(none)", which reads as "clean" rather than "could not check".
    That is the same empty-result-reads-as-pass failure AGENTS.md records for
    the `scope: 'tree'` checks, and it is worse here: the branch sweep is the
    whole of pass 4's branch bullet, so a false all-clear ends the only step
    that would have found unlanded work.
    """
    rc, fetchspecs, _ = _run_git(repo_dir, 'config', '--get-all',
                                 'remote.origin.fetch')
    if rc == 0 and 'refs/heads/*' not in fetchspecs:
        # Local config only, idempotent -- the same repair AGENTS.md
        # describes and templates/bootstrap.sh applies at session start.
        _run_git(repo_dir, 'config', '--add', 'remote.origin.fetch',
                 '+refs/heads/*:refs/remotes/origin/*')
    # Bounded: --unshallow is blocked by some git policy hooks, and a
    # depth-limited fetch works on a shallow and a full clone alike.
    rc, _, _ = _run_git(repo_dir, 'fetch', '--depth=50', 'origin')
    if rc != 0:
        _run_git(repo_dir, 'fetch', 'origin')
    # ls-remote asks the SERVER and ignores local refs entirely, so it is the
    # only thing that can say what this clone is still missing.
    rc, heads, _ = _run_git(repo_dir, 'ls-remote', '--heads', 'origin')
    if rc != 0:
        return None, ('could not reach origin to list its branches, so this '
                      'scan sees only what was already fetched')
    server = set()
    for line in heads.splitlines():
        parts = line.split('refs/heads/', 1)
        if len(parts) == 2:
            server.add(parts[1].strip())
    rc, local, _ = _run_git(repo_dir, 'for-each-ref',
                            '--format=%(refname:short)', 'refs/remotes/origin')
    have = {r.split('/', 1)[1] for r in local.splitlines() if '/' in r}
    missing = sorted(server - have - {'HEAD'})
    return missing, None


def scan_branches(repo_dir, target=None, exclude=()):
    """-> None if repo_dir isn't its own git checkout (a repo-local source
    living inside the parent checkout shares the parent's branches and has
    none of its own to scan) or its integration branch can't be resolved.
    Otherwise {'target': str, 'merged': [...], 'unmerged': [...]}: 'merged'
    branches are mechanically PROVEN safe to delete (every commit on them is
    already an ancestor of target); 'unmerged' is everything else remaining
    (default branch and target itself excluded) -- some of those may still
    be safe (closed because a later PR superseded them) but that call needs
    the branch's PR history, which this offline check cannot see. See
    practices/very-deep-check.md's Install section.

    `exclude` names branches never to report either way regardless of merge
    status -- the branch the invoking session is itself working on, which
    can be trivially "merged" (an ancestor of target) simply because no
    commits have landed on it yet, long before it is actually done."""
    repo_dir = pathlib.Path(repo_dir)
    if not (repo_dir / '.git').is_dir():
        return None
    default_branch = _default_remote_branch(repo_dir)
    # The DECLARED base branch wins over the inferred default: a repo whose
    # work is pinned away from its default (this repo, while
    # precedent-beta-v01 is unmerged) would otherwise have every branch
    # measured against a lineage its work never touched.
    declared = _declared_base_branch(repo_dir)
    target = target or declared or default_branch
    if not target:
        return None
    # A repo whose integration branch isn't its default (this repo's own
    # precedent-beta-v01, per AGENTS.md) still has that default branch
    # (main) sitting around -- never report it as a deletion candidate just
    # because it happens not to be an ancestor of the *other* protected
    # branch.
    protected = {target, default_branch, declared} - {None}
    # Populate refs/remotes/origin BEFORE enumerating it -- otherwise this
    # scan silently reports only what a single-branch clone happened to
    # fetch (practice: very-deep-check).
    missing_heads, reach_note = _fetch_all_heads(repo_dir)
    target_ref = f'origin/{target}'
    rc, _, _ = _run_git(repo_dir, 'rev-parse', '--verify', '--quiet', target_ref)
    if rc != 0:
        return None
    rc, out, _ = _run_git(repo_dir, 'for-each-ref', '--format=%(refname:short)',
                           'refs/remotes/origin')
    if rc != 0:
        return None
    merged, unmerged = [], []
    for ref in out.splitlines():
        if '/' not in ref:
            continue
        name = ref.split('/', 1)[1]
        if name == 'HEAD' or name in protected or name in exclude:
            continue
        rc, _, _ = _run_git(repo_dir, 'merge-base', '--is-ancestor', ref, target_ref)
        if rc == 0:
            merged.append(name)
        else:
            unmerged.append(_unmerged_row(repo_dir, name, ref, target_ref, target))
    return {'target': target, 'merged': sorted(merged),
            'unmerged': sorted(unmerged, key=lambda r: r['name']),
            'unfetched': missing_heads or [], 'unreachable': reach_note,
            'path': str(repo_dir)}


def enumerate_scope(repo=None, user_config=None):
    """-> {'checkout': {...}, 'sources': [...], 'missing': [...]}"""
    repo_root = pathlib.Path(repo or ROOT).resolve()
    sources = pr.load_config(str(repo_root), user_config)

    def _docs_and_practice_count(base):
        base = pathlib.Path(base)
        docs = [d for d in CANDIDATE_DOCS if (base / d).is_file()]
        practices_dir = base / 'practices'
        n_practices = len(list(practices_dir.glob('*.md'))) if practices_dir.is_dir() else 0
        return docs, n_practices

    checkout_docs, checkout_practices = _docs_and_practice_count(repo_root)
    checkout = {'path': str(repo_root), 'docs': checkout_docs,
                'practice_count': checkout_practices}

    missing = []
    source_rows = []
    for s in sources:
        docs, n_practices = _docs_and_practice_count(s['path'])
        if not docs and n_practices == 0:
            missing.append({'level': s['level'], 'name': s['name'],
                            'reason': f"{s['path']} has neither a "
                                       f"recognized top-level document nor "
                                       f"a practices/ directory -- source "
                                       f"unreachable or empty"})
            continue
        source_rows.append({'level': s['level'], 'name': s['name'],
                            'path': s['path'], 'docs': docs,
                            'practice_count': n_practices})

    return {'checkout': checkout, 'sources': source_rows, 'missing': missing}


def _exit(message):
    print(message, file=sys.stderr)
    return 1


def main():
    args = sys.argv[1:]
    repo, user_config, checkout_target = None, None, None
    for flag, dest in (('--repo', 'repo'), ('--user-config', 'user_config'),
                       ('--target', 'checkout_target')):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(f"very deep check FAIL: {flag} needs a value.")
            value = args[i + 1]
            args = args[:i] + args[i + 2:]
            if dest == 'repo':
                repo = value
            elif dest == 'user_config':
                user_config = value
            else:
                checkout_target = value
    as_json = '--json' in args
    allow_missing = '--allow-missing-sources' in args
    skip_branch_scan = '--skip-branch-scan' in args
    allow_stale = '--allow-stale' in args
    do_freshen = '--freshen' in args

    # FIRST, before the parse check and before enumerate_scope. Both of
    # those read files, and a file read out of a stale checkout is not
    # evidence about anything -- so proving the tree current has to precede
    # the first read, not follow it.
    repo_root = pathlib.Path(repo or ROOT).resolve()
    _fresh = {}
    _v = freshness(repo_root)
    if do_freshen:
        _v = freshen(repo_root, _v)
    _fresh['checkout'] = _v
    if not as_json:
        print("FRESHNESS -- every repo in force, before anything is read\n")
        report_freshness(f'this checkout ({repo_root})', _v)
    if _v['status'] not in FRESHNESS_CLEAN and not allow_stale:
        sys.exit(f"\nvery deep check FAIL: this checkout is not provably "
                 f"current ({_v['status']}). Everything below would be "
                 f"judgment about a tree that is not the one on origin -- "
                 f"current work reads as missing and fixed bugs read as "
                 f"open. Run the remedy above (or --freshen, for a clean "
                 f"tree that is merely behind) and start again. "
                 f"--allow-stale exists only for a deliberately offline "
                 f"run, and makes every finding provisional.")

    # BEFORE enumerate_scope, deliberately. Enumerating reads
    # precedent.json, so a malformed one used to kill this tool with a raw
    # traceback out of precedent_resolve -- and the diagnosis it needed to
    # print ("precedent.json is not valid JSON") was in the sweep it never
    # reached. The most useful finding must not be downstream of the thing
    # it explains.
    #
    # Whole tree, because that is this check's whole point: the deep check
    # already covers files a change TOUCHED, and a file nobody has touched
    # in months is exactly what only this sweep will ever look at again.
    _root = pathlib.Path(repo or ROOT).resolve()
    _paths = pcheck.tracked(_root)
    _failures, _parsed, _skipped = pcheck.validate(_root, _paths)
    if not as_json:
        print("MACHINE-READABLE FILES -- every tracked JSON and YAML file, "
              "parsed\n")
        for _rel, _why in _failures:
            print(f"  FAIL: {_rel}: {_why}")
        if _skipped:
            print(f"  SKIPPED {', '.join(_skipped)}: no parser installed here "
                  f"(pip install pyyaml). A file nobody parsed is not a file "
                  f"that parses.")
        if not _failures:
            print(f"  OK: {len(pcheck.candidates(_root, _paths))} file(s) parse "
                  f"({', '.join(_parsed) or 'none tracked'}).")
        print()
    if _failures:
        sys.exit(f"very deep check FAIL: {len(_failures)} tracked file(s) do "
                 f"not parse. Fix those first -- this tool reads "
                 f"precedent.json to enumerate its own scope, so it cannot "
                 f"report anything else while one of them is malformed.")

    data = enumerate_scope(repo, user_config)

    fatal_missing = [m for m in data['missing'] if m['level'] in FATAL_MISSING_LEVELS]
    other_missing = [m for m in data['missing'] if m not in fatal_missing]
    for m in other_missing:
        print(f"very deep check: the {m['level']} source {m['name']!r} "
             f"is not available ({m['reason']}) -- running WITHOUT it.",
             file=sys.stderr)
    if fatal_missing and not allow_missing:
        for m in fatal_missing:
            print(f"very deep check FAIL: the {m['level']} source {m['name']!r} "
                 f"is declared but not present in this session "
                 f"({m['reason']}). A very deep check that silently runs "
                 f"without a declared team or individual source defeats the "
                 f"reason it was asked for -- attach or clone it into this "
                 f"session (this harness's own repo-attachment mechanism, "
                 f"or a plain `git clone` of the source's repo) and re-run. "
                 f"Pass --allow-missing-sources only if proceeding without "
                 f"it is actually intended.", file=sys.stderr)
        return 1

    # Now the sources -- which needs enumerate_scope, because precedent.json
    # is what names them, and could not have run before the checkout's own
    # gate above. A sibling source is the likelier offender of the two: the
    # session-start freshness guard fires for the session's primary repo
    # only, so an attached source has never been checked by anything.
    _stale_sources = []
    if not as_json:
        print("FRESHNESS -- declared sources (below the parse, because "
              "precedent.json\nis what names them)\n")
    for s in data['sources']:
        if s['level'] not in FATAL_MISSING_LEVELS:
            continue
        v = freshness(s['path'])
        if do_freshen:
            v = freshen(s['path'], v)
        _fresh[s['name']] = v
        ok = True
        if not as_json:
            ok = report_freshness(f"{s['level']} source {s['name']!r} "
                                  f"({s['path']})", v)
        elif v['status'] not in FRESHNESS_CLEAN:
            ok = False
        if not ok:
            _stale_sources.append(s['name'])
    if not as_json:
        print()
    if _stale_sources and not allow_stale:
        return _exit(f"very deep check FAIL: {len(_stale_sources)} source(s) "
                     f"not provably current ({', '.join(_stale_sources)}). "
                     f"The check reads these repos against this one, so a "
                     f"stale source produces cross-source findings that are "
                     f"pure artifact -- a convention 'not rolled out' that "
                     f"was rolled out last week. Run each remedy above, or "
                     f"--freshen, and start again.")

    branch_scans = {}
    if not skip_branch_scan:
        _, checkout_branch, _ = _run_git(repo_root, 'rev-parse', '--abbrev-ref', 'HEAD')
        branch_scans['checkout'] = scan_branches(
            repo_root, checkout_target, exclude=(checkout_branch,) if checkout_branch else ())
        for s in data['sources']:
            if s['level'] in FATAL_MISSING_LEVELS:
                _, src_branch, _ = _run_git(s['path'], 'rev-parse', '--abbrev-ref', 'HEAD')
                branch_scans[s['name']] = scan_branches(
                    s['path'], exclude=(src_branch,) if src_branch else ())

    if as_json:
        data['branches'] = branch_scans
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    c = data['checkout']
    print(f"very deep check -- scope to read (not enforcement, judgment):\n")
    print(f"this checkout ({c['path']}):")
    print(f"  documents: {', '.join(c['docs']) if c['docs'] else '(none of the recognized names present)'}")
    print(f"  practices/: {c['practice_count']} file(s)\n")

    for s in data['sources']:
        print(f"{s['level']} source {s['name']!r} ({s['path']}):")
        print(f"  documents: {', '.join(s['docs']) if s['docs'] else '(none of the recognized names present)'}")
        print(f"  practices/: {s['practice_count']} file(s)\n")

    # Source shape. bootstrap only ever ran for sources it CREATED; a
    # source migrated into place from an older system never passed through
    # it, and nothing afterwards asked whether it came out the right shape.
    print("SOURCE SHAPE -- files each level's skeleton ships\n")
    _shape_any = False
    for _s in data['sources']:
        _lvl, _path = _s.get('level'), _s.get('path')
        if _lvl not in ('team', 'individual') or not _path:
            continue
        _shape_any = True
        _missing = bootstrap_source.verify(_lvl, _path)
        if _missing:
            # Each entry names its own origin where that is not the
            # skeleton -- the session hooks and settings.json come from the
            # harness adapter, and telling a reader to fetch them from a
            # skeleton that has never contained them sends them nowhere.
            print(f"  {_s['name']} ({_lvl}): missing:")
            for _m in _missing:
                _src = ('' if '(' in _m
                        else f" -- present in templates/practice-set-{_lvl}/")
                print(f"      {_m}{_src}")
        else:
            print(f"  {_s['name']} ({_lvl}): complete")
    if not _shape_any:
        print("  (no team or individual source resolved here)")
    print()

    print(checklist())

    if not skip_branch_scan:
        print("\nBRANCHES -- both directions. A merged branch nobody deleted is\n"
              "clutter; an unmerged branch nobody decided about is lost work, and\n"
              "the second costs more. Every branch below needs a verdict -- see\n"
              "practices/very-deep-check.md:\n")
        for name, scan in branch_scans.items():
            if scan is None:
                print(f"{name}: not its own git checkout, or integration "
                      f"branch could not be resolved -- skipped.\n")
                continue
            print(f"{name} (integration branch: {scan['target']}):")
            # "(none)" is only honest when the scan could actually SEE every
            # branch origin has. An under-fetched clone would otherwise report
            # a clean sweep it never performed (practice: very-deep-check).
            incomplete = scan.get('unreachable') or scan.get('unfetched')
            empty = ('(none)' if not incomplete
                     else '(CANNOT TELL -- see the incomplete-scan note below)')
            print(f"  merged, not deleted -- confirm authorship and the PR "
                  f"link, then delete:")
            if scan['merged']:
                for b in scan['merged']:
                    print(f"    {b}")
            else:
                print(f"    {empty}")
            print(f"  NOT merged -- merge it or close it, one verdict each:")
            if scan['unmerged']:
                for r in scan['unmerged']:
                    age = f", last commit {r['last']}" if r['last'] else ""
                    print(f"    {r['name']} ({r['ahead']} commit(s) ahead"
                          f"{age})")
                    print(f"      {r['verdict']}")
            else:
                print(f"    {empty}")
            if scan.get('unreachable'):
                print(f"  INCOMPLETE SCAN: {scan['unreachable']}. Treat both "
                      f"lists above as partial, not as clean.")
            elif scan.get('unfetched'):
                n = len(scan['unfetched'])
                shown = ', '.join(scan['unfetched'][:5])
                more = f" (+{n - 5} more)" if n > 5 else ""
                print(f"  INCOMPLETE SCAN: {n} branch(es) on origin were "
                      f"never fetched into this clone and so were NOT "
                      f"judged: {shown}{more}. Treat both lists above as "
                      f"partial, not as clean.")
                print(f"    -> git -C {scan.get('path', '<repo>')} fetch "
                      f"--depth=50 origin   # then re-run")
            print()

    return 0


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/HOW_TO_USE_THIS_TECHNICAL.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
