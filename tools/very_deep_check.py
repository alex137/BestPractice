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

Rehearses the ENDGAME MERGE, too (practice: very-deep-check, pass 4): the
integration branch merged into its base in a throwaway worktree, reporting
conflicting paths and silently-dropped paths as two separate sets. The
second set is the one that matters and the one nothing else here would ever
show -- a path that does not arrive raises no conflict and prints no line.
History surgery on the base branch (a reverted merge, a cherry-pick, a
force-push) is what fills it. `--skip-endgame-merge` skips it; `--json`
gives the full list.

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
import json, os, pathlib, re, subprocess, sys

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
import build_views as bv  # noqa: E402

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


# --- the endgame merge, rehearsed (practice: very-deep-check, pass 4) ----
# A repo pinned to an integration branch is aimed at one merge it has never
# performed, that gets one attempt, usually under time pressure and usually
# by whoever approves it rather than whoever built it. This rehearses it and
# reports the two outcomes SEPARATELY, because they have opposite
# visibilities: a conflict stops the merge and will be dealt with, while a
# path that simply does not arrive produces no conflict, no message and no
# line of output at all.
#
# THE INCIDENT (2026-09-07). `main` here merged this branch by accident and
# reverted it. The revert undid the files and left the commits in main's
# log, so git treats that work as already merged and then honours the
# deletion: a straight merge back would raise 125 conflicts and drop 507
# files in silence. A rehearsal the same day checked two files, found both
# present, and recorded that the trap did not fire -- both were files that
# session had just edited, which is precisely the class that survives.
# Hence a whole-tree set difference here rather than a sample
# (practice: very-deep-check, pass 2, "does a verification enumerate, or
# does it sample?").
def endgame_merge(repo_dir, target=None, base=None, keep=False):
    """-> None when no endgame merge is pending (no declared integration
    branch, or it IS the default branch), else a dict:

        {'target', 'base', 'status', 'conflicts': [...], 'dropped': [...],
         'shallow': bool, 'note': str|None}

    status: findings | clean | cannot-tell | error. `dropped` is the set
    that matters -- paths present on the integration branch and absent from
    the merge result, with no conflict raised about them.

    Never mutates the caller's working tree: the merge happens in a
    throwaway worktree checked out detached, nothing is committed, and the
    worktree is removed on every exit path. (A tool that checks out inside
    a clone handed to it is its own entry in AGENTS.md's gotchas.)"""
    import tempfile, shutil
    repo_dir = pathlib.Path(repo_dir)
    if not (repo_dir / '.git').exists():
        return None
    target = target or _declared_base_branch(repo_dir)
    base = base or _default_remote_branch(repo_dir)
    if not target or not base or target == base:
        return None
    out = {'target': target, 'base': base, 'status': 'cannot-tell',
           'conflicts': [], 'dropped': [], 'shallow': False, 'note': None}
    # --verify --quiet, never the bare form: `git rev-parse <missing-ref>`
    # exits non-zero but PRINTS the ref name, so the plain call hands a ref
    # name to anything expecting a hash (AGENTS.md, gotchas).
    for ref in (f'origin/{base}', f'origin/{target}'):
        rc, _, _ = _run_git(repo_dir, 'rev-parse', '--verify', '--quiet', ref)
        if rc != 0:
            out['note'] = (f'{ref} does not exist in this clone -- fetch it '
                           f'(`git fetch origin {ref.split("/", 1)[1]}`) and '
                           f're-run.')
            return out
    rc, _, _ = _run_git(repo_dir, 'merge-base', f'origin/{base}', f'origin/{target}')
    if rc != 0:
        out['note'] = ('the two branches have no common ancestor in this '
                       'clone. On a shallow clone that is usually the fetch '
                       'depth, not the history: `git fetch --unshallow origin` '
                       '(or a deep bounded fetch) and re-run. Reported as '
                       'CANNOT TELL rather than clean -- an under-fetched '
                       'history yields an empty difference that reads exactly '
                       'like a good result.')
        return out
    rc, shallow, _ = _run_git(repo_dir, 'rev-parse', '--is-shallow-repository')
    out['shallow'] = (rc == 0 and shallow.strip() == 'true')

    rc, expected, _ = _run_git(repo_dir, 'ls-tree', '-r', '--name-only',
                               f'origin/{target}')
    if rc != 0:
        out['note'] = f'could not list origin/{target}: {expected}'
        out['status'] = 'error'
        return out
    expected = {ln for ln in expected.splitlines() if ln}

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='vdc-endgame-'))
    work = tmp / 'merge'
    try:
        rc, _, err = _run_git(repo_dir, 'worktree', 'add', '--detach',
                              str(work), f'origin/{base}')
        if rc != 0:
            out['status'] = 'error'
            out['note'] = f'could not create a throwaway worktree: {err}'
            return out
        # Conflicts are the expected outcome, so the return code says
        # nothing here -- what the merge DID is read out of the index.
        # No identity is set for this: `--no-commit` never writes a
        # commit, so git never asks for one -- and an address literal here
        # is a leak-gate finding in a public tree (caught by that gate the
        # first time this ran).
        _run_git(work, 'merge', '--no-commit', '--no-ff', f'origin/{target}')
        rc, conflicted, _ = _run_git(work, 'diff', '--name-only',
                                     '--diff-filter=U')
        conflicts = {ln for ln in conflicted.splitlines() if ln} if rc == 0 else set()
        rc, staged, _ = _run_git(work, 'ls-files', '--stage')
        present = set(conflicts)
        if rc == 0:
            for line in staged.splitlines():
                meta, _, path = line.partition('\t')
                if path and meta.split()[-1] == '0':
                    present.add(path)
        out['conflicts'] = sorted(conflicts)
        out['dropped'] = sorted(expected - present)
        out['status'] = 'findings' if out['dropped'] else 'clean'
        return out
    finally:
        _run_git(work, 'merge', '--abort')
        if not keep:
            _run_git(repo_dir, 'worktree', 'remove', '--force', str(work))
            _run_git(repo_dir, 'worktree', 'prune')
            shutil.rmtree(tmp, ignore_errors=True)


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


# --------------------------------------------------------------------------
# Repository-visibility audit: the one check that needs the outside world
# --------------------------------------------------------------------------
#
# The leak gate's vocabulary layer is a hand-written list of literal strings.
# It cannot know a repository is private -- it only knows what somebody typed
# into it -- so it fails in BOTH directions, and did, twice on 2026-09-07:
#
#   MISSED. The philosophy import named four repositories. The gate caught
#   one of them and missed another, both private, both named from this public
#   tree, for the only reason a blocklist ever misses anything: it had never
#   been told about the second. Nothing offline could have found that.
#   (Neither is named here. This comment block named one of them in its first
#   draft, and THIS AUDIT caught it on its own first run -- the check's own
#   rationale leaking the name the check exists to protect.)
#
#   STALE. `COMPANY_BUILDING_RULES` and `HUMAN_VOICE_RULES` were blocked while
#   naming files that are public, forcing 88 hits clearable only by deleting
#   content about public files -- so the entries came off, and the note left
#   behind said: "Re-check visibility before removing any other repo-name
#   pattern here -- the check is one API call and it is the whole argument."
#   That instruction had no mechanism. Hours later the same day a repository
#   went private and the tree named it 58 times.
#
# This makes that instruction a check. It runs here rather than in the leak
# gate on purpose: the gate is a PUSH gate and must work offline and in CI,
# where a network call would either fail the push or fail open. very-deep-check
# is invoked by a person, on request, and can afford the network.
#
# SCOPE IS WHAT THIS TREE NAMES, not what the account owns. Enumerating an
# account's private repositories is unavailable here anyway -- `/user/repos`
# answers "sessions are bound to their configured repositories" -- but the
# narrower scope is the better one regardless: a private repository this tree
# never mentions is not a leak, and a mention is exactly what makes one.
#
# NEVER WRITES A PRIVATE NAME ANYWHERE. Findings go to the session's own
# output. Writing them into a report in this tree would publish the names the
# audit exists to protect, which is the failure it is looking for.

# A GitHub owner login: letters, digits and single hyphens, <=39 chars.
_OWNER = r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})'
# Only a github.com URL proves an `owner/name` IS a repository reference.
# Those URLs are then what tells us which owners to look for in bare prose.
_URL_REF_RE = re.compile(r'github\.com/(' + _OWNER + r')/([A-Za-z][\w.-]*?)'
                         r'(?=[\s)\]"\'`,;:]|\.git\b|/|$)')

# A first attempt matched any `x/y` and produced 389 candidates from this
# tree -- fractions, ratios, CSS line-heights, "10/10", "287/290". Anchoring
# to owners actually seen in a github.com URL is what makes the bare-prose
# half safe: an `owner/name` under a known owner is a repository reference,
# `16px/1.45` is not, and no cleverness about the right-hand side tells them
# apart.
def _bare_ref_re(owners):
    if not owners:
        return None
    alt = '|'.join(re.escape(o) for o in sorted(owners))
    return re.compile(r'(?<![\w./-])(' + alt + r')/([A-Za-z][\w.-]*?)'
                      r'(?=[\s)\]"\'`,;:]|\.git\b|/|$)')


_NOT_A_REPO_NAME = re.compile(
    r'.*\.(?:md|py|json|txt|sh|yml|yaml|html|template|jsonl)$', re.I)


def _api_json(path, timeout=20):
    """-> (parsed, error). Never raises: the caller reports, it does not crash."""
    try:
        r = subprocess.run(
            ['curl', '-s', '--max-time', str(timeout),
             '-H', 'Accept: application/vnd.github+json',
             f'https://api.github.com/{path.lstrip("/")}'],
            capture_output=True, text=True, timeout=timeout + 10)
    except Exception as e:                      # noqa: BLE001 -- reported
        return None, f'curl failed: {e}'
    if r.returncode != 0:
        return None, f'curl exited {r.returncode}: {r.stderr.strip()[:120]}'
    try:
        return json.loads(r.stdout), None
    except ValueError:
        return None, f'not JSON: {r.stdout.strip()[:120]}'


def _tracked_text_files(repo_dir):
    # _run_git returns (rc, stdout, stderr) -- the tuple, not the text. A
    # bare `out or ''` here read as a string and crashed on .splitlines().
    rc, out, _err = _run_git(repo_dir, 'ls-files')
    if rc != 0:
        return
    for rel in out.splitlines():
        if not rel.strip():
            continue
        if rel.startswith(('process/upstream/', '.git/')):
            continue      # vendored: another repo's tree, not this one's text
        p = pathlib.Path(repo_dir) / rel
        if p.suffix.lower() not in ('.md', '.py', '.json', '.txt', '.sh',
                                    '.yml', '.yaml', '.template'):
            continue
        try:
            yield rel, p.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue


def _referenced_repos(repo_dir):
    """-> {(owner, name): [files that mention it]} for this tree's own text.

    Two passes, and the first is what makes the second safe: only a
    `github.com/owner/name` URL PROVES an `owner/name` pair is a repository,
    so those URLs supply the owner names, and only those owners are then
    looked for in bare prose.
    """
    texts = list(_tracked_text_files(repo_dir))
    found, owners = {}, set()
    for rel, text in texts:
        for owner, name in _URL_REF_RE.findall(text):
            if _NOT_A_REPO_NAME.match(name):
                continue
            owners.add(owner)
            found.setdefault((owner, name), []).append(rel)
    bare = _bare_ref_re(owners)
    if bare:
        for rel, text in texts:
            for owner, name in bare.findall(text):
                if _NOT_A_REPO_NAME.match(name):
                    continue
                found.setdefault((owner, name), []).append(rel)
    return found


def repo_visibility_audit(repo_dir, blocklist_path=None, out=sys.stdout):
    """-> (findings, notes). Findings are real; notes are what could not run.

    A repository this PUBLIC tree names, which is PRIVATE, is a finding
    whether or not anybody blocklisted it -- that is the Write-Like case. A
    blocklist entry naming a repository that is now PUBLIC is the opposite
    finding: it costs false positives and pressure to delete real content.
    """
    findings, notes = [], []

    probe, err = _api_json('user')
    if err or not isinstance(probe, dict) or not probe.get('login'):
        notes.append(
            'the GitHub API could not be reached, so NO repository visibility '
            'was checked. This is not a clean result -- it is an unrun check '
            f'({err or "no login in response"}).')
        return findings, notes

    refs = _referenced_repos(repo_dir)
    # A repository whose name is DELIBERATELY public here -- named on purpose,
    # with the exposure accepted -- is declared in the blocklist file itself,
    # as a comment the audit reads:
    #
    #     # visibility-audit: allow owner/name -- why the exposure is accepted
    #
    # It lives there rather than in a new file because that file is already
    # the private, per-person place where "which names matter" is decided, and
    # a second file would be a second thing to keep in sync. A REASON is
    # required: an accepted exposure nobody argued for is the same silence the
    # blocklist exists to replace, and without one the audit keeps reporting.
    #
    # Needed because the alternative is a permanent nag. This account
    # deliberately names one private repository throughout its public tree --
    # the retired personal pack, whose name Morgan has said plainly he does
    # not mind being public -- and an audit that reports it on every run is an
    # audit people learn to skim.
    blocked, allowed = set(), {}
    if blocklist_path and pathlib.Path(blocklist_path).exists():
        try:
            for line in pathlib.Path(blocklist_path).read_text(
                    encoding='utf-8').splitlines():
                line = line.strip()
                m = re.match(r'#\s*visibility-audit:\s*allow\s+(\S+/\S+)\s*--\s*(.+)$',
                             line)
                if m:
                    allowed[m.group(1).lower()] = m.group(2).strip()
                    continue
                if line and not line.startswith('#'):
                    blocked.add(re.sub(r'^\\b|\\b$', '', line).lower())
        except OSError as e:
            notes.append(f'blocklist at {blocklist_path} could not be read ({e}) '
                         '-- the stale-entry half of this audit did NOT run.')
    else:
        notes.append('no blocklist path given, so the stale-entry half of this '
                     'audit did NOT run; only referenced repositories were '
                     'checked.')

    checked = 0
    for (owner, name), files in sorted(refs.items()):
        data, err = _api_json(f'repos/{owner}/{name}')
        if err:
            notes.append(f'{owner}/{name}: visibility not checked ({err})')
            continue
        if not isinstance(data, dict) or 'private' not in data:
            msg = (data or {}).get('message', 'no visibility in response')
            if 'Not Found' in str(msg):
                notes.append(
                    f'{owner}/{name}: the API reports Not Found -- deleted, '
                    f'renamed, or not visible to this session. Named in: '
                    f'{", ".join(sorted(set(files))[:3])}. A dead reference, '
                    f'not necessarily a leak.')
            else:
                notes.append(f'{owner}/{name}: visibility not checked ({msg})')
            continue
        checked += 1        # only now is the visibility actually KNOWN
        if data.get('private'):
            why = allowed.get(f'{owner}/{name}'.lower())
            if why:
                notes.append(f'{owner}/{name} is private and named here on '
                             f'purpose: {why}')
                continue
            findings.append(
                f'{owner}/{name} is PRIVATE and is named in this tree '
                f'({len(set(files))} file(s), e.g. '
                f'{", ".join(sorted(set(files))[:3])}). Either scrub the name '
                f'or, if it must appear, say why -- and add it to the leak '
                f'blocklist so the push gate catches the next one. Nothing '
                f'offline can find this: the gate blocks what it was told.')
        elif name.lower() in blocked:
            findings.append(
                f'{owner}/{name} is PUBLIC but its name is on the leak '
                f'blocklist. A stale entry costs real content: it forces hits '
                f'clearable only by deleting text about a public repository. '
                f'Re-check and remove the entry, recording the evidence.')

    # `checked` counts repositories whose visibility was actually
    # DETERMINED. It used to increment on any non-error API response,
    # including "access to this repository is not enabled for this session",
    # and so reported "14 of 14 checked" when 11 were unresolvable -- a check
    # overstating its own coverage, which is the shape this audit exists to
    # catch in the blocklist.
    unresolved = len(refs) - checked
    print(f'  repository visibility: {checked} of {len(refs)} referenced '
          f'repositories had their visibility determined'
          + (f'; {unresolved} could NOT be checked (this session only reaches '
             f'repositories attached to it) -- see the notes, they are not '
             f'passes' if unresolved else ''), file=out)
    return findings, notes


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
    skip_visibility = '--skip-visibility' in args
    skip_endgame = '--skip-endgame-merge' in args
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

    endgame = None if skip_endgame else endgame_merge(repo_root, checkout_target)

    if as_json:
        data['branches'] = branch_scans
        data['endgame_merge'] = endgame
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
    # CONFLICTING PRACTICES WITHIN ONE SOURCE (practice: very-deep-check,
    # pass 3). Requested by Morgan 2026-09-07, after two sessions landed the
    # same practice into both team sets on the same day.
    #
    # The CROSS-source half is already a hard refusal -- precedent_resolve
    # raises on two same-level sources defining one slug -- so this is the
    # within-source half, which nothing detected at all.
    #
    # DELIBERATELY NARROW, and the narrowness is the point. "Two rules that
    # contradict each other" is a reading task; a scanner that guessed at it
    # would flood. What IS decidable: two practices in one catalogue that
    # claim the SAME DEFINED TERM (GLOSSARY.md is built from `defines:`, so
    # a collision makes the glossary ambiguous and one entry silently win),
    # and a practice whose `overrides:` or `in_force_at:` names a sibling in
    # its OWN source (precedence orders LEVELS -- naming a same-source
    # sibling is either a no-op or a statement the resolver cannot honour).
    #
    # Measured against a shared `occasion:` first and rejected as a signal:
    # four universal practices share "writing or editing a document" and are
    # complementary, not conflicting. An occasion is a routing key, not a
    # claim of exclusivity.
    print("WITHIN-SOURCE CONFLICTS -- one catalogue disagreeing with itself\n")
    _conf_any = False
    for _src in [{'name': 'this checkout', 'path': str(repo_root)}] + [
            {'name': s['name'], 'path': s['path']} for s in data['sources']]:
        _pdir = pathlib.Path(_src['path']) / 'practices'
        if not _pdir.is_dir():
            continue
        _defs, _slugs, _fm_by = {}, set(), {}
        for _f in sorted(_pdir.glob('*.md')):
            try:
                _fm, _ = sp._read_practice_file(_f)
            except Exception:
                continue
            if (_fm.get('status') or '').strip('" ') != 'active':
                continue
            _slugs.add(_f.stem)
            _fm_by[_f.stem] = _fm
            # `defines:` is a RAW STRING holding a JSON list, not a list.
            # The first version of this scan iterated it directly and so
            # iterated its CHARACTERS -- reporting that 67 practices all
            # "define '['". Absurd output is what caught it; a subtler
            # field would not have. bv._json_list is what build_views uses
            # to build GLOSSARY.md from this same field, so the scan and
            # the glossary cannot disagree about what a term is.
            for _term in bv._json_list(_fm.get('defines', '[]')):
                _term = str(_term).strip().lower()
                if _term:
                    _defs.setdefault(_term, []).append(_f.stem)
        _found = []
        for _term, _owners in sorted(_defs.items()):
            if len(_owners) > 1:
                _found.append(f"two practices define {_term!r}: "
                              f"{', '.join(_owners)} -- GLOSSARY.md can only "
                              f"show one")
        for _slug, _fm in sorted(_fm_by.items()):
            for _field in ('overrides', 'in_force_at'):
                _v = (_fm.get(_field) or 'null')
                _v = str(_v).strip('" ').strip()
                if _v and _v != 'null' and _v in _slugs:
                    _found.append(f"{_slug}'s `{_field}:` names {_v}, a "
                                  f"practice active in this same source -- "
                                  f"precedence orders levels, not siblings")
        if _found:
            _conf_any = True
            print(f"  {_src['name']}:")
            for _msg in _found:
                print(f"      {_msg}")
    if not _conf_any:
        print("  none -- no duplicate `defines:` term, and no `overrides:` or\n"
              "  `in_force_at:` naming a sibling, in any source in force.")
    print()

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

    # UNLANDED WORK, printed BEFORE the checklist rather than with the rest
    # of the branch scan at the end (practice: very-deep-check, step 4 of its
    # order of operations).
    #
    # The two halves of the branch sweep have different costs and different
    # jobs, and bundling them put the cheap one behind the expensive one.
    # Deciding each branch's fate is judgment and belongs in pass 4. Knowing
    # WHAT ALREADY EXISTS is a list, costs nothing, and is the only step in
    # this whole check that prevents work instead of finding it.
    #
    # The 2026-09-07 run is the incident: it rediscovered two missing files
    # from scratch, wrote them up as findings and filed them as open TODO
    # items -- while the fixes sat finished on a branch from the previous
    # day, in both private sets, named in the commit subjects. Nothing had
    # asked what was sitting unmerged, because the list only appeared after
    # every pass had already run.
    if not skip_branch_scan:
        _unlanded = []
        for _name, _scan in branch_scans.items():
            for _r in (_scan or {}).get('unmerged', []):
                if _r.get('unique'):
                    _unlanded.append((_name, _scan['target'], _r))
        print("\nUNLANDED WORK -- read this BEFORE the passes, not after\n")
        if _unlanded:
            print("Work that was written and never landed is invisible to every\n"
                  "other step in this check. Read each branch's diff far enough to\n"
                  "know what it already fixes, THEN start the passes -- and check\n"
                  "any gap a pass turns up against this list before writing it up.\n"
                  "A finding that a branch already fixes is not a missing fix; it\n"
                  "is an unlanded one, which is a different problem.\n")
            for _name, _target, _r in _unlanded:
                _age = f", last moved {_r['last']}" if _r.get('last') else ""
                print(f"  {_name}: {_r['name']}")
                print(f"      {_r['unique']} commit(s) with no patch-equivalent "
                      f"on the integration branch{_age}")
                print(f"      git log --oneline origin/{_target}..origin/{_r['name']}")
            print(f"\n  {len(_unlanded)} branch(es) carry unlanded work. Verdicts are "
                  f"pass 4's job;\n  reading them is this step's job, and it comes first.\n")
        else:
            print("  No branch carries unlanded work. (A branch reported unmerged\n"
                  "  but carrying nothing was rebased or squash-merged in -- pass 4\n"
                  "  still gives it a deletion verdict.)\n")

    if not skip_visibility:
        print()
        print("REPOSITORY VISIBILITY -- private names in a public tree\n")
        _bl = os.environ.get('PRECEDENT_LEAK_BLOCKLIST')
        _vf, _vn = repo_visibility_audit(repo_root, _bl)
        for f in _vf:
            print(f'  FINDING: {f}')
        for n in _vn:
            print(f'  note: {n}')
        if not _vf and not _vn:
            print('  nothing referenced, nothing to check')
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

    # THE ENDGAME MERGE (practice: very-deep-check, pass 4). Printed with
    # the branch material because it is the same question one level up: the
    # branch sweep asks which branches never landed, this asks what happens
    # when the branch everything lands ON finally lands itself.
    if endgame is not None:
        print(f"ENDGAME MERGE -- rehearsing origin/{endgame['target']} into "
              f"origin/{endgame['base']}\n")
        if endgame['status'] in ('cannot-tell', 'error'):
            print(f"  CANNOT TELL: {endgame['note']}")
            print(f"  Reported as unknown, never as clean -- an empty "
                  f"difference from a check that could not run reads exactly "
                  f"like a good result.\n")
        else:
            print(f"  conflicting paths:              {len(endgame['conflicts'])}"
                  f"   (loud -- whoever runs the merge will see these)")
            print(f"  present on the branch, ABSENT\n"
                  f"  from the merge result:          {len(endgame['dropped'])}"
                  f"   (silent -- no conflict is raised)")
            if endgame['dropped']:
                print(f"\n  FINDING: {len(endgame['dropped'])} path(s) would "
                      f"disappear when this merge lands, with nothing said "
                      f"about them.\n  The cause is history surgery on "
                      f"origin/{endgame['base']} -- a reverted merge, a "
                      f"cherry-pick, a force-push --\n  which leaves the "
                      f"commits in its log while the tree no longer has the "
                      f"files, so git\n  treats the work as already merged "
                      f"and honours the deletion. First few:\n")
                for path in endgame['dropped'][:10]:
                    print(f"      {path}")
                if len(endgame['dropped']) > 10:
                    print(f"      ... and {len(endgame['dropped']) - 10} more "
                          f"(--json for the full list)")
                print()
            else:
                print(f"\n  Nothing disappears silently. Note what this does "
                      f"NOT say: a path present in\n  the merge result can "
                      f"still carry the wrong side's content, which only the\n"
                      f"  conflict set, read by a person, will catch.\n")
            if endgame['shallow']:
                print(f"  CAVEAT: this clone is shallow, so the merge base "
                      f"may not be the real one.\n  Deepen "
                      f"(`git fetch --unshallow origin`, or a bounded "
                      f"--depth=N) and re-run before\n  trusting an empty "
                      f"result.\n")

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
