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

Also scans this checkout and EVERY source precedent.json declares that is
its own git checkout -- any level, not only the private ones -- for
branches, in BOTH directions. A source that is a vendored tree inside the
parent checkout has no branches of its own and is skipped by looking, not
by guessing from its level; a source resolving to the same clone as another
is scanned once.

Fully merged and not yet deleted (git merge-base --is-ancestor -- true
regardless of whether GitHub's own "merged" flag is set, which it is not
for a repo that lands PRs by direct push) is the cheap half. Each of those
rows carries the date it last moved and its age, and the list is split at a
declared threshold (`branch_stale_days` in a repo's own precedent.json,
STALE_DAYS_DEFAULT otherwise, `--stale-days N` for one run): merged AND
long-finished is the safest thing on the page to delete, merged this week
may still be checked out on somebody's machine. Both halves are equally
proven safe by the ancestor test -- the split sorts the chore, it does not
grade the branches.

The half that costs more is the other one: a branch that never landed and
that nobody ever decided about.
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
import json, os, pathlib, re, subprocess, sys, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_resolve as pr

FATAL_MISSING_LEVELS = ('team', 'individual')

# How old a MERGED, undeleted branch has to be before the sweep marks it
# stale. A threshold nobody decided is doctrine, so this is a declared,
# overridable input rather than a number buried in the code
# (practice: constants-are-risk-inputs): a repo sets `branch_stale_days` in
# its own precedent.json, and `--stale-days N` overrides it for one run.
#
# 90 days is a STARTING VALUE, not a measured one, and it is the only kind
# of claim available here -- nobody has data on how long a merged branch
# sits before it stops meaning anything (practice: no-invented-specifics,
# which forbids dressing that up as a finding). It is deliberately well
# past any review cycle: a branch merged last month may still be open in
# somebody's editor, one merged last quarter is not.
STALE_DAYS_DEFAULT = 90

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
import leak_gate  # noqa: E402

# practice: one-formatter-per-quantity -- every moment in time this project
# writes down comes from ONE module, in the person's zone, carrying its
# offset. Never a bare datetime.date.today(): that is the container's UTC.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # noqa: E402


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


# Git subcommands that talk to a remote, and so may need a credential.
# Keyed on the subcommand rather than fixed up at each call site, because
# the call sites are the thing that changes: the sweep grew three new
# fetches in a fortnight, and a fix applied per-caller is a fix that covers
# whatever existed the day it was written (practice: durable-fix).
_NETWORK_GIT = frozenset({'fetch', 'ls-remote', 'pull', 'push', 'clone'})
_ORIGIN_URL = {}


def _origin_url(repo_dir):
    """-> a repo's origin URL, cached. Read through _run_git deliberately:
    `config` is not a network subcommand, so this cannot recurse."""
    key = str(repo_dir)
    if key not in _ORIGIN_URL:
        rc, out, _ = _run_git(repo_dir, 'config', '--get', 'remote.origin.url')
        _ORIGIN_URL[key] = out if rc == 0 else ''
    return _ORIGIN_URL[key]


def _credential_args(repo_dir):
    """-> the `git -c` flags that let one network call authenticate, or [].

    THE INCIDENT (2026-09-10, measured in a session where the credential
    route was working exactly as INSTALL.md section 8 describes). Every one
    of the four private sources failed this tool's own freshness gate with
    "could not read Username for 'https://github.com'", and the run refused
    to read a line -- in the configuration AGENTS.md calls verified-working.
    The token was fine. `_run_git` shelled out to plain `git`, while the
    credential lives in $PRECEDENT_GIT_TOKEN behind a helper that only
    precedent_source_bootstrap.py was passing. So the sources could be
    CLONED at session start and then not FETCHED by the check that reads
    them, and the failure named a missing username rather than a missing
    plumbing -- which sends the reader to re-set a token that was never
    the problem.

    Worth noting what made it invisible for a day: the tool fails CLOSED
    here, correctly, and a hard refusal reads as the gate doing its job.
    A guard that is right about the state and wrong about the cause is the
    expensive kind (practice: fail-gracefully -- name WHICH failure).

    The secret never reaches an argument list; see
    precedent_source_credentials.credential_args, which builds a helper
    naming the variable. Degrades to [] when the module is absent, since
    this engine is vendored into trees older than it (practice:
    fail-gracefully), and to [] for any non-https URL, so file:// fixtures
    are untouched.
    """
    try:
        import precedent_source_credentials as psc
    except Exception:
        return []
    url = _origin_url(repo_dir)
    if not url:
        return []
    try:
        return psc.credential_args(url)
    except Exception:
        return []


def _run_git(repo_dir, *args):
    pre = _credential_args(repo_dir) if args and args[0] in _NETWORK_GIT else []
    try:
        r = subprocess.run(['git', '-C', str(repo_dir), *pre, *args],
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
            # Name WHICH failure. "no credential", "credential refused" and
            # "no such repository" all end in a failed fetch, and their
            # remedies are opposite ones -- the first thing anybody does
            # with an unexplained failure is re-set a token that was fine.
            # precedent_source_bootstrap already tells them apart, so this
            # asks it rather than growing a second copy of the same
            # reasoning (practice: fail-gracefully, engine-plus-host-shims).
            try:
                _why = bootstrap_source._diagnose(err)
            except Exception:
                _why = 'it'
            out['remedy'] = (f'git -C {repo_dir} fetch origin {branch}   '
                             f'# failed: {err.splitlines()[-1] if err else "no detail"}'
                             + (f'\n      -> {_why}' if _why and _why != 'it' else ''))
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

def _declared_stale_days(repo_dir):
    """-> a repo's own `branch_stale_days` from its precedent.json, or None.

    Same shape and same reasoning as _declared_base_branch above: the number
    belongs to the repo, declared where a person can see and argue with it,
    not compiled into the engine every repo vendors
    (practice: constants-are-risk-inputs, layered-practice-packs). Returns
    None when undeclared, unreadable, or not a positive integer, so a
    malformed value falls back to the default rather than failing a sweep
    that has nothing to do with it (practice: fail-gracefully).
    """
    try:
        import json as _json, pathlib as _pathlib
        v = _json.loads((_pathlib.Path(repo_dir) / 'precedent.json')
                        .read_text(encoding='utf-8')).get('branch_stale_days')
        return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None
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


def _merge_base_resolves(repo_dir, target_ref, ref):
    """-> True if a merge base between the two refs actually resolves here.

    The precondition for trusting `git cherry`. Kept separate because the
    question "can this comparison run at all" is asked before the
    comparison, and answering it wrong is silent -- see _unmerged_row."""
    rc, out, _ = _run_git(repo_dir, 'merge-base', target_ref, ref)
    return rc == 0 and bool(out.strip())


def _branch_url(repo_dir, branch):
    """-> a URL that lands on GitHub's branches page filtered to `branch`,
    where the Delete button is, or None when the remote is not GitHub.

    WHY A LINK AND NOT JUST A NAME. This section routinely lists thirty-odd
    merged-but-undeleted branches, and a bare name is a name the reader then
    has to go find. Morgan, 2026-09-08: "make a list of them in the session
    including direct links to them so I can delete them". The branches page
    filtered to one name is the right target rather than the branch's tree
    view -- the tree view shows the code and offers no way to delete it.

    Parsed from the remote rather than assumed: a repository whose origin is
    not GitHub gets no link instead of a wrong one."""
    rc, url, _ = _run_git(repo_dir, 'config', '--get', 'remote.origin.url')
    if rc != 0 or not url:
        return None
    url = url.strip()
    if url.endswith('.git'):
        url = url[:-4]
    slug = None
    if 'github.com' in url:
        # Both remote forms -- the https one, and the SSH one whose host is
        # written with a user@ prefix and a colon before the owner. Spelled
        # out rather than shown: the literal example is email-shaped, and
        # the leak gate's secret-scan correctly refuses it in a tracked file.
        tail = url.split('github.com', 1)[1].lstrip(':/')
        parts = [x for x in tail.split('/') if x]
        if len(parts) >= 2:
            slug = f'{parts[0]}/{parts[1]}'
    if not slug:
        return None
    return (f'https://github.com/{slug}/branches/all?query='
            + urllib.parse.quote(branch, safe=''))


def _orphan_scan(repo_dir):
    """-> [str] files in one repo that nothing owns any more.

    WHY THIS IS ITS OWN SCAN. Every other check here asks whether something
    that should be present IS. An orphan is the mirror question -- something
    present that should not be -- and no existing check asks it, because
    each mechanism is keyed on its own current list and an orphan is by
    definition in nobody's list.

    THE INCIDENT, 2026-09-08. Upstream renamed `precedent_retire_path.py` to
    `precedent_decommission.py`. All three practice sets went on carrying the
    dead file, and `status` reported every one of them healthy: it was gone
    from KINDS, gone from the manifest, and `_untracked_engine_files` is
    keyed on the current lists by design. Three mechanisms, each correct, and
    the file was invisible to all of them at once. Morgan, reading the fix:
    "does very-deep-check look for orphan files? It should."

    Four kinds, cheapest first. Each is a DIFFERENT way a file stops being
    owned, which is why one query cannot find them all.
    """
    repo_dir = pathlib.Path(repo_dir)
    out = []
    tools_dir = repo_dir / 'tools'
    try:
        import precedent_vendor_engine as pve
    except ImportError:
        return ['could not import precedent_vendor_engine, so no engine '
                'orphan could be looked for -- this is not a clean result']

    manifest = None
    mpath = tools_dir / getattr(pve, 'MANIFEST_NAME', 'ENGINE_MANIFEST.json')
    if mpath.is_file():
        try:
            manifest = json.loads(mpath.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            out.append(f'tools/{mpath.name} is present but unreadable, so '
                       f'engine orphans cannot be found here')

    # 1. A name the engine once shipped and no longer does. Only a tombstone
    #    can find this -- it is in no current list to be compared against.
    for name, why in getattr(pve, '_retired_engine_files_present',
                             lambda d: [])(tools_dir):
        out.append(f'tools/{name} -- retired engine file: {why}')

    if manifest is not None:
        kind = manifest.get('kind', getattr(pve, 'DEFAULT_KIND', 'source'))
        wanted = set(pve.KINDS.get(kind, ())) | {'routing_scope.json'}
        # 2. Recorded by the manifest, no longer part of this kind, still on
        #    disk. The sweep that removes these runs only after a write.
        for name in sorted(manifest.get('files', [])):
            if name not in wanted and (tools_dir / name).is_file():
                out.append(f'tools/{name} -- the manifest records it but '
                           f'the {kind} engine no longer includes it')
        # 3. An engine name present but unrecorded: a hand-copy dropped in
        #    beside a properly vendored engine.
        for name in pve._untracked_engine_files(tools_dir, manifest):
            out.append(f'tools/{name} -- an engine file this manifest does '
                       f'not record (hand-copied in)')

    # 4. A check script whose practice is gone. `checked_by` points one way
    #    only, so a retired practice leaves its script with nothing naming
    #    it, and the script goes on being materialized into consumers.
    checks_dir = tools_dir / 'checks'
    practices_dir = repo_dir / 'practices'
    if checks_dir.is_dir() and practices_dir.is_dir():
        for f in sorted(checks_dir.glob('check_*.py')):
            slug = f.stem[len('check_'):].replace('_', '-')
            if not (practices_dir / f'{slug}.md').is_file():
                out.append(f'tools/checks/{f.name} -- no '
                           f'practices/{slug}.md in this source for it to '
                           f'check (renamed or retired practice?)')
    return out


def _last_commit(repo_dir, path):
    """-> (unix timestamp, short hash, subject) for the newest commit
    touching `path`, or None when git can name none.

    None means "this history cannot answer", not "never changed": on the
    --depth 1 clone a fresh session starts in, git log reaches exactly one
    commit and every path older than it looks untouched. Callers report
    that as UNKNOWN rather than folding it into "current"
    (practice: fail-gracefully).
    """
    # _run_git returns (rc, stdout, stderr). Reading only stdout is the
    # swallowed-exit-code shape AGENTS.md's gotchas record twice; here it
    # also crashes outright, because the tuple has no .strip().
    rc, out, _err = _run_git(repo_dir, 'log', '-1', '--format=%ct\t%h\t%s',
                             '--', str(path))
    if rc != 0 or not out.strip():
        return None
    parts = out.strip().split('\t', 2)
    if len(parts) != 3 or not parts[0].isdigit():
        return None
    return int(parts[0]), parts[1], parts[2]


def _spoken_commands(repo_dir):
    """-> sorted [(phrase, slug)] for every active practice defining a phrase
    that begins with a capital letter.

    The capital is the whole test, and it is a convention rather than a
    field: a `defines:` entry is either a term this catalogue names
    ("capture gate", "negative control") or a phrase a person SAYS
    ("Go merge", "Park it"). Only the second kind is capitalized, because
    only the second kind is quoted back in a sentence. Measured against the
    catalogue when this was written: 23 active practices define something,
    4 of them capitalized, and those 4 are exactly the standing commands.
    """
    found = []
    for sub in ('practices', 'local/practices'):
        d = pathlib.Path(repo_dir) / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob('*.md')):
            text = f.read_text(encoding='utf-8')
            if not text.startswith('---'):
                continue
            fm = sp.parse_frontmatter_fields(text.split('---', 2)[1], decode=True)
            if (fm.get('status') or 'active').strip() != 'active':
                continue
            defines = fm.get('defines') or []
            if isinstance(defines, str):
                defines = [defines]
            for phrase in defines:
                if isinstance(phrase, str) and phrase[:1].isupper():
                    found.append((phrase, fm.get('slug', f.stem)))
    return sorted(set(found))


# Rule-shaped prose: an imperative opener, or a modal that binds. Deliberately
# loose. This produces a WORKLIST for a person, never a verdict, so a false
# positive costs one glance and a false negative costs the thing this whole
# section exists to catch (practice: fail-gracefully).
_RULE_OPENER = re.compile(
    r'^\s*(?:[-*]\s*|\d+\.\s*)?(?:\*\*)?'
    r'(Never|Always|Don\'t|Do not|Avoid|Prefer|Use|Cut|No |Must|Write|Keep)\b',
    re.I)
_RULE_MODAL = re.compile(r'\b(must not|must always|should never|never|always)\b',
                         re.I)
_SHIPPED_SUFFIXES = ('.template', '.md', '.sh', '.txt')


# What a session pays before it does anything. The threshold is a prompt, not
# a limit: a section over it may be entirely correct and still worth splitting.
_SECTION_FLAG_TOKENS = 2500
# A live entry claiming its own trap is fixed is the archive candidate this
# whole pass exists to surface -- the entry is the thing that knows.
_SETTLED_MARKERS = ('fixed ', 'no longer true', 'applies itself now',
                    'resolved for this machine', 'now automated')


def _session_load(repo_dir):
    """-> (rows, findings) for everything a session loads before it works.

    WHY THIS IS A PASS AND NOT A GATE. Every line in an always-loaded file was
    right to add on the day it was added; nothing is wrong at any single
    commit. It only goes wrong in aggregate, months later, which is exactly
    what a per-commit gate cannot see and what an occasional deep read is for.

    WHAT IT MEASURES, and the distinction is the point: the resident block has
    a declared budget and is checked against it, so it was reported green for
    weeks while the file around it grew past 17,000 tokens. **The budget
    governed 4% of the cost.** This counts the whole of what is loaded --
    every `## ` section of the instructions file, plus the untracked practice
    file when private sources resolved -- so the number a person sees is the
    number a session actually pays.

    THE TRAP TO AVOID, stated here because the obvious use of this output is
    the wrong one: **do not optimise for the total.** Gotchas exist because
    sessions kept burning hours on the same environment traps, and a trimming
    pass that chases the number deletes the entries that are working. The
    question for each section is "would a session hit this today", never "how
    big is it".
    """
    root = pathlib.Path(repo_dir)
    rows, findings = [], []

    loaded = []
    for name in ('AGENTS.md', 'CLAUDE.md'):
        f = root / name
        if not f.is_file():
            continue
        text = f.read_text(encoding='utf-8', errors='replace')
        # CLAUDE.md is usually a one-line @AGENTS.md include; counting both
        # would double the total. Count it only when it carries real content.
        if name == 'CLAUDE.md' and len(text.strip()) < 200:
            continue
        loaded.append((name, text))
    sp = root / '.precedent' / 'SESSION_PRACTICES.md'
    if sp.is_file():
        loaded.append(('.precedent/SESSION_PRACTICES.md',
                       sp.read_text(encoding='utf-8', errors='replace')))
    if not loaded:
        return [], ['no instructions file found -- nothing to measure']

    total = 0
    for fname, text in loaded:
        heads = [(m.start(), m.group(0).strip('# ').strip())
                 for m in re.finditer(r'^## .+$', text, re.M)]
        spans = []
        if heads:
            spans.append(('(preamble)', text[:heads[0][0]]))
            for idx, (pos, name) in enumerate(heads):
                end = heads[idx + 1][0] if idx + 1 < len(heads) else len(text)
                spans.append((name, text[pos:end]))
        else:
            spans.append(('(whole file)', text))
        for name, body in spans:
            n = bv._approx_tokens(body)
            total += n
            rows.append((fname, name, n))
            if n >= _SECTION_FLAG_TOKENS:
                findings.append(
                    f'REVIEW   {fname} :: {name}\n'
                    f'      {n:,} tokens, every session, before any work starts.\n'
                    f'      Ask of each part: would a session hit this TODAY? What '
                    f'would not\n      bite any more belongs in a linked archive, '
                    f'in full -- not deleted.')

    # A live entry that says its own trap is settled is the strongest
    # mechanical signal available here, and it is the entry's own words.
    for fname, text in loaded:
        for m in re.finditer(r'^- \*\*(.{10,90})', text, re.M):
            start = m.start()
            nxt = text.find('\n- **', start + 1)
            entry = text[start:nxt if nxt != -1 else len(text)]
            low = entry.lower()
            if any(k in low for k in _SETTLED_MARKERS):
                findings.append(
                    f'note     {fname}: an entry says its own trap is settled '
                    f'({bv._approx_tokens(entry):,} tokens) --\n'
                    f'      "{m.group(1).strip()[:70]}"\n'
                    f'      Verify against the tree before archiving it; an '
                    f'entry\'s claim that it\n      was fixed is not evidence '
                    f'that it was.')
    return rows, findings


def _shipped_rules(repo_dir):
    """-> [(path, rule_line_count)] for every file this repo SHIPS into
    somebody else's repository that carries rule-shaped prose.

    WHAT THIS IS FOR, and why it is an inventory rather than a check.

    A template is inert here and binding there. The moment an adopter
    instantiates it, its imperative sentences sit in their repo alongside
    the resident practice block -- and nothing compares the two, because on
    this side it is skeleton content and on that side it is a local file no
    catalogue governs. So a generic rule shipped in a template can drift
    until it CONTRADICTS a live universal practice, and every adopter
    carries both orders at once with no way to know which wins.

    That is not hypothetical. templates/VOICE.md.template shipped 205 lines
    of general writing guidance to every project, one of which said "no bold
    inside paragraphs, and no bolded thesis sentence" while the resident
    practice `bold-key-phrases` said to bold key phrases by default
    (2026-09-08). Pass 3 already said to look for contradictions and had not
    found it in any run, because a coherence read of THIS repository reads
    documents, and a template does not read as a document making claims.

    No scan can decide whether a shipped sentence contradicts a practice --
    that is a reading, and the reading is the session's job. What a scan can
    do is hand it the short list instead of a directory tree.
    """
    root = pathlib.Path(repo_dir)
    out = []
    for base in ('templates',):
        d = root / base
        if not d.is_dir():
            continue
        for f in sorted(d.rglob('*')):
            if not f.is_file() or f.suffix not in _SHIPPED_SUFFIXES:
                continue
            try:
                lines = f.read_text(encoding='utf-8').splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            # A template's own HTML comment header is instructions to the
            # INSTALLER, not a rule shipped onward -- it is stripped at
            # instantiation. Counting it made every template look rule-heavy.
            body, in_comment = [], False
            for line in lines:
                if '<!--' in line:
                    in_comment = True
                if in_comment:
                    if '-->' in line:
                        in_comment = False
                    continue
                s = line.strip()
                if s and not s.startswith(('#!', '//')):
                    body.append(line)
            hits = [l for l in body
                    if _RULE_OPENER.match(l) or _RULE_MODAL.search(l)]
            if hits:
                out.append((f.relative_to(root).as_posix(), len(hits)))
    return sorted(out, key=lambda t: -t[1])


def _resident_slugs(repo_dir):
    """-> sorted slugs of the practices every session has loaded from turn one.

    These are what a shipped rule has to be read against, and the reason is
    the asymmetry: an on-demand practice reaches a session that thinks to
    ask, so a shipped file contradicting one is a conflict the session may
    never see both halves of. A RESIDENT practice is in front of every
    session always -- so a shipped file contradicting one puts two live
    orders in the same context window, every turn, in every adopter repo.
    """
    return sorted({fm.get('slug', '') for fm in _resident_practices(repo_dir)})


def _resident_practices(repo_dir):
    """-> frontmatter of every active resident practice, slug order.

    One walk feeding both readers -- the shipped-rules section, which needs
    the slugs, and the tier-placement section, which needs the occasion and
    whether a check already covers the practice. (practice: very-deep-check,
    pass 2 question 8: two of anything that should be one.)
    """
    out = {}
    for sub in ('practices', 'local/practices'):
        d = pathlib.Path(repo_dir) / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob('*.md')):
            text = f.read_text(encoding='utf-8')
            if not text.startswith('---'):
                continue
            fm = sp.parse_frontmatter_fields(text.split('---', 2)[1], decode=True)
            if (fm.get('status') or 'active').strip() != 'active':
                continue
            if (fm.get('tier') or '').strip() == 'resident':
                fm.setdefault('slug', f.stem)
                out[fm['slug']] = fm
    return [out[s] for s in sorted(out)]


def _doc_currency(repo_dir):
    """-> (findings, notes) for the documentation-currency sweep.

    Three questions, in the order a reader cares about them:

      1. STALE     -- a document whose subject moved after it did.
      2. UNMENTIONED -- a phrase a person says that no document teaches.
      3. UNREGISTERED -- a reader-facing document the registry never names,
                       so nothing above could have checked it.

    All three are REVIEW findings. A document older than its subject is
    often perfectly correct -- the change may have altered nothing a reader
    sees -- and no script can tell that from a real omission, which is why
    this prints for a person instead of failing
    (practice: change-updates-its-docs).
    """
    repo_dir = pathlib.Path(repo_dir)
    reg_path = repo_dir / 'tools' / 'doc_coverage.json'
    if not reg_path.is_file():
        return [], ['no tools/doc_coverage.json here -- nothing declares what '
                    'any document describes, so this sweep has nothing to '
                    'compare. That is the normal state outside the upstream '
                    'repository.']
    try:
        reg = json.loads(reg_path.read_text(encoding='utf-8'))
    except ValueError as exc:
        return [f'FINDING  tools/doc_coverage.json does not parse: {exc}'], []

    findings, notes = [], []
    documents = reg.get('documents', {})

    for doc, spec in sorted(documents.items()):
        if not (repo_dir / doc).is_file():
            findings.append(f'FINDING  {doc} is in the registry and not in the '
                            f'tree -- it moved or went, and nothing repointed '
                            f'the registry')
            continue
        doc_commit = _last_commit(repo_dir, doc)
        if doc_commit is None:
            # Two different states, and folding them together reported a
            # brand-new uncommitted document as a shallow-clone problem the
            # first time this ran. `ls-files --error-unmatch` separates
            # them: tracked-but-undateable is the shallow case, untracked
            # is simply a document that has not been committed yet.
            tracked = _run_git(repo_dir, 'ls-files', '--error-unmatch',
                               '--', doc)[0] == 0
            if tracked:
                notes.append(f'{doc}: tracked, and this history cannot date '
                             f'it (a shallow clone). UNKNOWN, not current.')
            else:
                notes.append(f'{doc}: not committed yet, so there is nothing '
                             f'to compare against. It dates from its first '
                             f'commit.')
            continue
        newer = []
        for described in spec.get('describes', []):
            if not (repo_dir / described).exists():
                findings.append(f'FINDING  {doc} says it describes {described}, '
                                f'which is not in the tree')
                continue
            sub = _last_commit(repo_dir, described)
            if sub is None:
                continue
            if sub[0] > doc_commit[0]:
                newer.append((described, sub))
        if newer:
            findings.append(
                f'REVIEW   {doc}\n'
                f'      last touched {_stamp(doc_commit[0])} ({doc_commit[1]} '
                f'{doc_commit[2][:60]})\n'
                f'      but its subject moved after that:')
            for described, sub in sorted(newer, key=lambda t: -t[1][0]):
                findings[-1] += (f'\n        {described} -- {_stamp(sub[0])} '
                                 f'({sub[1]} {sub[2][:60]})')
            findings[-1] += (f'\n      Read the document against those commits. '
                             f'If nothing a reader sees\n      changed, say so '
                             f'and move on -- this is a prompt, not a verdict.')

    # -- 2. every spoken command reaches the page that teaches them --------
    rules = reg.get('must_mention', {})
    for doc, spec in sorted(documents.items()):
        rule = spec.get('must_mention')
        if rule != 'spoken-commands' or not (repo_dir / doc).is_file():
            continue
        text = (repo_dir / doc).read_text(encoding='utf-8')
        commands = _spoken_commands(repo_dir)
        missing = [(p, s) for p, s in commands if p.lower() not in text.lower()]
        if missing:
            findings.append(
                f'FINDING  {doc} is the page that teaches the command '
                f'vocabulary, and\n      {len(missing)} command(s) a person '
                f'is expected to say are not in it:')
            for phrase, slug in missing:
                findings[-1] += f'\n        "{phrase}"  (practices/{slug}.md)'
            why = rules.get('spoken-commands', {}).get('why', '')
            if why:
                findings[-1] += f'\n      {why}'
        elif commands:
            notes.append(f'{doc}: all {len(commands)} spoken command(s) '
                         f'appear -- {", ".join(p for p, _ in commands)}.')

    # -- 3. a reader-facing document nothing in the registry names ---------
    doc_dir = repo_dir / 'documentation'
    if doc_dir.is_dir():
        for f in sorted(doc_dir.glob('*.md')):
            rel = f.relative_to(repo_dir).as_posix()
            if rel not in documents:
                findings.append(
                    f'FINDING  {rel} is reader-facing and the registry does '
                    f'not name it,\n      so nothing above could tell whether '
                    f'it has gone stale. Add it to\n      '
                    f'tools/doc_coverage.json with what it describes.')
    return findings, notes


def _stamp(unix_ts):
    """-> 'YYYY-MM-DD' for a unix timestamp, in UTC.

    One formatter for this quantity, declared once
    (practice: one-formatter-per-quantity).
    """
    import datetime
    return precedent_time.date_from_unix(unix_ts)


def _template_freshness(sources):
    """-> [str] what every real source of a level has and its skeleton does not.

    THE DIRECTION NOBODY CHECKED. precedent_bootstrap_source.verify() reads
    the skeleton and asks whether a real source has everything in it. That
    catches a source that drifted BELOW the template. It cannot catch the
    template drifting below reality -- a file every real source needs, that
    a newly bootstrapped one would be created without.

    Found 2026-09-08 on Morgan's prompting: the individual skeleton shipped
    no `identity.json`, which is the ONE place a person's name, address and
    timezone are written and the file `commit-identity.sh` reads to decide
    whether to ENFORCE an author-date offset or merely guess one. Every real
    set had it; a bootstrapped set would not have, and its wrong-offset
    commits would have reached the remote before anything said so.

    Evidence, not assertion: a level with ONE real source is n=1, and this
    says so rather than reporting a one-repo habit as a template gap."""
    try:
        import precedent_bootstrap_source as bss
    except ImportError:
        return ['could not import precedent_bootstrap_source, so template '
                'freshness was NOT checked -- this is not a clean result']
    # Generated or vendored at the destination, so a skeleton correctly has
    # none of them; and the session hooks come from the harness adapter.
    NOT_SKELETON = {
        'AGENTS.md', 'MAP.md', 'GLOSSARY.md', 'CODEOWNERS',
        'MANIFEST.json', 'ENGINE_MANIFEST.json',
    }
    by_level = {}
    for s in sources:
        lvl, path = s.get('level'), s.get('path')
        if lvl in ('team', 'individual') and path:
            p = pathlib.Path(path)
            if p.is_dir():
                by_level.setdefault(lvl, []).append((s.get('name'), p))

    out = []
    for lvl, repos in sorted(by_level.items()):
        skeleton = bss.SKELETONS.get(lvl)
        if skeleton is None or not skeleton.is_dir():
            continue
        ships = set()
        for f in skeleton.rglob('*'):
            if not f.is_file():
                continue
            # BOTH names, and the reason is a false positive this produced on
            # its first run: the skeleton's file is literally named
            # `config.json.sample`, and a real source keeps that same name.
            # Stripping the suffix and recording only `config.json` made the
            # check report a file the skeleton plainly ships.
            ships.add(f.name)
            n = f.name
            for suffix in ('.template', '.sample'):
                if n.endswith(suffix):
                    n = n[: -len(suffix)]
            ships.add(n)
        # Root files only: a directory's contents are the source's own
        # content, not its shape.
        common = None
        for _name, p in repos:
            here = {f.name for f in p.iterdir()
                    if f.is_file() and f.name not in NOT_SKELETON}
            common = here if common is None else (common & here)
        gaps = sorted((common or set()) - ships)
        if not gaps:
            continue
        n = len(repos)
        if n > 1:
            for name in gaps:
                out.append(f'FINDING {lvl}: all {n} resolved sources carry '
                           f'{name!r} and the skeleton ships no equivalent')
        else:
            # ONE source is not evidence of a shape, and labelling it a
            # finding would put a permanent list of that repo's own working
            # documents in front of every future run -- which is how a check
            # teaches people to skim it. Reported as candidates, once,
            # with what would settle them.
            out.append(f'note {lvl}: only ONE source of this level resolved, '
                       f'so nothing here is evidence of a template gap yet. '
                       f'Files it carries that the skeleton does not: '
                       f'{", ".join(repr(g) for g in gaps)}. A second source '
                       f'of this level is what would tell shape from habit.')
    return out


def _merged_row(repo_dir, name, ref, stale_days):
    """-> the evidence a session needs to DELETE one branch that is already
    an ancestor of the integration branch: {'name', 'last', 'age_days',
    'stale'}.

    THE GAP THIS CLOSES (asked 2026-09-10, by Morgan, reading a real sweep
    of this repo). The merged half used to be a bare list of names. That is
    the wrong shape for the decision it feeds: a person looking at 68 names
    with no dates cannot tell the branch merged this morning -- which may
    still be checked out in somebody's editor, and whose deletion is a small
    rudeness -- from the one merged in April, which is pure clutter. Both
    read identically, so the whole list gets waved through or none of it
    does, and in practice none of it does. The unmerged half had carried its
    date since it was written; the half that actually ends in a deletion had
    not.

    `stale` is age against a DECLARED threshold, never a judgment about the
    branch's content: every row here is already proven safe to delete by the
    ancestor test, so staleness only sorts the list by how obviously it is
    finished. A row whose date cannot be read is `stale: None` -- unknown,
    never False, since "no date" and "recent" are the same output otherwise
    and the first is the one that needs saying (practice: fail-gracefully).
    """
    row = {'name': name, 'last': None, 'age_days': None, 'stale': None}
    rc, out, _ = _run_git(repo_dir, 'log', '-1', '--format=%ct', ref)
    if rc == 0 and out.strip().isdigit():
        ts = int(out.strip())
        row['last'] = _stamp(ts)
        # Both sides aware and in one zone -- precedent_time owns every
        # moment this project writes down (practice: timestamps-carry-offset,
        # one-formatter-per-quantity).
        row['age_days'] = max(
            0, (precedent_time.now() - precedent_time.from_unix(ts)).days)
        row['stale'] = row['age_days'] >= stale_days
    return row


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
    # `git cherry` is only meaningful if a merge base between the two refs
    # actually resolves in THIS clone, so ask for one first.
    #
    # Guarding on `git cherry`'s exit code -- which is what this did until
    # 2026-09-08 -- never fires, because on a shallow clone there is no
    # failure to catch: git exits 0 and prints EVERY commit with a `+`, so
    # a fully-merged branch reports as carrying all of its work unlanded.
    # Measured on a fixture built for it: a branch merged --no-ff into its
    # target reported `+1` on a `--depth 1` clone and `0` on the full one,
    # both exit 0. It fired for real on this repo the same day, inventing
    # 22 unlanded commits across three branches of `precedent-individual`
    # that were all plain ancestors of `main` -- and this section's whole
    # job is to tell a session which branches to go read, so the cost was
    # three diffs read for nothing, in the step that exists to prevent
    # exactly that kind of waste.
    #
    # `git merge-base` is the honest witness: on the same fixture it exits
    # 1 where cherry exits 0 (AGENTS.md records that exit-1 separately, as
    # something NOT to read as a rewritten branch -- here it is the signal).
    # Deepen once before giving up: the answer is usually reachable, and a
    # bounded fetch works on a shallow and a full clone alike.
    if not _merge_base_resolves(repo_dir, target_ref, ref):
        _run_git(repo_dir, 'fetch', '--depth=5000', 'origin')
    if _merge_base_resolves(repo_dir, target_ref, ref):
        rc, out, _ = _run_git(repo_dir, 'cherry', target_ref, ref)
        if rc == 0:
            row['unique'] = sum(1 for ln in out.splitlines()
                                if ln.startswith('+'))
    if row['unique'] is None:
        # Never guess here. A fabricated verdict is worse than none: this is
        # the branch someone might delete on it.
        row['verdict'] = (f'UNKNOWN -- no merge base between {target} and this '
                          f'branch resolves in this clone, so the patch '
                          f'comparison cannot run and its result would be '
                          f'fiction. Deepen with `git fetch --depth=5000 '
                          f'origin` and re-check before acting')
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


def scan_branches(repo_dir, target=None, exclude=(), stale_days=None):
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
    commits have landed on it yet, long before it is actually done.

    `stale_days` is the age at which a merged branch is marked stale; None
    takes the repo's own declared `branch_stale_days`, then
    STALE_DAYS_DEFAULT. Each merged entry is a _merged_row dict, never a
    bare name -- see that function for why the deletion list needs dates."""
    repo_dir = pathlib.Path(repo_dir)
    if not (repo_dir / '.git').is_dir():
        return None
    if stale_days is None:
        stale_days = _declared_stale_days(repo_dir) or STALE_DAYS_DEFAULT
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
            merged.append(_merged_row(repo_dir, name, ref, stale_days))
        else:
            unmerged.append(_unmerged_row(repo_dir, name, ref, target_ref, target))
    return {'target': target,
            'merged': sorted(merged, key=lambda r: r['name']),
            'unmerged': sorted(unmerged, key=lambda r: r['name']),
            'stale_days': stale_days,
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
        # Which trees are mirrored is asked PER REPO, because this walks
        # every repo in force and they do not share an install model. The
        # literal 'process/upstream/' that used to sit here is INSTALL.md
        # §1's layout; a §0 repo's vendored catalogue sits wherever its
        # precedent.json points, so every one of those files was being read
        # as the repo's own text. (practice: durable-fix)
        if rel.startswith(pr.mirrored_prefixes(repo_dir) + ('.git/',)):
            continue      # mirrored: another repo's tree, not this one's text
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
    # THE BLOCKLIST IS READ AS PATTERNS, NOT AS STRINGS, and that is a repair
    # rather than a preference. This block used to strip `\b` off each end and
    # compare `name.lower() in blocked` -- exact string equality, which was
    # right for as long as every entry was a whole repository name. The
    # 2026-09-07 stem rewrite ended that: an entry is now a truncated head
    # plus a suffix match, so equality matches nothing and the stale-entry
    # half below would have reported a clean sweep it never performed. The
    # same read also gives the coverage question its answer -- "does any
    # pattern match this bare name" is one call for both halves.
    #
    # leak_gate._parse_blocklist is the one reader, so the push gate and this
    # audit cannot drift in how they interpret a line. It exits on a bad
    # regex, which is correct for a gate and wrong for an audit that must
    # finish and report, so the exit is caught and turned into a note.
    blocked_pats, allowed = None, {}
    if blocklist_path and pathlib.Path(blocklist_path).exists():
        bl = pathlib.Path(blocklist_path)
        try:
            for line in bl.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                m = re.match(r'#\s*visibility-audit:\s*allow\s+(\S+/\S+)\s*--\s*(.+)$',
                             line)
                if m:
                    allowed[m.group(1).lower()] = m.group(2).strip()
        except OSError as e:
            notes.append(f'blocklist at {blocklist_path} could not be read ({e}) '
                         '-- the allow lines were NOT read, so a deliberately '
                         'named repository may be reported below.')
        try:
            blocked_pats = leak_gate._parse_blocklist(bl)
        except SystemExit as e:
            notes.append(f'blocklist at {blocklist_path} did not compile ({e}) '
                         '-- the stale-entry and stem-coverage halves of this '
                         'audit did NOT run.')
        except OSError as e:
            notes.append(f'blocklist at {blocklist_path} could not be read ({e}) '
                         '-- the stale-entry and stem-coverage halves of this '
                         'audit did NOT run.')
    else:
        notes.append('no blocklist path given, so the stale-entry and '
                     'stem-coverage halves of this audit did NOT run; only '
                     'referenced repositories were checked.')

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
            # WHICH FORM IS UNGUARDED, said explicitly. A reader who is told
            # only "add it to the blocklist" adds the full name, which is what
            # the 2026-09-07 leak already had: the qualified form was covered
            # and the SHORT form walked out. So the finding says whether any
            # pattern matches the bare name, because that decides whether the
            # remedy is a new entry or a shorter cut of the entry you have.
            if blocked_pats is None:
                covers = (' Whether a blocklist pattern covers its bare name '
                          'was NOT checked -- no blocklist was readable.')
            elif any(p.search(name) for p in blocked_pats):
                covers = (' A blocklist pattern DOES match its bare name, so '
                          'the short form is guarded and only the qualified '
                          'form got through.')
            else:
                covers = (' NO blocklist pattern matches its bare name either, '
                          'so the short form -- the one people actually type, '
                          'and the one that leaked on 2026-09-07 -- is '
                          'unguarded too. Add a stem: truncate to a '
                          'distinctive head, and measure its hit count against '
                          'this tree before committing to the cut.')
            findings.append(
                f'{owner}/{name} is PRIVATE and is named in this tree '
                f'({len(set(files))} file(s), e.g. '
                f'{", ".join(sorted(set(files))[:3])}). Either scrub the name '
                f'or, if it must appear, say why -- and add it to the leak '
                f'blocklist so the push gate catches the next one. Nothing '
                f'offline can find this: the gate blocks what it was told.'
                + covers)
        elif blocked_pats and any(p.search(name) for p in blocked_pats):
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
    repo, user_config, checkout_target, stale_days = None, None, None, None
    for flag, dest in (('--repo', 'repo'), ('--user-config', 'user_config'),
                       ('--target', 'checkout_target'),
                       ('--stale-days', 'stale_days')):
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
            elif dest == 'stale_days':
                # Refuse rather than silently falling back: a run asked for
                # a threshold and given a different one reports a staleness
                # that is not the one anybody asked about.
                if not value.isdigit() or int(value) <= 0:
                    sys.exit(f"very deep check FAIL: --stale-days needs a "
                             f"positive whole number of days, not {value!r}.")
                stale_days = int(value)
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

    # EVERY source precedent.json declares, not only the private ones.
    # This used to be gated on FATAL_MISSING_LEVELS ('team', 'individual'),
    # which is the answer to a DIFFERENT question -- "whose absence should
    # abort the run" -- reused here as if it also meant "whose branches are
    # worth sweeping". The two came apart the moment a repo declared a
    # universal or repo-local source that IS its own checkout: a vendored
    # tree has no branches of its own and is right to skip, but a sibling
    # clone of the upstream set has plenty, and nothing was looking at them.
    # Asked 2026-09-10, by Morgan, of a sweep that had silently covered one
    # repository and read as if it had covered them all.
    #
    # The level is the wrong test either way -- what matters is whether the
    # path is its own git checkout, which scan_branches already decides by
    # looking (it returns None for anything else). So ask every source and
    # let that guard answer, rather than guessing from the level.
    #
    # Deduplicate by RESOLVED path: this repo declares itself as its own
    # universal source (`"path": "."`), and several sources can point at one
    # clone. Scanning it twice would print the same 68 branches under two
    # headings, which reads as two repos needing attention.
    branch_scans = {}
    if not skip_branch_scan:
        _, checkout_branch, _ = _run_git(repo_root, 'rev-parse', '--abbrev-ref', 'HEAD')
        branch_scans['checkout'] = scan_branches(
            repo_root, checkout_target,
            exclude=(checkout_branch,) if checkout_branch else (),
            stale_days=stale_days)
        _seen = {repo_root.resolve()}
        for s in data['sources']:
            try:
                _p = pathlib.Path(s['path']).resolve()
            except OSError:
                continue
            if _p in _seen:
                continue
            _seen.add(_p)
            _, src_branch, _ = _run_git(s['path'], 'rev-parse', '--abbrev-ref', 'HEAD')
            branch_scans[f"{s['level']} source {s['name']}"] = scan_branches(
                s['path'], exclude=(src_branch,) if src_branch else (),
                stale_days=stale_days)

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

    # The mirror of SOURCE SHAPE above, in both directions it cannot see.
    print("TEMPLATE FRESHNESS -- what the skeletons do NOT ship\n")
    _tf = _template_freshness(data['sources'])
    if _tf:
        print("  verify() reads the skeleton and asks whether a real source "
              "has\n  everything in it. Nothing asks the reverse. These are "
              "files every\n  resolved source of a level carries that a newly "
              "bootstrapped one\n  would be created without:\n")
        for _m in _tf:
            # The strength is decided where the evidence is, not here --
            # _template_freshness already prefixes 'FINDING' or 'note', and
            # stamping FINDING over a note re-labels weak evidence as strong.
            print(f"  {_m}")
    else:
        print("  none -- every file the resolved sources share at their root "
              "is\n  either shipped by the skeleton, generated, or vendored.")
    print()

    # A condition-shaped `expires:` field cannot be evaluated by any script, so
    # it is surfaced instead -- every run, in front of a person, rather than
    # silently doing nothing (practice: fail-gracefully).
    print("EXPIRING PRACTICES -- rules with a stated end, that nothing can "
          "auto-evaluate\n")
    _exp = []
    for _s in [{'name': 'this checkout', 'path': str(repo_root)}] + [
            dict(name=x.get('name'), path=x.get('path'))
            for x in data['sources'] if x.get('path')]:
        _base = pathlib.Path(_s['path'])
        for _sub in ('practices', 'local/practices'):
            for _f in sorted((_base / _sub).glob('*.md')) if (
                    _base / _sub).is_dir() else []:
                _t = _f.read_text(encoding='utf-8')
                if not _t.startswith('---'):
                    continue
                # The one frontmatter reader. Calling a non-existent one
                # inside `except Exception: continue` made this section
                # report "none" while a real expiry sat in the tree.
                _fm = sp.parse_frontmatter_fields(_t.split('---', 2)[1],
                                                  decode=True)
                _e = _fm.get('expires')
                if not isinstance(_e, str) or not _e.strip():
                    continue
                if re.match(r'^\d{4}-\d{2}-\d{2}$', _e.strip()):
                    continue  # a DATE -- precedent_check.py enforces those
                _st = (_fm.get('status') or 'active').strip()
                if _st != 'active':
                    continue
                # Keyed on the RESOLVED FILE, not the source name: this
                # checkout, the universal source (path ".") and a repo-local
                # source all overlap on disk, so the same file arrives three
                # times and read as three separate expiring rules.
                _exp.append((_f.resolve(), _fm.get('slug', _f.stem),
                             _e.strip()))
    _exp = sorted({(k, s2, c) for k, s2, c in _exp}, key=lambda t: t[1])
    if _exp:
        print("  Each is STILL BINDING. The condition is prose, so no check "
              "can read it --\n  that is why it is printed here rather than "
              "enforced. Ask of each one:\n  has this happened yet? If it "
              "has, retire or deduplicate the practice now.\n")
        for _path, _slug, _cond in _exp:
            try:
                _where = _path.relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                _where = str(_path)
            print(f"  {_slug}  ({_where})")
            print(f"      expires: {_cond}")
    else:
        print("  none -- no practice in force carries a condition-shaped "
              "expiry.")
    print()

    print("ORPHANS -- files nothing owns any more\n")
    _orph_any = False
    _orph_seen = False
    _orph_targets = [('this checkout', repo_root)]
    for _s in data['sources']:
        _p = _s.get('path')
        if _s.get('level') in ('team', 'individual') and _p:
            _orph_targets.append((_s.get('name'), pathlib.Path(_p)))
    for _name, _p in _orph_targets:
        if not pathlib.Path(_p).is_dir():
            continue
        _orph_seen = True
        _found = _orphan_scan(_p)
        if _found:
            _orph_any = True
            print(f"  {_name}:")
            for _m in _found:
                print(f"      {_m}")
    if not _orph_seen:
        print("  (no repository to scan)")
    elif not _orph_any:
        print("  none -- no retired engine file left behind, no manifest "
              "entry the\n  current kind dropped, no unrecorded engine "
              "file, and no check\n  script whose practice is gone.")
    print()

    print("SESSION LOAD -- what every session pays before it does anything\n")
    _rows, _sl = _session_load(repo_root)
    if _rows:
        _tot = sum(n for _, _, n in _rows)
        for _f, _name, _n in sorted(_rows, key=lambda r: -r[2])[:8]:
            print(f"  {_n:7,d}  {_f} :: {_name[:60]}")
        _rest = len(_rows) - min(8, len(_rows))
        if _rest > 0:
            print(f"  {sum(n for _,_,n in sorted(_rows, key=lambda r: -r[2])[8:]):7,d}"
                  f"  ({_rest} smaller section(s), combined)")
        print(f"  {'-'*7}")
        print(f"  {_tot:7,d}  TOTAL, every session, before any work starts "
              f"(rough: words x 1.3)\n")
    for _m in _sl:
        print(f"  {_m}")
    if not _sl:
        print("  no section is large enough to be worth splitting, and no "
              "entry claims its\n  own trap is settled.")
    print("\n  Do NOT optimise for the total. These entries exist because "
          "sessions kept\n  losing hours to the same traps -- a trimming pass "
          "that chases the number\n  deletes the ones that are working. The "
          "question is \"would a session hit\n  this today\", never \"how big "
          "is it\". What no longer bites moves to a\n  linked archive IN FULL, "
          "never to a deletion.")
    print()

    print("TIER PLACEMENT -- which practices are loaded from turn one\n")
    _resp = _resident_practices(repo_root)
    if _resp:
        print("  The resident set is capped by tools/build_views.py, which fails "
              "the build\n  when it is over budget -- so the trade is forced once, "
              "when somebody adds\n  a resident practice, and nothing revisits it "
              "afterwards. This is that read.\n")
        for _fm in _resp:
            _chk = 'checked' if (_fm.get('checked_by') or '').strip() not in ('', 'null') else '  --   '
            print(f"  {_chk}  {_fm.get('slug', '')}")
            print(f"           occasion: {(_fm.get('occasion') or '(none)').strip()[:88]}")
        print("\n  Both directions, and judge the OCCASIONS, not the token count: "
              "is each of\n  these really every-session-always, and is any "
              "on-demand practice being\n  missed because it only reaches a "
              "session that thought to ask? A third\n  answer is available and "
              "was right twice (spec/LOADER.md): the loader arm\n  found "
              "`verify-postcondition` and `environment-gotchas` 0 times while "
              "both\n  were resident, at two Rule lengths -- what they needed was "
              "a `checked_by`,\n  not a tier. The unchecked rows above are where "
              "that question lives.")
    else:
        print("  none -- this repository has no resident practice.")
    print()

    print("RULES WE SHIP SOMEWHERE ELSE -- inert here, binding there\n")
    _ship = _shipped_rules(repo_root)
    _res = _resident_slugs(repo_root)
    if _ship:
        print("  Each of these lands in an ADOPTER's repository carrying "
              "imperative prose.\n  There it sits beside the resident practice "
              "block, and nothing compares the\n  two -- on this side it is "
              "skeleton content, on that side a local file no\n  catalogue "
              "governs. Read each against the resident practices below and "
              "ask:\n  does this shipped sentence state, or contradict, a rule "
              "the catalogue\n  already owns? If it states one, it belongs in "
              "the catalogue and not here.\n")
        for _rel, _n in _ship:
            print(f"  {_n:4d} rule-shaped line(s)  {_rel}")
        print(f"\n  Read them against the {len(_res)} RESIDENT practice(s) "
              f"first -- those are in\n  front of every session from turn one, "
              f"so a shipped file contradicting one\n  puts two live orders in "
              f"the same context window in every adopter repo:\n"
              f"    {', '.join(_res)}")
        print("\n  No scan decides this; the reading is the session's. "
              "(2026-09-08: VOICE.md's\n  template said \"no bold inside "
              "paragraphs\" while resident `bold-key-phrases`\n  said to bold "
              "by default -- shipped to every adopter, unnoticed by every\n"
              "  earlier run of this check.)")
    else:
        print("  none -- this repository ships no templates carrying "
              "rule-shaped prose.")
    print()

    print("DOCUMENTATION CURRENCY -- what changed, against what still says "
          "it is true\n")
    _doc_find, _doc_notes = _doc_currency(repo_root)
    for _n in _doc_notes:
        print(f"  note: {_n}")
    if _doc_notes and _doc_find:
        print()
    for _f in _doc_find:
        print(f"  {_f}")
    if not _doc_find:
        print("  none -- every registered document is at least as new as the "
              "things it\n  describes, every spoken command reaches the page "
              "that teaches them, and\n  no reader-facing document is "
              "missing from the registry.")
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
        _unknown = []
        for _name, _scan in branch_scans.items():
            for _r in (_scan or {}).get('unmerged', []):
                if _r.get('unique'):
                    _unlanded.append((_name, _scan['target'], _r))
                elif _r.get('unique') is None:
                    # NOT falsy-equivalent to zero, and the distinction is the
                    # whole point: 0 means "measured, nothing there", None
                    # means "could not measure". Folding None in with 0 --
                    # which `if _r.get('unique')` alone did until 2026-09-08 --
                    # deletes the unmeasurable branch from this section and
                    # then prints the all-clear below, which is a confident
                    # wrong answer produced by a scan that never ran.
                    _unknown.append((_name, _scan['target'], _r))
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
        elif not _unknown:
            print("  No branch carries unlanded work. (A branch reported unmerged\n"
                  "  but carrying nothing was rebased or squash-merged in -- pass 4\n"
                  "  still gives it a deletion verdict.)\n")
        if _unknown:
            print("  COULD NOT DETERMINE, which is not the same as clean -- these\n"
                  "  branches may carry unlanded work and this run cannot say:\n")
            for _name, _target, _r in _unknown:
                _age = f", last moved {_r['last']}" if _r.get('last') else ""
                print(f"  {_name}: {_r['name']}{_age}")
                print(f"      {_r['verdict']}")
            print(f"\n  {len(_unknown)} branch(es) unmeasurable. Deepen the clone and\n"
                  f"  re-run before treating this section as read.\n")

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
            # Split by age, not merely dated. A flat list of 68 names is
            # one undifferentiated chore nobody starts; the same list with
            # the long-finished branches gathered at the top is a short one
            # that can be done now and a remainder that can wait.
            _sd = scan.get('stale_days') or STALE_DAYS_DEFAULT
            _stale = [r for r in scan['merged'] if r.get('stale')]
            _recent = [r for r in scan['merged'] if not r.get('stale')]

            def _print_merged(rows):
                for r in rows:
                    _age = (f"last commit {r['last']}, {r['age_days']} day(s) "
                            f"old" if r['last']
                            else "last commit date unreadable in this clone")
                    print(f"    {r['name']} ({_age})")
                    _u = _branch_url(scan.get('path'), r['name'])
                    if _u:
                        print(f"      {_u}")

            print(f"  merged and STALE (>= {_sd} days) -- the safest deletions "
                  f"here; confirm authorship and the PR link, then delete:")
            if _stale:
                _print_merged(_stale)
            else:
                print(f"    {'(none)' if not incomplete else empty}")
            print(f"  merged, not deleted, still recent (< {_sd} days) -- "
                  f"same proof, but someone may still have it checked out:")
            if _recent:
                _print_merged(_recent)
            else:
                print(f"    {'(none)' if not incomplete else empty}")
            print(f"  NOT merged -- merge it or close it, one verdict each:")
            if scan['unmerged']:
                for r in scan['unmerged']:
                    age = f", last commit {r['last']}" if r['last'] else ""
                    print(f"    {r['name']} ({r['ahead']} commit(s) ahead"
                          f"{age})")
                    print(f"      {r['verdict']}")
                    _u = _branch_url(scan.get('path'), r['name'])
                    if _u:
                        print(f"      {_u}")
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
    # documentation/HOW_TO_USE_THIS_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
