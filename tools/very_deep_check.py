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
Detail section for the fixed checklist. A pointer to it closes this tool's
output; `--checklist` prints it in full beside the enumeration (off by
default since 2026-09-14 -- it was 46% of every run's output, and a session
that has loaded the practice already holds it).

READ practices/very-deep-check.md's Why section before trusting this
mechanism's own reliability -- it has not been evaluated the way
full-practice-audit and routing-audit have.

Runs the BOOTSTRAP GENERATOR against every resolved team/individual
source and diffs the result file by file -- the one direction neither
`bootstrap_source.verify()` (does a real set still have every skeleton file?)
nor `_template_freshness()` (does the skeleton still ship what real sets
carry?) can see, since both are about which files exist and neither compares
a byte. A difference in a file the skeleton ships is the set being lived in
and is reported as a note; a difference in a file bootstrap GENERATES -- the
vendored engine, the session hooks, settings.json -- is a finding, with the
set's own ENGINE_MANIFEST saying whether it is an older vendoring to refresh
or a hand-edit to move upstream. Nothing resolved is reported as a SKIP, not
as clean.

Then compares the SETS AGAINST EACH OTHER, which none of the three above
does: each of them measures one set against one template, so a change every
set made identically reads as healthy in all of them. `CONVERGENT DRIFT`
reports a file two or more sets of a level changed the same way -- the
skeleton-owned ones included, which `BOOTSTRAP DRIFT` downgrades to notes per
set for good reasons that stop applying the moment two sets agree. It names
the files and quotes the shared lines; it does not claim which side is wrong,
since the sets sharing an older build and the template missing a change look
identical from here.

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

Asks the cheap half of that same question too, and asks it first: when the
branch this repo works on is NOT its base branch, what has landed on the
base that the branch never took? Reported per commit -- date, subject,
files -- using git cherry, so work CARRIED across in another shape is not
listed as missing. It reports and stops: nothing is merged or cherry-picked
by this tool, and the session reading it asks the person row by row before
implementing any of it. `--skip-base-drift` skips it.

FIRST, before it reads anything: every repo in force must be provably
current against its origin -- this checkout and every declared team or
individual source -- and each one is asked, over the API, whether it still
EXISTS and still accepts a push (--skip-liveness to skip). Current and
archived is the pair nothing else here can tell apart: an archived repo
fetches like a live one and refuses every push. Not provably current FAILS the run (--allow-stale for a
deliberately offline one). "Stale" and "cannot prove it isn't" are the same
verdict, because the failure mode is identical: a confident report that
current work is missing and fixed bugs are open. It verifies rather than
mutates; --freshen fast-forwards, and only a clean tree that is strictly
behind.

RECORDS WHAT EACH OF ITS OWN SECTIONS RETURNED AND COST, every run, into
the CHECKED repo's record/very-deep-check-ledger.json -- `--repo X` records
into X's ledger, never this engine's -- and prints the cross-run read at
the end. This check grew a section at a time and nothing ever asked the reverse
question -- does any of them still earn its place? A section that has come
back empty across several runs is named at the end of every run with three
answers offered (keep, cheapen, retire) and none taken automatically: a
guard that never fires may be exactly why nothing is broken. "Tokens" here
is what a section PRINTED (words x 1.3), which is what it costs a session's
context to read it -- never the model's spend on judging it, which no tool
here can see. The four hand-worked passes are the expensive half, and a
session records what one cost with --record-pass, from its own measurement.

Run:
  python3 tools/very_deep_check.py [--repo PATH] [--user-config PATH]
      -- the scope to read, as plain text, with a pointer to the checklist.
  python3 tools/very_deep_check.py --checklist
      -- also print the four passes in full (practices/very-deep-check.md's
      Detail, ~10,000 tokens). Off by default since 2026-09-14: the ledger
      measured it at 46% of every run's output, and a session that has
      loaded the practice already holds it.
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
  python3 tools/very_deep_check.py --skip-base-drift
      -- skip the scan for work that landed on the base branch and never
      came across to the integration branch.
  python3 tools/very_deep_check.py --stale-days N
      -- override the repo's declared `branch_stale_days` for one run. The
      branch sweep covers EVERY branch on origin, whoever wrote it, and
      names its author rather than filtering by one.
  python3 tools/very_deep_check.py --session-days N
      -- how far back the live-session sweep looks (default: the repo's
      `session_window_days`, else 14). That sweep prints the repo half --
      what was pushed, by whom, and what is sitting uncommitted -- for a
      session to hold the harness's own session list against.
  python3 tools/very_deep_check.py --skip-session-sweep
      -- skip that sweep entirely.
  python3 tools/very_deep_check.py --with-harness
      -- run `verify_harness.py --all` from inside this run and record the
      result as its own ledger section. Off by default: it is minutes, and
      its stress checks have OOM-killed a session's shell before. Left off,
      the PLANTED CASE COVERAGE section says the rotation is still owed and
      names the command.
  python3 tools/very_deep_check.py --skip-liveness
  python3 tools/very_deep_check.py --landable-only  # only repos this
                                  # session can push to; findings in the seam
                                  # with a dropped source go unreachable
      -- skip the one-API-call-per-repo check that each repo in force still
      exists and is not archived. For an offline run.
  python3 tools/very_deep_check.py --freshen
      -- fast-forward any repo in force that is strictly behind on a clean
      tree, then proceed. Never touches a diverged or dirty one: there,
      fast-forwarding discards commits.
  python3 tools/very_deep_check.py --allow-stale
      -- run anyway on a tree that is not provably current. For a
      deliberately offline run only; every finding is then provisional.
  python3 tools/very_deep_check.py --emit merged-stale-checkout
      -- print this checkout's merged-and-stale (safe-to-delete) branch
      list, as markdown, and exit -- nothing else runs. The block
      tools/doc_sync.py embeds into spec/VERY_DEEP_CHECK.md, never
      truncated (practice: very-deep-check, computed-numbers-in-scripts).
  python3 tools/very_deep_check.py --record-pass '2=done,findings=3,tokens=120000,note=...'
      -- record a hand-worked pass's outcome against the most recent run in
      the ledger, and exit. `findings`, `tokens` and `note` are each
      optional; an absent one is recorded as absent, never estimated.
  python3 tools/very_deep_check.py --record-read 'tools/verify_harness.py,by=...,note=...'
      -- record that somebody read that file END TO END today, in
      record/holistic-reads.json, and exit. The ACCRETION section ranks by
      commits since a file's last recorded read, so this is what moves a
      file off the top of it. Commit the registry: it is the only thing
      that knows.
  python3 tools/very_deep_check.py --ledger PATH
      -- read and write the run ledger somewhere else (a fixture, or a
      second repository's own ledger).
  python3 tools/very_deep_check.py --branch-report PATH
      -- write the branch sweep's committable Markdown (every merged,
      merged-elsewhere and unmerged branch, one clickable delete or
      compare link per row) somewhere other than the checked repo's own
      record/stale_branches.md. Written on every run that does not pass
      --skip-branch-scan; this only relocates it.
Exit: 1 if any repo in force is not provably current (unless --allow-stale),
or if a declared team/individual source is missing (unless
--allow-missing-sources); 0 otherwise.
"""
import collections, datetime, io, json, os, pathlib, re, shutil, subprocess, sys, tempfile, time, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_resolve as pr

FATAL_MISSING_LEVELS = ('shared', 'team', 'individual')

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

# How far back the session sweep looks when it asks what has happened here
# recently. Same reasoning as the threshold above -- a number nobody decided
# is doctrine (practice: constants-are-risk-inputs) -- so a repo overrides it
# with `session_window_days` in its own precedent.json, and `--session-days N`
# overrides that for one run.
#
# 14 days is a STARTING VALUE, not a measured one. It is chosen to be longer
# than any single session and longer than a weekend either side of one, so a
# piece of work begun on a Friday and abandoned on the Monday is still inside
# the window when somebody runs this on the Wednesday after.
SESSION_WINDOW_DAYS_DEFAULT = 14

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

# Optional, and deliberately so: this engine is vendored into trees older
# than github_budget.py, and a visibility audit that refused to run there
# would be a regression dressed as a fix (practice: fail-gracefully). Where
# it IS present, every API call this tool makes goes through it -- one
# implementation, one cache, one counter.
try:
    import github_budget as gh_budget  # noqa: E402
except Exception:                      # noqa: BLE001 -- reported, never raised
    gh_budget = None

# practice: one-formatter-per-quantity -- every moment in time this project
# writes down comes from ONE module, in the person's zone, carrying its
# offset. Never a bare datetime.date.today(): that is the container's UTC.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # noqa: E402
import build_todo_index as bti  # noqa: E402 -- reads todo/*.md's frontmatter,
                                 # the one place that parsing lives


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


def report_freshness(label, verdict, out=None):
    """-> True if this repo is clean enough to read."""
    # `out` is resolved HERE, not in the signature: a default
    # evaluated at import time captures the ORIGINAL sys.stdout, so
    # this helper would write straight past the run ledger's tee and
    # its section would report a cost it never paid
    # (practice: very-deep-check).
    out = out if out is not None else sys.stdout
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

def _vendored_exclusion_findings(repo_dir):
    """-> [str] findings, or None if `repo_dir` is not a vendored consumer.

    A vendored consumer is one with a process/upstream/ directory, or a
    process/manifest.json declaring upstream.commit -- the same two signals
    tools/checkin.py itself looks for. Reads NOT_VENDORED from checkin.py by
    import, not a second copy, so the two can never disagree about what is
    excluded (practice: registry-source-of-truth).

    This is the audit-time half of the NOT_VENDORED mechanism fix
    (practice: very-deep-check); checkin.py's own `update` prints the same
    signal every time it runs, but only for a repo that actually runs
    `update` again after a path is newly excluded. This check is what still
    catches the other case -- a consumer that has not re-run `update` since,
    or is vendoring from a pre-fix engine copy that never had the sweep at
    all -- since a very deep check reads the tree as it sits, not as the
    last `update` left it.
    """
    repo_dir = pathlib.Path(repo_dir)
    upstream_dir = repo_dir / 'process' / 'upstream'
    is_consumer = upstream_dir.is_dir()
    if not is_consumer:
        manifest_path = repo_dir / 'process' / 'manifest.json'
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            is_consumer = bool((manifest.get('upstream') or {}).get('commit'))
        except Exception:                                        # noqa: BLE001
            pass
    if not is_consumer:
        return None
    try:
        import checkin
        not_vendored = checkin.NOT_VENDORED
        not_vendored_root = checkin._NOT_VENDORED_ROOT_PATHS
    except Exception as exc:                                      # noqa: BLE001
        return [f"could not read NOT_VENDORED from tools/checkin.py -- "
                f"{type(exc).__name__}: {exc} -- so this repo's "
                f"process/upstream/ was NOT checked against it"]
    if not upstream_dir.is_dir():
        return []              # manifest declares a consumer, tree not present locally
    hits = {}          # name -> (file count, is a root file rather than a dir)
    for p in upstream_dir.rglob('*'):
        if not p.is_file() or '.git' in p.parts:
            continue
        rel = p.relative_to(upstream_dir)
        excluded = [part for part in rel.parts if part in not_vendored]
        is_root = not excluded and rel in not_vendored_root
        if is_root:
            excluded = [str(rel)]
        if excluded:
            name = excluded[0]
            n, _ = hits.get(name, (0, is_root))
            hits[name] = (n + 1, is_root)
    out = []
    for name, (n, is_root) in sorted(hits.items()):
        where = f"process/upstream/{name}" if is_root else f"process/upstream/{name}/"
        out.append(f"{where} still present, {n} file(s) under an excluded path -- "
                   f"either checkin.py update's sweep has not run here since "
                   f"{name!r} was excluded (re-run it: it now reports this every "
                   f"time), or this repo vendors from a pre-fix engine copy")
    return out


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


def _declared_session_window_days(repo_dir):
    """-> a repo's own `session_window_days` from its precedent.json, or None.

    Same shape and same reasoning as _declared_stale_days above: how far back
    "recently" reaches is a property of how fast a repo works, so it is
    declared where a person can argue with it rather than compiled into the
    engine every repo vendors (practice: constants-are-risk-inputs)."""
    try:
        import json as _json, pathlib as _pathlib
        v = _json.loads((_pathlib.Path(repo_dir) / 'precedent.json')
                        .read_text(encoding='utf-8')).get('session_window_days')
        return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None
    except Exception:
        return None


def _default_remote_branch(repo_dir):
    """-> the short branch name origin/HEAD points at ('main', typically),
    or None if it can't be determined. `refs/remotes/origin/HEAD` is not set
    on every clone this tool will see -- reproduced directly on this repo's
    own sibling checkouts of precedent-team-repo-maintenance and
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


def _github_slug(repo_dir):
    """-> 'owner/repo' for repo_dir's origin, or None when it is not GitHub.

    Shared by every URL-builder below -- _branch_url and _compare_url both
    need exactly this parse and used to each carry their own copy."""
    rc, url, _ = _run_git(repo_dir, 'config', '--get', 'remote.origin.url')
    if rc != 0 or not url:
        return None
    url = url.strip()
    if url.endswith('.git'):
        url = url[:-4]
    if 'github.com' not in url:
        return None
    # Both remote forms -- the https one, and the SSH one whose host is
    # written with a user@ prefix and a colon before the owner. Spelled
    # out rather than shown: the literal example is email-shaped, and
    # the leak gate's secret-scan correctly refuses it in a tracked file.
    tail = url.split('github.com', 1)[1].lstrip(':/')
    parts = [x for x in tail.split('/') if x]
    if len(parts) >= 2:
        return f'{parts[0]}/{parts[1]}'
    return None


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
    not GitHub gets no link instead of a wrong one.

    THE LINK FORM IS NOT THIS FUNCTION'S TO CHANGE (practice:
    branch-delete-links). That practice owns the `/branches/all?query=` form,
    the `safe=''` encoding and the two rules this file implements beside it
    -- the substring check in `_filter_is_ambiguous` and the separated
    unmerged list -- because a fleet sweep with no clone to read needs the
    same mechanism and must not re-derive it. Changing the URL here without
    changing it there is the drift that practice exists to stop."""
    slug = _github_slug(repo_dir)
    if not slug:
        return None
    return (f'https://github.com/{slug}/branches/all?query='
            + urllib.parse.quote(branch, safe=''))


def _filter_is_ambiguous(name, all_names):
    """True when `name` is a strict substring of some OTHER branch name in
    the same repo, so the filtered branches page shows more than one row.

    WHY IT IS CHECKED AT ALL (practice: branch-delete-links). The delete link
    promises ONE row with its trash icon on screen. `?query=` is a substring
    filter, so a repo holding both `fix-login` and `fix-login-retry` renders
    an identical-looking link for the first that opens two rows -- and the
    reader finds that out by clicking, because nothing about the URL or the
    row says so. The check costs one pass over a list already in memory and
    the failure it prevents is silent, which is the whole argument for it.

    Measured 2026-09-21 across 110 branches in a nine-repo fleet audit: zero
    collisions. That is the expected result, not evidence the check is
    pointless -- a guard whose failure mode is a reader quietly losing trust
    in the links earns its keep at zero hits."""
    return any(other != name and name in other for other in all_names)


def _compare_url(repo_dir, target, branch):
    """-> a GitHub compare-view URL for `branch` against `target`, or None
    when the remote is not GitHub.

    Pass 4's spec (item 2 of the four things an unmerged branch is written up
    with, practice: very-deep-check) wants a link on every unmerged row: its
    most recent pull request when one exists, else "the branch's own compare
    view". This offline scan has no GitHub API access to look up a PR (see
    scan_branches' own docstring), so it can only ever produce the fallback
    -- the compare view is what it links, always, rather than silently
    omitting the row's link because the better one is out of reach."""
    slug = _github_slug(repo_dir)
    if not slug:
        return None
    return (f'https://github.com/{slug}/compare/'
            + urllib.parse.quote(target, safe='')
            + '...' + urllib.parse.quote(branch, safe=''))


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


def planted_case_coverage(repo_root, run=False, timeout=2400):
    """-> (status, lines) for the push gate's planted-case ROTATION, settled
    or still owed. (practice: very-deep-check, order of operations step 2)

    WHY THIS IS A SECTION AND NOT A SENTENCE. verify_harness.py runs a 10%
    slice of its planted cases per commit and says so in its own result
    line -- "covered within 10 commits (--all forces every one)". That is a
    promise with no settlement date: nothing in the project ever forces the
    full set, so a case that stopped firing months ago is covered by an
    argument rather than by a run. The very deep check is the one moment
    already expensive on purpose, which makes it the place to collect.

    Default is to REPORT rather than run. A full harness run is minutes and
    its stress checks have OOM-killed a session's shell before
    (gotcha-2026-09-18-verify-harnesss-stress-checks-can-oom-kill-the-bash-tools),
    so a tool that silently started one inside another long run would be
    making that call for the session. --with-harness asks for it.

    status is 'ran', 'owed', or 'n/a'."""
    repo_root = pathlib.Path(repo_root)
    harness = repo_root / 'tools' / 'verify_harness.py'
    if not harness.is_file():
        return 'n/a', ['no tools/verify_harness.py here -- this repo runs no '
                       'planted cases, so there is no rotation to settle']
    cmd = 'python3 tools/verify_harness.py --all'
    if not run:
        return 'owed', [
            f'NOT RUN this invocation -- step 2 of the order of operations '
            f'owes `{cmd}`',
            'The bare command every other gate runs covers a 10% slice; this '
            'check is the one place the whole set is meant to run.',
            'Pass --with-harness to run it from here and record the result '
            'in the ledger.']
    started = time.time()
    try:
        proc = subprocess.run([sys.executable, str(harness), '--all'],
                              cwd=str(repo_root), capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 'owed', [f'FAIL: `{cmd}` did not finish within {timeout}s -- '
                        f'the rotation is NOT settled by this run']
    except OSError as exc:                                    # noqa: BLE001
        return 'owed', [f'FAIL: could not run `{cmd}` -- {exc}']
    took = time.time() - started
    body = (proc.stdout or '') + (proc.stderr or '')
    # The harness states its own selection in the result line; quoting it
    # back is the evidence that --all actually took effect, rather than
    # this section asserting it did.
    sel = [l.strip() for l in body.splitlines()
           if 'planted case' in l and 'ran' in l]
    lines = [f'ran `{cmd}` in {took:.0f}s -- exit {proc.returncode}']
    lines += [f'  {s}' for s in sel[:2]]
    if proc.returncode != 0:
        tail = [l for l in body.splitlines() if l.strip()][-8:]
        lines.append('FAIL -- the full set does not pass. Tail:')
        lines += [f'    {l}' for l in tail]
    return 'ran', lines


def _workflow_liveness_scan(repo_dir):
    """-> [str] CANDIDATES for a human to read, in one repo -- never a claim
    that any of them is actually dead.
    (practice: workflow-file-outside-vendoring)

    NOT A FIFTH KIND OF ORPHAN. _orphan_scan's four kinds above all report
    a firm claim ("the manifest records it but the current kind no longer
    includes it") because each is keyed against a list that says so
    definitively. A .github/workflows/*.yml file outside what
    ci_workflow_files tracks has no such list to be definitive against --
    CI_WORKFLOW_TEMPLATES names exactly one file per kind, so almost any
    repo with more than that single workflow file will have entries here BY
    DESIGN, most of them completely legitimate (a practice set's own
    commit-identity.yml and engine-refresh.yml, or a repo's own
    hand-authored check unrelated to Precedent entirely). Reusing
    _orphan_scan's confident wording here would be the exact mistake this
    function exists to prevent repeating -- see the incident below.

    THE INCIDENT THIS GUARDS AGAINST, 2026-09-20. A sweep list built by
    matching filenames against a table of names spec/CI_MINUTES_PLAN.md
    recorded as retired flagged `light-check.yml` in a real dependent repo
    as a retired duplicate. Verified directly: it was a
    live, required, hand-authored check with no relationship to anything
    Precedent ever templated. This function enumerates by CONTENT tracking
    (the manifest's own ci_workflow_files, not a name list) and reports
    candidates for a person to read -- it never classifies one as orphaned,
    which is exactly the step that mistake skipped."""
    repo_dir = pathlib.Path(repo_dir)
    try:
        import precedent_vendor_engine as pve
    except ImportError:
        return ['could not import precedent_vendor_engine, so no workflow '
                'file could be checked against this repo\'s manifest']

    mpath = repo_dir / 'tools' / getattr(pve, 'MANIFEST_NAME', 'ENGINE_MANIFEST.json')
    if not mpath.is_file():
        return []                     # nothing vendored here -- nothing to compare
    try:
        manifest = json.loads(mpath.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return ['tools/ENGINE_MANIFEST.json is present but unreadable, so '
               'workflow files could not be checked against it']

    exempt = set()
    cfg_path = repo_dir / 'precedent.json'
    if cfg_path.is_file():
        try:
            cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
            exempt = {e['path'] for e in
                     (cfg.get('ci_workflow_outside_vendoring_exempt') or [])
                     if e.get('reason') and e.get('path')}
        except (OSError, ValueError):
            pass

    return [f'.github/workflows/{pathlib.PurePosixPath(rel).name} -- not in '
           f'ci_workflow_files, not a known retired entry -- CANDIDATE, '
           f'read its content before concluding anything'
           for rel in pve._untracked_ci_workflow_files(repo_dir, manifest)
           if rel not in exempt]


HOLISTIC_READS_RELPATH = pathlib.Path('record') / 'holistic-reads.json'

# How far back the accretion ranking counts commits for a file nobody has
# ever recorded reading. A window, not "all history", for a reason that is
# mechanical rather than aesthetic: a fresh session starts in a --depth 1
# clone, where "all history" is one commit and every file would tie at 1.
# Declared here as an input rather than buried in a call
# (practice: constants-are-risk-inputs); a repo overrides it with
# `holistic_read_window_days` in its own precedent.json.
ACCRETION_WINDOW_DAYS = 30


def holistic_reads_path_for(repo_root=None):
    return pathlib.Path(repo_root or ROOT) / HOLISTIC_READS_RELPATH


def _load_holistic_reads(repo_root):
    """-> {path: {'date','by','note'}} keeping the NEWEST read per path."""
    try:
        data = json.loads(
            holistic_reads_path_for(repo_root).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    newest = {}
    for row in (data.get('reads') or []):
        path, date = str(row.get('path') or ''), str(row.get('date') or '')
        if not path or not date:
            continue
        if path not in newest or date > newest[path]['date']:
            newest[path] = {'date': date, 'by': row.get('by') or '',
                            'note': row.get('note') or ''}
    return newest


def _record_read(value, repo=None):
    """Append one holistic read to the registry. `value` is
    'PATH' or 'PATH,by=...,note=...'.

    A REGISTRY, not a sentence in a document
    (practice: registry-source-of-truth), for the reason the run ledger is
    one: "when did anybody last read this whole file" is exactly the claim
    memory gets wrong, and a prose note about it drifts from the tree the
    moment either moves."""
    repo_root = pathlib.Path(repo or ROOT).resolve()
    parts = [x.strip() for x in value.split(',')]
    path = parts[0]
    if not path:
        sys.exit("very deep check FAIL: --record-read needs a path, e.g. "
                 "--record-read 'tools/verify_harness.py,note=...'.")
    fields = {}
    for part in parts[1:]:
        k, _, v = part.partition('=')
        if k.strip() in ('by', 'note') and v:
            fields[k.strip()] = v.strip()
    if not (repo_root / path).exists():
        # Refused rather than recorded: a read recorded against a path that
        # is not there is a claim about nothing, and it would sit in the
        # registry suppressing the real file's row forever.
        sys.exit(f"very deep check FAIL: {path} does not exist in "
                 f"{repo_root} -- a read is recorded against a file, and a "
                 f"typo here would silently retire the real file's row.")
    out = holistic_reads_path_for(repo_root)
    try:
        data = json.loads(out.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        data = {'_generated_by': 'tools/very_deep_check.py --record-read',
                'reads': []}
    data.setdefault('reads', []).append({
        'path': path,
        'date': precedent_time.date_from_unix(time.time()),
        'by': fields.get('by', ''),
        'note': fields.get('note', '')})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print(f"recorded a holistic read of {path} in "
          f"{out.relative_to(repo_root)}. Commit it -- the registry is the "
          f"only thing that knows, and a chat thread is not.")
    return 0


def _accretion(repo_dir, window_days=None, top=10):
    """-> (rows, window, note). Tracked files ranked by how much has been
    added to them since anybody last read the whole thing.
    (practice: very-deep-check, pass 3)

    THE SHAPE OF THE PROBLEM. Every other question here asks whether a file
    is WRONG. This one asks whether anybody has looked at it as a thing
    lately, which no amount of correctness per commit can answer: a file
    grows one defensible line at a time and nobody is ever wrong on the day
    they add theirs. The close read of the always-loaded instructions file
    was added the day somebody noticed it had gone stale twice in one
    file -- and nothing generalized that fix, while the measurement said the
    instructions file was not even the worst offender.

    rows are (path, commits, lines, last_read_date or None), ranked by
    commits since the last recorded read, or across the window for a file
    with no recorded read at all.

    IT RANKS AND DOES NOT JUDGE. Churn is not a defect and a heavily edited
    file may be exactly the healthy one; what the ranking buys is that the
    file nobody has opened whole cannot stay invisible just because every
    individual commit to it was fine."""
    repo_dir = pathlib.Path(repo_dir)
    window = window_days or _declared_holistic_window(repo_dir) \
        or ACCRETION_WINDOW_DAYS
    reads = _load_holistic_reads(repo_dir)
    rc, out, _err = _run_git(repo_dir, 'log', f'--since={window} days ago',
                             '--no-merges', '--name-only', '--pretty=format:')
    if rc != 0:
        return [], window, 'git log could not be read here'
    counts = collections.Counter(x for x in out.split('\n') if x.strip())
    if not counts:
        return [], window, (f'no commits in the last {window} days, or a '
                            f'shallow clone with no history to count')
    rows = []
    for path, n in counts.items():
        f = repo_dir / path
        if not f.is_file():
            continue                      # deleted since: not a candidate
        read = reads.get(path)
        if read:
            rc2, out2, _e = _run_git(
                repo_dir, 'log', f'--since={read["date"]}', '--no-merges',
                '--oneline', '--', path)
            n = len([x for x in out2.split('\n') if x.strip()]) \
                if rc2 == 0 else n
        try:
            lines = sum(1 for _ in f.open('r', encoding='utf-8',
                                          errors='replace'))
        except OSError:
            lines = 0
        rows.append((path, n, lines, read['date'] if read else None))
    rows.sort(key=lambda r: (-r[1], -r[2]))
    return rows[:top], window, ''


def _declared_holistic_window(repo_dir):
    """-> a repo's own `holistic_read_window_days`, or None. Same shape and
    same reasoning as _declared_stale_days."""
    try:
        v = json.loads((pathlib.Path(repo_dir) / 'precedent.json')
                       .read_text(encoding='utf-8')
                       ).get('holistic_read_window_days')
        return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 \
            else None
    except Exception:                                         # noqa: BLE001
        return None


def _incident_frontmatter(path):
    """-> {key: value} for the simple `key: value` frontmatter block these
    catalogues use. Deliberately not a YAML load: parse_check.py already
    reports a file PyYAML rejects, and this one must keep working on the
    file that is currently malformed rather than vanishing with it."""
    out = {}
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        return out
    if not text.startswith('---'):
        return out
    body = text.split('---', 2)
    if len(body) < 3:
        return out
    for line in body[1].splitlines():
        if ':' not in line or line.startswith((' ', '\t')):
            continue
        k, _, v = line.partition(':')
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _last_run_date(repo_dir):
    """-> 'YYYY-MM-DD' of the newest recorded very deep check run here, or
    None. The ledger is the only record of when this check last looked, so
    it is also the only honest start date for "what has happened since"."""
    try:
        data = json.loads(ledger_path_for(repo_dir).read_text(encoding='utf-8'))
        runs = data.get('runs') or []
        return str(runs[-1].get('date')) if runs else None
    except (OSError, ValueError, AttributeError, IndexError):
        return None


def _incident_coverage(repo_dir, since=None):
    """-> (since, rows, note). Every incident FILED here since the last
    recorded run, with whatever in the tree cites it.
    (practice: very-deep-check, pass 2)

    THE QUESTION. This check has grown one bullet at a time, each added
    after somebody noticed a gap -- which makes growth a function of who
    happened to be looking. The standing version of that is cheap: take
    every gotcha filed and every open item closed since the last run, and
    ask of each one thing -- **what now prevents a recurrence, and is
    there a planted case proving it fires?**

    Three answers are honest, and the third is the one worth writing down:
    a named check with a planted case; a named check with no planted case;
    and nothing, deliberately, because the class is not mechanically
    detectable. A gap that has been examined and declined is not the same
    state as a gap nobody has looked at, and only the catalogue can tell
    them apart.

    IT ENUMERATES AND CITES; IT DOES NOT JUDGE. A slug appearing in a
    tool's source is evidence that something cites the incident, never
    proof that the incident cannot recur -- a docstring naming it reads
    identically to a check testing for it. The reading is the session's;
    what this removes is the part nobody does, which is assembling the
    list."""
    repo_dir = pathlib.Path(repo_dir)
    since = since or _last_run_date(repo_dir)
    if not since:
        return None, [], ('no recorded run in the ledger here, so there is '
                          'no "since" to read from')
    corpus = {}
    for sub in ('tools', 'practices'):
        d = repo_dir / sub
        if not d.is_dir():
            continue
        for f in sorted(d.rglob('*')):
            if f.is_file() and f.suffix in ('.py', '.md', '.json'):
                try:
                    corpus[str(f.relative_to(repo_dir))] = f.read_text(
                        encoding='utf-8')
                except (OSError, UnicodeDecodeError):
                    continue
    rows = []
    for kind, sub, datefield in (('gotcha filed', 'gotchas', 'noted'),
                                 ('open item closed', 'todo', 'closed')):
        d = repo_dir / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob('*.md')):
            fm = _incident_frontmatter(f)
            when = fm.get(datefield) or ''
            slug = fm.get('slug') or f.stem
            if not when or when in ('null', 'None') or when < since:
                continue
            cites = sorted(path for path, text in corpus.items()
                           if slug in text)
            rows.append((kind, slug, when, cites))
    rows.sort(key=lambda r: (r[2], r[1]))
    return since, rows, ''



_CHECK_REG = re.compile(r"^@check\(\s*'([a-z0-9-]+)'", re.M)


def _detectors_added(repo_dir, since):
    """-> (slugs, note, caveat). Checks registered in tools/precedent_check.py
    that were NOT registered as of `since`. `note` means the question could not
    be asked at all; `caveat` means it was asked over a narrower window than
    the ledger called for, and the sweep still runs.

    Reads the SET of registered slugs at two revisions and subtracts, rather
    than scanning the diff for added lines. A registration moved, reindented
    or rewrapped shows up in a diff as an addition and is not a new detector;
    the set difference cannot make that mistake."""
    repo_dir = pathlib.Path(repo_dir)
    rel = 'tools/precedent_check.py'
    if not (repo_dir / rel).is_file():
        return [], f'no {rel} here -- nothing registers a detector', ''
    if not since:
        return [], ('no recorded run in the ledger here, so there is no '
                    '"since" to read from'), ''
    old_rev = subprocess.run(
        ['git', 'rev-list', '-1', f'--before={since} 00:00:00', 'HEAD'],
        cwd=str(repo_dir), capture_output=True, text=True).stdout.strip()
    shallow = ''
    if not old_rev:
        # A DEPTH-LIMITED CLONE IS THE NORMAL CASE HERE, not a broken one:
        # sessions clone with --depth, so the history often starts AFTER the
        # ledger's last run. Falling back to the oldest commit the clone
        # actually has keeps the sweep running on a narrower window, which
        # UNDER-reports -- a detector registered before that commit reads as
        # old and is not carried. That is the safe direction for a silent
        # error and the wrong one to leave unsaid, so it is named in the
        # return and printed by the caller.
        old_rev = subprocess.run(
            ['git', 'rev-list', '--max-parents=0', '-1', 'HEAD'],
            cwd=str(repo_dir), capture_output=True, text=True).stdout.strip()
        if not old_rev:
            return [], (f'no commit here before {since}, and no root '
                        f'commit either -- nothing to compare against'), ''
        when = subprocess.run(
            ['git', 'log', '-1', '--format=%ad', '--date=short', old_rev],
            cwd=str(repo_dir), capture_output=True, text=True).stdout.strip()
        shallow = (f' (this clone holds no commit before {since} -- the '
                   f'comparison runs from its oldest, {old_rev[:9]} of '
                   f'{when}, so a detector older than that is not carried)')
    old = subprocess.run(['git', 'show', f'{old_rev}:{rel}'],
                         cwd=str(repo_dir), capture_output=True, text=True)
    if old.returncode != 0:
        return [], f'{rel} did not exist at {old_rev[:9]} -- nothing to diff', ''
    try:
        now_text = (repo_dir / rel).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as exc:
        return [], f'could not read {rel} ({type(exc).__name__})', ''
    before = set(_CHECK_REG.findall(old.stdout))
    after = set(_CHECK_REG.findall(now_text))
    return sorted(after - before), '', shallow


def _scratch_tree(src, dest, engine_src):
    """Copy `src`'s tracked tree to `dest`, give it a one-commit history, and
    drop THIS checkout's precedent_check.py in as its engine.

    WHY A COPY AND NOT THE REPO ITSELF. precedent_check.py resolves ROOT from
    its own location's git toplevel, so this checkout's copy cannot be pointed
    at another tree from the outside -- it has to physically sit inside one.
    Writing it into a real clone would leave an untracked file in somebody's
    working tree if this run died halfway, which is exactly the residue the
    container scanner exists to shout about.

    THE SYNTHESISED HISTORY IS A LIMIT, NOT A TRICK, and the caller prints it:
    the copy has one commit and a clean tree, so every change-scope check sees
    no change and declines. What this sweep asks is a TREE question -- does
    the new detector fire against what that repo holds right now -- and a
    tree-scope check answers it correctly here. A change-scope one cannot be
    answered from another repo's tree at all, and says so rather than passing."""
    files = subprocess.run(['git', 'ls-files', '-z'], cwd=str(src),
                           capture_output=True, text=True)
    if files.returncode != 0:
        return 'could not list its tracked files'
    for rel in files.stdout.split('\0'):
        if not rel:
            continue
        s, d = pathlib.Path(src) / rel, pathlib.Path(dest) / rel
        if not s.is_file():
            continue
        d.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(s, d)
        except OSError:
            continue
    shutil.copy2(engine_src, pathlib.Path(dest) / 'tools' / 'precedent_check.py')
    for args in (['init', '-q'], ['add', '-A'],
                 ['-c', 'user.email=sweep@localhost', '-c', 'user.name=sweep',
                  'commit', '-qm', 'fix sweep scratch']):
        r = subprocess.run(['git', *args], cwd=str(dest),
                           capture_output=True, text=True)
        if r.returncode != 0 and args[0] != '-c':
            return f'could not git {args[0]} the copy'
    return ''


def _fix_sweep(repo_root, targets, since=None, timeout=300):
    """-> (since, slugs, rows, note, caveat). Every detector added since the
    last recorded run, run against every repo in force.
    (practice: very-deep-check, pass 2 item 13 -- fix-the-original\'s half)

    THE GAP THIS CLOSES. fix-the-original requires fixing the origin and then
    every copy. Nothing checked that the sweep happened. The hardcoded-identity
    check was written the day the trap was reported, HERE, and the repo that
    actually had the problem was a consumer nobody re-scanned -- a check built
    in response to an incident and never run where the incident happened is the
    most expensive kind of clean result.

    CHECK COVERAGE beside this asks the opposite question and they are easy to
    confuse: it runs each repo\'s OWN vendored engine, because what a consumer
    actually enforces is the code it has. This runs THIS checkout\'s engine
    against that repo\'s tree, because the whole point is a detector the
    consumer has not vendored yet. A consumer running an engine from before the
    fix reports nothing, correctly, and that silence is what this is for.

    IT SWEEPS REGISTERED CHECKS AND NOTHING ELSE. A fix that shipped its
    detector as a standalone tool, a planted harness case or a hook is not
    reached here, and the caller says so -- naming the limit beats a row that
    reads like coverage it does not have."""
    since = since or _last_run_date(repo_root)
    slugs, note, caveat = _detectors_added(repo_root, since)
    if note:
        return since, [], [], note, ''
    if not slugs:
        return since, [], [], '', caveat
    engine = pathlib.Path(repo_root) / 'tools' / 'precedent_check.py'
    rows = []
    for label, path in targets:
        if not path or not pathlib.Path(path).is_dir():
            rows.append((label, None, 'not on this disk -- cannot be swept'))
            continue
        if pathlib.Path(path).resolve() == pathlib.Path(repo_root).resolve():
            rows.append((label, None, 'the origin of the fix -- swept by its '
                                      'own gate, not here'))
            continue
        tmp = pathlib.Path(tempfile.mkdtemp(prefix='fix-sweep-'))
        try:
            bad = _scratch_tree(path, tmp, engine)
            if bad:
                rows.append((label, None, bad))
                continue
            verdicts = []
            for slug in slugs:
                try:
                    proc = subprocess.run(
                        [sys.executable, str(tmp / 'tools' /
                                             'precedent_check.py'),
                         '--only', slug, '--full-sweep'],
                        cwd=str(tmp), capture_output=True, text=True,
                        timeout=timeout)
                except (OSError, subprocess.SubprocessError) as exc:
                    verdicts.append((slug, 'ERRORED', type(exc).__name__))
                    continue
                body = (proc.stdout or '') + (proc.stderr or '')
                why = ''
                for line in body.splitlines():
                    if line.startswith(('SKIPPED', 'VIOLATION')):
                        for sep in ('\u2014', '--'):
                            if sep in line:
                                why = line.split(sep, 1)[1].strip()
                                break
                        break
                m = re.search(r'precedent_check: (\d+) passed, (\d+) violated,'
                              r' (\d+) advisory, (\d+) errored, (\d+) skipped',
                              body)
                if not m:
                    verdicts.append((slug, 'UNREADABLE', 'no summary line'))
                elif int(m.group(2)):
                    verdicts.append((slug, 'VIOLATION', why))
                elif int(m.group(1)):
                    verdicts.append((slug, 'clean', ''))
                elif int(m.group(5)):
                    verdicts.append((slug, 'SKIPPED', why))
                else:
                    verdicts.append((slug, 'did not run', ''))
            rows.append((label, verdicts, ''))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return since, slugs, rows, '', caveat

def _pending_deletions(repo_dir):
    """-> (rows, note) for files the NEXT refresh would delete here, each
    with whatever still names them. rows is [(rel, [(path, line, text)])].

    THE DIRECTION NOTHING ELSE REHEARSES. Pass 1 builds fixtures that
    install and fixtures that move forward; both test a repo receiving
    something. A deletion decided in one tree and executed in many is the
    other direction, and until 2026-09-21 the two vendoring paths did not
    even agree on whether it happened at all -- engine files diffed the
    manifest and propagated, CI workflow files waited for somebody to
    remember a tombstone.

    This asks BEFORE the refresh what that refresh would take away, and who
    is still leaning on it. precedent_vendor_engine warns after the fact
    now, which is the same question asked too late to plan around.

    Read against THIS checkout's engine lists deliberately -- the upstream's
    current ones, which is what the next refresh will actually apply -- and
    never against the consumer's own vendored copy, which may be months
    old."""
    repo_dir = pathlib.Path(repo_dir)
    mpath = repo_dir / 'tools' / 'ENGINE_MANIFEST.json'
    if not mpath.is_file():
        return None, 'nothing vendored here -- no manifest to diff'
    try:
        manifest = json.loads(mpath.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None, 'tools/ENGINE_MANIFEST.json is unreadable'
    try:
        import precedent_vendor_engine as pve
    except ImportError:
        return None, 'precedent_vendor_engine did not import'
    kind = manifest.get('kind', getattr(pve, 'DEFAULT_KIND', None))
    rels = []
    if kind in getattr(pve, 'KINDS', {}):
        ships = set(pve.KINDS.get(kind, ())) | {'routing_scope.json'}
        rels += [f'tools/{n}' for n in
                 sorted(set(manifest.get('files') or []) - ships)]
    recorded = set(manifest.get('ci_workflow_files') or ())
    if kind in getattr(pve, 'CI_WORKFLOW_TEMPLATES', {}):
        ships_ci = {ia for _t, ia in pve.CI_WORKFLOW_TEMPLATES[kind]}
        rels += sorted(recorded - ships_ci)
    rels += sorted(r for r in recorded
                   if r in getattr(pve, 'RETIRED_CI_WORKFLOW_FILES', {}))
    # HOOKS, the third path, added 2026-09-21 the same day the engine grew
    # a remover for them. Same empty-directory guard the remover itself
    # carries: an upstream hooks/ that globs to nothing means this checkout
    # cannot see upstream, not that upstream ships no hooks, and reading it
    # the other way would report every installed hook as about to vanish.
    ships_hooks = set(pve._hook_file_names(ROOT / pve.HOOK_SOURCE_DIR)) \
        if hasattr(pve, '_hook_file_names') else set()
    if ships_hooks:
        rels += sorted(f'{pve.HOOK_DEST_DIR}/{n}'
                       for n in (manifest.get('hook_files') or [])
                       if n not in ships_hooks)
    # Only what is actually still on disk: a name the manifest tracks and
    # the tree no longer has is already gone, and reporting it as pending
    # would be reporting bookkeeping.
    rels = sorted({r for r in rels if (repo_dir / r).is_file()})
    if not rels:
        return [], (f'kind {kind!r}: nothing this kind stopped shipping is '
                    f'still on disk here')
    deps = pve.dependents_of(repo_dir, rels)
    return [(r, deps.get(r, [])) for r in rels], f'kind {kind!r}'


def _identity_reality(repo_dir, days=30, cap=300):
    """-> (rows, notes) for one repo: who the commits that LANDED say wrote
    them, read against the identity this repo declares.
    (practice: very-deep-check, pass 2, extending question 13)

    QUESTION 13 ASKS WHAT A SESSION INHERITS -- every git config, env var
    and sibling clone a person set up by hand. Nothing asked what actually
    landed, which is the only place the answer shows. Three incidents in
    six days made that gap expensive: commit identity unset in four clones,
    so commits landed under the wrong author; a consumer's tracked
    settings.json hardcoding one person's GIT_AUTHOR_* for every
    collaborator who loads it; and a whole design document written for a
    repo-scoped identity override no real requirement asked for.

    Three mechanical reads here:

    1. THE AUTHOR AND COMMITTER of every commit in the window, against the
       declared identity. A commit by somebody else is a NOTE and never a
       finding -- other people and machines commit, and a check that called
       that wrong would be unusable. What IS a finding is a commit authored
       by nobody in particular: the default identity a container invents
       when nothing configured one.
    2. THE AUTHOR-DATE OFFSET, against the declared timezone at that
       instant. This is the field commit-identity.sh either ENFORCES or
       merely guesses at depending on whether an identity is declared, so
       drift here is the guess having been wrong, silently, in the past
       tense.
    3. A TRACKED settings.json naming GIT_AUTHOR_NAME or GIT_AUTHOR_EMAIL.
       `no-hardcoded-git-identity` already checks this -- in a repo that
       runs precedent_check.py. The repository where it was actually found
       was a consumer, reported by hand, by a session that happened to
       look, so asking it of every repo in force is the half that was
       missing.

    Never a finding on somebody else's authorship, and never a claim about
    a repo whose identity cannot be read: both come back as notes."""
    repo_dir = pathlib.Path(repo_dir)
    rows, notes = [], []
    try:
        import precedent_identity as pi
        declared = pi.declared_identity(str(repo_dir)) or {}
    except Exception as exc:                                  # noqa: BLE001
        declared = {}
        notes.append(f'could not read a declared identity here '
                     f'({type(exc).__name__}), so authorship is reported '
                     f'without one to compare against')
    email = (declared.get('email') or '').strip().lower()
    tzname = (declared.get('timezone') or '').strip()

    rc, out, _err = _run_git(repo_dir, 'log', f'--since={days} days ago',
                             f'--max-count={cap}', '--no-merges',
                             '--pretty=format:%H%x09%an%x09%ae%x09%aI')
    if rc != 0:
        notes.append('git log could not be read here')
        return rows, notes
    commits = [l.split('\t') for l in out.split('\n') if l.count('\t') == 3]
    if not commits:
        notes.append(f'no commits in the last {days} days to read')
        return rows, notes

    # 1 -- who wrote them
    others, anonymous = {}, []
    for sha, name, mail, _when in commits:
        low = (mail or '').strip().lower()
        if email and low == email:
            continue
        # The shapes a container invents when nothing configured an
        # identity. Matched on the ADDRESS, never the name: a person may
        # legitimately be called root somewhere, and nobody's real address
        # ends in .(none).
        if (not low or low.endswith('.(none)') or low.endswith('@localhost')
                or '@' not in low):
            anonymous.append((sha[:9], name, mail))
        else:
            others[low] = others.get(low, 0) + 1
    if anonymous:
        rows.append(('FINDING', f'{len(anonymous)} commit(s) authored with no '
                                f'configured identity -- the address a '
                                f'container invents when nothing set one: '
                                + ', '.join(f'{s} <{m}>'
                                            for s, _n, m in anonymous[:3])))
    if others:
        notes.append('other authors in the window (not a finding): '
                     + ', '.join(f'{k} x{v}' for k, v in
                                 sorted(others.items(), key=lambda x: -x[1])[:5]))

    # 2 -- the author-date offset against the declared timezone
    if not (email and tzname):
        notes.append('no declared email and timezone here, so the '
                     'author-date offset was not checked -- unverified, not '
                     'clean')
    else:
        try:
            from zoneinfo import ZoneInfo
            zone = ZoneInfo(tzname)
        except Exception as exc:                              # noqa: BLE001
            zone = None
            notes.append(f'timezone {tzname!r} could not be loaded '
                         f'({type(exc).__name__}: no tzdata here?), so the '
                         f'offset was not checked')
        if zone is not None:
            wrong = []
            for sha, _name, mail, when in commits:
                if (mail or '').strip().lower() != email:
                    continue
                try:
                    stamp = datetime.datetime.fromisoformat(when)
                except ValueError:
                    continue
                if stamp.utcoffset() is None:
                    continue
                expected = stamp.astimezone(zone).utcoffset()
                if expected != stamp.utcoffset():
                    # str(timedelta) renders -03:00 as "-1 day, 21:00:00",
                    # which is the correct value and an unreadable one. One
                    # formatter for this quantity, here
                    # (practice: one-formatter-per-quantity).
                    total = int(expected.total_seconds())
                    sign = '-' if total < 0 else '+'
                    total = abs(total)
                    wrong.append((sha[:9], when,
                                  f'{sign}{total // 3600:02d}:'
                                  f'{(total % 3600) // 60:02d}'))
            if wrong:
                rows.append(('FINDING', f'{len(wrong)} commit(s) carry an '
                                        f'author-date offset that is not '
                                        f'{tzname} at that moment (first: '
                                        f'{wrong[0][0]} at {wrong[0][1]}, '
                                        f'expected {wrong[0][2]})'))
            else:
                rows.append(('OK', f'every commit of the declared person in '
                                   f'the window carries the {tzname} offset '
                                   f'for its own moment'))

    # 3 -- a tracked settings.json that hardcodes somebody
    for rel in ('.claude/settings.json', '.claude/settings.local.json'):
        f = repo_dir / rel
        if not f.is_file():
            continue
        if rel.endswith('local.json'):
            continue                      # untracked and per-machine by design
        try:
            env = (json.loads(f.read_text(encoding='utf-8')).get('env')
                   or {})
        except (OSError, ValueError):
            continue
        named = [k for k in ('GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL')
                 if env.get(k)]
        if named and not (repo_dir / 'identity.json').is_file():
            rows.append(('FINDING', f'{rel} hardcodes {" and ".join(named)} '
                                    f'in its tracked env block -- every '
                                    f'session and every collaborator who '
                                    f'loads this file commits as that one '
                                    f'person, because GIT_AUTHOR_* outranks '
                                    f'`git config user.*`'))
        elif named:
            notes.append(f'{rel} names {" and ".join(named)}, and a root '
                         f'identity.json says this repo IS that person\'s '
                         f'own source -- the documented, correct case')
    return rows, notes


def _config_key_reads(repo_dir, others=()):
    """-> (rows, note). Every key a repo DECLARES in its own config, and
    which tool source mentions it.
    (practice: very-deep-check, pass 2, beside the duplicate question)

    THE INCIDENT (spec/CI_MINUTES_PLAN.md item 15, corrected 2026-09-21).
    The plan told a session to set `ci_workflows: disabled` in a consuming
    repo's precedent.json and then delete a workflow. `ci_preference()`
    resolves that key from an individual or team SOURCE's identity.json and
    never from a consumer's precedent.json, so the key would have been read
    by nothing, and the deletion would have carried a commit message
    claiming a toggle permitted it. A session read the engine and refused.
    The next one might not.

    A key nobody reads is not a typo, it is a BELIEF -- somebody wrote it
    expecting it to do something, and the file goes on looking exactly as
    intentional as a live one, forever. That is the same shape as an
    orphan, which this check already sweeps for files.

    IT CITES AND DOES NOT JUDGE, for the reason INCIDENT COVERAGE does:
    a key name appearing in a tool's source proves something mentions it,
    never that this file is where it is read from -- which is precisely the
    distinction the incident above turned on. The reading is the session's;
    what this removes is assembling the list.

    Keys beginning with `_` are skipped: this tree uses them for comments,
    by convention, and they are not read by design."""
    repo_dir = pathlib.Path(repo_dir)
    # THE CORPUS IS NOT JUST tools/*.py, AND THAT WAS THIS CHECK'S OWN FIRST
    # FALSE POSITIVE. Run against tools/ alone, it reported
    # `stale_checkout_hours` as read by nothing -- and it is read, by
    # `freshness-guard.sh`, a HOOK. A config key is consumed by whatever
    # runs, in whatever language, so the corpus is every script a repo
    # carries: its tools, its hooks, its bootstrap, and the harness
    # templates it ships. Caught before this shipped, by checking the one
    # finding the first run produced rather than relaying it -- a detector
    # that cries wolf on its first real run is one nobody runs twice.
    roots = [repo_dir / 'tools', repo_dir / '.claude',
             repo_dir / 'bootstrap', repo_dir / 'templates']
    if not (repo_dir / 'tools').is_dir():
        roots.append(ROOT / 'tools')
    corpus = {}
    for root in roots:
        if not root.is_dir():
            continue
        for f in sorted(root.rglob('*')):
            if f.is_file() and f.suffix in ('.py', '.sh'):
                try:
                    corpus[str(f.relative_to(repo_dir))
                           if repo_dir in f.parents or f.is_relative_to(repo_dir)
                           else f.name] = f.read_text(encoding='utf-8')
                except (OSError, UnicodeDecodeError, ValueError):
                    continue
    if not corpus:
        return [], 'no tool or hook sources to read the keys against'
    rows = []
    for name in ('precedent.json', 'identity.json'):
        f = repo_dir / name
        if not f.is_file():
            continue
        try:
            doc = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            rows.append((name, '(unreadable)', [], []))
            continue
        if not isinstance(doc, dict):
            continue
        for key in sorted(doc):
            if key.startswith('_'):
                continue
            where = sorted(n for n, text in corpus.items()
                           if f"'{key}'" in text or f'"{key}"' in text)
            elsewhere = []
            if not where:
                # A KEY READ BY NOTHING HERE IS NOT THE SAME AS A KEY READ
                # BY NOTHING, and the difference is a whole class. One
                # source declares `grandfathered_commit_shas` and its
                # readers live in a DIFFERENT repo in force -- which may be
                # exactly right, since a private check can run against
                # every repo. Saying which repo mentions it is what makes
                # that row decidable instead of alarming.
                for label, other in others:
                    other = pathlib.Path(other)
                    if other == repo_dir or not other.is_dir():
                        continue
                    hit = False
                    for root in ('tools', '.claude', 'bootstrap'):
                        d = other / root
                        if not d.is_dir():
                            continue
                        for g in d.rglob('*'):
                            if (g.is_file() and g.suffix in ('.py', '.sh')):
                                try:
                                    text = g.read_text(encoding='utf-8')
                                except (OSError, UnicodeDecodeError):
                                    continue
                                if f"'{key}'" in text or f'"{key}"' in text:
                                    hit = True
                                    break
                        if hit:
                            break
                    if hit:
                        elsewhere.append(label)
            rows.append((name, key, where, elsewhere))
    return rows, ''


_MOVED_CLAIM = re.compile(
    # `see X` is DELIBERATELY NOT HERE. It was, for one measurement: it
    # produced 11 rows in this repo and 28 in a source, and every one was a
    # pointer rather than a claim -- a fixture's invented path, a template
    # describing the repo it will be installed into, a vendored tool citing
    # a document that lives upstream. "See X" says where to look; it does
    # not assert that work moved there, which is the class this exists for,
    # and its bare-name half is already doc_lint's unlinked-reference
    # warning.
    r'(?P<claim>now runs? (?:as \w+ )?in|now lives? in|has moved to|'
    r'moved into|folded into|superseded by|replaced by)\s+'
    r'[`\[(]*'
    r'(?P<target>(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+'
    r'\.(?:md|py|sh|yml|yaml|json|template))',
    re.IGNORECASE)


def _moved_claims(repo_dir, cap=40):
    """-> [(file, line number, claim, target)] for sentences that say the
    work moved SOMEWHERE, where the somewhere is not there -- or None when
    this could not be established at all, which is NOT the same as [].
    (practice: very-deep-check, pass 3)

    THE INCIDENT (2026-09-21). `commit-identity.yml` was paused, its header
    saying its checks "now run as steps in
    .github/workflows/precedent-check.yml's single job". Four hours later a
    refresh deleted that file from all four sets. The sentence was true when
    it was written and false the same afternoon, and nothing looked, because
    a claim about a DIFFERENT file is only ever caught by somebody who
    happens to open that file.

    A grep would have found it at any point in the following month. Nothing
    ran one, because nothing was looking for the sentence shape.

    WHAT IT DOES NOT COVER, said plainly: a destination that exists but no
    longer does the thing (doc_lint catches neither, and pass 3's
    documents-against-mechanisms bullet is the read that does). This asks
    the cheap half -- is the named file even there -- which is the half
    that produced the incident."""
    repo_dir = pathlib.Path(repo_dir)
    files = list(_tracked_text_files(repo_dir))
    # EVERY BASENAME IN THE TREE, not just the tracked text ones: a claim
    # naming `precedent_resolve.py` when the file is `tools/precedent_
    # resolve.py` is under-qualified, which doc_lint already warns about as
    # an unlinked reference. It is not this check's class, and reporting it
    # here buries the one row that is. Measured on the first run: of 40
    # rows, all but a handful were this and the markdown-link case below.
    # A FAILED READ IS NOT AN EMPTY TREE, and this set is a SUPPRESSION:
    # a target found among these basenames is a file named without its
    # path, which the loop below skips. Coerce the failure to an empty set
    # and the suppression silently disappears, so every under-qualified
    # name becomes a row claiming no such file exists -- findings
    # manufactured out of a read that did not happen. That is the same
    # defect the endgame rehearsal carried into six red CI runs, in a
    # different function: `git ls-files` failing there made every file on
    # the integration branch look silently dropped. Found by sweeping for
    # the pattern afterwards rather than by anything going wrong here
    # (practice: control-asserts-which-failure -- a guard that cannot
    # establish its own inputs says so, never returns a result).
    rc, out_ls, _e = _run_git(repo_dir, 'ls-files')
    if rc != 0:
        return None
    basenames = {pathlib.PurePosixPath(x).name
                 for x in out_ls.splitlines()}
    # THIS REPO WROTE IT vs THIS REPO RECEIVED IT, which is pass 2's own
    # first question applied here. A vendored engine file's comments are
    # UPSTREAM's prose, citing upstream's paths, and a repo that received
    # the copy can neither fix nor be blamed for them -- reporting those
    # rows makes a check that produces permanently unactionable findings,
    # which is the one shape people learn to ignore.
    vendored = set()
    try:
        _m = json.loads((repo_dir / 'tools' / 'ENGINE_MANIFEST.json')
                        .read_text(encoding='utf-8'))
        vendored = {f'tools/{n}' for n in (_m.get('files') or [])}
    except (OSError, ValueError):
        pass
    out = []
    for rel, text in files:
        if rel in vendored:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            # A markdown link carries its own target and doc_lint checks
            # that target; matching the link TEXT would report the label.
            bare = re.sub(r'\[[^\]]*\]\([^)]*\)', ' ', line)
            for m in _MOVED_CLAIM.finditer(bare):
                target = m.group('target')
                here = (repo_dir / target)
                beside = (repo_dir / rel).parent / target
                if here.exists() or beside.exists():
                    continue
                if pathlib.PurePosixPath(target).name in basenames:
                    continue              # exists, just named without its path
                out.append((rel, i, m.group('claim').strip(), target))
                if len(out) >= cap:
                    return out
    return out


def _check_coverage(repo_dir, timeout=300):
    """-> (summary dict, note) -- what every registered check ACTUALLY did
    in this repo, not what its practice claims.
    (practice: very-deep-check, pass 2 questions 14 and 15)

    QUESTION 15 ASKS WHETHER A CHECK EVER RUNS HERE, and says to enumerate
    rather than sample, for every registered check in every repo in force.
    It had no mechanism, so it was a read nobody could finish: one repo's
    output at a time, by hand, with the comparison held in a session's
    head. This is the enumeration.

    THE SHAPE THE ANSWER TAKES IS THE FINDING. A team source measured
    2026-09-12 ran 12 checks and skipped 42, and **every one of the 42 had
    the same cause** -- each check is keyed to a `practices/<slug>.md` the
    set does not carry, because a source set's practices/ holds its own
    level only. One cause, 42 silent skips, and among them the rule
    governing what a published practice file may link. So the grouping by
    CAUSE is the point, not the count: forty skips for one structural
    reason is a different problem from forty for forty reasons.

    IT RUNS THE REPO'S OWN COPY, deliberately -- a consuming repo runs the
    engine it vendored, not this checkout's, and asking this checkout's
    copy what happens there would answer about the wrong code.

    A skip is not a pass, and neither is a repo that could not be asked."""
    repo_dir = pathlib.Path(repo_dir)
    own = repo_dir / 'tools' / 'precedent_check.py'
    if not own.is_file():
        return None, 'no tools/precedent_check.py here -- nothing registered'
    try:
        proc = subprocess.run([sys.executable, str(own), '--full-sweep'],
                              cwd=str(repo_dir), capture_output=True,
                              text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f'could not run it here ({type(exc).__name__})'
    body = (proc.stdout or '') + (proc.stderr or '')
    skipped, violated = {}, []
    for line in body.splitlines():
        if line.startswith('SKIPPED'):
            rest = line[len('SKIPPED'):].strip()
            slug = rest.split(None, 1)[0] if rest else '?'
            why = ''
            for sep in ('—', '--'):
                if sep in rest:
                    why = rest.split(sep, 1)[1].strip()
                    break
            skipped[slug] = why
        elif line.startswith('VIOLATION'):
            rest = line[len('VIOLATION'):].strip()
            violated.append(rest.split(None, 1)[0] if rest else '?')
    counts = {}
    m = re.search(r'precedent_check: (\d+) passed, (\d+) violated, '
                  r'(\d+) advisory, (\d+) errored, (\d+) skipped', body)
    if m:
        counts = dict(zip(('passed', 'violated', 'advisory', 'errored',
                           'skipped'), (int(x) for x in m.groups())))
    # Group by CAUSE, coarsely: the first clause of the reason, which is
    # what distinguishes "one structural reason" from "forty reasons".
    causes = {}
    for _slug, why in skipped.items():
        key = (why.split(',')[0].split(' -- ')[0].strip() or 'no reason given')
        # NORMALISE THE SLUG OUT, or the grouping defeats itself: 42 skips
        # reading "no practices/<a>.md", "no practices/<b>.md" ... are ONE
        # structural cause wearing 42 names, and reporting them apart is
        # exactly the shape that hid the real finding in the first place.
        key = re.sub(r'practices/[A-Za-z0-9._-]+\.md',
                     'practices/<slug>.md', key)
        key = re.sub(r'\btools/checks/[A-Za-z0-9._-]+', 'tools/checks/<file>',
                     key)
        causes[key] = causes.get(key, 0) + 1
    return {'counts': counts, 'violated': violated, 'skipped': len(skipped),
            'causes': causes}, ''


def _job_count(path):
    """-> how many jobs a workflow file defines, or None.

    PyYAML where it exists, a structural count where it does not -- the same
    split, for the same reason, as workflow-yaml-github-can-parse: CI
    installs no PyYAML, and a section that silently declines in the one
    environment that gates every pull request is not a section."""
    try:
        text = pathlib.Path(path).read_text(encoding='utf-8')
    except OSError:
        return None
    try:
        import yaml
        doc = yaml.safe_load(text)
        jobs = doc.get('jobs') if isinstance(doc, dict) else None
        if isinstance(jobs, dict):
            return len(jobs)
    except Exception:                                         # noqa: BLE001
        pass
    n, inside = 0, False
    for line in text.splitlines():
        if re.match(r'^jobs:\s*$', line):
            inside = True
            continue
        if inside and re.match(r'^[A-Za-z]', line):
            break
        if inside and re.match(r'^  [A-Za-z0-9_-]+:\s*$', line):
            n += 1
    return n or None


def _actions_bill(repo_dir, days=30):
    """-> (rows, total_minutes, note) -- what this repo's workflows cost at
    GitHub's per-job floor over a window.
    (practice: very-deep-check, the closing budget section)

    THE RUN ALREADY READS ITS OWN GITHUB API BILL and read nothing about the
    bill that has actually been hurting. spec/CI_MINUTES_PLAN.md item 15
    measured a 13-second job billed as a minute, 14 times a day, in one
    repository: about 420 minutes a month with nothing misconfigured, the
    floor being the entire cost. That number was found by a session doing a
    one-off audit, and a number found once is a number that goes stale.

    WHAT IT COMPUTES, AND WHAT IT DOES NOT. GitHub bills a whole minute per
    JOB, so the floor is runs x jobs -- both of which are cheap to get: the
    run count from one API call per workflow with a `created` filter, the
    job count by reading the workflow file. **It is a floor, not an
    invoice**: real minutes are at least this and usually more, and whether
    they are billed at all depends on the repository being private. The
    useful number was never the invoice anyway -- item 13 and item 15 both
    landed on JOB COUNT as the only lever that moved, which is exactly what
    this makes visible per workflow."""
    repo_dir = pathlib.Path(repo_dir)
    wf_dir = repo_dir / '.github' / 'workflows'
    if not wf_dir.is_dir():
        return [], 0, 'no .github/workflows/ here'
    slug = _github_slug(repo_dir)
    if not slug:
        return [], 0, 'origin is not GitHub, so run counts cannot be asked'
    data, err = _api_json(f'repos/{slug}/actions/workflows')
    if err or not isinstance(data, dict) or 'workflows' not in data:
        return [], 0, (f'could not list workflows for {slug} -- '
                       f'{err or str(data)[:80]}')
    since = precedent_time.date_from_unix(time.time() - days * 86400)
    rows, total = [], 0
    for w in (data.get('workflows') or []):
        rel = w.get('path') or ''
        local = repo_dir / rel
        jobs = _job_count(local) if local.is_file() else None
        runs, rerr = _api_json(
            f'repos/{slug}/actions/workflows/{w.get("id")}/runs'
            f'?per_page=1&created=%3E%3D{since}')
        count = (runs or {}).get('total_count') if not rerr else None
        if count is None or jobs is None:
            rows.append((rel, count, jobs, None,
                         'run count or job count unknown'))
            continue
        floor = count * jobs
        total += floor
        rows.append((rel, count, jobs, floor, ''))
    return rows, total, ''


def _carry_through(repo_dir):
    """-> (status, lines) for one repo: how far its VENDORED engine is
    behind the upstream it was vendored from.
    (practice: very-deep-check, order of operations step 1)

    CURRENT IS NOT THE SAME AS CARRIED, and this is the half nothing else
    here asks. The freshness gate above proves a clone matches ITS OWN
    origin -- a repo can be perfectly current with itself and be running an
    engine from three weeks ago, because a fix merged upstream reaches an
    installed repo only when somebody goes there and runs "Update Vendors".
    Measured 2026-09-20: 18 of 22 repositories had never taken one.

    That is also the structural reason a very deep check had never once
    found a stale vendored tree. Not a gap in its passes -- a gap in what
    any pass could see, since every pass reads one repository against
    itself (todo-2026-09-21-nothing-checks-a-consumer-against-upstream.md).

    A REMOVAL IS NAMED, NOT COUNTED. Among the three kinds of drift, a file
    upstream DELETED is the one whose arrival breaks something here, so the
    line prints those names while the other two get counts.

    SCOPE IS THE REPOS THIS RUN ALREADY OPENS -- this checkout and every
    attached source. The fleet version of this question, every Precedent
    repo the person owns, is chief-of-staff's, and widening it here would
    duplicate that practice while making an expensive check more expensive
    for no new judgment."""
    try:
        import precedent_engine_freshness as pef
    except ImportError:
        return 'unverified', ['precedent_engine_freshness did not import']
    manifest, why = pef.read_manifest(repo_dir)
    if manifest is None:
        return 'n/a', [why]
    url = manifest.get('source_repo')
    branch = manifest.get('source_branch')
    recorded = manifest.get('source_commit')
    if not (url and branch and recorded):
        return 'unverified', ['the manifest records no source_repo/'
                              'source_branch/source_commit, so what it was '
                              'vendored from cannot be asked']
    tip = pef.upstream_tip(url, branch)
    if tip is None:
        return 'unverified', [f'could not reach {url} ({branch}) -- whether '
                              f'this engine is current is unknown, which is '
                              f'not the same answer as current']
    if tip == recorded:
        return 'current', [f'vendored engine matches {branch} at '
                           f'{recorded[:12]}']
    lines = [f'vendored {recorded[:12]}; upstream {branch} is at {tip[:12]}']
    result = pef.changed_files(repo_dir, url, recorded, tip,
                              manifest.get('files') or [])
    if result is None:
        lines.append('could not fetch upstream objects, so WHICH files moved '
                     'is unknown -- the commit difference still stands')
        return 'behind', lines
    added, removed, changed = result
    new_here = [n for n in added if 'NOT YET VENDORED HERE' in n]
    lines.append(f'{len(added)} added upstream ({len(new_here)} of them not '
                 f'vendored here), {len(changed)} changed, '
                 f'{len(removed)} removed')
    if removed:
        lines.append('REMOVED upstream, and still on disk here until a '
                     'refresh: ' + ', '.join(removed[:6])
                     + (f' (+{len(removed) - 6} more)' if len(removed) > 6
                        else ''))
    return 'behind', lines


def _workflow_reality(repo_dir, max_workflows=25):
    """-> [(verdict, message)] for one repo, asking GITHUB what it knows
    about each workflow file in the tree. (practice: very-deep-check, pass 2)

    THE CLASS THIS EXISTS FOR. Everything else in this tool reads the
    repository against itself, and a workflow has a second existence nothing
    local can see. A file GitHub's parser REFUSES does not go red -- it does
    not appear at all, so the branch reads as having no CI rather than broken
    CI (gotcha-2026-09-21-github-actions-rejects-yaml-anchors-python-accepts).
    Actions switched off looks, from the tracked tree, exactly like working
    CI. A trigger that stopped matching looks like nothing whatsoever.

    Four questions, in cost order: is the file registered with Actions at
    all; is it active; when did it last run; does that run postdate the
    file's newest commit.

    THE HONEST LIMITS, reported rather than assumed away:

    - GitHub lists workflows from the DEFAULT BRANCH. A file that exists only
      on this branch is correctly absent from the listing, so absence is a
      FINDING only when the file is also on the default branch, and a NOTE
      otherwise. Getting this backwards would make every feature branch look
      broken.
    - A workflow that has never run cannot be told apart from Actions being
      disabled by this endpoint alone, which is why the disabled case is read
      off the listing call's own error rather than inferred from silence
      (gotcha-2026-09-21-actions-permissions-are-unreadable-from-a-session:
      GET /repos/{owner}/{repo}/actions/permissions is unreachable from a
      session, so this is the route that remains).
    - Everything here needs a credential. Unauthenticated, a private repo
      answers Not Found, which is not the same answer as "no workflows", so
      the failure is reported as UNVERIFIED and never as clean."""
    repo_dir = pathlib.Path(repo_dir)
    wf_dir = repo_dir / '.github' / 'workflows'
    local = sorted(x for x in wf_dir.iterdir()
                   if x.suffix in ('.yml', '.yaml')) if wf_dir.is_dir() else []
    if not local:
        return []
    slug = _github_slug(repo_dir)
    if not slug:
        return [('UNVERIFIED', 'origin is not GitHub, so nothing here can be '
                               'asked about these workflow files')]
    data, err = _api_json(f'repos/{slug}/actions/workflows')
    if err or not isinstance(data, dict):
        return [('UNVERIFIED', f'could not list workflows for {slug}: '
                               f'{err or "unexpected response"} -- NOT the '
                               f'same as having none')]
    if 'workflows' not in data:
        # TWO UNLIKE REFUSALS ARRIVE HERE AND MUST NOT BE REPORTED AS ONE.
        # The 403 body for a repo with Actions switched off says so in as
        # many words, and that is the one place this session can read that
        # fact. Everything else -- a repo this session was never granted,
        # a private repo asked without a credential -- is the check failing
        # to look, which is not a finding about the repo
        # (practice: diagnosis-is-measured; the misreading has its own
        # gotcha: a session read "access to this repository is not enabled"
        # as a token problem and went hunting for a credential that was
        # fine).
        msg = str(data.get('message') or data)[:160]
        low = msg.lower()
        if 'actions' in low and ('disabled' in low or 'not allowed' in low):
            return [('FINDING', f'{slug}: Actions is off -- "{msg}". A repo '
                                f'with workflow files committed and Actions '
                                f'off looks, from the tree, exactly like a '
                                f'repo with working CI')]
        return [('UNVERIFIED', f'{slug}: could not list workflows -- '
                               f'"{msg}". That is this session failing to '
                               f'look, not a fact about the repo')]
    registered = {w.get('path'): w for w in (data.get('workflows') or [])
                  if isinstance(w, dict)}
    default_branch = _default_remote_branch(repo_dir)
    out = []
    for path in local[:max_workflows]:
        rel = f'.github/workflows/{path.name}'
        meta = registered.get(rel)
        if meta is None:
            on_default = False
            if default_branch:
                rc, _o, _e = _run_git(repo_dir, 'cat-file', '-e',
                                      f'origin/{default_branch}:{rel}')
                on_default = rc == 0
            if on_default:
                out.append(('FINDING', f'{rel}: on origin/{default_branch} '
                                       f'and NOT registered with Actions. '
                                       f'GitHub parses workflow files when '
                                       f'it receives them and silently keeps '
                                       f'none it rejects, so this file is '
                                       f'running nowhere and reporting '
                                       f'nothing'))
            else:
                out.append(('NOTE', f'{rel}: not registered, and not on '
                                    f'origin/{default_branch or "(unknown)"} '
                                    f'either -- Actions lists the default '
                                    f'branch, so this is expected, not a '
                                    f'finding'))
            continue
        state = str(meta.get('state') or 'unknown')
        if state != 'active':
            out.append(('FINDING', f'{rel}: registered but state is '
                                   f'{state!r} -- it is committed, it looks '
                                   f'live in the tree, and it does not run'))
        runs, rerr = _api_json(
            f'repos/{slug}/actions/workflows/{meta.get("id")}/runs?per_page=1')
        newest = None
        if not rerr and isinstance(runs, dict):
            rows = runs.get('workflow_runs') or []
            if rows:
                newest = str(rows[0].get('created_at') or '')[:10]
        if rerr:
            out.append(('UNVERIFIED', f'{rel}: could not read its runs -- '
                                      f'{rerr}'))
            continue
        edited = _last_commit(repo_dir, rel)
        edited_day = _stamp(edited[0])[:10] if edited else None
        if newest is None:
            out.append(('NOTE', f'{rel}: registered and active, and has '
                                f'never run. Either nothing has matched its '
                                f'triggers yet or it is newer than the last '
                                f'event -- read it, do not assume'))
        elif edited_day and newest < edited_day:
            out.append(('FINDING', f'{rel}: last run {newest}, last edited '
                                   f'{edited_day}. Every event since the '
                                   f'edit either did not match its triggers '
                                   f'or did not reach it'))
    if len(local) > max_workflows:
        out.append(('UNVERIFIED', f'{len(local) - max_workflows} more '
                                  f'workflow file(s) not asked about this '
                                  f'run -- the per-repo cap is '
                                  f'{max_workflows}, to bound the API bill'))
    if not out:
        # A clean repo must not return the same empty list as a repo with no
        # workflows at all: this section's whole subject is a thing that is
        # silent when broken, so "asked and clean" has to be distinguishable
        # from "never asked" in the row itself, not in the caller's memory.
        out.append(('OK', f'{len(local)} workflow file(s): each registered '
                          f'with Actions, active, and run since it was last '
                          f'edited'))
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
    """-> sorted [(phrase, slug)] for every active practice that declares a
    `command:` field -- the phrases a person SAYS.

    The field is the test, and it is the same field tools/precedent_vocabulary.py
    reads to build the page this scan checks. Until 2026-09-14 this function
    used a different test -- any capitalized `defines:` entry -- on the
    reasoning that only a spoken phrase is capitalized. That held for the four
    commands that existed when it was written and failed the first time a
    practice defined a capitalized TERM ("API budget", "Relayed authorization"):
    this scan reported two commands missing from DAILY_HABITS.md while
    doc_sync, reading the real field, reported the page current. Two
    definitions of one thing, one of them wrong (practice: very-deep-check,
    pass 2 question 8). A phrase in `command:` and nowhere else is still a
    command; a capitalized term in `defines:` alone is not.
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
            raw = fm.get('command')
            if not raw or raw == 'null':
                continue
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except ValueError:
                    # A malformed field is precedent_vocabulary.py's to
                    # report; here it is simply not a readable command.
                    continue
            phrases = raw.keys() if isinstance(raw, dict) else raw
            for phrase in phrases:
                if isinstance(phrase, str) and phrase.strip():
                    found.append((phrase.strip(), fm.get('slug', f.stem)))
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
# code-cites-practice: session-load-budget -- the registry owns it.
_SECTION_FLAG_TOKENS = bv._budget('section_review_tokens', 2500)
# A live entry claiming its own trap is fixed is the archive candidate this
# whole pass exists to surface -- the entry is the thing that knows.
_SETTLED_MARKERS = ('fixed ', 'no longer true', 'applies itself now',
                    'resolved for this machine', 'now automated')


def _declared_ceilings(root):
    """-> {surface path: ceiling} from THIS repo's own budget registry, or {}.

    Each measured repo's own `tools/session_load_budgets.json`, never this
    checkout's: a source set declares its own ceilings for its own always-loaded
    files, and comparing one repo's surfaces against another's numbers would be
    worse than not checking at all. `bv._budget` deliberately reads BestPractice's
    copy for the engine-wide thresholds (`section_review_tokens`), which is a
    different question and stays where it is.
    """
    f = pathlib.Path(root) / 'tools' / 'session_load_budgets.json'
    try:
        reg = json.loads(f.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    out = {}
    for rel, entry in (reg.get('surfaces') or {}).items():
        if isinstance(entry, dict) and isinstance(entry.get('ceiling'), int):
            out[rel] = entry['ceiling']
    return out


def _split_projection(section):
    """-> a costed line for the SPLIT move, or '' when the section has no
    bulleted entries to split.

    WHY A PROJECTION AND NOT JUST ADVICE. Told a section is 8,858 tokens and
    that splitting is an option, a person still cannot choose: the question is
    always "what would that leave, and what would it cost me". Deriving that
    by hand is what made the 2026-09-13 decision take a whole pass -- the
    figures existed only because a session computed them on request, and the
    deep read that flagged the section could have handed them over.

    Four rows rather than one, because the honest choice is graduated: keeping
    the bolded lead alone is the cheapest and loses the most, and each extra
    sentence buys back context. Mechanically truncated, so these BOUND the
    saving rather than predict it -- a careful edit keeps the remedy line
    wherever it sits, and the output says so.
    """
    entries = _md_bullet_entries(section)
    if len(entries) < 8:
        return ''
    whole = bv._approx_tokens(section)
    rows = []
    for keep in (0, 1, 2, 3):
        tot = 0
        for _line, _title, body in entries:
            m = re.match(r'- \*\*(.*?)\*\*(.*)', body, re.S)
            if not m:
                tot += bv._approx_tokens(body)
                continue
            lead = ' '.join(m.group(1).split())
            rest = ' '.join(m.group(2).split())
            sents = re.split(r'(?<=[.?!]) ', rest) if rest else []
            tot += bv._approx_tokens(lead + ' ' + ' '.join(sents[:keep]))
        rows.append((keep, tot))
    out = [f'\n      COSTED, if you split this one ({len(entries)} entries, '
           f'{whole:,} tokens now). Mechanically\n      truncated, so each '
           f'bounds the saving rather than predicting it:']
    for keep, tot in rows:
        what = 'bolded lead only' if keep == 0 else \
            f'lead + {keep} sentence' + ('' if keep == 1 else 's')
        out.append(f'        {what:<22} leaves {tot:6,d}   saves {whole - tot:6,d}')
    out.append('      The text moves out whole either way; only the loading '
               'changes.')
    return '\n'.join(out)


def _gotchas_section(text):
    """-> the gotchas section of an instructions file, or None if it has none.

    One extractor, so the two passes that read that section cannot disagree
    about where it starts and stops.
    """
    head = re.search(r'(?m)^#{2,4}\s*.*' + re.escape(_GOTCHA_HEADING) + r'.*$',
                     text, re.I)
    if not head:
        return None
    after = re.search(r'(?m)^#{1,4}\s', text[head.end():])
    return text[head.start():head.end() + (after.start() if after else len(text))]


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

    AND SEPARATELY, whether each FILE is inside the ceiling its own repo
    declared for it -- read from that repo's tools/session_load_budgets.json,
    alongside the section findings and never instead of them. The two answer
    different questions, which is why both are here: a fat section is a
    reading-cost problem somebody may reasonably decide to live with, and a
    file over its ceiling is a budget somebody already decided being broken.
    Nothing in a consuming repo was asking the second one. Measured
    2026-09-22, in precedent-individual: AGENTS.md at 2,276 tokens against a
    declared 1,800 -- 476 tokens, 26% over -- with every check green,
    because the overage was spread across five sections and the largest of
    them was 990. This pass would have reported ZERO findings on it. The one mechanism that does
    compare a file to its ceiling, precedent_check.py's session-load-budget,
    skips in any repo that does not carry the practice FILE -- and that repo
    declared ceilings without carrying it. It surfaced because somebody ran
    tools/session_load_trend.py by hand, which is not a mechanism.

    THE TRAP TO AVOID, stated here because the obvious use of this output is
    the wrong one: **do not optimise for the total.** Gotchas exist because
    sessions kept burning hours on the same environment traps, and a trimming
    pass that chases the number deletes the entries that are working. The
    question for each section is "would a session hit this today", never "how
    big is it". The ceiling finding does not soften that: what it asks for is
    reduction-pass's menu -- delete what is duplicated, retire what cannot
    happen, split what is still live and still long -- and never a raise.
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
    file_totals = {}
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
            file_totals[fname] = file_totals.get(fname, 0) + n
            rows.append((fname, name, n))
            if n >= _SECTION_FLAG_TOKENS:
                findings.append(
                    f'REVIEW   {fname} :: {name}\n'
                    f'      {n:,} tokens, every session, before any work starts.\n'
                    f'      Ask of each part: would a session hit this TODAY? Then '
                    f'three moves,\n      in this order (session-load-budget):\n'
                    f'        DELETE what is duplicated somewhere the session '
                    f'already reads --\n                and check that it really '
                    f'is, word for word. See DUPLICATED below.\n'
                    f'        RETIRE what can no longer happen, to a linked record, '
                    f'IN FULL,\n                with the verdict that retired it.\n'
                    f'        SPLIT what is still live and still long: one line per '
                    f'item here,\n                the text moved out whole. Nothing '
                    f'is shortened on its way out,\n                and whatever '
                    f'checked the text has to follow it.'
                    + _split_projection(body))

    # THE FILE AGAINST ITS OWN DECLARED CEILING -- see the docstring for the
    # measurement that went silent. Every declared surface, not only the ones
    # the loop above walked: CLAUDE.md is skipped up there when it is a bare
    # @AGENTS.md include, so that its tokens are not counted twice into the
    # total, and it still carries a ceiling of its own that something has to
    # test.
    over = []
    for rel, ceiling in sorted(_declared_ceilings(root).items()):
        n = file_totals.get(rel)
        if n is None:
            f = root / rel
            if not f.is_file():
                continue
            n = bv._approx_tokens(f.read_text(encoding='utf-8',
                                              errors='replace'))
        if n <= ceiling:
            continue
        over.append(
            f'OVER CEILING {rel}\n'
            f'      {n:,} tokens, every session, against the {ceiling:,} this '
            f'repo declares for it\n      in tools/session_load_budgets.json '
            f'-- over by {n - ceiling:,} ({100.0 * (n - ceiling) / ceiling:.1f}%).\n'
            f'      This is a budget somebody already decided, so it is not a '
            f'judgment call\n      the way a large section is. Work '
            f'reduction-pass\'s menu in order, cheapest\n      and provably '
            f'lossless first: DELETE what is duplicated somewhere the\n'
            f'      session already reads, RETIRE what can no longer happen '
            f'(to a linked\n      record, IN FULL, with the verdict that '
            f'retired it), SPLIT what is still\n      live and still long. '
            f'Then report what moved and what it cost.\n'
            f'      NEVER raise the ceiling to clear this -- '
            f'session-load-budget\'s own line.\n'
            f'      The overage may be spread thin, with no single section '
            f'large enough to\n      appear above; that is the case this '
            f'finding exists for.')

    # A live entry that says its own trap is settled is the strongest
    # mechanical signal available here, and it is the entry's own words.
    #
    # SCOPED TO THE GOTCHAS SECTION, and both halves of that are lessons paid
    # for. This used to scan every bullet in the whole instructions file, which
    # was harmless only while the gotchas were the only bulleted list in it.
    # The 2026-09-13 reduction pass turned the standing commands into bullets
    # too, and the last of them swallowed everything up to the next bullet --
    # 8,582 tokens of resident block, occasion index and quick index reported
    # as one "entry" whose trap was settled. Then the same pass split the
    # gotchas into an index plus record/GOTCHAS.md, and the bodies this reads
    # left the file entirely: the signal went to ZERO findings, which reads
    # exactly like a clean bill of health. Both directions of the same
    # mistake, in one commit -- scanning text this pass does not understand,
    # and not following text it does.
    for fname, text in loaded:
        sec = _gotchas_section(text)
        if sec is None:
            continue
        for _line, _title, entry in _follow_gotcha_index(root, _md_bullet_entries(sec)):
            low = entry.lower()
            if any(k in low for k in _SETTLED_MARKERS):
                findings.append(
                    f'note     {fname}: an entry says its own trap is settled '
                    f'({bv._approx_tokens(entry):,} tokens) --\n'
                    f'      "{_title[:70]}"\n'
                    f'      Verify against the tree before archiving it; an '
                    f'entry\'s claim that it\n      was fixed is not evidence '
                    f'that it was.')

    # DELETE is the first of the three moves and the only one a script can
    # point straight at: text sitting in an always-loaded file that also sits
    # in a practice file the session reaches on demand is paid for twice, and
    # removing it costs a session nothing. Two hand passes over this repo
    # found 903 tokens of it and nothing mechanical was looking.
    #
    # It reports and never edits. Some repetition is deliberate -- a rule
    # sharp enough to be worth saying twice -- and a script cannot tell that
    # from an accident, so the verdict stays a person's.
    try:
        import precedent_check as _pc
        corpus = _pc._practice_corpus(root)
    except Exception:
        corpus = None
    if corpus:
        for fname, text in loaded:
            for src, quote, words in _pc.duplicated_resident_text(
                    root, text, corpus):
                findings.append(
                    f'DUPLICATED {fname}: {words} words also in {src}, which a '
                    f'session\n      reaches on demand -- so this sentence is '
                    f'paid for twice, every\n      session. Deliberate '
                    f'repetition is a real answer; check which it is.\n'
                    f'      "{quote[:72]}..."')
    # Ceilings lead: a section flagged for review is a question, and a surface
    # over a number somebody chose is work.
    return rows, over + findings


# --- gotcha currency (practice: very-deep-check) ------------------------
# WHY A SECOND SIGNAL, when _session_load already flags settled entries.
# That flag is a string match on an entry's SELF-DESCRIPTION, and it works --
# it found three real candidates on 2026-09-11. But it can only find the
# entries honest enough to say "fixed" about themselves. The expensive case is
# the opposite one: an entry that still reads as live while the tree has
# quietly renamed or deleted the remedy it names. **Nothing about that entry's
# prose changes on the day it goes stale**, so no amount of reading it will
# say so.
#
# These three read the TREE against the entry instead, and each is a question
# rather than a verdict:
#   dead remedy    -- a file, check slug or fixture the entry names is gone.
#   no corroboration -- the newest date in the entry is old, and nothing in it
#                    has been re-measured since.
#   tree moved on  -- files the entry names carry commits well after the
#                    entry's own newest date, so its story may describe a
#                    mechanism that has since been replaced.
#
# ALL OF IT IS ADVISORY and none of it archives anything, in the same spirit
# as precedent_retire.py. Every signal here has a legitimate quiet case: an
# entry may name a file that is gone precisely BECAUSE it tells the story of a
# decommission, and an old date on a trap nobody has hit recently is not the
# same as a trap that cannot fire. What this owes a person is the short list
# and what each entry costs, so the reading stays a reading.
#
# It deliberately does NOT re-check what precedent_check.py --only
# environment-gotchas already gates -- that every entry carries its failure
# and not only its fix. That is a per-commit gate on new entries; this is an
# occasional read of old ones.

_GOTCHA_HEADING = 'Build-environment gotchas'
# An entry whose newest date is older than this has not been re-measured in a
# season. That is not evidence of staleness -- it is the absence of evidence
# either way, which is the thing worth a person's eye.
_GOTCHA_STALE_DAYS = 120
# Below this, "the tree moved on" is noise: a file an entry names gets touched
# constantly for reasons that have nothing to do with that entry's trap.
_GOTCHA_TREE_LEAD_DAYS = 45

_GOTCHA_REPO_DIRS = ('tools', 'spec', 'record', 'templates', 'local',
                     'practices', 'documentation', 'deck', 'examples',
                     'process', 'evals', 'decisions', 'philosophy',
                     '.claude', '.github')
_GOTCHA_PATH_IN_TICKS = re.compile(
    r'`((?:' + '|'.join(d.replace('.', r'\.') for d in _GOTCHA_REPO_DIRS) +
    r')/[\w./-]+)`')
_GOTCHA_MD_LINK = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
_GOTCHA_ONLY_SLUG = re.compile(r'--only\s+`?([a-z0-9][a-z0-9-]{2,})`?')
_GOTCHA_FIXTURE = re.compile(r'`(check_[a-z0-9_]+)`')
_GOTCHA_DATE = re.compile(r'\b(20\d\d-\d\d-\d\d)\b')


def _md_bullet_entries(text, line_base=0):
    """-> [(line, title, body)] for a markdown bullet list whose items open
    with a bolded lead, which is the shape both gotcha passes parse.

    One parser for both, deliberately. Two copies of "what counts as an entry"
    would drift and then disagree about the entry count, which is the number
    a person uses to decide the section is under control.
    """
    pos = [m.start() for m in re.finditer(r'(?m)^- \*\*', text)]
    out = []
    for i, p in enumerate(pos):
        body = text[p:pos[i + 1] if i + 1 < len(pos) else len(text)]
        out.append((line_base + text[:p].count('\n') + 1,
                    ' '.join(body[4:].split()), body))
    return out


def _gotcha_check_slugs(repo_dir):
    """-> set of check slugs precedent_check.py will actually answer to, or
    an empty set if it cannot be asked. Empty means the slug signal is
    skipped rather than every slug reported missing -- a check that cannot
    run is not a check that failed."""
    try:
        import precedent_check as _pc
    except Exception:
        return set()
    slugs = set(getattr(_pc, 'CHECKS', {}))
    reg = getattr(_pc, 'register_materialized_checks', None)
    if callable(reg):
        try:
            reg()
            slugs |= set(getattr(_pc, 'CHECKS', {}))
        except Exception:
            pass
    return slugs


_GOTCHA_INDEX_LINK = re.compile(r'\]\(([^)#]*GOTCHAS[^)#]*\.md)#([A-Za-z0-9_-]+)\)')


def _follow_gotcha_index(root, entries):
    """-> entries with each split index line's body replaced by the record's.

    Returns `entries` unchanged for an unsplit section, for a record that is
    missing, and for any single line whose anchor does not resolve -- this is
    a reading list, not a gate, and precedent_check.py's environment-gotchas
    is what refuses a broken link.
    """
    targets = [m.group(1) for _l, _t, b in entries
               for m in [_GOTCHA_INDEX_LINK.search(b)] if m]
    if len(targets) * 2 <= len(entries):
        return entries
    rel = collections.Counter(targets).most_common(1)[0][0]
    f = root / rel
    if not f.is_file():
        return entries
    try:
        text = f.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return entries
    heads = list(re.finditer(r'(?m)^#{2,3}\s+.*?<a id="([A-Za-z0-9_-]+)">', text))
    bodies = {}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        bodies[h.group(1)] = text[h.end():end]
    # The record sits in a subdirectory, so its links are written relative to
    # ITSELF (`../tools/x.py`). Every signal downstream resolves a named path
    # against the repo root, so hand them root-relative text or the pass
    # reports fifteen live tools as deleted -- which it did, once, before this
    # normalization was here.
    import posixpath
    base = posixpath.dirname(rel)

    def reroot(body):
        return re.sub(
            r'\]\((?!https?://|mailto:|#)([^)]+)\)',
            lambda m: '](' + posixpath.normpath(posixpath.join(base, m.group(1)))
                      + ')',
            body)

    out = []
    for line, title, body in entries:
        m = _GOTCHA_INDEX_LINK.search(body)
        got = bodies.get(m.group(2)) if m else None
        out.append((line, title, reroot(got) if got is not None else body))
    return out


def _reroot_md_links(body, base):
    """-> body with every markdown link's target rewritten from being
    relative to `base` to being relative to the repo root.

    Same normalization _follow_gotcha_index needs for a record living in a
    subdirectory, needed here for the same reason: gotchas/*.md's own
    relative links (`../tools/x.py`) are correct from gotchas/, and every
    signal below resolves a named path against the repo root, so handed the
    text unrooted the pass reports every such link as missing. Backtick
    paths (`tools/x.py`, no link markup) are untouched -- they are prose
    written root-relative already and were never relocated.
    """
    import posixpath
    return re.sub(
        r'\]\((?!https?://|mailto:|#)([^)]+)\)',
        lambda m: '](' + posixpath.normpath(posixpath.join(base, m.group(1)))
                  + ')',
        body)


def _gotcha_file_entries(gotchas_dir):
    """-> [(loc, title, body)] for every status: live gotchas/gotcha-*.md
    file, `loc` being the file's own slug (there is no AGENTS.md line number
    once the catalogue lives here) and `body` its Story text, which is what
    every signal below actually scans (dates, remedy paths, check slugs,
    fixture names)."""
    import posixpath
    base = posixpath.basename(str(gotchas_dir).rstrip('/'))
    out = []
    for p in sorted(gotchas_dir.glob('gotcha-*.md')):
        text = p.read_text(encoding='utf-8', errors='replace')
        status_m = re.search(r'^status:\s*(\S+)', text, re.M)
        if not status_m or status_m.group(1).strip() != 'live':
            continue
        sm = re.search(r'^##\s*Symptom\s*\n+(.+?)(?:\n\n|\n##|\Z)', text,
                       re.M | re.S)
        title = ' '.join((sm.group(1) if sm else p.stem).split())
        story_m = re.search(r'^##\s*Story\s*\n+(.*?)(?:\n##\s*Fix|\Z)', text,
                            re.M | re.S)
        body = story_m.group(1) if story_m else text
        out.append((p.stem, title, _reroot_md_links(body, base)))
    return out


def _gotchas_currency(repo_dir):
    """-> (rows, findings) -- a reading list for the gotcha catalogue.

    rows are (tokens, loc, title, [signals]) for every live entry, so the
    caller can order a reduction pass by what trimming each one would
    actually save rather than by which happened to trip a signal. `loc` is
    an AGENTS.md line number (as `L123`) on the pre-migration shape, or a
    gotchas/*.md slug once a repo has migrated -- cosmetic either way, never
    parsed back.
    """
    root = pathlib.Path(repo_dir)

    # The 2026-09-16 shape (spec/OPEN_ITEM_AND_GOTCHA_PLAN.md Part 2): one
    # file per trap under gotchas/, AGENTS.md carrying only a pointer with
    # no entries of its own. Checked FIRST and unconditionally -- a repo
    # that has migrated has nothing left in AGENTS.md's section for the
    # fallback below to find, which is the point of the migration, not a
    # degradation this pass should read as "nothing to check".
    gotchas_dir = root / 'gotchas'
    if gotchas_dir.is_dir() and sorted(gotchas_dir.glob('gotcha-*.md')):
        entries = _gotcha_file_entries(gotchas_dir)
        if not entries:
            return [], []
    else:
        f = root / 'AGENTS.md'
        if not f.is_file():
            return [], []
        text = f.read_text(encoding='utf-8', errors='replace')
        head = re.search(r'(?m)^## .*' + re.escape(_GOTCHA_HEADING) + r'.*$', text)
        if not head:
            return [], []
        after = re.search(r'(?m)^## ', text[head.end():])
        sec = text[head.start():head.end() + (after.start() if after else len(text))]
        entries = _md_bullet_entries(sec, text[:head.start()].count('\n'))
        if not entries:
            return [], []

        # A SPLIT section is an index: one line per trap in AGENTS.md, the
        # entry itself in a linked record (practice: environment-gotchas).
        # Every signal below reads the entry's BODY -- the dates, the remedy
        # paths, the check slugs, the fixture names -- so on a split section
        # the bodies here are one sentence of symptom and the pass would go
        # quietly blind, reporting a clean bill of health for a section it
        # never actually read. Follow the link. Unsplit repos are untouched:
        # nothing matches, nothing is swapped.
        entries = _follow_gotcha_index(root, entries)
        entries = [(f'L{line}', title, body) for line, title, body in entries]

    slugs = _gotcha_check_slugs(repo_dir)
    tools_text = ''
    for p in sorted((root / 'tools').rglob('*.py')) if (root / 'tools').is_dir() else []:
        try:
            tools_text += p.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
    # git dates are unusable on a shallow clone -- every path answers with the
    # boundary commit's date, which would report the whole section as outrun
    # at once. This repo is normally cloned --depth 1, so this is the common
    # case, not the edge one (AGENTS.md, gotchas).
    shallow = (root / '.git' / 'shallow').exists()
    try:
        today = datetime.date.fromisoformat(precedent_time.today(root))
    except Exception:
        today = None

    _log_cache = {}

    def _last_commit(rel):
        if rel in _log_cache:
            return _log_cache[rel]
        code, out, _ = _run_git(root, 'log', '-1', '--format=%cs', '--', rel)
        val = out.strip() if code == 0 and out.strip() else None
        _log_cache[rel] = val
        return val

    rows, findings, undated = [], [], []
    for loc, title, body in entries:
        signals, named = [], set()
        for raw in _GOTCHA_MD_LINK.findall(body):
            tgt = raw.split('#')[0].strip()
            if not tgt or tgt.startswith(('http', 'mailto:', '#')):
                continue
            named.add(tgt)
        named |= set(_GOTCHA_PATH_IN_TICKS.findall(body))
        # A path ending in / is a directory, and the ones an entry names are
        # usually generated output (tools/checks/ is deleted and rewritten on
        # every materialize) -- absent by design, not by drift. Reporting
        # those buried the one real finding on the first run.
        gone = sorted(p for p in named
                      if not p.endswith('/') and not (root / p).exists())
        if gone:
            signals.append('names a remedy that is not in the tree: '
                           + ', '.join(gone[:3])
                           + (f' (+{len(gone) - 3} more)' if len(gone) > 3 else ''))
        if slugs:
            bad = sorted({s for s in _GOTCHA_ONLY_SLUG.findall(body)
                          if s not in slugs})
            if bad:
                signals.append('names a check slug precedent_check.py does '
                               'not answer to: ' + ', '.join(bad[:3]))
        if tools_text:
            missing_fx = sorted({x for x in _GOTCHA_FIXTURE.findall(body)
                                 if x not in tools_text})
            if missing_fx:
                signals.append('names a fixture that no longer exists: '
                               + ', '.join(missing_fx[:3]))
        dates = sorted(_GOTCHA_DATE.findall(body))
        newest = dates[-1] if dates else None
        if today and newest:
            try:
                age = (today - datetime.date.fromisoformat(newest)).days
            except ValueError:
                age = None
            if age is not None and age > _GOTCHA_STALE_DAYS:
                signals.append(f'nothing re-measured since {newest} '
                               f'({age} days)')
            if age is not None and not shallow:
                lead = []
                for rel in sorted(named):
                    d = _last_commit(rel)
                    if not d:
                        continue
                    try:
                        gap = (datetime.date.fromisoformat(d)
                               - datetime.date.fromisoformat(newest)).days
                    except ValueError:
                        continue
                    if gap > _GOTCHA_TREE_LEAD_DAYS:
                        lead.append(f'{rel} last changed {d}')
                if lead:
                    signals.append(f'the tree moved on after {newest}: '
                                   + '; '.join(lead[:2]))
        rows.append((bv._approx_tokens(body), loc, title, signals))
        if not dates:
            undated.append((bv._approx_tokens(body), loc))

    flagged = [r for r in rows if r[3]]
    if flagged:
        findings.append(
            'REVIEW   the gotcha catalogue -- '
            f'{len(flagged)} of {len(rows)} entries raise a currency question '
            f'({sum(r[0] for r in flagged):,} tokens between them).')
        for tok, loc, title, signals in sorted(flagged, key=lambda r: -r[0]):
            findings.append(f'  {tok:5,d} tok  {loc}  "{title[:64]}"')
            for s in signals:
                findings.append(f'            - {s}')
        findings.append(
            '  Each is a QUESTION, not a verdict, and nothing here archives '
            'anything.\n  An entry may name a file that is gone precisely '
            'because it tells the story\n  of a decommission, and an old date '
            'on a trap nobody has hit lately is not\n  a trap that cannot '
            'fire. Verify against the tree, then retire what no longer bites '
            'IN FULL --\n  flip `status: retired` in its own gotchas/*.md '
            'file (or move it to\n  record/GOTCHAS_ARCHIVE.md on the '
            'pre-migration shape), with the verdict that '
            'moved it.')
    if undated:
        findings.append(
            f'  note: {len(undated)} entries carry no date at all '
            f'({sum(t for t, _ in undated):,} tokens), so nothing in them says '
            f'whether\n  they have ever been re-measured. That is weak on its '
            f'own -- several are short\n  and plainly still true -- but it is '
            f'where a dated re-measurement is worth most.')
    if shallow:
        findings.append(
            '  note: this is a shallow clone, so "the tree moved on" was not '
            'run --\n  every path answers with the boundary commit\'s date. '
            '`git fetch --depth=500`\n  first to get that signal.')
    return rows, findings


# spec/OPEN_ITEM_AND_GOTCHA_PLAN.md Part 3, "Open-item sweep": reads every
# todo/*.md and reports, without closing anything. Below this threshold a
# Reminder that has just come due is not yet worth a session's unprompted
# attention (todo/TODO.md's own Due Reminders view already surfaces it the
# moment it arrives, per the format's normal, non-sweep channel); above it,
# nobody has been working here to see the due view, which is exactly the
# safety-net case Part 3 names this pass for.
_REMINDER_WELL_PAST_DAYS = 7
_OPEN_ITEM_OLDEST_N = 5


def _open_item_sweep(repo_dir):
    """-> findings (list[str]) for the OPEN ITEMS section. Three mechanical
    signals, each a question rather than a verdict -- matching
    _gotchas_currency's own discipline, and item-closes-on-its-condition's:
    a resemblance to done is not done."""
    todo_dir = pathlib.Path(repo_dir) / 'todo'
    if not todo_dir.is_dir():
        return []
    items = [it for it in bti.load_items(todo_dir)
             if it.get('status', 'open') == 'open']
    if not items:
        return []

    try:
        today = datetime.date.fromisoformat(precedent_time.today(repo_dir))
    except Exception:
        today = None

    out = []

    unblocked = sorted(
        (it for it in items
         if it.get('kind') == 'analysis' and not it.get('blocked_on')),
        key=lambda it: it.get('noted') or '')
    if unblocked:
        out.append(f'  UNBLOCKED -- {len(unblocked)} open, kind: analysis '
                   f'item(s) with no stated blocker. Either do them now or '
                   f'say why not:')
        for it in unblocked:
            out.append(f'    {it.slug} -- {it.title[:80]}')

    named_gone = []
    for it in items:
        blocked = it.get('blocked_on') or ''
        named = set(_GOTCHA_MD_LINK.findall(blocked))
        named |= set(_GOTCHA_PATH_IN_TICKS.findall(blocked))
        gone = sorted(p for p in named
                     if not p.startswith(('http', 'mailto:', '#'))
                     and not p.endswith('/')
                     # resolved against todo/, not the repo root -- these
                     # are links as written INSIDE a todo/*.md file, so a
                     # bare sibling name or a "../" prefix both mean what
                     # they say from there, same as a browser would read it
                     and not (todo_dir / p.split('#')[0]).resolve().exists())
        if gone:
            named_gone.append((it, gone))
    if named_gone:
        out.append(f'  BLOCKED-ON NAMES SOMETHING GONE -- {len(named_gone)} '
                   f'item(s). Either the blocker\n  cleared under another '
                   f'name or the reference rotted -- read the item\'s own '
                   f'stated\n  condition before touching `status`:')
        for it, gone in named_gone:
            out.append(f'    {it.slug} -- {it.title[:80]}')
            for g in gone[:3]:
                out.append(f'        missing: {g}')

    if today:
        aged = []
        for it in items:
            noted = it.get('noted')
            try:
                age = (today - datetime.date.fromisoformat(noted)).days
            except (TypeError, ValueError):
                continue
            aged.append((age, it))
        aged.sort(key=lambda r: -r[0])
        if aged:
            out.append(f'  OLDEST {min(_OPEN_ITEM_OLDEST_N, len(aged))} of '
                       f'{len(aged)} open item(s), by age:')
            for age, it in aged[:_OPEN_ITEM_OLDEST_N]:
                out.append(f'    {age:4d}d  {it.slug} -- {it.title[:70]}')

        due = []
        for it in items:
            if it.get('disposition') != 'ask':
                continue
            remind_on = it.get('remind_on')
            if not remind_on:
                continue
            try:
                gap = (today - datetime.date.fromisoformat(remind_on)).days
            except ValueError:
                continue
            if gap >= _REMINDER_WELL_PAST_DAYS:
                due.append((gap, it))
        if due:
            due.sort(key=lambda r: -r[0])
            out.append(f'  REMINDER WELL PAST DUE -- {len(due)} item(s), due '
                       f'{_REMINDER_WELL_PAST_DAYS}+ days ago and (this run '
                       f'aside) nobody has surfaced them since. '
                       f'todo/TODO.md\'s own Due\n  Reminders view is the '
                       f'normal channel; this is the safety net for a '
                       f'Reminder\n  that arrived while nobody was working '
                       f'here to see it:')
            for gap, it in due:
                out.append(f'    {gap:4d}d overdue  {it.slug} -- {it.title[:60]}')

    if not out:
        out.append('  none -- no unblocked analysis item, no blocked_on '
                   'naming something gone, and no\n  Reminder overdue by '
                   f'{_REMINDER_WELL_PAST_DAYS}+ days.')
    out.append('  This pass proposes and never closes. An item closes only '
               'when its OWN\n  stated condition is met -- a resemblance is '
               'not that, and a closed item\n  is not re-read.')
    return out


def _gotcha_retirement_candidates(repo_dir):
    """spec/OPEN_ITEM_AND_GOTCHA_PLAN.md Part 3's other half: "extended to
    read retires_when and report entries whose condition looks met."
    `retires_when` is declared in the schema now and populated later
    (Part 2) -- as of this migration every gotchas/*.md carries it `null`,
    so this reports NOTHING today and is wired for the day a future
    session (Part 4.1 step 9) starts filling it in. Deliberately does not
    try to judge whether a stated condition is MET: the three shapes Part
    2 gives as examples ("a check refuses this", "the harness fixes X",
    "nothing has hit this since DATE") are freeform prose, and guessing at
    which read as satisfied is exactly the auto-closer Part 5 rules out --
    this surfaces every entry that has one stated, for a person to judge."""
    gotchas_dir = pathlib.Path(repo_dir) / 'gotchas'
    if not gotchas_dir.is_dir():
        return []
    out = []
    for p in sorted(gotchas_dir.glob('gotcha-*.md')):
        text = p.read_text(encoding='utf-8', errors='replace')
        m = re.search(r'^retires_when:\s*(.+)$', text, re.M)
        if not m:
            continue
        val = m.group(1).strip()
        if val in ('null', ''):
            continue
        status_m = re.search(r'^status:\s*(\S+)', text, re.M)
        if status_m and status_m.group(1).strip() == 'retired':
            continue  # already retired -- nothing left to judge
        out.append(f'  {p.stem} -- retires_when: {val}')
    return out


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
    # bootstrap() writes these itself, from the harness adapter rather than
    # from the skeleton, so a skeleton correctly ships none of them and
    # reporting them as gaps would be a false positive in every set at once.
    # Read from the module rather than retyped: a hook added to SESSION_HOOKS
    # upstream would otherwise start reading as a template gap here.
    NOT_SKELETON |= set(bss.SESSION_HOOKS) | {'settings.json'}
    # WHICH DIRECTORIES COUNT. Root files plus the two directories bootstrap
    # itself writes into -- those are the set's SHAPE. `practices/` and
    # anything else is the set's own content, where a name every set happens
    # to share says nothing about the template. Until 2026-09-13 this was
    # root files only, which made a missing hook or a missing settings file
    # invisible to the one check whose whole job is spotting what the
    # skeleton fails to ship.
    SHAPE_DIRS = ('.claude', 'bootstrap')
    by_level = {}
    for s in sources:
        lvl, path = s.get('level'), s.get('path')
        if lvl in FATAL_MISSING_LEVELS and path:
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
        common = None
        for _name, p in repos:
            tracked = _tracked_files(p)
            def _keep(f, _p=p, _tracked=tracked):
                return _tracked is None or str(
                    f.relative_to(_p)) in _tracked
            here = {f.name for f in p.iterdir()
                    if f.is_file() and _keep(f)}
            for sub_dir in SHAPE_DIRS:
                d = p / sub_dir
                if d.is_dir():
                    here |= {f.name for f in d.rglob('*')
                             if f.is_file() and _keep(f)}
            here -= NOT_SKELETON
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


def _skeleton_rel_paths(level):
    """-> {str} every path the level's skeleton ships, spelled the way
    bootstrap() writes it at the destination (`.template` stripped, the
    `.sample` suffix kept -- _copy_skeleton strips one and not the other,
    and a check that guesses at that mismatches every file it touches)."""
    level = getattr(bootstrap_source, 'LEVEL_ALIASES', {}).get(level, level)
    skeleton = bootstrap_source.SKELETONS.get(level)
    if skeleton is None or not skeleton.is_dir():
        return set()
    out = set()
    for src in skeleton.rglob('*'):
        if not src.is_file():
            continue
        rel = str(src.relative_to(skeleton))
        if rel.endswith('.template'):
            rel = rel[: -len('.template')]
        out.add(rel)
    return out


def _same_bytes(gen_path, real_path, gen_root, real_root):
    """-> True if the two files say the same thing once the one difference
    that is never drift is normalized away: bootstrap() substitutes
    {{DEST_PATH}}, so every generated file that quotes its own location
    differs from a real set by nothing but the path it was written to."""
    gen, real = gen_path.read_bytes(), real_path.read_bytes()
    if gen == real:
        return True
    try:
        gen_text = gen.decode('utf-8')
    except UnicodeDecodeError:
        return False
    normalized = gen_text.replace(str(gen_root), str(real_root))
    return normalized.encode('utf-8') == real


def _tracked_files(repo_dir):
    """-> {str} every path git TRACKS in a set, relative, or None when the
    question could not be answered.

    UNTRACKED IS NOT DRIFT, and this exists because the first run of the
    extended checks reported that all three team sets carry a
    `.claude/settings.local.json` the skeleton does not ship. True, and not a
    template gap: the file is untracked in all three, written by the harness
    into whatever container the set happens to be cloned in. A check that
    reads container state as a shape the template is missing would have every
    adopter adding harness scratch files to the skeleton.

    None rather than an empty set when git cannot answer, so a caller can
    tell "nothing is tracked" from "tracking could not be read" and decline to
    filter on the second (practice: fail-gracefully)."""
    code, out, _err = _run_git(repo_dir, 'ls-files', '-z')
    if code != 0:
        return None
    return {n for n in out.split('\0') if n}


def _extra_lines(gen_path, real_path, gen_root, real_root):
    """-> frozenset of lines the real file has and the generated one does not.

    Line-level rather than whole-file, because the question _convergent_drift
    asks is which CHANGE several sets share, and two sets that each added the
    same line to a file they otherwise edited differently are exactly the case
    a whole-file comparison cannot see.

    Normalized the same way _same_bytes() normalizes, for the same reason:
    bootstrap() substitutes {{DEST_PATH}}, so every line quoting the set's own
    location differs in every set and would otherwise never converge.

    Lines of three non-whitespace characters or fewer are dropped. They are
    structural -- a fence, a rule, a closing brace -- and shared by every file
    of a kind regardless of what anybody changed, so counting them reports
    agreement that carries no information.
    """
    try:
        gen = gen_path.read_text(encoding='utf-8')
        real = real_path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        # A binary or unreadable file has no lines to compare. Recorded as no
        # difference rather than skipped, so the set still appears in the
        # denominator (see the empty-frozenset note in _bootstrap_drift_one).
        return frozenset()
    gen_lines = set(gen.replace(str(gen_root), str(real_root)).splitlines())
    return frozenset(
        line for line in real.splitlines()
        if line not in gen_lines and len(line.strip()) > 3)


_LEDGER_VERDICTS = {'intentional-customization', 'template-candidate',
                     'stale-shared-build', 'tracked-elsewhere'}


def _load_decisions_ledger(root_path):
    """-> {(section, key): entry} the per-repo dedup ledger a SOURCE holds at
    <root_path>/very-deep-check-decisions.json (VERY_DEEP_CHECK_DEDUP_LEDGER_PROPOSAL.md,
    precedent-individual). {} when the file is absent, unparseable, or has no
    `entries` -- a source that has never judged a finding behaves exactly as
    one with an empty ledger, which is what keeps this additive rather than a
    breaking change to the section that reads it (practice: fail-gracefully).

    An entry whose `verdict` is not one of the four fixed values is dropped
    rather than trusted -- the ledger is closed vocabulary so the tool can
    act on it, and an unrecognized value is safer read as no decision at all
    than as some fifth verdict nothing here knows how to handle."""
    try:
        data = json.loads(
            (pathlib.Path(root_path) / 'very-deep-check-decisions.json')
            .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    out = {}
    for entry in data.get('entries') or ():
        section, key = entry.get('section'), entry.get('key')
        if section and key and entry.get('verdict') in _LEDGER_VERDICTS:
            out[(section, key)] = entry
    return out


def _convergent_drift(collect, sources=None):
    """-> [str] changes that SEVERAL sets of a level made the same way, which
    is the template being wrong rather than several people living in their
    sets.

    THE DIRECTION THE OTHER TWO CANNOT SEE, and the reason this exists.
    _bootstrap_drift() compares each set against the generator and never
    compares the sets against each other, so it reports one shared change as
    N separate per-set lines and never says the sentence that matters. Worse,
    it deliberately downgrades a difference in a SKELETON-OWNED file to a note
    -- correct per set, since those files are the person's to edit, and wrong
    across sets, because four sets that edited the same file the same way is
    not four people living in their sets. _template_freshness() asks the same
    source-to-template question but about filenames only, so a file that every
    set has and every set changed identically reads as present and healthy.

    Raised by Morgan on 2026-09-13: "I think the level files like
    precedent-individual and precedent-team-* get out of sync with the
    original templates in important ways very quickly." Measured the same day
    before it was built: across the three resolved team sets there was no
    shared line-level change in any skeleton-owned file -- zero -- so this
    lands against a clean baseline and its first real finding will be a real
    one. What the measurement DID show is the shape being right: all three
    team sets carry a `freshness-guard.sh` byte-identical to each other and
    different from the generator, reported until now as three unrelated
    findings.

    TWO SETS IS THE THRESHOLD, and it is evidence rather than proof. One set
    is a person; two sets that did the same thing independently is a habit the
    template is missing. A level with fewer than two resolved sources says so
    rather than reporting nothing, since a section that prints nothing when it
    compared nothing reads exactly like a clean result (practice:
    fail-gracefully, and the same n=1 reasoning _template_freshness() gives).

    THE DEDUP LEDGER (VERY_DEEP_CHECK_DEDUP_LEDGER_PROPOSAL.md, proposed by
    Morgan, 2026-09-20, from a session rooted in precedent-individual with no
    push access here). Without `sources`, a file that converges prints as a
    fresh FINDING on every single run forever, including one a person has
    already read and judged -- exactly the expense this section's own Rule
    says a person should not have to keep paying. `sources` -- the same list
    `_bootstrap_drift()` was already given -- lets this read each converged
    SET's own `very-deep-check-decisions.json` (a file that lives in the set,
    not here, because the decision belongs to the repo the finding is about).
    That principle used to be illustrated by where the beta-branch watermark
    lived; it is a poor example now, since that file moved into this repo's
    own tools/beta_branch_watermark.json on 2026-09-22 -- the principle
    held, the example did not. When every set that shares a convergence
    has recorded the SAME verdict there and no `revisit` date has passed, the
    line prints as DECIDED instead of FINDING. Disagreement, a partial
    decision, or an expired `revisit` all still print the ordinary FINDING,
    annotated with what is already on record -- a person is never talked out
    of seeing a real disagreement, only spared re-litigating a settled one. A
    ledger entry whose file no longer exists in that set prints as its own
    ORPHANED LEDGER ENTRY line rather than being silently ignored, matching
    the `ORPHANS` section's own philosophy elsewhere in this tool. A repo
    with no ledger file, or `sources=None`, behaves exactly as before this
    was added -- additive, never a breaking change to what was already here.
    """
    if collect is None:
        return ['nothing was collected, so no set was compared against any '
                'other -- this is a skip, not a clean result']
    today_iso = precedent_time.today()
    name_to_path = {s.get('name'): s.get('path') for s in (sources or ())
                    if s.get('name') and s.get('path')}
    _ledgers = {}

    def ledger_for(name):
        if name not in _ledgers:
            path = name_to_path.get(name)
            _ledgers[name] = _load_decisions_ledger(path) if path else {}
        return _ledgers[name]

    def entry_active(entry):
        revisit = entry.get('revisit')
        return not (revisit and revisit <= today_iso)

    by_level = {}
    for (level, rel), per_source in collect.items():
        by_level.setdefault(level, set()).update(per_source)
    out = []
    for level in sorted(by_level):
        if len(by_level[level]) < 2:
            only = ', '.join(sorted(by_level[level])) or 'none'
            out.append(
                f'note {level}: only {len(by_level[level])} source of this '
                f'level resolved ({only}), so nothing at this level can '
                f'converge with anything. A second source is what would make '
                f'this level checkable at all.')
    for (level, rel), per_source in sorted(collect.items()):
        if len(by_level.get(level, ())) < 2:
            continue
        total = len(per_source)
        absent = sorted(n for n, v in per_source.items() if v is None)
        if len(absent) >= 2:
            out.append(
                f'FINDING {level}: the generator writes {rel!r} and '
                f'{len(absent)} of {total} sets do not have it '
                f'({", ".join(absent)}) -- either the generator should stop '
                f'writing it, or those sets are missing something they need')
        counts = {}
        for name, lines in per_source.items():
            for line in (lines or ()):
                counts.setdefault(line, []).append(name)
        # Widest agreement first, so the cap below drops the WEAKEST
        # evidence rather than whatever sorted first by set name. A cap that
        # hides the line every set shares would defeat the section.
        shared = sorted(((names, line) for line, names in counts.items()
                         if len(names) >= 2),
                        key=lambda pair: (-len(pair[0]), pair[1]))
        if not shared:
            continue
        widest = max(len(names) for names, _ in shared)
        sets = sorted({n for names, _ in shared for n in names})

        # Every set that shares this convergence gets one chance to have
        # already judged it. A verdict past its own `revisit` date counts as
        # no decision, not as a stale yes -- entry_active() is what makes
        # that re-surface rather than trusting a September call into March.
        decisions = {}
        for n in sets:
            entry = ledger_for(n).get(('CONVERGENT DRIFT', rel))
            if entry and entry_active(entry):
                decisions[n] = entry
        verdicts = {e['verdict'] for e in decisions.values()}

        if decisions and len(decisions) == len(sets) and len(verdicts) == 1:
            verdict = next(iter(verdicts))
            # Attributed to whoever decided first, so two sets agreeing on
            # the same call are not double-counted as two decisions.
            lead_name = min(decisions, key=lambda n: (decisions[n].get('decided') or '', n))
            lead = decisions[lead_name]
            out.append(
                f'DECIDED {level}: {rel!r} -- {verdict} (by '
                f'{lead.get("decided_by", "?")} {lead.get("decided", "?")}). '
                f'{len(shared)} converged line(s) across {", ".join(sets)} '
                f'already judged; suppressed rather than reprinted -- see '
                f'that set\'s very-deep-check-decisions.json to revisit.')
            continue

        out.append(
            f'FINDING {level}: {len(shared)} line(s) in {rel!r} appear in up '
            f'to {widest} of {total} sets ({", ".join(sets)}) and in nothing '
            f'the generator writes. Two readings, and this check cannot tell '
            f'them apart: the sets share a change the template should carry, '
            f'or they share an OLDER build the generator has since moved past. '
            f'Which one it is, is one diff between a set and this checkout:')
        # Capped, and the cap is stated. A finding that prints two hundred
        # lines is a finding nobody reads; the file is named, so the rest is
        # one diff away (practice: deliverables-look-like-output).
        for names, line in shared[:8]:
            out.append(f'    [{len(names)}/{total}] {line[:120]}')
        if len(shared) > 8:
            out.append(f'    ... and {len(shared) - 8} more line(s); '
                       f'diff {rel!r} across those sets for the rest')
        if decisions:
            # Only some of the converged sets agree, or they agree with each
            # other but not on the SAME verdict -- either way this is not a
            # settled question, and the finding stays a FINDING. What was
            # already decided is on record so nobody re-argues it from zero.
            noted = ', '.join(
                (f'{n} decided {decisions[n]["verdict"]} (by '
                 f'{decisions[n].get("decided_by", "?")} '
                 f'{decisions[n].get("decided", "?")})')
                if n in decisions else f'{n} undecided'
                for n in sets)
            out.append(f'    ledger: {noted}')

    for name, path in sorted(name_to_path.items()):
        root = pathlib.Path(path)
        for (section, key), entry in sorted(ledger_for(name).items()):
            if section != 'CONVERGENT DRIFT' or (root / key).is_file():
                continue
            out.append(
                f'ORPHANED LEDGER ENTRY: {name} recorded {key!r} as '
                f'{entry.get("verdict", "?")} (by '
                f'{entry.get("decided_by", "?")} {entry.get("decided", "?")}) '
                f'but that file no longer exists in {name} -- nothing left '
                f'for the decision to suppress; remove or update the entry')
    return out


def _bootstrap_drift_one(level, name, path, collect=None):
    """-> [str] what today's generator would write for a set that already
    exists, where that differs from the set itself.

    THE QUESTION NEITHER OTHER CHECK ASKS. bootstrap_source.verify() asks
    whether a real source still has every file the skeleton ships;
    _template_freshness() asks the reverse, for names. Both are about which
    files EXIST. Neither has ever compared a byte -- so a set and the
    generator that made it can say different things in the same file
    forever, in either direction (the generator moving on after the set was
    created, or the set being edited where it was never meant to be), while
    every mechanism here reports healthy.

    Raised by Morgan on 2026-09-11, reading the brand-new-adopter path:
    "I'm worried about my updating those levels files but the original
    generator generating something different." No incident is attached and
    none is invented -- this is a gap found by reading rather than by a
    failure, which is the other way findings arrive here
    (practice: cite-the-incident, no-invented-specifics).

    The owned/shape split is what keeps the output short enough to read. A
    file the SKELETON ships is the person's -- "edit this file freely
    afterward, it is yours", in the skeleton README's own words -- so a
    difference there is a note, never a finding. A file bootstrap
    GENERATES (the vendored engine, the session hooks, settings.json) is
    the set's shape and carries "never hand-edit these", so a difference
    there is a finding WITH A DIRECTION: the set's own ENGINE_MANIFEST says
    whether it is a faithful vendoring of an older upstream commit (refresh
    it) or a hand-edit that needs to move upstream instead
    (practice: engine-plus-host-shims).

    Runs the real generator into a throwaway directory rather than reading
    the skeleton, because the skeleton is only half of what bootstrap()
    writes -- the half this check was asked about is the other half.

    `collect`, when given a dict, also records what this run already knows
    per file, for _convergent_drift() to read afterwards. It is a parameter
    rather than a second pass because the generator run is the expensive
    part of this section, and running it twice to ask two questions of the
    same bytes would double the cost of the whole check for nothing."""
    import contextlib, io, shutil, tempfile

    real_root = pathlib.Path(path)
    approvers = None
    if level in ('shared', 'team'):
        try:
            data = json.loads((real_root / 'approvers.json').read_text(encoding='utf-8'))
            approvers = data.get('approvers') or None
        except Exception:                                         # noqa: BLE001
            pass
        if not approvers:
            # bootstrap() refuses a team set with no approver, and refusing
            # to run the check at all over a seed value that never reaches
            # a compared file (approvers.json is skeleton-owned) would be
            # the guard costing more than it protects.
            approvers = [{'name': 'drift-check placeholder', 'github': 'drift-check'}]

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-drift-'))
    gen_root = tmp / 'generated'
    try:
        try:
            # bootstrap() prints its own stale-clone warning; that belongs to
            # a person bootstrapping a set, not to this section's output.
            with contextlib.redirect_stdout(io.StringIO()):
                bootstrap_source.bootstrap(level, name, gen_root, approvers=approvers)
        except Exception as exc:                                  # noqa: BLE001
            return [f'FINDING {level}: the generator could not be run for '
                    f'{name!r}, so NOTHING here was compared -- '
                    f'{type(exc).__name__}: {exc}']

        owned = _skeleton_rel_paths(level)
        # Untracked files are the container's, not the set's -- see
        # _tracked_files. Collected-for-convergence only; the per-set findings
        # below are unchanged, since a wrong-content file is worth reporting
        # whether or not the set commits it.
        tracked = _tracked_files(real_root)
        wired = {w.name: w for w in bootstrap_source._wired_hook_paths(real_root)}
        manifest = {}
        try:
            manifest = json.loads(
                (real_root / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))
        except Exception:                                         # noqa: BLE001
            pass
        recorded = manifest.get('sha256', {})

        findings, notes, absent, behind = [], [], [], []
        for gen_path in sorted(gen_root.rglob('*')):
            if not gen_path.is_file():
                continue
            rel = str(gen_path.relative_to(gen_root))
            # __pycache__ is a Python runtime artifact, never a generator
            # output -- comparing it reads a bytecode cache Python happened
            # to write during THIS run of the generator as drift. Found
            # 2026-09-16: bootstrap()'s own build_views.py subprocess is
            # already `-B` (its own comment: "a tools/__pycache__/ it left
            # behind read as bootstrap drift in every audit afterwards"),
            # but that only covers build_views.py's own execution -- it does
            # not stop whatever else in this process's run of bootstrap()
            # writes bytecode into gen_root along the way. Measured: 100%
            # reproducible through _bootstrap_drift_one, 0% through a direct
            # bootstrap_source.bootstrap() call replaying the same
            # arguments -- so the cache is a real side effect of THIS
            # code path, whatever its exact trigger, and belongs excluded
            # here rather than chased further upstream.
            if '__pycache__' in pathlib.Path(rel).parts:
                continue
            # .precedent/ is session state the set's own .gitignore excludes:
            # SESSION_PRACTICES.md is rendered for the session that is
            # running, and since the stale-render self-heal (2026-09-18)
            # bootstrap()'s own build_views run renders it into a brand-new
            # set too -- so two generations of the same set differ there by
            # construction, and the first real run of this check reported a
            # just-generated set as drifted (2026-09-19).
            if rel.split(os.sep)[0] == '.precedent':
                continue
            # practices/ is the set's own content, and example-starter-<level> is
            # the one file an adopter is told to delete.
            if rel.split(os.sep)[0] == 'practices':
                continue
            # The manifest records the commit and hashes of the vendoring
            # that happened, so it differs by construction; what it has to
            # say is reported below as a commit gap, not as a diff.
            if rel.endswith('ENGINE_MANIFEST.json'):
                continue
            real_path = real_root / rel
            if not real_path.is_file():
                # A hook the set wires from somewhere other than
                # .claude/hooks/ is installed, not missing -- the same
                # allowance verify() makes, for the same live source.
                alt = wired.get(pathlib.Path(rel).name)
                real_path = (real_root / alt) if alt and (real_root / alt).is_file() else None
            if real_path is None:
                if collect is not None:
                    collect.setdefault((level, rel), {})[name] = None
                if rel not in owned:
                    absent.append(rel)
                continue
            if _same_bytes(gen_path, real_path, gen_root, real_root):
                if collect is not None:
                    # Recorded as an EMPTY difference rather than skipped: a
                    # file two sets changed the same way is only evidence
                    # against the template if the third set is known to have
                    # left it alone, and a set that never appears in the
                    # record is indistinguishable from one that was never
                    # compared (practice: fail-gracefully).
                    collect.setdefault((level, rel), {})[name] = frozenset()
                continue
            if collect is not None and (
                    tracked is None
                    or str(real_path.relative_to(real_root)) in tracked):
                collect.setdefault((level, rel), {})[name] = _extra_lines(
                    gen_path, real_path, gen_root, real_root)
            # settings.json is the set's OWN wiring, not a file with one
            # right content: verify() already allows a source to point it at
            # hooks kept somewhere else, and precedent-individual does
            # exactly that, on purpose and documented. Calling that a finding
            # would report a deliberate decision as drift every run
            # (practice: control-asserts-which-failure -- a check that fires
            # on the wrong thing teaches people to skim it).
            if rel in owned or rel.endswith('settings.json'):
                notes.append(rel)
                continue
            eng_name = pathlib.Path(rel).name
            if rel.startswith('tools' + os.sep) and eng_name in recorded:
                actual = bootstrap_source.precedent_vendor_engine._sha256(real_path)
                if actual == recorded[eng_name]:
                    # Not news per file: the set is a faithful vendoring of an
                    # older commit, so EVERY engine file differs and one fact
                    # prints as a dozen findings. Collapsed below.
                    behind.append(rel)
                else:
                    findings.append(
                        f'{rel} differs from what the generator writes today '
                        f'and does NOT match its own ENGINE_MANIFEST either, so '
                        f'it was hand-edited in place: move the change upstream '
                        f'rather than refreshing over it')
                continue
            findings.append(f'{rel} differs from what the generator writes today')

        # Absent engine files are the same one fact as `behind` -- a name the
        # engine gained after this set was last vendored -- so they collapse
        # with it rather than printing per file. Anything else absent is its
        # own news and stays.
        if behind:
            absent, folded = ([a for a in absent if not a.startswith('tools' + os.sep)],
                              [a for a in absent if a.startswith('tools' + os.sep)])
        else:
            folded = []

        if collect is not None:
            # An engine file that is a faithful vendoring of an older commit
            # differs in EVERY set at once, identically, which is textbook
            # convergence and is not news: it is the one fact the stale-
            # vendoring finding below already states, and letting it through
            # would bury every real finding under a dozen engine files.
            for rel in behind:
                collect.get((level, rel), {}).pop(name, None)

        out = []
        commit = manifest.get('source_commit')
        head = bootstrap_source.precedent_vendor_engine._head_commit(ROOT)
        if behind:
            where = (f' (vendored at {commit[:9]}, this checkout at {head[:9]})'
                     if commit and head else '')
            gained = (f'; {len(folded)} file(s) the engine gained since are '
                      f'absent: {", ".join(sorted(folded))}' if folded else '')
            out.append(f'FINDING {level} {name}: its vendored engine is an '
                       f'OLDER upstream vendoring{where} -- {len(behind)} file(s) '
                       f'differ, every one still matching its own '
                       f'ENGINE_MANIFEST{gained}. `precedent_vendor_engine.py '
                       f'refresh` is the whole fix.')
        for rel in absent:
            out.append(f'FINDING {level} {name}: the generator writes {rel!r} '
                       f'and this set does not have it')
        for msg in findings:
            out.append(f'FINDING {level} {name}: {msg}')
        if notes:
            out.append(f'note {level} {name}: {len(notes)} skeleton-shipped '
                       f'file(s) differ, which is what a set being lived in '
                       f'looks like, not drift: {", ".join(sorted(notes))}')
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _bootstrap_drift(sources, collect=None):
    """-> [str] _bootstrap_drift_one across every resolved team/individual
    source, or one line saying why nothing was compared. A section that
    prints nothing when no source resolved reads exactly like a section
    that compared everything and found it clean
    (practice: fail-gracefully)."""
    out, seen = [], False
    for s in sources:
        level, path = s.get('level'), s.get('path')
        if level not in FATAL_MISSING_LEVELS or not path:
            continue
        if not pathlib.Path(path).is_dir():
            continue
        seen = True
        out.extend(_bootstrap_drift_one(level, s.get('name'), path,
                                        collect=collect))
    if not seen:
        return ['no team or individual source resolved here, so the generator '
                'was NOT compared against anything -- this is a skip, not a '
                'clean result. Attach the sets and re-run.']
    return out


def _merged_row(repo_dir, name, ref, stale_days, into=None):
    """-> the evidence a session needs to DELETE one branch that is already
    an ancestor of a protected branch: {'name', 'into', 'last', 'age_days',
    'stale', 'author'}.

    `into` names WHICH protected branch already carries it. That is not
    decoration: a branch merged into the integration branch is finished
    here, while one merged into the base branch and not the integration
    branch is finished somewhere else -- equally safe to delete, and its
    work is not in this line of development. Reporting the second as
    "not merged" (which is what a single-target sweep does) turns every
    long-finished branch on the base branch into a false unlanded-work
    finding.

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
    row = {'name': name, 'into': into}
    row.update(_branch_meta(repo_dir, ref, stale_days))
    return row


def _branch_meta(repo_dir, ref, stale_days):
    """-> {'last', 'age_days', 'stale', 'author'} for one branch tip.

    Shared by both halves of the sweep, because both halves need the same two
    facts and used to carry only one of them each. The merged half had the
    date and no author; the unmerged half had the date and no age. Neither
    could answer the question the sweep is actually for -- "whose branch is
    this, and has anybody touched it since" -- so the fact-gathering is one
    function and the two rows differ only in the verdict they carry.

    AUTHOR IS NOT A FILTER. The sweep used to be scoped to the invoking
    person's own login, on the sound reasoning that you do not delete
    somebody else's branch. That kept the deletion safe and made the LIST
    wrong: the branches that accumulate longest are exactly the ones nobody
    in the room opened, so the sweep reported a short clean list while the
    repo's branch page grew every month (asked 2026-09-12, by Morgan:
    "find stale branches, even if worked on by someone else"). Every branch
    is listed, and the author is printed so a verdict can be routed to
    whoever owns it rather than silently skipped."""
    meta = {'last': None, 'age_days': None, 'stale': None, 'author': None}
    rc, out, _ = _run_git(repo_dir, 'log', '-1', '--format=%ct%x00%an', ref)
    if rc == 0 and '\x00' in out:
        ts_s, author = out.strip().split('\x00', 1)
        meta['author'] = author.strip() or None
        if ts_s.strip().isdigit():
            ts = int(ts_s.strip())
            meta['last'] = _stamp(ts)
            # Both sides aware and in one zone -- precedent_time owns every
            # moment this project writes down (practice:
            # timestamps-carry-offset, one-formatter-per-quantity).
            meta['age_days'] = max(
                0, (precedent_time.now() - precedent_time.from_unix(ts)).days)
            meta['stale'] = meta['age_days'] >= stale_days
    return meta


def _unmerged_row(repo_dir, name, ref, target_ref, target, stale_days=None):
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
    row = {'name': name, 'ahead': None, 'unique': None, 'verdict': None}
    # Date, age against the declared threshold, and author -- the same three
    # facts the merged half carries. An unmerged branch that nobody has
    # touched in a year is the one most likely to be lost work AND the one
    # least likely to belong to whoever is running the sweep, so both facts
    # belong on the row rather than on the half of the sweep that ends in a
    # deletion.
    row.update(_branch_meta(repo_dir, ref, stale_days))
    # `git cherry` is only meaningful if a merge base between the two refs
    # actually resolves in THIS clone, so ask for one first -- and `ahead`
    # below needs exactly the same precondition, for the same reason.
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
    resolves = _merge_base_resolves(repo_dir, target_ref, ref)
    # `rev-list --count target..ref` moved here, gated on the SAME
    # precondition as `cherry` (practice: very-deep-check). On a shallow
    # clone whose merge-base does not truly resolve, `rev-list` does not
    # fail the way `cherry` used to -- it silently counts every commit
    # reachable from `ref` back to the grafted shallow boundary and calls
    # that "ahead", which is a fabricated boundary, not history. Found
    # 2026-09-19, pass 4 of a very deep check: four branches that were
    # plain, fully-landed ancestors of the target read as 210-485 commits
    # "ahead" on a shallow clone, and 0 once genuinely resolved.
    if resolves:
        rc, out, _ = _run_git(repo_dir, 'rev-list', '--count',
                              f'{target_ref}..{ref}')
        if rc == 0 and out.isdigit():
            row['ahead'] = int(out)
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
        _age = ''
        if row.get('stale'):
            # Age changes what the verdict means, so it is said in the
            # verdict rather than left in a column. A branch carrying
            # unlanded work that nothing has touched in months is not
            # "in progress"; it is the thing this sweep exists to surface.
            _age = (f', and nothing has touched it in {row["age_days"]} '
                    f'day(s) -- long past the point where it can be assumed '
                    f'to be in progress')
        row['verdict'] = (f'CARRIES {row["unique"]} unlanded commit(s){_age} -- '
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
    #
    # --prune (practice: very-deep-check), added 2026-09-19: without it, a
    # remote-tracking ref for a branch someone already deleted on the server
    # sits here forever, and scan_branches below enumerates it as if it were
    # live. Found the same run as the `ahead`/`cherry` fix above: 4 of 8
    # branches this check reported as carrying hundreds of unlanded commits
    # were plain, already-merged, ALREADY-DELETED-ON-THE-REMOTE stale refs --
    # `have - server` never having been computed here is why nothing caught
    # it. `--prune` deletes only local tracking refs; it touches nothing on
    # the remote.
    rc, _, _ = _run_git(repo_dir, 'fetch', '--prune', '--depth=50', 'origin')
    if rc != 0:
        _run_git(repo_dir, 'fetch', '--prune', 'origin')
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
    Otherwise {'target': str, 'merged': [...], 'merged_elsewhere': [...],
    'unmerged': [...]}: 'merged' branches are mechanically PROVEN safe to
    delete (every commit on them is already an ancestor of target);
    'merged_elsewhere' are proven the same way against another PROTECTED
    branch -- the base branch this repo's integration branch will eventually
    fold into -- so they are equally safe to delete and their work is not on
    the integration branch; 'unmerged' is everything else remaining (the
    protected branches themselves excluded) -- some of those may still be
    safe (closed because a later PR superseded them) but that call needs
    the branch's PR history, which this offline check cannot see. See
    practices/very-deep-check.md's Install section.

    Nothing here is scoped to one author. Every branch on origin is swept
    and every row names who last touched it -- see _branch_meta.

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
    # Every OTHER protected branch is a second place a branch's work can
    # already have landed -- on this repo, `main`, while the integration
    # branch is `precedent-beta-v01`. A branch merged into main and never
    # into the integration branch is finished work, and a sweep that tests
    # only the integration branch reports it as carrying unlanded commits
    # forever. That is not a cosmetic mislabel: it is the class that
    # accumulates (asked 2026-09-12, by Morgan -- "Alex likely has branches
    # on main from bestpractice from weeks ago"), so the false readings
    # outnumber the true ones and the list stops being read.
    others = [b for b in sorted(protected) if b != target]
    merged, elsewhere, unmerged = [], [], []
    # Every name on the branches page, PROTECTED AND EXCLUDED ONES INCLUDED
    # -- the `?query=` filter does not know this sweep skipped them, so a
    # branch whose name is a substring of the integration branch's still
    # opens two rows (practice: branch-delete-links).
    all_names = []
    for ref in out.splitlines():
        if '/' not in ref:
            continue
        name = ref.split('/', 1)[1]
        if name == 'HEAD':
            continue
        all_names.append(name)
        if name in protected or name in exclude:
            continue
        rc, _, _ = _run_git(repo_dir, 'merge-base', '--is-ancestor', ref, target_ref)
        if rc == 0:
            merged.append(_merged_row(repo_dir, name, ref, stale_days,
                                      into=target))
            continue
        landed_in = None
        for other in others:
            other_ref = f'origin/{other}'
            rc, _, _ = _run_git(repo_dir, 'rev-parse', '--verify', '--quiet',
                                other_ref)
            if rc != 0:
                continue
            rc, _, _ = _run_git(repo_dir, 'merge-base', '--is-ancestor', ref,
                                other_ref)
            if rc == 0:
                landed_in = other
                break
        if landed_in:
            elsewhere.append(_merged_row(repo_dir, name, ref, stale_days,
                                         into=landed_in))
        else:
            unmerged.append(_unmerged_row(repo_dir, name, ref, target_ref,
                                          target, stale_days=stale_days))
    for _row_list in (merged, elsewhere, unmerged):
        for _r in _row_list:
            _r['filter_ambiguous'] = _filter_is_ambiguous(_r['name'],
                                                          all_names)
    return {'target': target,
            'merged': sorted(merged, key=lambda r: r['name']),
            'merged_elsewhere': sorted(elsewhere, key=lambda r: r['name']),
            'unmerged': sorted(unmerged, key=lambda r: r['name']),
            'protected': sorted(protected),
            'stale_days': stale_days,
            'unfetched': missing_heads or [], 'unreachable': reach_note,
            'path': str(repo_dir)}


def recent_activity(repo_dir, days):
    """-> what landed in one repo inside the last `days`, as the repo half of
    the live-session sweep:

        {'days', 'shallow', 'commits': [{'sha','date','author','ref','subject'}],
         'branches': [{'name','last','author'}], 'note': str|None}

    None when repo_dir is not its own git checkout.

    WHY THIS EXISTS (asked 2026-09-12, by Morgan: "do a sweep of live
    sessions against the repo to see if there's anything recent being
    missed"). Every other part of this check reads the repository against
    itself. None of them can see the failure where the repository is
    internally perfect and a piece of work simply never arrived in it -- a
    session that ran, decided something, fixed something, and ended with its
    conclusion in a chat thread and nothing on a branch. `repo-is-memory`
    names that as the loss; nothing looks for it afterwards.

    THIS HALF IS THE REPO SIDE ONLY, and says so rather than implying
    coverage it does not have. The session side -- which sessions ran, which
    are still running, what each was asked to do -- lives in the harness, not
    in git, and no tool in this repository can read it. So this function
    builds the inventory a session can hold the harness's own session list
    against, and the practice tells the session to go and fetch that list.
    A mechanical half that pretended to the whole thing would be the
    "sample reads as clean" failure pass 2 question 14 is about."""
    repo_dir = pathlib.Path(repo_dir)
    if not (repo_dir / '.git').is_dir():
        return None
    out = {'days': days, 'shallow': False, 'commits': [], 'branches': [],
           'note': None}
    rc, shallow, _ = _run_git(repo_dir, 'rev-parse', '--is-shallow-repository')
    if rc == 0 and shallow.strip() == 'true':
        out['shallow'] = True
        out['note'] = ('this clone is shallow, so commits older than its '
                       'grafted boundary are invisible here -- read the list '
                       'below as partial, never as everything that happened')
    since = f'{days}.days.ago'
    # --remotes, not --all: a local branch nobody pushed is not evidence that
    # work LANDED, which is the question this section asks. It is also the
    # answer to a different one worth keeping in view -- see the printed
    # section, which names unpushed local work as its own finding.
    rc, log, _ = _run_git(repo_dir, 'log', '--remotes=origin',
                          f'--since={since}', '--date-order',
                          '--format=%h%x00%cs%x00%an%x00%s')
    if rc == 0:
        for line in log.splitlines():
            parts = line.split('\x00')
            if len(parts) == 4:
                out['commits'].append({'sha': parts[0], 'date': parts[1],
                                       'author': parts[2], 'subject': parts[3]})
    rc, refs, _ = _run_git(repo_dir, 'for-each-ref', 'refs/remotes/origin',
                           '--format=%(refname:short)%00%(committerdate:short)'
                           '%00%(authorname)%00%(committerdate:unix)')
    if rc == 0:
        cutoff = time.time() - days * 86400
        for line in refs.splitlines():
            parts = line.split('\x00')
            if len(parts) != 4 or not parts[3].strip().isdigit():
                continue
            if int(parts[3]) < cutoff:
                continue
            # `refs/remotes/origin/HEAD` shortens to the bare remote name
            # ("origin"), not to "origin/HEAD" -- so a name with no slash in
            # it is the remote's symbolic HEAD and not a branch at all. It
            # printed as a branch called "origin" in every repo on the first
            # run of this section.
            if '/' not in parts[0]:
                continue
            name = parts[0].split('/', 1)[1]
            if name == 'HEAD':
                continue
            out['branches'].append({'name': name, 'last': parts[1],
                                    'author': parts[2]})
    out['branches'].sort(key=lambda r: (r['last'], r['name']), reverse=True)
    # Uncommitted and unpushed work in THIS checkout is the same failure one
    # step earlier, and it is the cheapest thing here to check.
    rc, dirty, _ = _run_git(repo_dir, 'status', '--porcelain')
    out['dirty'] = len([l for l in dirty.splitlines() if l.strip()]) if rc == 0 else None
    return out


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
        # AN IDENTITY, SET ON THE INVOCATION. The comment that stood here
        # said `--no-commit` never writes a commit, so git never asks for
        # one. It does ask, and it REFUSES -- `Committer identity unknown`,
        # `fatal: unable to auto-detect email address`, exit 128. A CI
        # runner has no global identity and a session container does, which
        # is the whole reason this rehearsal was green locally and red in
        # continuous integration for five runs (2026-09-22). Set with `-c`
        # so nothing outlives the command, and at a `.invalid` address --
        # the old comment was right that a real address literal in this
        # public tree is a leak-gate finding.
        mrc, _, merr = _run_git(work, '-c', 'user.name=Precedent rehearsal',
                                '-c', 'user.email=rehearsal@invalid',
                                'merge', '--no-commit', '--no-ff',
                                f'origin/{target}')

        # A MERGE THAT COULD NOT RUN IS NOT A MERGE THAT DROPPED EVERYTHING.
        # Until 2026-09-22 those were the same answer: the return code was
        # discarded on the grounds that conflicts make it meaningless, so a
        # refusal left the index holding only the base branch's files and
        # `expected - present` named EVERY file on the integration branch.
        # The most alarming output this tool can produce was what it
        # produced when it had done nothing at all.
        #
        # The return code alone cannot decide it -- a conflicted merge is
        # the expected outcome and exits 1. MERGE_HEAD is the evidence that
        # a merge actually started: present after a clean `--no-commit`
        # merge AND after a conflicted one, absent when git refused. Absent
        # with a non-zero return is a refusal; absent with a zero return is
        # "Already up to date", which is a real clean result.
        # (practice: checks-plant-their-state)
        hrc, _, _ = _run_git(work, 'rev-parse', '--verify', '--quiet',
                             'MERGE_HEAD')
        if mrc != 0 and hrc != 0:
            out['status'] = 'error'
            out['note'] = (
                'the rehearsal merge could not run, so nothing here is a '
                'finding about your branches -- treat this as UNKNOWN, not '
                f'as clean and not as a drop. git said: {merr or "(nothing)"}')
            return out

        # THE SAME DEFECT, ONE LAYER DOWN. The merge is now known to have
        # run -- but these two reads are how the result is learned, and
        # until 2026-09-22 each coerced its own failure to an empty set.
        # An `ls-files` that fails leaves `present` holding only the
        # conflicts, so `expected - present` names almost every file on the
        # integration branch: the identical fabricated drop list the merge
        # refusal used to produce, arrived at by a different route and just
        # as confident. Neither read is allowed to fail quietly. UNKNOWN is
        # a worse-sounding answer than `clean` and a far better one than an
        # invented finding (practice: control-asserts-which-failure -- a
        # guard that cannot establish its own inputs says so).
        rc, conflicted, diff_err = _run_git(work, 'diff', '--name-only',
                                            '--diff-filter=U')
        if rc != 0:
            out['status'] = 'error'
            out['note'] = (
                f'the merge ran, but its result could not be read: '
                f'`git diff --name-only --diff-filter=U` exited {rc}. Treat '
                f'this as UNKNOWN -- nothing here is a statement about what '
                f'{target} would lose. git said: '
                f'{diff_err or "(nothing)"}')
            return out
        conflicts = {ln for ln in conflicted.splitlines() if ln}
        rc, staged, staged_err = _run_git(work, 'ls-files', '--stage')
        if rc != 0:
            out['status'] = 'error'
            out['note'] = (
                f'the merge ran, but its result could not be read: '
                f'`git ls-files --stage` exited {rc}. Treat this as UNKNOWN '
                f'-- nothing here is a statement about what {target} would '
                f'lose. git said: {staged_err or "(nothing)"}')
            return out
        present = set(conflicts)
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


# --- what landed on the base branch and never came across ---------------
# (practice: very-deep-check, pass 4)
#
# The rehearsal above asks what happens to OUR files when the integration
# branch finally lands. This asks the opposite question, and asks it much
# earlier: what has landed on the BASE branch that this branch has never
# taken? Work pinned to a long-lived integration branch stops looking at the
# base, and the base does not stop moving -- somebody fixes a bug on it, or
# lands a document -- and that change is invisible to every session working
# on the branch until the two are far enough apart that reconciling them is
# its own project. Morgan asked for it on 2026-09-12, with the limit stated
# in the same breath: report it, and ASK; never implement it automatically.

def base_branch_drift(repo_dir, target=None, base=None, limit=25):
    """-> None when this checkout's integration branch IS its base branch
    (nothing can drift from itself), else a dict:

        {'target', 'base', 'status', 'commits': [...], 'files': [...],
         'shallow': bool, 'note': str|None}

    status: findings | clean | cannot-tell | error. Each commit row is
    {'sha', 'date', 'subject', 'files'} -- enough to decide from, which a
    bare count never is.

    `git cherry` rather than `merge-base --is-ancestor`, for the same reason
    _unmerged_row uses it: work often reaches an integration branch by being
    CARRIED -- rewritten into that branch's own shape on the way -- rather
    than merged, so commit identity reports "never arrived" about changes
    whose content landed weeks ago. A patch-equivalent commit is not drift,
    and listing it as drift would train the reader to wave the whole list
    through.

    REPORTS ONLY. Nothing here merges, cherry-picks, fetches into a working
    branch or edits a file. The practice is explicit that the session hands
    this list to the person and asks before implementing any of it, which is
    the same shape precedent_upstream_check.py was given for this repo's own
    carry notice: *"I don't want it to merge invisibly, I'd like to do it in
    a session when I'm there."*
    """
    repo_dir = pathlib.Path(repo_dir)
    if not (repo_dir / '.git').exists():
        return None
    target = target or _declared_base_branch(repo_dir)
    base = base or _default_remote_branch(repo_dir)
    if not target or not base or target == base:
        return None
    out = {'target': target, 'base': base, 'status': 'cannot-tell',
           'commits': [], 'files': [], 'shallow': False, 'note': None}
    target_ref, base_ref = f'origin/{target}', f'origin/{base}'
    # --verify --quiet, never the bare form: `git rev-parse <missing-ref>`
    # exits non-zero but PRINTS the ref name back (AGENTS.md, gotchas).
    for ref in (base_ref, target_ref):
        rc, _, _ = _run_git(repo_dir, 'rev-parse', '--verify', '--quiet', ref)
        if rc != 0:
            _run_git(repo_dir, 'fetch', '--depth=5000', 'origin',
                     ref.split('/', 1)[1])
        rc, _, _ = _run_git(repo_dir, 'rev-parse', '--verify', '--quiet', ref)
        if rc != 0:
            out['note'] = (f'{ref} does not exist in this clone, and fetching '
                           f'it failed -- run `git fetch origin '
                           f'{ref.split("/", 1)[1]}` and re-run.')
            return out
    rc, shallow, _ = _run_git(repo_dir, 'rev-parse', '--is-shallow-repository')
    out['shallow'] = (rc == 0 and shallow.strip() == 'true')
    # The precondition for trusting `git cherry` at all: on a clone whose
    # history does not reach the merge base, cherry exits 0 and marks EVERY
    # commit `+`, which here would invent a base branch's whole history as
    # undelivered drift. Deepen once, then refuse rather than guess.
    if not _merge_base_resolves(repo_dir, target_ref, base_ref):
        _run_git(repo_dir, 'fetch', '--depth=5000', 'origin')
    if not _merge_base_resolves(repo_dir, target_ref, base_ref):
        out['note'] = (f'no merge base between {target_ref} and {base_ref} '
                       f'resolves in this clone, so the patch comparison '
                       f'cannot run and its result would be fiction. Deepen '
                       f'(`git fetch --unshallow origin`, or --depth=5000) '
                       f'and re-run. Reported as unknown, never as clean.')
        return out
    rc, cherry, err = _run_git(repo_dir, 'cherry', target_ref, base_ref)
    if rc != 0:
        out['status'] = 'error'
        out['note'] = f'git cherry {target_ref} {base_ref} failed: {err}'
        return out
    shas = [ln.split()[1] for ln in cherry.splitlines()
            if ln.startswith('+') and len(ln.split()) > 1]
    touched = set()
    for sha in shas[:limit]:
        rc, meta, _ = _run_git(repo_dir, 'show', '-s', '--format=%cs%x1f%s', sha)
        date, _, subject = (meta.partition('\x1f') if rc == 0
                            else ('', '', ''))
        # `git show <commit>:<path>` exits 128 with EMPTY stdout for two
        # unrelated reasons, so the return code is consulted rather than the
        # output read alone (AGENTS.md, gotchas).
        rc_f, names, _ = _run_git(repo_dir, 'show', '--name-only',
                                  '--format=', sha)
        files = sorted({ln for ln in names.splitlines() if ln}) if rc_f == 0 else []
        touched.update(files)
        out['commits'].append({'sha': sha[:12], 'date': date or None,
                               'subject': subject or None, 'files': files})
    out['truncated'] = max(0, len(shas) - limit)
    out['total'] = len(shas)
    out['files'] = sorted(touched)
    out['status'] = 'findings' if shas else 'clean'
    return out


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
                            'path': s['path'],
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


def _api_token():
    """-> (value, var_name) for a usable GitHub token, or (None, None).

    Read through precedent_source_credentials so there is ONE answer to
    "is there a credential here" (it also resolves
    PRECEDENT_GIT_TOKEN=inherit). Degrades to no token when the module is
    absent -- this engine is vendored into trees older than it.
    """
    try:
        import precedent_source_credentials as psc
        var = psc.token_var()
    except Exception:                           # noqa: BLE001 -- reported
        return None, None
    if not var:
        return None, None
    value = (os.environ.get(var) or '').strip()
    # A curl config file is a quoted format. A token carrying a quote, a
    # backslash or a newline would either break the parse or -- worse --
    # smuggle a second directive into it, so such a value is refused rather
    # than escaped. No GitHub token looks like that; a mis-set variable
    # (a whole `export` line pasted in, say) does.
    if not value or any(c in value for c in '"\\\n\r'):
        return None, var
    return value, var


def _api_json(path, timeout=20, auth=True):
    """-> (parsed, error). Never raises: the caller reports, it does not crash.

    DELEGATES TO github_budget.call, which is the one implementation of "ask
    GitHub something" in this engine. It caches within a run and counts what
    the run spent, so the GITHUB API BUDGET section below can report this
    tool's own bill rather than guessing at it -- and the second ask about a
    repository two of these trees both mention costs nothing.

    Degrades to the older uncached path where the module is absent: this
    engine is vendored into trees older than it, and a visibility audit that
    refused to run there would be a regression dressed as a fix.
    """
    if gh_budget is not None:
        return gh_budget.call(path, timeout=timeout, auth=auth)

    token, _var = _api_token() if auth else (None, None)
    argv = ['curl', '-s', '--max-time', str(timeout),
            '-H', 'Accept: application/vnd.github+json']
    if token:
        argv += ['-K', '-']
    argv.append(f'https://api.github.com/{path.lstrip("/")}')
    try:
        r = subprocess.run(
            argv, input=(f'header = "Authorization: Bearer {token}"\n'
                         if token else ''),
            capture_output=True, text=True, timeout=timeout + 10)
    except Exception as e:                      # noqa: BLE001 -- reported
        return None, f'curl failed: {e}'
    if r.returncode != 0:
        return None, f'curl exited {r.returncode}: {r.stderr.strip()[:120]}'
    try:
        return json.loads(r.stdout), None
    except ValueError:
        return None, f'not JSON: {r.stdout.strip()[:120]}'


def _markdown_sweep(repo_dir, timeout=900):
    """-> (summary_lines, findings_count, note). The whole tree's markdown,
    strictly (practice: very-deep-check, pass 3).

    The light check reads what a change TOUCHED and the deep check gates on
    it; neither ever looks at a file nobody has edited in months, and the
    warning classes -- unlinked references, unglossed acronyms, target=
    anchors -- are not gated anywhere at all, by design (they were, for an
    hour, and the gate refused a one-line edit over 111 pre-existing
    warnings). So they accumulate where only a sweep will find them, which
    is what `doc_lint.py --strict` exists for and why this is the only
    caller of it. It REPORTS a work list; it never refuses the run.

    Shelled out rather than imported: doc_lint computes its ROOT from its
    own location, so the copy that must run is the one in the repo being
    swept, not whichever one this module imported first."""
    script = pathlib.Path(repo_dir) / 'tools' / 'doc_lint.py'
    if not script.exists():
        return [], 0, (f'no tools/doc_lint.py in {repo_dir} -- nothing here '
                       f'checks markdown, which is a finding in itself')
    try:
        r = subprocess.run([sys.executable, str(script), '--strict', '--all'],
                           cwd=str(repo_dir), capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return [], 0, f'doc_lint --strict --all did not finish in {timeout}s'
    except Exception as e:                      # noqa: BLE001 -- reported
        return [], 0, f'doc_lint --strict --all could not run: {e}'
    out = (r.stdout or '') + (r.stderr or '')
    # The per-class/per-file summary, not the thousands of finding lines
    # above it -- those are for the session that picks a file and runs
    # doc_lint on it directly.
    marker = out.find('doc_lint --strict')
    if marker < 0:
        return [], 0, (f'doc_lint --strict --all exited {r.returncode} '
                       f'without printing a summary: {out.strip()[:200]}')
    summary = out[marker:].strip().splitlines()
    m = re.search(r'doc_lint --strict FAIL: ([\d,]+) finding', out)
    count = int(m.group(1).replace(',', '')) if m else 0
    return summary, count, None


# --- cross-repo absolute link check (practice: very-deep-check, pass 3) --
#
# doc_lint's broken-link check (check 4) is a single repo's own concern by
# design: it resolves a RELATIVE link against the linking file's own
# directory, and it explicitly skips absolute URLs. So a link written the
# way doc-references-are-links asks for cross-repo citations -- a full
# `https://github.com/<owner>/<repo>/blob/<ref>/<path>` URL, chosen
# precisely because a relative path cannot cross a repo boundary and still
# open for a raw-markdown reader -- is invisible to it. That includes a
# repo linking to ITSELF this way, not only to a sibling: the absolute
# form is exempt everywhere it appears, self-citation included.
#
# Found real, 2026-09-22: four links in precedent-individual citing files
# at the root of BestPractice (PRACTICE_ENGINE_PLAN.md,
# CHANGES_TO_TELL_ALEX.md) that actually live under spec/, plus a fifth
# citing WHAT_IS_THIS_AND_BENEFITS.md, a path with no trace anywhere in
# BestPractice's history. None of doc_lint --strict --all's findings, in
# either repo, was this bug -- the class was structurally unreachable to
# it, which is what a session reading only that summary would miss.
#
# WHAT THIS CHECKS. Every markdown link in every repo in force whose URL
# is `https://github.com/<owner>/<repo>/(blob|tree)/<ref>/<path>`, where
# `<owner>/<repo>` names a repo ALSO in force this run (compared by origin
# URL, not by the string) -- this session already has that repo cloned, so
# the check is a local git read, never a network fetch. `<ref>` is
# ambiguous on its own (a branch name may itself contain `/`), so the
# resolver tries the longest prefix of what follows `/blob/` that is a
# real local ref (a branch, `origin/<branch>`, a tag, or a bare commit)
# and treats the remainder as the path; a URL where no prefix resolves is
# reported broken on the ref itself, not skipped -- that is exactly what a
# reader clicking it gets, a 404, whether the file moved or the branch
# was deleted.
#
# WHAT IT DOES NOT CHECK. A link into a repo that is not ALSO in force
# this run -- an unrelated public repository, or a Precedent repo this
# session never opened -- reads exactly like check_broken_links' own skip
# of absolute URLs: out of reach without a live network call, which this
# deliberately never makes. And it is a Pass 3 READ, same as
# _markdown_sweep: it reports, it never refuses a commit or a push.
_GITHUB_URL_RE = re.compile(
    r'\[([^\]\n]*)\]\((https://github\.com/([\w.-]+)/([\w.-]+)/'
    r'(blob|tree)/([^)\s#]+)(#[^\s)]*)?)\)'
)
_CROSS_LINK_CODE_SPAN_RE = re.compile(r'`[^`]*`')
# Same reasoning as doc_lint's own LINK_CHECK_EXEMPT_DIRS: a deck slide's
# and an eval fixture's links are not references to audit against today's
# tree.
_CROSS_LINK_EXEMPT_DIRS = ('deck/', 'evals/')


def _local_ref_and_path(repo_dir, ref_and_path):
    """-> (ref, path), or (None, reason) if no local ref in `repo_dir` is
    a prefix of `ref_and_path`. Longest prefix first, so
    `claude/foo-bar/practices/x.md` resolves to the branch
    `claude/foo-bar`, not the near-always-wrong single segment `claude`.
    `path` comes back empty for a bare `tree/<ref>` link (a link to a
    branch itself, no file inside it) -- that is a real, common link
    shape and not a truncated one."""
    parts = ref_and_path.split('/')
    for i in range(len(parts), 0, -1):
        ref = '/'.join(parts[:i])
        path = '/'.join(parts[i:])
        for candidate in (ref, f'origin/{ref}', f'refs/tags/{ref}'):
            rc, _out, _err = _run_git(repo_dir, 'rev-parse', '--verify',
                                       '--quiet', candidate + '^{commit}')
            if rc == 0:
                return candidate, path
    return None, ("no local ref is a prefix of this URL (branch deleted, "
                   "never fetched here, or a bare commit this clone lacks)")


def _path_exists_at_ref(repo_dir, ref, path):
    rc, _out, _err = _run_git(repo_dir, 'cat-file', '-e', f'{ref}:{path}')
    return rc == 0


def _cross_repo_link_check(targets):
    """-> (finding_lines, count, notes). Every repo in `targets`, read
    against every repo in `targets` (self included) -- see the module
    comment above for what this catches that doc_lint cannot."""
    slug_to_target = {}
    for name, repo_dir in targets:
        url = _origin_url(repo_dir)
        m = re.search(r'github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$', url)
        if m:
            slug_to_target[f'{m.group(1)}/{m.group(2)}'] = (name, pathlib.Path(repo_dir))

    findings = []
    scanned = 0
    for name, repo_dir in targets:
        root = pathlib.Path(repo_dir)
        rc, tracked, _err = _run_git(repo_dir, 'ls-files', '*.md')
        if rc != 0:
            findings.append(f'{name}: CANNOT TELL -- `git ls-files` failed, not scanned')
            continue
        for rel in tracked.splitlines():
            if not rel.strip() or rel.startswith(_CROSS_LINK_EXEMPT_DIRS):
                continue
            try:
                text = (root / rel).read_text(encoding='utf-8', errors='ignore')
            except OSError:
                continue
            in_fence = False
            for lineno, line in enumerate(text.splitlines(), 1):
                if line.lstrip().startswith(('```', '~~~')):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                stripped = _CROSS_LINK_CODE_SPAN_RE.sub('', line)
                for m in _GITHUB_URL_RE.finditer(stripped):
                    _label, url, owner, repo_name, _kind, ref_and_path, _frag = m.groups()
                    slug = f'{owner}/{repo_name}'
                    if slug not in slug_to_target:
                        continue  # not a repo this session has open
                    scanned += 1
                    target_name, target_dir = slug_to_target[slug]
                    ref, path_or_reason = _local_ref_and_path(target_dir, ref_and_path)
                    if ref is None:
                        findings.append(f'{name}/{rel}:{lineno}  {url}  -- {path_or_reason}')
                        continue
                    if not path_or_reason:
                        continue  # a bare tree/<ref> link -- the ref existing is the whole claim
                    if not _path_exists_at_ref(target_dir, ref, path_or_reason):
                        findings.append(
                            f'{name}/{rel}:{lineno}  {url}  -- {path_or_reason!r} '
                            f'does not exist at {target_name} @ {ref}')
    notes = [f'{scanned} absolute github.com link(s) checked, into '
             f'{len(slug_to_target)} repo(s) also in force this run.']
    return findings, len(findings), notes


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


def repo_visibility_audit(repo_dir, blocklist_path=None, out=None):
    """-> (findings, notes). Findings are real; notes are what could not run.

    A repository this PUBLIC tree names, which is PRIVATE, is a finding
    whether or not anybody blocklisted it -- that is the Write-Like case. A
    blocklist entry naming a repository that is now PUBLIC is the opposite
    finding: it costs false positives and pressure to delete real content.
    """
    findings, notes = [], []
    out = out if out is not None else sys.stdout   # see report_freshness

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
        # THE SAME FAIL-OPEN THE PUSH GATE NOW REFUSES, in the tool that
        # actually runs the visibility audit. The loop above carries its own
        # copy of the allow regex, so a directive that parses as neither is
        # invisible HERE too -- and the cost is the opposite of the gate's: a
        # dropped `allow` line makes this audit report a disclosure somebody
        # already accepted, and a dropped `private-owner` line means the
        # blocklist says a rule is configured while nothing enforces it.
        # Reported as findings rather than an exit, because an audit that
        # stops on the first bad line cannot tell you what else is wrong
        # (practice: fail-gracefully -- keep going, never look complete). The
        # push gate is where this is fatal; leak_gate.repo_policy_errors is
        # the one implementation, so the two cannot drift in what they call
        # malformed.
        for _ln, _txt, _why in leak_gate.repo_policy_errors(bl):
            where = f'{bl}:{_ln}' if _ln else str(bl)
            findings.append(
                f'{where}: {_why}. A `# visibility-audit:` line that does not '
                f'parse is indistinguishable from an ordinary comment, so the '
                f'allow lines below may be narrower than the file reads -- and '
                f'this audit and the push gate are both reading it.'
                + (f' Line reads: {_txt}' if _txt else ''))

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
    # COLLAPSED, NOT DROPPED. The 2026-09-11 run spent about 1,738 tokens here and
    # 26 of its 28 lines were one identical sentence -- "GitHub access to this
    # repository is not enabled for this session" -- repeated per repository.
    # Morgan, 2026-09-13, approved cheapening it: the check earns its place
    # (a private name in a public tree is the failure it exists for) and the
    # repetition does not. One line per DISTINCT reason, carrying the count
    # and every name, says exactly as much and is read; twenty-six copies of
    # one sentence are skimmed, which is how a real finding sitting among
    # them gets missed. The full paragraph is still printed for a repository
    # whose visibility was actually determined -- that is where the content
    # differs per repository. (practice: very-deep-check)
    unreachable = {}
    for (owner, name), files in sorted(refs.items()):
        data, err = _api_json(f'repos/{owner}/{name}')
        if err:
            unreachable.setdefault(str(err), []).append(f'{owner}/{name}')
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
                # The 26-of-28 case: the API answers, but the answer is
                # "this session cannot see that repository". Collapsed with
                # the `err` ones above -- same non-result, same one line.
                unreachable.setdefault(str(msg), []).append(f'{owner}/{name}')
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

    for why, names in sorted(unreachable.items()):
        notes.append(
            f'visibility not checked for {len(names)} repositor'
            f'{"y" if len(names) == 1 else "ies"} ({why}): '
            + ', '.join(sorted(names)))

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


def leak_stem_recommendations(repo_dir, blocklist_path=None):
    """-> [str] recommendations: private-by-default clones with no stem.

    THE SAME SURVEY leak_gate.py runs, deliberately moved rather than copied
    (pass 2 asks whether two implementations of one rule have drifted -- so
    this calls the gate's own functions and owns none of the logic).

    WHY IT LIVES HERE NOW. The gate printed this on every run, and a note
    printed beside every push is one a person stops reading: Morgan,
    2026-09-12, asking for exactly this move -- "you look to see if anything
    is being leaked that you think shouldn't be and you make the
    recommendation to me ... but only when I ask for it as part of a very
    thorough review I'm in the mindset of doing". Silencing it in the gate
    without a home to move it to would have traded noise for a blind spot.

    Offline by construction: it reads clones on this disk and the blocklist,
    and asks GitHub nothing. repo_visibility_audit above is the networked
    half, and answers the other question -- the repositories this tree
    already NAMES.
    """
    path = pathlib.Path(blocklist_path).expanduser() if blocklist_path else None
    if path is None:
        path, _how = leak_gate.resolve_blocklist_path()
    if path is None or not path.is_file():
        return []
    owners, allowed = leak_gate.parse_repo_policy(path)
    if not owners:
        return []
    pats = leak_gate.load_default_blocklist() + leak_gate._parse_blocklist(path)
    gaps = leak_gate.uncovered_repo_stems(
        leak_gate.local_clone_refs(pathlib.Path(repo_dir).resolve()), owners, allowed, pats)
    out = []
    for owner, name in gaps:
        out.append(
            f'{owner}/{name} is a clone on this disk under a private-by-default '
            f'owner, and no blocklist pattern matches its bare name "{name}". '
            f'The qualified form is refused by the allowlist; the short form '
            f'somebody actually types is not. RECOMMENDATION: add a stem -- '
            f'truncate to a distinctive head and measure the hit count against '
            f'the tree before committing to the cut -- or decide the name may '
            f'be said and add an `allow` line. Nothing in this tree says the '
            f'name today, so this is latent risk, not a hit.')
    return out


# --------------------------------------------------------------------------
# Repos in force: does each one still exist, and can work still land in it?
# --------------------------------------------------------------------------
#
# Every repo in force here is opened AUTOMATICALLY, by something nobody
# watches: the SessionStart hook clones each declared source, the freshness
# gate fetches each one, and precedent_refresh_sources pulls them. All of
# that assumes the repository on the other end is still there and still
# accepts a push. Three states break that assumption and NONE of them is
# visible from this side:
#
#   DELETED or RENAMED. The clone still works from a redirect, or stops
#   working with an error that reads like a credential problem -- which is
#   the diagnosis AGENTS.md's gotchas show sessions reaching for first, and
#   costing hours to. A renamed source keeps resolving through GitHub's
#   redirect until somebody creates a new repository under the old name.
#
#   ARCHIVED. The worst of the three, because nothing fails until the end:
#   an archived repository clones, fetches and reads exactly like a live
#   one, and refuses every push. A session can spend its whole run editing
#   a source it will never be able to write to, and the freshness gate --
#   which only ever compares against origin -- will call it clean the whole
#   time.
#
#   ACCESS REVOKED. Indistinguishable from deleted over the API, and the
#   remedy is different, so the finding says both rather than picking one.
#
# WHY HERE rather than in a gate: it needs the network, like the visibility
# audit above, and for the same reason it cannot live in the push gate.
#
# WHY IT IS WORTH THE CALL: this is the check that ends a retry loop. A
# source that no longer exists is re-cloned at every session start, forever,
# by a hook whose failure is deliberately quiet (practice: fail-gracefully)
# -- and a quiet failure repeated daily is one nobody ever traces.
#
# LIKE THE VISIBILITY AUDIT, THIS WRITES NO NAME ANYWHERE. The private
# sources' names appear in their own origin URLs; findings go to the
# session's own output and never into a file in this tree.

_GH_REMOTE_RE = re.compile(
    r'github\.com[:/](' + _OWNER + r')/([A-Za-z][\w.-]*?)(?:\.git)?/?$')


def _repos_in_force(repo_root, sources=(), missing=(), base_url=None):
    """-> [(label, url, path_or_None)], one per repo this session opens.

    A source that resolved is asked for its OWN origin -- what it was
    cloned from is the thing being fetched every session, which is not
    necessarily what anything declares. A source that did NOT resolve has
    no clone to ask, so its URL is rebuilt the way the bootstrap builds it
    (`<PRECEDENT_SOURCE_BASE_URL>/<name>`); that is the case this check
    exists for, since "declared, never resolved" is exactly what a deleted
    source looks like from here.
    """
    rows, seen = [], set()

    def _add(label, url, path):
        url = (url or '').strip()
        if not url or url in seen:
            return
        seen.add(url)
        rows.append((label, url, path))

    _add('this checkout', _origin_url(repo_root), repo_root)
    for s in sources or ():
        _add(f"{s['level']} source {s['name']!r}", _origin_url(s['path']),
             s['path'])
    base = (base_url if base_url is not None
            else os.environ.get('PRECEDENT_SOURCE_BASE_URL', ''))
    base = (base or '').strip().rstrip('/')
    for m in missing or ():
        url = _origin_url(m['path']) if m.get('path') else ''
        if not url and base and m.get('name'):
            url = f"{base}/{m['name']}"
        _add(f"{m['level']} source {m['name']!r} (declared, not resolved)",
             url, m.get('path'))
    return rows


# THE PROBE MOVED, 2026-09-14, and this import is the point of the move.
# `can_land_here` was defined here from 2026-09-13 and was correct. But this
# file is in neither ENGINE_FILES nor CONSUMER_ENGINE_FILES, so it reaches no
# adopting repo -- and the probe was wanted at SESSION START, where it would
# have saved a session four days and about a hundred dollars (see
# precedent_access_check's own docstring). A session-start step importing THIS
# module would have worked in the upstream repo and silently WARNed in every
# repo that actually vendors the engine.
#
# So the definition went DOWN into the small file that travels, and the big
# on-request audit imports it (practice: fix-the-original). Keeping a copy
# here is how two probes drift apart; `access_audit` below is unchanged and
# still owns the TABLE, which is this tool's own presentation concern.
from precedent_access_check import can_land_here  # noqa: E402


def access_audit(repo_root, sources=(), out=None):
    """-> (rows, notes). One probe per repo in force, printed as a table.

    Prints rather than fails: this is scope information for the session about
    to read, not a gate.
    """
    out = out if out is not None else sys.stdout
    rows, notes = [], []
    targets = [('this checkout', repo_root)]
    for s in sources or ():
        targets.append((f"{s['level']} source {s['name']!r}", s['path']))
    print('\nACCESS -- can THIS session land work in each repo in force', file=out)
    for label, path in targets:
        verdict, detail = can_land_here(path)
        rows.append((label, path, verdict, detail))
        mark = {'land': 'LAND    ', 'handoff': 'HANDOFF ',
                'unknown': 'UNKNOWN '}[verdict]
        print(f'  {mark} {label} ({path})'
              + ('' if verdict == 'land' else f' -- {detail}'), file=out)
    n_handoff = sum(1 for r in rows if r[2] == 'handoff')
    n_unknown = sum(1 for r in rows if r[2] == 'unknown')
    if n_handoff or n_unknown:
        notes.append(
            f'{n_handoff} repo(s) need a handoff and {n_unknown} could not be '
            f'probed. A finding in one of those does not end in a commit from '
            f'this session -- it ends in a paste-ready prompt for a new session '
            f'(practice: prompt-please). Group them that way when you report.')
        print('  ' + notes[-1], file=out)
    return rows, notes


def boundary_audit(repo_root, sources=(), skip_api=False, out=None):
    """-> (findings, notes). One row per repo in force that draws a
    contributor boundary, plus the document-project skeleton.

    A boundary is a SETTING, not a document (practice: very-deep-check,
    pass 2, "is a boundary a setting or a document?"). spec/CONTRIBUTOR_ACCESS.md
    keeps a contributor out of the machinery with two things that can each
    silently stop being true while every document goes on describing them:
    a generated CODEOWNERS that a hand-edit or a stale registry can leave
    saying something other than its source, and branch protection that
    lives on a GitHub settings page nothing in the tree can see. So this
    reads both, per repo:

      - build_codeowners --check: is the generated file current with the
        registry that owns it (a project's `owned_paths` + `maintainers` in
        precedent.json, a practice set's approvers.json)?
      - precedent_boundary_check: is the base branch protected the way the
        plan needs? PASS is a row, FAIL is a finding, and UNVERIFIED is a
        NOTE and never a pass -- a session without a token that can read
        protection settings learns here that it could not look, which is
        different from learning that the boundary is off
        (practice: fail-gracefully).

    A repo with neither registry draws no boundary and says so in one line;
    that is the normal state of this repository and of an individual set.
    The document-project skeleton under templates/ gets the generator check
    only -- its origin is this repository's, so asking GitHub about "its"
    protection would answer a question about the wrong repo.
    """
    import contextlib
    out = out if out is not None else sys.stdout
    findings, notes = [], []
    try:
        import build_codeowners as bco
        import precedent_boundary_check as pbc
    except ImportError as exc:  # an engine vendored without the pair
        notes.append(f'not checked: {exc}')
        return findings, notes
    root = pathlib.Path(repo_root)
    targets = [('this checkout', root, True)]
    for s in sources or ():
        targets.append((f"{s['level']} source {s['name']!r}",
                        pathlib.Path(s['path']), True))
    skeleton = root / 'templates' / 'document-project'
    if (skeleton / 'precedent.json').is_file():
        targets.append(('templates/document-project (skeleton: generator only)',
                        skeleton, False))
    for label, path, ask_github in targets:
        cfg, approvers = path / 'precedent.json', path / 'approvers.json'
        draws = False
        if cfg.is_file():
            try:
                draws = json.loads(cfg.read_text(encoding='utf-8')).get(
                    'owned_paths') is not None
            except ValueError as exc:
                findings.append(f'{label}: precedent.json does not parse ({exc})')
                print(f'  FINDING    {label} -- precedent.json does not parse',
                      file=out)
                continue
        if not draws and not approvers.is_file():
            print(f'  none       {label} -- draws no boundary (no owned_paths, '
                  f'no approvers.json)', file=out)
            continue
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = bco.main(check_only=True, root=path)
        text = buf.getvalue().strip()
        line = text.splitlines()[-1] if text else '(no output)'
        if rc != 0:
            findings.append(f'{label}: {line}')
            print(f'  FINDING    {label} -- {line}', file=out)
        else:
            print(f'  current    {label} -- {line}', file=out)
        if not draws or not ask_github:
            continue
        if skip_api:
            notes.append(f'{label}: protection not asked (--skip-liveness); '
                         f'not a pass')
            print(f'  not asked  {label} -- --skip-liveness', file=out)
            continue
        r = pbc.assess(path)
        why = '; '.join(r['reasons'])
        if r['verdict'] == 'FAIL':
            findings.append(f'{label}: protection FAIL -- {why}')
            print(f'  FINDING    {label} -- protection FAIL -- {why}', file=out)
        elif r['verdict'] == 'UNVERIFIED':
            notes.append(f'{label}: protection UNVERIFIED -- {why} -- not a pass')
            print(f'  UNVERIFIED {label} -- {why}', file=out)
        else:
            print(f'  PASS       {label} -- protection on, shaped as the plan '
                  f'needs, CODEOWNERS in the tree', file=out)
    return findings, notes


# The files a session reads before it does anything. A wrong repository
# name here is worse than anywhere else in the tree, because it is the one
# document nobody chooses to open -- it is simply in force.
INSTRUCTION_FILES = ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md',
                     'WHERE_THINGS_ARE.md')

# `github.com/owner/name`, and a bare `owner/name` where the owner is one
# this session already knows from a real remote. The second half is what
# makes this usable: an unanchored `\w+/\w+` matches `practices/park-it.md`
# and `tools/doc_lint.py` on every line of every instructions file. Anchor
# on owners that actually exist here and the noise goes to zero.
_GH_URL_REF_RE = re.compile(r'github\.com/([A-Za-z0-9][\w.-]*)/([\w.-]+?)(?=[/\s)\]"\'`>,.]|$)')


def _known_owners(rows):
    """-> {owner} seen in the remotes of the repos in force."""
    owners = set()
    for _label, url, _path in rows:
        m = _GH_REMOTE_RE.search(url or '')
        if m:
            owners.add(m.group(1))
    return owners


def _repo_refs_in_instruction_files(rows):
    """-> {(owner, name): [where, ...]} for every repository an always-loaded
    instructions file NAMES, across every repo in force.

    WHY THIS IS NOT A CLOSE READ (Morgan, 2026-09-21, strength: decided).
    An Update Vendors pass found a consuming repo's AGENTS.md naming
    `VoiceDefinitionMorgan` twice -- in the session-start step and again in
    a tool's description -- where the real repository is `VoiceDefMorgan`.
    That file's own step 1 warns about a source name going stale silently.

    Two checks came close and neither asks this. `repo-reference-allowlist`
    asks whether a name MAY be mentioned -- a leak control, offline by
    design because it runs in the push gate. `repos_in_force_audit` below
    asks whether a repository EXISTS, but only about the ones declared as
    sources. A name in prose is not a source, so a repository reference was
    checked for permission and never for existence.

    Anchored two ways, and the second is what keeps it quiet: a full
    github.com URL, or a bare `owner/name` whose owner is one this session
    has actually seen on a remote. Without that anchor the pattern matches
    every `practices/foo.md` and `tools/bar.py` in the file.
    """
    owners = _known_owners(rows)
    bare = (re.compile(r'(?<![\w./-])(' + '|'.join(re.escape(o) for o in sorted(owners))
                       + r')/([A-Za-z0-9][\w.-]*)') if owners else None)
    found = {}
    for label, _url, path in rows:
        if not path:
            continue
        for name in INSTRUCTION_FILES:
            f = pathlib.Path(path) / name
            try:
                text = f.read_text(encoding='utf-8', errors='ignore')
            except OSError:
                continue
            hits = set(_GH_URL_REF_RE.findall(text))
            if bare:
                hits |= set(bare.findall(text))
            for owner, repo in hits:
                repo = repo.rstrip('.,);:')
                if not repo or repo.endswith('.md') or repo.endswith('.py'):
                    continue
                found.setdefault((owner, repo), []).append(f'{label}:{name}')
    return found


def instruction_file_repo_refs_audit(repo_root, sources=(), missing=(),
                                     base_url=None, out=None, already=()):
    """-> (findings, notes). One API call per DISTINCT repository named in an
    always-loaded instructions file and not already probed as a source.

    `already` is the set of (owner, name) repos_in_force_audit has just
    asked about, so the two sections never pay twice for the same name --
    this tool reports its own API bill, and a section that silently doubled
    a cost the run already paid would make that report a lie.
    """
    findings, notes = [], []
    out = out if out is not None else sys.stdout
    rows = _repos_in_force(repo_root, sources, missing, base_url)
    refs = _repo_refs_in_instruction_files(rows)
    already = {(o.lower(), n.lower()) for o, n in already}
    todo = {k: v for k, v in refs.items()
            if (k[0].lower(), k[1].lower()) not in already}
    if not refs:
        print('  instruction-file repo references: none found', file=out)
        return findings, notes
    token, var = _api_token()
    checked = 0
    for (owner, name), where in sorted(todo.items()):
        seen = ', '.join(sorted(set(where)))
        data, err = _api_json(f'repos/{owner}/{name}')
        if err:
            notes.append(f'{owner}/{name} (named in {seen}): not checked ({err})')
            continue
        if not isinstance(data, dict) or 'full_name' not in data:
            msg = str((data or {}).get('message', 'no repository in response'))
            if 'Not Found' in msg and token:
                findings.append(
                    f'{owner}/{name} is named in {seen} and DOES NOT EXIST '
                    f'-- asked with a credential ({var}). An instructions '
                    f'file is the one document every session reads before '
                    f'doing anything, so a name that resolves to nothing '
                    f'sends every one of them somewhere that is not there. '
                    f'Find the real name and fix every occurrence, not the '
                    f'first.')
            elif 'Not Found' in msg:
                notes.append(
                    f'{owner}/{name} (named in {seen}): Not Found asked '
                    f'ANONYMOUSLY, which is also what a private repository '
                    f'answers -- says nothing either way. Set '
                    f'PRECEDENT_GIT_TOKEN and re-run.')
            else:
                notes.append(f'{owner}/{name} (named in {seen}): not checked ({msg})')
            continue
        checked += 1
        canonical = str(data.get('full_name') or '')
        if canonical and canonical.lower() != f'{owner}/{name}'.lower():
            findings.append(
                f'{owner}/{name} is named in {seen} and the API answers '
                f'{canonical} -- it has been RENAMED. The old name keeps '
                f'working through a redirect that lasts only until somebody '
                f'creates a repository under it, which is why this is worth '
                f'fixing before it breaks rather than after.')
    print(f'  instruction-file repo references: {len(refs)} named, '
          f'{len(refs) - len(todo)} already asked as sources, '
          f'{checked} of {len(todo)} answered'
          + (f' -- {len(findings)} finding(s)' if findings else ''), file=out)
    return findings, notes


def repos_in_force_audit(repo_root, sources=(), missing=(), base_url=None,
                         out=None):
    """-> (findings, notes). One API call per repo in force."""
    findings, notes = [], []
    out = out if out is not None else sys.stdout   # see report_freshness
    rows = _repos_in_force(repo_root, sources, missing, base_url)
    token, var = _api_token()
    checked = bad = 0
    for label, url, _path in rows:
        m = _GH_REMOTE_RE.search(url)
        if not m:
            notes.append(f'{label}: origin is not a github.com remote '
                         f'({url[:60]}) -- liveness not checked.')
            continue
        owner, name = m.group(1), m.group(2)
        data, err = _api_json(f'repos/{owner}/{name}')
        if err:
            notes.append(f'{label} ({owner}/{name}): not checked ({err})')
            continue
        if not isinstance(data, dict) or 'full_name' not in data:
            msg = str((data or {}).get('message', 'no repository in response'))
            if 'Not Found' in msg and token:
                findings.append(
                    f'{label} ({owner}/{name}): the API reports Not Found, '
                    f'ASKED WITH A CREDENTIAL ({var}) -- so the repository '
                    f'has been deleted or renamed, or this token\'s access '
                    f'to it was revoked. Everything that opens it '
                    f'automatically -- the session-start clone, this '
                    f'check\'s own fetch, precedent_refresh_sources -- is '
                    f'retrying it every session and failing quietly. Find '
                    f'where it is now and repoint the declaration, or stop '
                    f'declaring it.')
            elif 'Not Found' in msg:
                notes.append(
                    f'{label} ({owner}/{name}): the API reports Not Found, '
                    f'asked ANONYMOUSLY -- which is also what a private '
                    f'repository answers, so this says nothing either way. '
                    f'Set PRECEDENT_GIT_TOKEN (INSTALL.md section 8) '
                    f'and re-run to get an answer.')
            else:
                notes.append(f'{label} ({owner}/{name}): not checked ({msg})')
            continue
        checked += 1
        before = len(findings)
        if data.get('archived'):
            findings.append(
                f'{label} ({owner}/{name}) is ARCHIVED. It clones, fetches '
                f'and reads exactly like a live repository and refuses every '
                f'push, so nothing here reports it: the freshness gate '
                f'compares against origin and calls it clean. Work done in '
                f'it cannot land. Unarchive it, or stop declaring it.')
        if data.get('disabled'):
            findings.append(
                f'{label} ({owner}/{name}) is DISABLED by GitHub. Same shape '
                f'as archived: it reads and does not accept work.')
        canonical = str(data.get('full_name') or '')
        if canonical and canonical.lower() != f'{owner}/{name}'.lower():
            findings.append(
                f'{label} is declared or cloned as {owner}/{name} and the '
                f'API answers {canonical} -- it has been RENAMED, and every '
                f'clone and fetch is running through a redirect that lasts '
                f'only until somebody creates a repository under the old '
                f'name. Repoint the remote (git remote set-url) and any '
                f'declaration that names it.')
        if len(findings) > before:
            bad += 1
    # `checked` is how many repos ANSWERED, which is not how many are
    # healthy -- an archived repo answers perfectly. Counting the two
    # separately is the same correction the visibility audit above already
    # had to make: a check that reports its own coverage as a pass rate is
    # the shape this whole tool exists to catch.
    print(f'  repos in force: {checked} of {len(rows)} answered '
          f'({checked - bad} live and writable'
          + (f', {bad} NOT -- see the findings' if bad else '') + ')'
          + ('' if checked == len(rows) else
             f'; {len(rows) - checked} could NOT be determined -- see the '
             f'notes, they are not passes'), file=out)
    return findings, notes


# ---------------------------------------------------------------------------
# THE COMPONENT LEDGER (practice: very-deep-check).
#
# This check grew a section at a time -- each one added because a real run
# wanted it -- and nothing has ever asked the reverse question: does any of
# them still earn its place? A section that has found nothing across several
# runs is not automatically waste (a guard that never fires may be the reason
# nothing is broken), but nobody could even ASK, because no run recorded what
# its parts returned or cost.
#
# So every section reports three things -- what it found, what it printed,
# how long it took -- and the run is appended to a ledger on disk, because
# the question is a comparison ACROSS runs and one run cannot answer it
# (practice: repo-is-memory: a figure that lives only in a chat thread is
# already lost). The cross-run read is printed at the end of every run.
#
# WHAT "tokens" MEANS HERE, and it is the narrow thing: the tokens this
# section PRINTED, which is what it costs the session's context to read it.
# It is not the model's spend on judging that material, which no tool here
# can see -- claiming otherwise would be a manufactured figure
# (practice: no-invented-specifics). The expensive half of this check is the
# four passes a session works by hand, and a session records what those cost
# with --record-pass, from its own measurement, or not at all.
# The ledger belongs to the REPO BEING CHECKED, not to this engine's own
# checkout, and that distinction was got wrong once in the hour this landed:
# with the path anchored at ROOT, every harness fixture that ran the tool
# against a scratch repository appended a row about that scratch repository
# to THIS repository's ledger -- six of them inside one harness run, each
# one a 20-section row whose averages and quiet-section verdicts were about
# a temporary directory. The cross-run read is a comparison, so a foreign
# row does not merely add noise: it moves every number in it.
LEDGER_RELPATH = pathlib.Path('record') / 'very-deep-check-ledger.json'


def ledger_path_for(repo_root=None):
    return pathlib.Path(repo_root or ROOT) / LEDGER_RELPATH
LEDGER_VERSION = 1

# How many recorded runs a section has to come back empty across before the
# ledger asks about it. A threshold nobody decided is doctrine, so it is
# declared here as an input rather than buried in a comparison
# (practice: constants-are-risk-inputs). 3 is a STARTING VALUE, not a
# measured one: it is the smallest number at which "it found nothing" stops
# reading as "nothing was wrong that day".
QUIET_RUNS_BEFORE_QUESTION = 3

# The ledger keeps the most recent runs and says so when it drops one.
# Silently discarding history is the failure this file exists to avoid.
LEDGER_KEEP_RUNS = 50


class _Tee:
    """Writes through to the real stream and keeps a copy for measuring."""

    def __init__(self, real):
        self.real, self.buf = real, io.StringIO()

    def write(self, s):
        self.buf.write(s)
        return self.real.write(s)

    def flush(self):
        self.real.flush()

    def isatty(self):
        return False


class RunLedger:
    """Per-section results and cost for one run, plus the runs before it.

    Deliberately NOT a context manager wrapping each section: the sections
    are long inline blocks in main(), and re-indenting three thousand lines
    to gain a `with` is a large diff whose every hunk has to be read for a
    change that is really two lines per section.
    """

    def __init__(self, path=None, repo=None, argv=()):
        path = path if path is not None else ledger_path_for(repo)
        self.path = pathlib.Path(path)
        self.repo = str(repo) if repo else None
        self.argv = list(argv)
        self.components = []
        self.passes = []
        self._open = None
        self._real_stdout = None
        self._t0 = time.monotonic()
        # practice: timestamps-carry-offset -- the person's zone, with its
        # offset, never the container's UTC.
        self.started = precedent_time.stamp_iso(repo)
        self.date = precedent_time.today(repo)
        self.history = self._load()
        self.saved = False

    # -- history ---------------------------------------------------------
    def _load(self):
        if not self.path.is_file():
            return []
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except (ValueError, OSError) as exc:
            # Loud and non-fatal: a ledger that does not parse is a finding
            # about the ledger, never a reason to lose this run's check
            # (practice: fail-gracefully).
            print(f"  note: {self.path} does not parse ({exc}) -- this run "
                  f"is recorded, the runs before it cannot be read.",
                  file=sys.stderr)
            return []
        runs = data.get('runs')
        return runs if isinstance(runs, list) else []

    # -- recording one section -------------------------------------------
    def start(self, name, kind='mechanical'):
        """Begin measuring a section. Everything printed until end() counts."""
        if self._open is not None:          # a section left open by a raise
            self.end(status='aborted')
        self._open = {'name': name, 'kind': kind, 'started': time.monotonic()}
        self._real_stdout = sys.stdout
        sys.stdout = _Tee(sys.stdout)

    def end(self, findings=None, items=None, status=None, extra_seconds=0.0):
        """Close the open section.

        `findings` is the count of things a person has to act on. None is
        NOT zero and is never folded into it: None means this section does
        not produce a countable finding, or could not measure one, and the
        cross-run read below refuses to grade an unknown as quiet.
        """
        if self._open is None:
            return
        tee, self._open['tee'] = sys.stdout, None
        sys.stdout = self._real_stdout
        printed = tee.buf.getvalue() if isinstance(tee, _Tee) else ''
        row = {
            'name': self._open['name'],
            'kind': self._open['kind'],
            'findings': findings,
            'items': items,
            # practice: one-formatter-per-quantity -- the same words x 1.3
            # estimate build_views.py caps the resident block with, so a
            # token here and a token there are the same unit.
            'output_tokens': bv._approx_tokens(printed),
            'seconds': round(time.monotonic() - self._open['started']
                             + (extra_seconds or 0.0), 2),
        }
        if status:
            row['status'] = status
        elif findings is None:
            row['status'] = 'material' if self._open['kind'] == 'read' else 'unknown'
        elif findings:
            row['status'] = 'findings'
        else:
            row['status'] = 'clean'
        self.components.append(row)
        self._open = None

    def skipped(self, name, why, kind='mechanical'):
        """Record a section this run did not run, and why."""
        self.components.append({'name': name, 'kind': kind, 'findings': None,
                                'items': None, 'output_tokens': 0,
                                'seconds': 0.0, 'status': 'skipped',
                                'note': why})

    # -- writing ---------------------------------------------------------
    def record(self):
        return {
            'run_id': self.started,
            'date': self.date,
            'repo': self.repo,
            'argv': self.argv,
            'seconds': round(time.monotonic() - self._t0, 2),
            'components': self.components,
            'passes': self.passes,
        }

    def finish(self, completed=True):
        if self._open is not None:
            self.end(status='aborted')
        if self.saved:
            return
        run = self.record()
        run['completed'] = bool(completed)
        runs = list(self.history) + [run]
        dropped = max(0, len(runs) - LEDGER_KEEP_RUNS)
        if dropped:
            runs = runs[dropped:]
            print(f"  note: the ledger keeps the last {LEDGER_KEEP_RUNS} "
                  f"runs; {dropped} older run(s) dropped.", file=sys.stderr)
        payload = {
            '_generated_by': 'tools/very_deep_check.py -- never hand-edit; '
                             'each run appends itself',
            'ledger_version': LEDGER_VERSION,
            'runs': runs,
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(payload, indent=2) + '\n',
                                 encoding='utf-8')
            self.saved = True
        except OSError as exc:
            print(f"  note: could not write {self.path} ({exc}) -- this "
                  f"run's component results are NOT recorded.",
                  file=sys.stderr)

    # -- the cross-run read ----------------------------------------------
    def report(self, out=None):
        out = out if out is not None else sys.stdout   # see report_freshness
        print("COMPONENT LEDGER -- what each part of this check returned, and "
              "what it cost\n", file=out)
        print("  Tokens are what the section PRINTED (words x 1.3) -- the "
              "context it costs\n  a session to read it, not the model's "
              "spend on judging it, which nothing\n  here can see. Findings "
              "are things a person has to act on; '--' means the\n  section "
              "produces material to read rather than a countable finding.\n",
              file=out)
        print(f"  {'result':>9}  {'find':>5}  {'out-tok':>8}  {'secs':>6}  "
              f"section", file=out)
        for row in self.components:
            find = '--' if row['findings'] is None else f"{row['findings']:,}"
            print(f"  {row['status']:>9}  {find:>5}  "
                  f"{row['output_tokens']:>8,}  {row['seconds']:>6.1f}  "
                  f"{row['name']}", file=out)
        tot_tok = sum(r['output_tokens'] for r in self.components)
        tot_find = sum(r['findings'] or 0 for r in self.components)
        print(f"  {'':>9}  {tot_find:>5,}  {tot_tok:>8,}  "
              f"{round(time.monotonic() - self._t0, 1):>6.1f}  TOTAL, this "
              f"run", file=out)
        self._report_across_runs(out)

    def _report_passes(self, runs, out):
        """The hand-worked passes, across the ledger.

        They are where this check spends most of what it costs, and no tool
        can measure them -- so they appear only when a session recorded
        them, and their absence is printed as absence rather than left to
        read as "the passes were free" (practice: no-invented-specifics).
        """
        rows = [(r.get('date'), p) for r in runs for p in (r.get('passes') or [])]
        if rows:
            print("\n  PASSES recorded by hand, across the ledger:\n", file=out)
            for date, p in rows:
                tok = (f"{p['tokens']:,} tok" if p.get('tokens')
                       else 'cost not recorded')
                fnd = ('-- finding(s)' if p.get('findings') is None
                       else f"{p['findings']} finding(s)")
                print(f"    {date}  pass {p.get('pass')}: "
                      f"{p.get('status')}, {fnd}, {tok}"
                      + (f"\n      {p['note']}" if p.get('note') else ''),
                      file=out)
        else:
            print("\n  No pass has been recorded by hand (--record-pass), so "
                  "the table above is\n  the tool's own sections only, not "
                  "what the four passes cost.", file=out)

    def _report_across_runs(self, out):
        runs = list(self.history) + [self.record()]
        completed = [r for r in runs if r.get('completed', True)]
        print(f"\n  ACROSS {len(runs)} RECORDED RUN(S) -- "
              f"{self.path.relative_to(ROOT) if self.path.is_relative_to(ROOT) else self.path}\n",
              file=out)
        if len(runs) < 2:
            print("  This is the first run in the ledger, so there is nothing "
                  "to compare it\n  against yet. The question this section "
                  "exists to answer -- which parts of\n  this check stopped "
                  "earning their place -- needs several runs, and it is\n"
                  "  deliberately not guessed at from one.\n", file=out)
            self._report_passes(runs, out)
            return
        seen = {}
        order = []
        for run in runs:
            for row in run.get('components', []):
                name = row.get('name')
                if name not in seen:
                    seen[name] = []
                    order.append(name)
                seen[name].append((run, row))
        print(f"  {'runs':>5}  {'found':>5}  {'tok/run':>8}  {'last found':>10}"
              f"  section", file=out)
        quiet, unknown, gone = [], [], []
        for name in order:
            rows = seen[name]
            ran = [r for _, r in rows if r.get('status') != 'skipped']
            with_find = [(run, r) for run, r in rows if (r.get('findings') or 0) > 0]
            unk = [r for _, r in rows if r.get('status') == 'unknown']
            toks = [r.get('output_tokens', 0) for _, r in rows]
            avg = int(sum(toks) / len(toks)) if toks else 0
            # A read section cannot find anything by construction, so a 0
            # in its row would read as "it looked and found nothing" -- the
            # one reading that would put it on the retirement list below for
            # doing exactly its job.
            is_read = all(r.get('kind') == 'read' for _, r in rows)
            found = '--' if is_read else f"{len(with_find):,}"
            last = ('n/a' if is_read else
                    max((run.get('date') or '?' for run, _ in with_find),
                        default='never'))
            print(f"  {len(ran):>5}  {found:>5}  {avg:>8,}  "
                  f"{last:>10}  {name}", file=out)
            if name not in {r['name'] for r in self.components}:
                gone.append(name)
            elif (len(ran) >= QUIET_RUNS_BEFORE_QUESTION and not with_find
                    and not unk
                    and any(r.get('kind') == 'mechanical' for _, r in rows)):
                quiet.append((name, len(ran), avg))
            if len(unk) >= QUIET_RUNS_BEFORE_QUESTION:
                unknown.append((name, len(unk)))
        # Usefulness is only half the question Morgan asked; the other half
        # is what each part costs, and the two have to be read side by side
        # or a cheap quiet section reads the same as an expensive one.
        costly = sorted(
            ((int(sum(r.get('output_tokens', 0) for _, r in seen[n])
                  / max(1, len(seen[n]))), n) for n in order),
            reverse=True)[:3]
        if costly and costly[0][0]:
            total = sum(int(sum(r.get('output_tokens', 0) for _, r in seen[n])
                            / max(1, len(seen[n]))) for n in order)
            print("\n  COSTLIEST TO READ, per run -- cost and usefulness are "
                  "separate questions\n  and this is the other one:\n", file=out)
            for tok, name in costly:
                share = f" ({tok * 100 // total}% of the run's output)" if total else ''
                print(f"    {tok:>7,} tok  {name}{share}", file=out)
        self._report_passes(runs, out)
        print(f"\n  ({len(completed)} of {len(runs)} run(s) reached the end; "
              f"a run that aborted early\n  recorded only the sections it got "
              f"to, and its empty sections are not\n  evidence of anything.)",
              file=out)
        if quiet:
            print("\n  FOUND NOTHING, ACROSS EVERY RECORDED RUN -- decide, do "
                  "not drift:\n", file=out)
            for name, ran, avg in quiet:
                print(f"    {name}: {ran} run(s), no finding, "
                      f"≈{avg:,} tokens each time", file=out)
            print("\n  Nothing is retired automatically, and a quiet section "
                  "is not a useless one:\n  a guard that never fires may be "
                  "why nothing is broken, and several of these\n  were "
                  "written after one expensive incident they are meant never "
                  "to repeat.\n  The three answers are KEEP (say why, here), "
                  "CHEAPEN (same check, less\n  printed), and RETIRE (the "
                  "practice's own Detail loses the bullet, and\n"
                  "  decommission-deletes-files applies to whatever it owned).",
                  file=out)
        if unknown:
            print("\n  COULD NOT MEASURE, repeatedly -- an unknown is not a "
                  "quiet section:\n", file=out)
            for name, n in unknown:
                print(f"    {name}: {n} run(s) could not produce a count",
                      file=out)
        if gone:
            print("\n  In earlier runs and NOT in this one (skipped by a flag, "
                  "renamed, or\n  removed) -- their history above is about a "
                  "section this run never ran:\n", file=out)
            for name in gone:
                print(f"    {name}", file=out)
        print(file=out)


def _record_pass(value, path=None, repo=None):
    """--record-pass: append a hand-worked pass's outcome to the last run.

    The four passes are where this check actually spends its time, and their
    cost is the session's own measurement -- so it is recorded when a session
    has it and left absent when it does not, never estimated here
    (practice: no-invented-specifics).
    """
    head, _, rest = value.partition('=')
    name = head.strip()
    if not name or not rest.strip():
        print("very deep check FAIL: --record-pass wants PASS=STATUS, e.g. "
              "--record-pass '2=done,findings=3,tokens=120000,note=...'",
              file=sys.stderr)
        return 1
    fields, note = {}, None
    parts = rest.split(',')
    # `note=` takes the rest of the string verbatim, commas included -- it is
    # prose, and splitting it would truncate the one field a person wrote.
    for i, part in enumerate(parts):
        if part.strip().startswith('note='):
            note = ','.join(parts[i:]).strip()[len('note='):].strip()
            parts = parts[:i]
            break
    status = parts[0].strip() if parts else ''
    for part in parts[1:]:
        k, _, v = part.partition('=')
        fields[k.strip()] = v.strip()
    entry = {'pass': name, 'status': status,
             'recorded': precedent_time.stamp_iso(repo)}
    for key in ('findings', 'tokens'):
        raw = fields.get(key)
        if raw is None:
            entry[key] = None
            continue
        if not raw.isdigit():
            print(f"very deep check FAIL: --record-pass {key}= wants a whole "
                  f"number, not {raw!r}.", file=sys.stderr)
            return 1
        entry[key] = int(raw)
    if note:
        entry['note'] = note
    path = pathlib.Path(path) if path is not None else ledger_path_for(repo)
    if not path.is_file():
        print(f"very deep check FAIL: no ledger at {path} yet -- run the "
              f"check once before recording a pass against it.",
              file=sys.stderr)
        return 1
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as exc:
        print(f"very deep check FAIL: {path} does not parse ({exc}).",
              file=sys.stderr)
        return 1
    runs = data.get('runs') or []
    if not runs:
        print(f"very deep check FAIL: {path} records no run yet.",
              file=sys.stderr)
        return 1
    runs[-1].setdefault('passes', []).append(entry)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(f"recorded: pass {name} = {status or '(no status)'} against the run "
          f"of {runs[-1].get('run_id')} in {path}.")
    return 0


# Where the branch sweep's own write-up lands, same reasoning and same
# per-repo anchoring as LEDGER_RELPATH just above: the file describes the
# REPO BEING CHECKED, not this engine's own checkout, so a fixture that
# points --repo at a scratch directory must write there, never here.
#
# Underscore, not hyphen (practice: filename-separator): record/ already
# carries GOTCHAS_ARCHIVE.md, and a hyphenated name sitting next to it is
# exactly the mixed-separator case the practice's own planted fixture
# exists to catch -- it did, the first time this file was ever committed.
BRANCH_REPORT_RELPATH = pathlib.Path('record') / 'stale_branches.md'


def branch_report_path_for(repo_root=None):
    return pathlib.Path(repo_root or ROOT) / BRANCH_REPORT_RELPATH


def _delete_row_lines(r, path, show_into=False):
    """-> the bullet + delete-link lines for one merged branch row.

    Shared by `_write_branch_report` (every section, every repo) and
    `emit_merged_stale_checkout` (just the checkout's safe-to-delete list,
    for the `--emit` block spec/VERY_DEEP_CHECK.md embeds) so the two
    never drift into two different renderings of the same row."""
    age = (f"last commit {r['last']}, {r['age_days']} day(s) old"
           if r['last'] else "last commit date unreadable in this clone")
    who = f", last touched by {r['author']}" if r.get('author') else ''
    into = f", merged into `{r['into']}`" if show_into and r.get('into') else ''
    lines = [f"- **`{r['name']}`** -- {age}{who}{into}"]
    url = _branch_url(path, r['name'])
    if url and r.get('filter_ambiguous'):
        # Still linked, never silently dropped -- but the row says what the
        # reader will actually see, so the one-click promise is not made and
        # broken (practice: branch-delete-links).
        lines.append(f"  [Branches page (SEVERAL ROWS -- another branch's "
                     f"name contains this one; pick the exact match) →]({url})")
    elif url:
        lines.append(f"  [Delete branch →]({url})")
    return lines


def _merged_stale_checkout_markdown(scan):
    """-> the merged-and-stale (safe-to-delete) branch list from an
    already-computed `scan_branches()` result, as markdown. Shared by
    `emit_merged_stale_checkout` (its own fresh scan, for `--emit`) and the
    main run (the scan it already paid for), so the two never drift into
    two different renderings of the same list."""
    if scan is None:
        return ('(this checkout could not be scanned -- not its own git '
                'checkout, or its integration branch could not be '
                'resolved)')
    path = scan.get('path')
    sd = scan.get('stale_days') or STALE_DAYS_DEFAULT
    stale = [r for r in scan['merged'] if r.get('stale')]
    if not stale:
        return f'(none -- no merged branch is >= {sd} days stale right now)'
    lines = []
    for r in stale:
        lines.extend(_delete_row_lines(r, path))
    # What SUCCESS looks like, said once (practice: branch-delete-links). A
    # deleted branch's filtered page reads "no branches matched", which reads
    # as an error to anyone who has not been told otherwise.
    lines.append('')
    lines.append('After a deletion the filtered page reads **"no branches '
                 'matched"** -- that is the success state, not an error. '
                 'GitHub offers a brief Undo, so a misclick is recoverable.')
    return '\n'.join(lines)


def emit_merged_stale_checkout(repo_root=None):
    """-> the merged-and-stale (safe-to-delete) branch list for THIS
    checkout alone, as markdown, for `--emit` (practice: very-deep-check).

    WHY THIS EXISTS AND WHY IT IS SEPARATE FROM record/stale_branches.md
    (2026-09-19). The full branch report already carries this list, but a
    session handed a run's write-up read the file's EXISTENCE and still
    did not carry the list itself into the reply -- "you named there were
    10 but never actually gave them the list to act on". Morgan: "This
    list should be generated and included in the VERY DEEP CHECK MD
    document when it's generated... And if there are more than 10,
    include them!" A pointer that still requires a session to remember to
    open, read and paste a second file is the same failure
    record/stale_branches.md itself was built to end
    ([spawn-session]'s own Story: "existed only in that Sunday session's
    own transcript"). NEVER truncated -- every merged-and-stale branch is
    listed, however many there are.

    NOT wired into `doc_sync.py` -- see the comment above `PAIRS` in
    [tools/doc_sync.py](../tools/doc_sync.py) for why a live remote scan
    cannot be a doc_sync-gated invariant. `_update_spec_doc_block()` below
    is what actually keeps spec/VERY_DEEP_CHECK.md current, writing this
    same markdown whenever the checkout's own branch scan runs for real."""
    return _merged_stale_checkout_markdown(scan_branches(repo_root or ROOT))


SPEC_DOC_RELPATH = pathlib.Path('spec') / 'VERY_DEEP_CHECK.md'
_VDC_EMBED_RE = re.compile(
    r'(<!--vdc-embed:merged-stale-checkout:[^>]*-->\n).*?'
    r'(\n<!--/vdc-embed:merged-stale-checkout-->)', re.S)


def _update_spec_doc_block(repo_root, markdown):
    """Rewrite the `<!--vdc-embed:merged-stale-checkout:...-->` block in
    THIS repo's own spec/VERY_DEEP_CHECK.md, in place -- never in a
    checked repo other than this one, since that document and this
    practice both live only here. A silent no-op when the file or the
    block is absent (a checked repo that vendors this engine has neither,
    and a run against it must not fail over a document it does not own)."""
    path = pathlib.Path(repo_root) / SPEC_DOC_RELPATH
    if not path.is_file():
        return False
    text = path.read_text(encoding='utf-8')
    if not _VDC_EMBED_RE.search(text):
        return False
    new_text = _VDC_EMBED_RE.sub(lambda m: m.group(1) + markdown + m.group(2),
                                 text, count=1)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
        return True
    return False


def _write_branch_report(branch_scans, out_path, repo_root):
    """Write `branch_scans` (the same dict the console BRANCHES section
    prints, and --json's 'branches' key) to `out_path` as committable
    Markdown, with a real clickable link on every row.

    WHY A FILE, NOT JUST THE PRINTED SECTION (practice: very-deep-check,
    pass 4). The console section already lists every merged-and-stale,
    merged-and-recent, merged-elsewhere and unmerged branch, one repo at a
    time, with a link under each row -- everything asked for is already
    computed. What is missing is durability: a run's stdout lives in that
    session's chat transcript, which is disposable (practice:
    repo-is-memory), so a person who wants the list later has to ask a
    session to re-run the whole check and scroll to find it again, or hope
    it was pasted somewhere. A committed file is a page they can open and
    click links on directly.

    Every branch is written here exactly as the console prints it --
    whoever last touched it, not filtered to the person running the check
    (practice: very-deep-check's `_branch_meta` docstring: "you do not
    delete somebody else's branch" is why the author is named, never why a
    row is dropped)."""
    out_path = pathlib.Path(out_path)
    today = precedent_time.today(repo_root)
    lines = []
    # Lifecycle frontmatter (practice: document-status-header): this file
    # lands in record/, which the check requires it of. It is a full
    # snapshot rewritten on every run, never partially written, so it is
    # `closed` the moment it is generated rather than cycling through
    # `live` the way a progressively-written record does.
    lines.append('---')
    lines.append('title:         Stale and unmerged branches')
    lines.append('kind:          record')
    lines.append('status:        closed')
    lines.append(f'opened:        {today}')
    lines.append(f'closed:        {today}')
    lines.append('superseded_by: null')
    lines.append('supersedes:    []')
    lines.append('audience:      session')
    lines.append('summary:       "The branch sweep from the most recent '
                 'very deep check: every merged-and-undeleted and every '
                 'unmerged branch across this checkout and its declared '
                 'sources, one verdict owed per row."')
    lines.append('---')
    lines.append('')
    lines.append('# Stale and unmerged branches')
    lines.append('')
    lines.append('<!-- GENERATED by tools/very_deep_check.py -- never '
                 'hand-edit. Regenerated on every `very_deep_check.py` run '
                 'that does not pass --skip-branch-scan; run it again and '
                 'commit the result to refresh this file. Source: '
                 'practices/very-deep-check.md, pass 4. -->')
    lines.append('')
    lines.append(f'Generated {precedent_time.stamp_iso(repo_root)}, '
                 f'sweeping this checkout plus every source its '
                 f'`precedent.json` declares. A repo-local source living '
                 f'inside the parent checkout shares its parent\'s '
                 f'branches and is not swept separately; every other '
                 f'declared source that is its own git checkout is -- '
                 f'whoever last touched a branch, not only the person who '
                 f'ran this check.')
    lines.append('')
    lines.append('**After you delete a branch, its filtered page reads "no '
                 'branches matched" -- that is success, not an error.** '
                 'GitHub offers a brief Undo immediately afterwards. A row '
                 'whose link says SEVERAL ROWS is one whose name another '
                 'branch contains, so the filter cannot narrow to it alone '
                 '(practice: branch-delete-links).')
    lines.append('')

    def _row(r, path, show_into):
        lines.extend(_delete_row_lines(r, path, show_into=show_into))

    def _section(title, rows, empty_note, path, show_into=False):
        lines.append(f'### {title}')
        lines.append('')
        if not rows:
            lines.append(empty_note)
            lines.append('')
            return
        for r in rows:
            _row(r, path, show_into)
        lines.append('')

    for name, scan in branch_scans.items():
        lines.append(f'## {name}')
        lines.append('')
        if scan is None:
            lines.append('Not its own git checkout, or its integration '
                         'branch could not be resolved -- skipped.')
            lines.append('')
            continue
        path = scan.get('path')
        lines.append(f"Repository: `{path}`  \nIntegration branch: "
                     f"`{scan['target']}`")
        lines.append('')
        incomplete = scan.get('unreachable') or scan.get('unfetched')
        empty = ('(none)' if not incomplete
                 else '(CANNOT TELL -- see the incomplete-scan note below)')
        sd = scan.get('stale_days') or STALE_DAYS_DEFAULT
        stale = [r for r in scan['merged'] if r.get('stale')]
        recent = [r for r in scan['merged'] if not r.get('stale')]

        _section(f'Merged and STALE (>= {sd} days) -- safest deletions '
                 f'here', stale, empty, path)
        _section(f'Merged, not deleted, still recent (< {sd} days) -- '
                 f'same proof, but someone may still have it checked out',
                 recent, empty, path)

        others = [b for b in scan.get('protected', []) if b != scan['target']]
        elsewhere = scan.get('merged_elsewhere') or []
        if others:
            _section(f"Merged into {', '.join(f'`{o}`' for o in others)} "
                     f"but NOT into `{scan['target']}` -- equally proven "
                     f"safe to delete; their work is finished elsewhere",
                     elsewhere, empty, path, show_into=len(others) > 1)

        lines.append('### NOT merged anywhere -- needs a verdict (merge or '
                     'close), not a deletion')
        lines.append('')
        if scan['unmerged']:
            for r in scan['unmerged']:
                ahead = f", {r['ahead']} commit(s) ahead" if r.get('ahead') is not None else ''
                who = f", last touched by {r['author']}" if r.get('author') else ''
                age = f", last commit {r['last']}" if r['last'] else ''
                lines.append(f"- **`{r['name']}`**{ahead}{age}{who}")
                lines.append(f"  {r['verdict']}")
                for label, url in (('Branches page', _branch_url(path, r['name'])),
                                   ('Compare view',
                                    _compare_url(path, scan['target'], r['name']))):
                    if url:
                        lines.append(f"  [{label} →]({url})")
        else:
            lines.append(empty)
        lines.append('')

        if scan.get('unreachable'):
            lines.append(f"**INCOMPLETE SCAN:** {scan['unreachable']}. "
                         f"Treat every list above as partial, not as clean.")
            lines.append('')
        elif scan.get('unfetched'):
            n = len(scan['unfetched'])
            shown = ', '.join(scan['unfetched'][:5])
            more = f' (+{n - 5} more)' if n > 5 else ''
            lines.append(f"**INCOMPLETE SCAN:** {n} branch(es) on origin "
                         f"were never fetched into this clone and so were "
                         f"NOT judged: {shown}{more}. Treat every list "
                         f"above as partial, not as clean. Run "
                         f"`git -C {path} fetch --depth=50 origin` and "
                         f"re-run this check.")
            lines.append('')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    return out_path


def _exit(message):
    print(message, file=sys.stderr)
    return 1


def main():
    """Run the check, and record what each of its parts returned and cost.

    The recording is in a finally, deliberately: a run that aborts at the
    freshness gate has still told the ledger something (which sections it
    reached), and losing that is losing the only evidence the aborted run
    produced (practice: very-deep-check).
    """
    box = {'completed': False}
    try:
        return _main(box)
    finally:
        led = box.get('ledger')
        if led is not None:
            led.finish(completed=box['completed'])


def _main(box):
    args = sys.argv[1:]
    repo, user_config, checkout_target, stale_days = None, None, None, None
    session_days = None
    for flag, dest in (('--repo', 'repo'), ('--user-config', 'user_config'),
                       ('--target', 'checkout_target'),
                       ('--stale-days', 'stale_days'),
                       ('--session-days', 'session_days')):
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
            elif dest == 'session_days':
                # Same refusal as --stale-days, same reason: a window asked
                # for and quietly replaced reports about a period nobody
                # asked about.
                if not value.isdigit() or int(value) <= 0:
                    sys.exit(f"very deep check FAIL: --session-days needs a "
                             f"positive whole number of days, not {value!r}.")
                session_days = int(value)
            else:
                checkout_target = value
    record_pass = None
    if '--record-pass' in args:
        i = args.index('--record-pass')
        if i + 1 >= len(args):
            sys.exit("very deep check FAIL: --record-pass needs a value, "
                     "e.g. --record-pass '2=done,findings=3'.")
        record_pass = args[i + 1]
        args = args[:i] + args[i + 2:]
    record_read = None
    if '--record-read' in args:
        i = args.index('--record-read')
        if i + 1 >= len(args):
            sys.exit("very deep check FAIL: --record-read needs a path, "
                     "e.g. --record-read 'tools/verify_harness.py,note=...'.")
        record_read = args[i + 1]
        args = args[:i] + args[i + 2:]
    ledger_path = None          # default: the checked repo's own ledger
    if '--ledger' in args:
        i = args.index('--ledger')
        if i + 1 >= len(args):
            sys.exit("very deep check FAIL: --ledger needs a path.")
        ledger_path = pathlib.Path(args[i + 1])
        args = args[:i] + args[i + 2:]
    branch_report_path = None   # default: the checked repo's own report
    if '--branch-report' in args:
        i = args.index('--branch-report')
        if i + 1 >= len(args):
            sys.exit("very deep check FAIL: --branch-report needs a path.")
        branch_report_path = pathlib.Path(args[i + 1])
        args = args[:i] + args[i + 2:]
    if record_read is not None:
        return _record_read(record_read, repo)
    if record_pass is not None:
        return _record_pass(record_pass, ledger_path, repo)
    if '--emit' in args:
        # doc_sync's own contract (practice: computed-numbers-in-scripts):
        # print exactly the named block's content and exit -- no ledger, no
        # freshness gate, no other section. Deliberately its own path
        # through main() rather than reusing the full pipeline below,
        # which reads and judges everything in force; a doc_sync gate
        # needs only this checkout's own branches, fast.
        i = args.index('--emit')
        if i + 1 >= len(args):
            sys.exit("very deep check FAIL: --emit needs a block name.")
        name = args[i + 1]
        if name != 'merged-stale-checkout':
            sys.exit(f"very deep check FAIL: --emit {name!r} is not a "
                     f"block this script owns; the only one is "
                     f"'merged-stale-checkout'.")
        print(emit_merged_stale_checkout(repo))
        return 0

    as_json = '--json' in args
    allow_missing = '--allow-missing-sources' in args
    skip_branch_scan = '--skip-branch-scan' in args
    print_checklist = '--checklist' in args
    with_harness = '--with-harness' in args
    skip_visibility = '--skip-visibility' in args
    skip_liveness = '--skip-liveness' in args
    # Narrow the read to repos this session can actually land work in. NOT the
    # default: see can_land_here()'s docstring for why a repo needing a
    # handoff is still worth reading.
    landable_only = '--landable-only' in args
    skip_endgame = '--skip-endgame-merge' in args
    skip_base_drift = '--skip-base-drift' in args
    skip_session_sweep = '--skip-session-sweep' in args
    allow_stale = '--allow-stale' in args
    do_freshen = '--freshen' in args

    # FIRST, before the parse check and before enumerate_scope. Both of
    # those read files, and a file read out of a stale checkout is not
    # evidence about anything -- so proving the tree current has to precede
    # the first read, not follow it.
    repo_root = pathlib.Path(repo or ROOT).resolve()
    # The ledger opens before the first section so that a run which aborts
    # at the freshness gate still records having got that far.
    led = None
    if not as_json:
        led = RunLedger(ledger_path, repo_root, sys.argv[1:])
        box['ledger'] = led
    _fresh = {}
    if led:
        led.start('FRESHNESS -- this checkout')
    _v = freshness(repo_root)
    if do_freshen:
        _v = freshen(repo_root, _v)
    _fresh['checkout'] = _v
    if not as_json:
        print("FRESHNESS -- every repo in force, before anything is read\n")
        report_freshness(f'this checkout ({repo_root})', _v)
    if led:
        led.end(findings=0 if _v['status'] in FRESHNESS_CLEAN else 1)
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
    if led:
        led.start('MACHINE-READABLE FILES')
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
    if led:
        led.end(findings=len(_failures))
    if _failures:
        sys.exit(f"very deep check FAIL: {len(_failures)} tracked file(s) do "
                 f"not parse. Fix those first -- this tool reads "
                 f"precedent.json to enumerate its own scope, so it cannot "
                 f"report anything else while one of them is malformed.")

    if led:
        led.start('PLANTED CASE COVERAGE')
    _pc_status, _pc_lines = planted_case_coverage(_root, run=with_harness)
    if not as_json:
        print("PLANTED CASE COVERAGE -- the push gate's rotation, settled "
              "or still owed\n")
        for _l in _pc_lines:
            print(f"  {_l}")
        print()
    if led:
        # An owed rotation is a finding: the promise "covered within 10
        # commits" is the thing this section exists to stop taking on
        # trust. 'n/a' is unmeasurable, never clean.
        led.end(findings=None if _pc_status == 'n/a'
                else (0 if _pc_status == 'ran' and not any(
                    l.startswith('FAIL') for l in _pc_lines) else 1))
        led.start('VENDORING EXCLUSIONS')
    _vendor_findings = _vendored_exclusion_findings(_root)
    if not as_json:
        print("VENDORING EXCLUSIONS -- a vendored consumer's process/upstream/ "
              "checked against\ntools/checkin.py's NOT_VENDORED\n")
        if _vendor_findings is None:
            print("  N/A: not a vendored consumer (no process/upstream/, no "
                  "process/manifest.json upstream.commit).")
        elif not _vendor_findings:
            print("  OK: process/upstream/ carries nothing under an excluded path.")
        else:
            for _f in _vendor_findings:
                print(f"  FINDING: {_f}")
        print()
    if led:
        led.end(findings=len(_vendor_findings or []))

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
    if led:
        led.start('FRESHNESS -- declared sources')
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
    if led:
        led.end(findings=len(_stale_sources))
    if _stale_sources and not allow_stale:
        return _exit(f"very deep check FAIL: {len(_stale_sources)} source(s) "
                     f"not provably current ({', '.join(_stale_sources)}). "
                     f"The check reads these repos against this one, so a "
                     f"stale source produces cross-source findings that are "
                     f"pure artifact -- a convention 'not rolled out' that "
                     f"was rolled out last week. Run each remedy above, or "
                     f"--freshen, and start again.")

    # Still THERE, not only still current. The freshness gate above proves
    # each repo in force matches its origin; it cannot see that the origin
    # has been deleted, renamed, or archived, because an archived repo
    # fetches exactly like a live one and a deleted source simply never
    # resolved. Runs here, right after freshness and before anything
    # expensive, for the same reason freshness does: a finding that says
    # "nothing you write here can ever land" is worth more before the read
    # than after it.
    if not skip_liveness and not as_json:
        if led:
            led.start('REPOS IN FORCE -- still there, still writable')
        print("REPOS IN FORCE -- still there, still writable\n")
        _lf, _ln = repos_in_force_audit(repo_root, data['sources'],
                                        data['missing'])
        for f in _lf:
            print(f'  FINDING: {f}')
        for n in _ln:
            print(f'  note: {n}')
        # AND THE REPOSITORIES THE INSTRUCTIONS FILES NAME, which the audit
        # above does not reach: it asks about repos declared as SOURCES, and
        # a name sitting in prose is not a source. Same call, same handling
        # of Not Found and of a rename; `already` keeps the two sections from
        # paying twice for one name, since this tool reports its own bill.
        _already = set()
        for _lbl, _url, _pth in _repos_in_force(repo_root, data['sources'],
                                                data['missing']):
            _m = _GH_REMOTE_RE.search(_url or '')
            if _m:
                _already.add((_m.group(1), _m.group(2)))
        _rf, _rn = instruction_file_repo_refs_audit(
            repo_root, data['sources'], data['missing'], already=_already)
        for f in _rf:
            print(f'  FINDING: {f}')
        for n in _rn:
            print(f'  note: {n}')
        print()
        # WHETHER THIS SESSION CAN LAND WORK IN EACH ONE, which the audit
        # above does not answer: it asks whether the REPOSITORY accepts work,
        # and this asks whether these credentials do. Printed right after it,
        # before any reading, for the same reason -- knowing a finding will
        # need a handoff is worth more before the read than after.
        _ar, _an = access_audit(repo_root, data['sources'])
        if landable_only:
            _drop = {r[1] for r in _ar if r[2] != 'land'}
            if _drop:
                data['sources'] = [s for s in data['sources']
                                   if s['path'] not in _drop]
                print(f'  --landable-only: {len(_drop)} repo(s) dropped from '
                      f'scope. Findings in the seam between a dropped source '
                      f'and one still in scope are NOT reachable this run.')
        print()
        if led:
            led.end(findings=len(_lf))
    elif led and skip_liveness:
        led.skipped('REPOS IN FORCE -- still there, still writable',
                    '--skip-liveness')

    # CONTRIBUTOR BOUNDARY (practice: very-deep-check, pass 2). Right after
    # ACCESS, because it answers the next question about the same repos: not
    # whether THIS session can land work there, but whether the repository's
    # own line between content and machinery is enforced by a setting or
    # merely described by a document. Findings are a stale generated
    # CODEOWNERS or protection that is off; "could not ask GitHub" is a note
    # and is never counted as clean.
    if not as_json:
        if led:
            led.start('CONTRIBUTOR BOUNDARY -- CODEOWNERS current, protection on')
        print("CONTRIBUTOR BOUNDARY -- is each repo's boundary a setting, or "
              "only a document\n")
        _cb, _cn = boundary_audit(repo_root, data['sources'],
                                  skip_api=skip_liveness)
        for n in _cn:
            print(f'  note: {n}')
        if not _cb and not _cn:
            print('  clean -- every boundary drawn here is current and on')
        print()
        if led:
            led.end(findings=len(_cb))

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
    # The scan FETCHES and runs a merge test per branch, so it is one of the
    # most expensive parts of this check and it prints nothing where it runs
    # -- its output comes out under BRANCHES, much later. Timed here and
    # added to that section's row, so the ledger's cost column is about the
    # work and not about where the text happened to be printed.
    _scan_secs = 0.0
    _branch_report_path = None
    if not skip_branch_scan:
        _scan_t0 = time.monotonic()
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
        _scan_secs = round(time.monotonic() - _scan_t0, 2)
        # Written every time the scan runs, --json included, so the
        # committable list is never behind whatever the console happened to
        # print (practice: very-deep-check, pass 4; repo-is-memory).
        _branch_report_path = _write_branch_report(
            branch_scans, branch_report_path or branch_report_path_for(repo_root),
            repo_root)
        # This repo's own spec/VERY_DEEP_CHECK.md only, never a checked
        # repo's -- see _update_spec_doc_block's docstring.
        if pathlib.Path(repo_root).resolve() == ROOT.resolve():
            _update_spec_doc_block(
                repo_root, _merged_stale_checkout_markdown(
                    branch_scans.get('checkout')))

    # THE REPO SIDE of the live-session sweep, gathered here beside the
    # branch scan because it reads the same clones and asks the neighbouring
    # question: the branch sweep asks what was written and never landed,
    # this asks what a session did and left nowhere at all.
    activity = {}
    if not skip_session_sweep:
        _win = (session_days or _declared_session_window_days(repo_root)
                or SESSION_WINDOW_DAYS_DEFAULT)
        activity['checkout'] = recent_activity(repo_root, _win)
        _seen_a = {repo_root.resolve()}
        for s_ in data['sources']:
            try:
                _p = pathlib.Path(s_['path']).resolve()
            except OSError:
                continue
            if _p in _seen_a:
                continue
            _seen_a.add(_p)
            activity[f"{s_['level']} source {s_['name']}"] = recent_activity(
                s_['path'], _win)

    _endgame_t0 = time.monotonic()
    endgame = None if skip_endgame else endgame_merge(repo_root, checkout_target)
    _endgame_secs = round(time.monotonic() - _endgame_t0, 2)
    _drift_t0 = time.monotonic()
    drift = None if skip_base_drift else base_branch_drift(repo_root,
                                                           checkout_target)
    _drift_secs = round(time.monotonic() - _drift_t0, 2)

    if as_json:
        data['branches'] = branch_scans
        data['recent_activity'] = activity
        data['endgame_merge'] = endgame
        data['base_branch_drift'] = drift
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    c = data['checkout']
    if led:
        led.start('SCOPE -- documents and practices to read', kind='read')
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
    if led:
        led.end(items=c['practice_count']
                + sum(s['practice_count'] for s in data['sources']))
        led.start('WITHIN-SOURCE CONFLICTS')
    print("WITHIN-SOURCE CONFLICTS -- one catalogue disagreeing with itself\n")
    _conf_n = 0
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
            _conf_n += len(_found)
            print(f"  {_src['name']}:")
            for _msg in _found:
                print(f"      {_msg}")
    if not _conf_any:
        print("  none -- no duplicate `defines:` term, and no `overrides:` or\n"
              "  `in_force_at:` naming a sibling, in any source in force.")
    print()
    if led:
        led.end(findings=_conf_n)
        led.start('SOURCE SHAPE')

    print("SOURCE SHAPE -- files each level's skeleton ships\n")
    _shape_n = 0
    _shape_any = False
    for _s in data['sources']:
        _lvl, _path = _s.get('level'), _s.get('path')
        if _lvl not in FATAL_MISSING_LEVELS or not _path:
            continue
        _shape_any = True
        _missing = bootstrap_source.verify(_lvl, _path)
        _shape_n += len(_missing)
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
    if led:
        # No source resolved means this section could not run, which is not
        # the same as a source with nothing missing -- an unknown, never a
        # clean row (practice: fail-gracefully).
        led.end(findings=_shape_n if _shape_any else None)
        led.start('TEMPLATE FRESHNESS')

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
    if led:
        led.end(findings=len(_tf))
        led.start('BOOTSTRAP DRIFT')

    # The third direction, and the only one that reads the files rather than
    # their names: run the generator now and diff it against the sets that
    # exist (practice: very-deep-check, pass 1).
    print("BOOTSTRAP DRIFT -- what the generator would write today, against "
          "the real sets\n")
    _collect = {}
    _bd = _bootstrap_drift(data['sources'], collect=_collect)
    if _bd:
        for _m in _bd:
            print(f"  {_m}")
    else:
        print("  none -- every file the generator writes is present in each "
              "resolved\n  source and says the same thing, outside the "
              "skeleton files a set owns.")
    print()
    if led:
        led.end(findings=len(_bd))
        led.start('CONVERGENT DRIFT')

    # The fourth direction, and the only one that compares the sets against
    # EACH OTHER: the three above all measure one set against one template,
    # so a change every set made identically reads as healthy in all of them
    # (practice: very-deep-check, pass 1).
    print("CONVERGENT DRIFT -- changes several sets made the same way, which "
          "the generator does not\n")
    _cd = _convergent_drift(_collect, sources=data['sources'])
    if _cd:
        for _m in _cd:
            print(f"  {_m}")
    else:
        print("  none -- no file differs from the generator in the same way "
              "in two or\n  more sets of a level.")
    print()
    if led:
        led.end(findings=sum(1 for _m in _cd if _m.startswith('FINDING')))
        led.start('EXPIRING PRACTICES')

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
    if led:
        led.end(findings=len(_exp))
        led.start('ORPHANS')

    print("ORPHANS -- files nothing owns any more\n")
    _orph_n = 0
    _orph_any = False
    _orph_seen = False
    _orph_targets = [('this checkout', repo_root)]
    for _s in data['sources']:
        _p = _s.get('path')
        if _s.get('level') in FATAL_MISSING_LEVELS and _p:
            _orph_targets.append((_s.get('name'), pathlib.Path(_p)))
    for _name, _p in _orph_targets:
        if not pathlib.Path(_p).is_dir():
            continue
        _orph_seen = True
        _found = _orphan_scan(_p)
        _orph_n += len(_found)
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
    if led:
        led.end(findings=_orph_n if _orph_seen else None)
        led.start('CONFIG KEYS', kind='read')

    print("CONFIG KEYS -- every key a repo declares, and what reads it\n")
    _ck_unread = 0
    _ck_rows = 0
    for _name, _p in _orph_targets:
        if not pathlib.Path(_p).is_dir():
            continue
        _rows, _note = _config_key_reads(_p, _orph_targets)
        if _note:
            print(f"  {_name}: not measured -- {_note}")
            continue
        _unread = [r for r in _rows if not r[2]]
        _ck_rows += len(_rows)
        _ck_unread += len(_unread)
        if not _unread:
            print(f"  {_name}: {len(_rows)} declared key(s), every one "
                  f"mentioned by a script here")
            continue
        print(f"  {_name}: {len(_rows)} declared key(s), {len(_unread)} "
              f"read by nothing here:")
        for _file, _key, _where, _elsewhere in _unread:
            _tail = (f" -- mentioned in {', '.join(_elsewhere)}"
                     if _elsewhere else
                     " -- mentioned in no repo in force")
            print(f"      {_file}: {_key}{_tail}")
    if _ck_rows:
        print("\n  A key nothing reads is a BELIEF, not a typo: somebody "
              "wrote it expecting it\n  to do something, and the file goes "
              "on looking as intentional as a live one.\n  Mentioned "
              "elsewhere is not a finding on its own -- a private check may "
              "run\n  against every repo in force -- but mentioned nowhere "
              "is worth an answer.")
    print()
    if led:
        led.end(items=_ck_rows or None, findings=_ck_unread if _ck_rows
                else None)
        led.start('CHECK COVERAGE')

    print("CHECK COVERAGE -- what every registered check actually did, per "
          "repo in force\n")
    _cc_findings = 0
    _cc_measured = False
    for _name, _p in _orph_targets:
        if not pathlib.Path(_p).is_dir():
            continue
        _sum, _note = _check_coverage(_p)
        if _sum is None:
            print(f"  {_name}: not measured -- {_note}")
            continue
        _cc_measured = True
        _c = _sum['counts']
        print(f"  {_name}: {_c.get('passed', '?')} passed, "
              f"{_c.get('violated', '?')} violated, "
              f"{_c.get('skipped', '?')} SKIPPED")
        if _sum['violated']:
            _cc_findings += len(_sum['violated'])
            print(f"      violated: {', '.join(_sum['violated'])}")
        _top = sorted(_sum['causes'].items(), key=lambda x: -x[1])[:3]
        for _cause, _n in _top:
            # One cause behind most of a repo's skips is the finding; a
            # long tail of one-offs is housekeeping.
            _flag = 'ONE CAUSE' if _n >= 5 else 'cause    '
            print(f"      {_flag} {_n:>3} skip(s): {_cause[:96]}")
            if _n >= 5:
                _cc_findings += 1
    if not _cc_measured:
        print("  nothing measured -- no repo in force carries a check "
              "registry to run.")
    else:
        print("\n  A skip is not a pass. What matters is the CAUSE: many "
              "skips behind one\n  structural reason is a coverage hole "
              "wearing many names -- a source set whose\n  practices/ "
              "holds its own level only skips every other level's check, "
              "silently\n  and permanently. A long tail of one-offs is "
              "housekeeping.")
    print()
    if led:
        led.end(findings=_cc_findings if _cc_measured else None)
        led.start('CI WORKFLOW FILES OUTSIDE VENDORING')

    # Scope is honest, not aspirational: this checkout plus every FATAL_
    # MISSING_LEVELS source reachable on disk -- the SAME _orph_targets
    # ORPHANS above already computed. There is no existing mechanism
    # anywhere in this tool for discovering a CONSUMING repo (one that
    # vendors FROM this one) -- only upstream sources this repo itself
    # declares are enumerable here. A consuming repo needs its own
    # very-deep-check run, with itself as the checkout.
    print("CI WORKFLOW FILES OUTSIDE VENDORING -- candidates for Pass 2's "
         "own read, never a verdict\n")
    print("  Scope: this checkout and every attached source reachable on "
         "disk -- NOT any\n  repo that vendors FROM this one, which this "
         "tool has no way to discover.\n")
    _wf_n = 0
    _wf_any = False
    _wf_seen = False
    for _name, _p in _orph_targets:
        if not pathlib.Path(_p).is_dir():
            continue
        _wf_seen = True
        _wf_found = _workflow_liveness_scan(_p)
        _wf_n += len(_wf_found)
        if _wf_found:
            _wf_any = True
            print(f"  {_name}:")
            for _m in _wf_found:
                print(f"      {_m}")
    if not _wf_seen:
        print("  (no repository to scan)")
    elif not _wf_any:
        print("  none -- every .github/workflows/*.yml file present is "
              "either vendored,\n  a known retired entry, or declared "
              "exempt with a reason.")
    else:
        print("\n  Read each one (practice: workflow-file-outside-vendoring): "
             "open the file,\n  compare what it actually runs "
             "against what this repo's vendored template\n  provides. "
             "Verify by content, never by name -- see that practice's own "
             "Story\n  for the incident this line exists to prevent "
             "repeating.")
    print()
    if led:
        led.end(findings=_wf_n if _wf_seen else None)
        led.start('WORKFLOW REALITY')

    print("WORKFLOW REALITY -- what GitHub says about each workflow file, "
          "not what the tree says\n")
    _wr_n = 0
    _wr_measured = False
    if skip_liveness:
        print("  not asked (--skip-liveness) -- UNVERIFIED, which is not the "
              "same answer as clean.")
    else:
        for _name, _p in _orph_targets:
            if not pathlib.Path(_p).is_dir():
                continue
            _rows = _workflow_reality(_p)
            if not _rows:
                continue
            _measured_here = any(v != 'UNVERIFIED' for v, _ in _rows)
            _wr_measured = _wr_measured or _measured_here
            print(f"  {_name}:")
            for _verdict, _msg in _rows:
                print(f"      {_verdict:<11} {_msg}")
                if _verdict == 'FINDING':
                    _wr_n += 1
        if not _wr_measured and _wr_n == 0:
            print("  nothing measured -- no workflow file in any repo in "
                  "force, or GitHub\n  could not be asked. Never read as "
                  "clean.")
        elif _wr_n == 0:
            print("\n  No finding: every workflow file in force is "
                  "registered, active, and has\n  run since it was last "
                  "edited.")
    print()
    if led:
        led.end(findings=_wr_n if (_wr_measured and not skip_liveness)
                else None)
        led.start('DELETIONS PENDING')

    print("DELETIONS PENDING -- what the next refresh would take away, and "
          "who still names it\n")
    _del_n = 0
    _del_measured = False
    for _name, _p in _orph_targets:
        if not pathlib.Path(_p).is_dir():
            continue
        _rows, _note = _pending_deletions(_p)
        if _rows is None:
            print(f"  {_name}: N/A -- {_note}")
            continue
        _del_measured = True
        if not _rows:
            print(f"  {_name}: none -- {_note}")
            continue
        print(f"  {_name} ({_note}):")
        for _rel, _refs in _rows:
            if _refs:
                _del_n += 1
                print(f"      FINDING     {_rel} -- the next refresh deletes "
                      f"it, and {len(_refs)} tracked file(s) still name it:")
                for _path, _line, _text in _refs[:4]:
                    print(f"                    {_path}:{_line}  {_text}")
            else:
                print(f"      pending     {_rel} -- the next refresh deletes "
                      f"it; nothing else names it")
    if not _del_measured:
        print("  nothing measured -- no repo in force vendors an engine "
              "manifest to diff.")
    print()
    if led:
        led.end(findings=_del_n if _del_measured else None)
        led.start('CARRY-THROUGH')

    print("CARRY-THROUGH -- how far each repo's vendored engine is behind "
          "the upstream it came from\n")
    _ct_n = 0
    _ct_measured = False
    if skip_liveness:
        print("  not asked (--skip-liveness) -- UNVERIFIED, which is not the "
              "same answer as current.")
    else:
        for _name, _p in _orph_targets:
            if not pathlib.Path(_p).is_dir():
                continue
            _status, _lines = _carry_through(_p)
            if _status in ('current', 'behind'):
                _ct_measured = True
            if _status == 'behind':
                _ct_n += 1
            print(f"  {_status.upper():<11} {_name}")
            for _l in _lines:
                print(f"                  {_l}")
        if not _ct_measured:
            print("\n  nothing measured -- no repo in force vendors an "
                  "engine, or upstream could not\n  be reached. Never read "
                  "as current.")
        elif _ct_n == 0:
            print("\n  Every repo in force is carrying the current engine.")
        else:
            print(f"\n  {_ct_n} repo(s) behind. Nothing here refreshes "
                  f"anything: taking an update is\n  \"Update Vendors\", run "
                  f"in that repo, and it is ordinary work authorized the\n"
                  f"  ordinary way.")
    print()
    if led:
        led.end(findings=_ct_n if _ct_measured else None)
        led.start('IDENTITY REALITY')

    _id_days = session_days or _declared_session_window_days(repo_root) or 30
    print(f"IDENTITY REALITY -- who the commits that LANDED say wrote them "
          f"({_id_days}-day window)\n")
    _id_n = 0
    _id_measured = False
    for _name, _p in _orph_targets:
        if not pathlib.Path(_p).is_dir():
            continue
        _rows, _notes = _identity_reality(_p, days=_id_days)
        if not _rows and not _notes:
            continue
        _id_measured = _id_measured or bool(_rows)
        print(f"  {_name}:")
        for _verdict, _msg in _rows:
            print(f"      {_verdict:<11} {_msg}")
            if _verdict == 'FINDING':
                _id_n += 1
        for _note in _notes:
            print(f"      note        {_note}")
    if not _id_measured and _id_n == 0:
        print("  nothing measured -- no repo in force could be read for "
              "authorship. Never read as clean.")
    elif _id_n == 0:
        print("\n  No finding: every commit in the window carries a "
              "configured identity, the\n  declared person's own offsets, "
              "and no tracked settings.json hardcodes anyone.")
    print()
    if led:
        led.end(findings=_id_n if _id_measured else None)
        led.start('INCIDENT COVERAGE', kind='read')

    print("INCIDENT COVERAGE -- what was filed since the last run, and what "
          "cites it\n")
    _ic_since, _ic_rows, _ic_note = _incident_coverage(repo_root)
    if _ic_note:
        print(f"  not measured -- {_ic_note}")
    else:
        print(f"  Since the last recorded run ({_ic_since}): "
              f"{len(_ic_rows)} incident(s).\n")
        for _kind, _slug, _when, _cites in _ic_rows:
            print(f"      {_when}  {_kind}: {_slug}")
            if _cites:
                print(f"                  cited by {len(_cites)}: "
                      f"{', '.join(_cites[:4])}")
            else:
                print("                  cited by NOTHING in tools/ or "
                      "practices/")
        if _ic_rows:
            print("\n  Ask of each: what prevents a recurrence, and is "
                  "there a planted case proving\n  it fires? A citation is "
                  "evidence something names the incident, never proof the\n"
                  "  class is closed -- a docstring reads the same as a "
                  "check. 'Nothing, and\n  deliberately so' is an answer "
                  "worth writing down; unexamined is not.")
    print()
    if led:
        led.end(items=len(_ic_rows) if not _ic_note else None)
        led.start('FIX SWEEP -- new detectors, run everywhere')

    print("FIX SWEEP -- every detector added since the last run, against "
          "every repo in force\n")
    # The targets are the sources with a clone on this disk. A repo with no
    # local clone is named and skipped rather than dropped: "could not be
    # swept" and "swept clean" are different answers and must not read alike.
    _fs_targets = [(_s.get('name'), _s.get('path')) for _s in data['sources']
                   if _s.get('level') in FATAL_MISSING_LEVELS]
    (_fs_since, _fs_slugs, _fs_rows,
     _fs_note, _fs_caveat) = _fix_sweep(repo_root, _fs_targets)
    _fs_findings = 0
    if _fs_note:
        print(f"  not measured -- {_fs_note}")
    elif not _fs_slugs:
        print(f"  No check was registered here since the last recorded run "
              f"({_fs_since}), so there is\n  no new detector to carry "
              f"anywhere.")
        if _fs_caveat:
            print(f"  NARROWER WINDOW THAN ASKED FOR{_fs_caveat}")
    else:
        print(f"  Registered here since {_fs_since}: "
              f"{', '.join(_fs_slugs)}\n")
        if _fs_caveat:
            print(f"  NARROWER WINDOW THAN ASKED FOR{_fs_caveat}\n")
        for _label, _verdicts, _why in _fs_rows:
            if _verdicts is None:
                print(f"      {_label}: {_why}")
                continue
            for _slug, _verdict, _detail in _verdicts:
                if _verdict in ('VIOLATION', 'ERRORED', 'UNREADABLE'):
                    _fs_findings += 1
                _tail = f" -- {_detail}" if _detail else ''
                print(f"      {_label}: {_slug} -> {_verdict}{_tail}")
        print("\n  A VIOLATION here is the case this exists for: the fix "
              "landed where the bug was\n  found, the detector came with "
              "it, and the repo that still has the bug has not\n  vendored "
              "the detector yet, so its own checks report nothing. Fix it "
              "there, in\n  this run -- a sweep that only lists is the "
              "clean result that costs the most.\n\n  Two limits, both "
              "real. This sweeps REGISTERED CHECKS only: a fix whose "
              "detector\n  shipped as a standalone tool, a planted harness "
              "case or a hook is not reached\n  here. And each repo is "
              "read as a one-commit copy, so a change-scope check has\n"
              "  no change to look at and declines -- correctly, since "
              "another repo's tree\n  cannot answer a question about this "
              "one's diff.")
    print()
    if led:
        led.end(findings=_fs_findings if not _fs_note else None)
        led.start('ACCRETION -- files nobody has read whole', kind='read')

    _ac_rows, _ac_window, _ac_note = _accretion(repo_root)
    print(f"ACCRETION -- what has been added since anybody read the whole "
          f"file ({_ac_window}-day window)\n")
    if _ac_note:
        print(f"  not measured -- {_ac_note}")
    else:
        print("  commits  lines  last read   file")
        for _path, _n, _lines, _read in _ac_rows:
            print(f"  {_n:>7}  {_lines:>5}  "
                  f"{_read or 'never':<11} {_path}")
        print("\n  Read ONE of these end to end this run, then "
              "`--record-read '<path>,note=...'`.\n  Churn is not a defect "
              "and the top row may be the healthy one; what the ranking\n"
              "  buys is that a file nobody has opened whole cannot stay "
              "invisible just\n  because every commit to it was fine.")
    print()
    if led:
        led.end(items=len(_ac_rows) if not _ac_note else None)
        led.start('SESSION LOAD')

    print("SESSION LOAD -- what every session pays before it does anything\n")
    # Every repo in force, not this checkout alone (session-load-budget): a
    # session loads its own instructions file AND whatever each attached
    # source contributes, and what it pays is the sum. Measuring repo_root
    # alone reported a fraction of the real cost and read as the whole of it.
    _sl_targets = [('this checkout', repo_root)]
    for _s in data['sources']:
        _p = _s.get('path')
        if _s.get('level') in FATAL_MISSING_LEVELS and _p:
            _sl_targets.append((_s.get('name'), pathlib.Path(_p)))
    _grand, _sl = 0, []
    for _sname, _sp in _sl_targets:
        if not pathlib.Path(_sp).is_dir():
            continue
        _rows, _msgs = _session_load(_sp)
        _sl.extend(_msgs)
        if not _rows:
            continue
        _tot = sum(n for _, _, n in _rows)
        _grand += _tot
        print(f"  {_sname}:")
        for _f, _name, _n in sorted(_rows, key=lambda r: -r[2])[:8]:
            print(f"  {_n:7,d}  {_f} :: {_name[:60]}")
        _rest = len(_rows) - min(8, len(_rows))
        if _rest > 0:
            print(f"  {sum(n for _,_,n in sorted(_rows, key=lambda r: -r[2])[8:]):7,d}"
                  f"  ({_rest} smaller section(s), combined)")
        print(f"  {'-'*7}")
        print(f"  {_tot:7,d}  subtotal\n")
    if _grand:
        print(f"  {_grand:7,d}  TOTAL across every repo in force, every session, "
              f"before any\n           work starts (rough: words x 1.3). Each "
              f"repo's own declared ceilings\n           live in its "
              f"tools/session_load_budgets.json, and every surface above is\n"
              f"           tested against them below -- for each repo measured, "
              f"not this\n           checkout alone, which is the half "
              f"precedent_check.py --only\n           session-load-budget "
              f"cannot reach from here.\n")
    for _m in _sl:
        print(f"  {_m}")
    if not _sl:
        print("  every surface is inside the ceiling its own repo declares "
              "for it, no section\n  is large enough to be worth splitting, "
              "and no entry claims its own trap is\n  settled. A repo that "
              "declares no ceiling is not tested against one -- "
              "session-\n  load-budget asks for the registry, and nothing "
              "here can invent the number.")
    _gc_rows, _gc_msgs = _gotchas_currency(repo_root)
    if _gc_rows:
        print("\n  GOTCHA CURRENCY -- the tree read against each entry, not "
              "the entry against\n  itself. The settled-marker note above "
              "catches an entry honest enough to\n  say it is fixed; these "
              "catch one that still reads as live while the remedy\n  it "
              "names has been renamed or deleted underneath it.\n")
        if _gc_msgs:
            for _m in _gc_msgs:
                print(f"  {_m}")
        else:
            print("  none -- every entry names a remedy that is still in the "
                  "tree, and each\n  carries a date recent enough that "
                  "nothing says it has gone stale.")
        _big = sorted(_gc_rows, key=lambda r: -r[0])[:5]
        print("\n  Largest entries, whatever they signalled -- a reduction "
              "pass ordered by\n  what it would actually save:")
        for _tok, _loc, _title, _sig in _big:
            print(f"  {_tok:5,d} tok  {_loc}  {_title[:62]}")
        print(f"  {sum(r[0] for r in _gc_rows):5,d} tok  "
              f"{len(_gc_rows)} entries, whole section")
    print("\n  Do NOT optimise for the total. These entries exist because "
          "sessions kept\n  losing hours to the same traps -- a trimming pass "
          "that chases the number\n  deletes the ones that are working. The "
          "question is \"would a session hit\n  this today\", never \"how big "
          "is it\". What no longer bites moves to a\n  linked archive IN FULL, "
          "never to a deletion.")
    _gr_candidates = _gotcha_retirement_candidates(repo_root)
    if _gr_candidates:
        print("\n  RETIRES_WHEN STATED -- the condition is written, judging "
              "whether it is MET\n  is a person's call (Part 5 rules out an "
              "auto-closer for the same reason\n  item-closes-on-its-condition "
              "does):")
        for _line in _gr_candidates:
            print(_line)
    print()

    # OPEN ITEMS. The deep read is the one moment somebody is looking at the
    # whole repository at once, which is the only moment an item nobody has
    # touched in months gets looked at at all. Two mechanical signals and no
    # verdicts: what the person asked to be reminded of, and items naming a
    # file the tree no longer has -- which is what an item that quietly got
    # done under another name looks like from outside
    # (practice: item-closes-on-its-condition).
    # spec/OPEN_ITEM_AND_GOTCHA_PLAN.md Part 4.1 step 8: since the
    # 2026-09-16 migration, open items live one-per-file under todo/, not
    # as TODO.md bullets -- todo_progress.py's TODO.md-shaped reading
    # would silently report "none" against the redirect stub it now finds
    # there, which is worse than not running at all
    # (practice: fail-gracefully). _open_item_sweep reads todo/*.md
    # directly, per Part 3's "Open-item sweep".
    _todo_findings = _open_item_sweep(repo_root)
    _todo_n = len(_todo_findings)
    if _todo_findings:
        print("OPEN ITEMS -- what the queue says about itself\n")
        for _line in _todo_findings:
            print(_line)
        print()
    if led:
        led.end(findings=len(_sl) + len(_gc_msgs if _gc_rows else []) + _todo_n)
        led.start('TIER PLACEMENT', kind='read')

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
    if led:
        led.end(items=len(_resp))
        led.start('RULES WE SHIP SOMEWHERE ELSE', kind='read')

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
    if led:
        led.end(items=len(_ship))
        led.start('MOVED CLAIMS')

    print("MOVED CLAIMS -- \"the work now lives in X\", where X is not "
          "there\n")
    _mc_n = 0
    _mc_seen = False
    _mc_unknown = []
    for _name, _p in _orph_targets:
        if not pathlib.Path(_p).is_dir():
            continue
        _mc_seen = True
        _rows = _moved_claims(_p)
        if _rows is None:
            # Could not list the repo's tracked files, so the
            # named-without-its-path suppression could not be built. Any
            # rows produced from here would be artefacts of the failed
            # read, not claims about this repository.
            _mc_unknown.append(_name)
            print(f"  {_name}: CANNOT TELL -- `git ls-files` failed, so "
                  f"this repository was not scanned. Not a clean result.")
            continue
        if not _rows:
            continue
        _mc_n += len(_rows)
        print(f"  {_name}:")
        for _file, _line, _claim, _target in _rows:
            print(f"      {_file}:{_line}  \"{_claim} {_target}\" -- no such "
                  f"file here")
    if not _mc_seen:
        print("  (no repository to scan)")
    elif _mc_n == 0 and _mc_unknown:
        print("  no rows -- but " + ", ".join(_mc_unknown) + " could not be "
              "scanned, so this is NOT 'none'.")
    elif _mc_n == 0:
        print("  none -- every file named as somewhere work moved to "
              "exists.")
    else:
        print("\n  Each row is a premise that was true when it was written. "
              "The file saying it\n  cannot know its destination went away, "
              "and nobody reads a paused file to\n  check -- which is "
              "exactly how two commit-scope checks came to run nowhere.")
    print()
    if led:
        # Unknown is not zero: a count that silently omits an unscanned
        # repository reads as a clean pass on it.
        led.end(findings=(_mc_n if _mc_seen and not _mc_unknown
                          else (None if _mc_unknown or not _mc_seen
                                else _mc_n)))
        led.start('DOCUMENTATION CURRENCY')

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
    if led:
        led.end(findings=len(_doc_find))
        led.start('MARKDOWN -- STRICT SWEEP')

    _md_summary, _md_count, _md_note = _markdown_sweep(repo_root)
    print("MARKDOWN -- STRICT SWEEP -- every tracked document, warning "
          "classes included\n")
    if _md_note:
        print(f"  note: {_md_note}")
    elif not _md_count:
        print("  clean -- no markdown finding of any class, in any tracked "
              "document.")
    else:
        for _line in _md_summary:
            print(f"  {_line}" if _line.strip() else "")
        print("\n  Pass 3 works this list; it does not gate the run. "
              "`python3 tools/doc_lint.py FILE`\n  for one file's findings "
              "in full, and `--fix FILE` for the strikethrough class.")
    print()
    if led:
        led.end(findings=_md_count)
        led.start('CROSS-REPO LINKS')

    print("CROSS-REPO LINKS -- do absolute github.com links into a repo "
          "in force actually resolve\n")
    _xl_findings, _xl_count, _xl_notes = _cross_repo_link_check(_orph_targets)
    for _n in _xl_notes:
        print(f"  note: {_n}")
    if _xl_notes and _xl_findings:
        print()
    if not _xl_findings:
        print("  clean -- every absolute github.com link into a repo this "
              "session has open\n  resolves, self-citation included.")
    else:
        for _f in _xl_findings:
            print(f"  {_f}")
    print()
    if led:
        led.end(findings=_xl_count)

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
        if led:
            led.start('UNLANDED WORK')
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
        if led:
            # An unmeasurable branch makes the count unknown, not zero: the
            # same distinction the section itself is written around.
            led.end(findings=None if _unknown else len(_unlanded))
    elif led:
        led.skipped('UNLANDED WORK', '--skip-branch-scan')

    # LIVE SESSIONS AGAINST THE REPO (practice: very-deep-check). Printed
    # beside UNLANDED WORK, for the same reason and one step further out:
    # unlanded work is a decision written down on a branch nobody merged,
    # and this is a decision never written down at all.
    #
    # The tool can only do the repo half. Which sessions ran, which are
    # still running and what each was asked for lives in the harness, and
    # nothing in this repository can read it -- so the inventory is printed
    # here and the session is told, in the same breath, to go and fetch the
    # other half rather than being left with a list that looks complete.
    if not skip_session_sweep:
        if led:
            led.start('LIVE SESSIONS -- recent work against the repo',
                      kind='read')
        _win = (session_days or _declared_session_window_days(repo_root)
                or SESSION_WINDOW_DAYS_DEFAULT)
        print(f"\nLIVE SESSIONS -- what ran recently, against what actually "
              f"landed\n")
        print(f"  The repo half, mechanical: everything pushed in the last "
              f"{_win} day(s).\n")
        _dirty_total = 0
        for _name, _act in activity.items():
            if _act is None:
                print(f"  {_name}: not its own git checkout -- skipped.\n")
                continue
            print(f"  {_name}: {len(_act['commits'])} commit(s), "
                  f"{len(_act['branches'])} branch(es) touched")
            for _b in _act['branches'][:12]:
                print(f"      {_b['last']}  {_b['name']}  "
                      f"({_b['author'] or 'author unreadable'})")
            if len(_act['branches']) > 12:
                print(f"      ... and {len(_act['branches']) - 12} more "
                      f"(--json for all)")
            if _act.get('dirty'):
                _dirty_total += _act['dirty']
                print(f"      UNCOMMITTED: {_act['dirty']} path(s) in the "
                      f"working tree of this clone -- work that exists in no "
                      f"commit at all")
            if _act.get('note'):
                print(f"      note: {_act['note']}")
            print()
        print("  The session half is NOT mechanical from here, and this "
              "section is not\n  read until you have fetched it. Ask the "
              "harness for this account's own\n  sessions -- its session "
              "listing tool (claude-code-remote's list_sessions,\n  then "
              "get_session for anything recent or still running) -- and hold "
              "each\n  one against the rows above:\n")
        print("    * a session that ran inside the window and left no commit, "
              "no branch\n      and no open pull request is the finding. Its "
              "conclusion exists only in\n      a chat thread, which "
              "repo-is-memory says is already lost. Recover what\n      it "
              "decided and commit it, or record that there was nothing to "
              "keep.\n"
              "    * a session still RUNNING against a repo in force is a "
              "different risk:\n      anything this check fixes may be "
              "overwritten by it, and anything it is\n      mid-way through "
              "will read here as half-done work. Name those before\n"
              "      starting the passes rather than discovering them in a "
              "conflict.\n"
              "    * a commit or branch above that matches no session anybody "
              "can account\n      for is the same question from the other "
              "side -- ask who did it before\n      giving its branch a "
              "verdict in pass 4.\n")
        if _dirty_total:
            print(f"  FINDING: {_dirty_total} uncommitted path(s) across the "
                  f"repos in force.\n  Some session's work is sitting in a "
                  f"working tree, where a fresh container\n  will take it "
                  f"with it.\n")
        if led:
            # Never a findings COUNT: the count this section is about is on
            # the other side of a tool this engine cannot call, so reporting
            # the repo half's zero would be a clean result from a check that
            # ran half way (practice: very-deep-check, pass 2 question 14).
            led.end(status='partial',
                    items=sum(len((a or {}).get('commits', []))
                              for a in activity.values()))
    elif led:
        led.skipped('LIVE SESSIONS -- recent work against the repo',
                    '--skip-session-sweep')

    if not skip_visibility:
        if led:
            led.start('REPOSITORY VISIBILITY')
        print()
        print("REPOSITORY VISIBILITY -- private names in a public tree\n")
        _bl = os.environ.get('PRECEDENT_LEAK_BLOCKLIST')
        _vf, _vn = repo_visibility_audit(repo_root, _bl)
        for f in _vf:
            print(f'  FINDING: {f}')
        for n in _vn:
            print(f'  note: {n}')
        # The offline half: names nothing has typed YET. These are
        # recommendations for the person, not findings against the tree --
        # this is the one place they are raised (practice: very-deep-check;
        # leak_gate.py's own copy is silenced by `stem-notes off`).
        _recs = leak_stem_recommendations(repo_root, _bl)
        for r in _recs:
            print(f'  RECOMMENDATION: {r}')
        if not _vf and not _vn and not _recs:
            print('  nothing referenced, nothing to check')
        print()
        if led:
            led.end(findings=len(_vf))
    elif led:
        led.skipped('REPOSITORY VISIBILITY', '--skip-visibility')

    if led:
        led.start('CHECKLIST -- the four passes a session works', kind='read')
    if print_checklist:
        print(checklist())
    else:
        # CHEAPENED 2026-09-14, on the component ledger's own reading: this
        # section printed ~9,900 tokens a run, 46% of the whole output, and it
        # is a verbatim copy of a section the session loads anyway with
        # `precedent_show.py very-deep-check --detail` before it can work a
        # single pass. The pointer is the section now; `--checklist` prints
        # the text for a session that wants it beside the enumeration.
        print('CHECKLIST -- the four passes a session works')
        print()
        print('  Not printed here (pass --checklist to print it). Read it from '
              'the practice:\n'
              '  python3 tools/precedent_show.py very-deep-check --detail\n'
              '  Pass 1 — adopter installs; Pass 2 — mechanisms; Pass 3 — '
              'coherence read;\n  Pass 4 — catalogue, backlog and branches. '
              'Work them in order.')
        print()
    if led:
        led.end()

    if not skip_branch_scan:
        if led:
            led.start('BRANCHES -- verdicts owed')
        print("\nBRANCHES -- both directions. A merged branch nobody deleted is\n"
              "clutter; an unmerged branch nobody decided about is lost work, and\n"
              "the second costs more. Every branch below needs a verdict -- see\n"
              "practices/very-deep-check.md:\n")
        if _branch_report_path:
            print(f"Also written, with a clickable delete link on every row, to "
                  f"{_branch_report_path} -- commit it, then work from that page "
                  f"instead of this transcript.\n")
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

            def _print_merged(rows, show_into=False):
                for r in rows:
                    _age = (f"last commit {r['last']}, {r['age_days']} day(s) "
                            f"old" if r['last']
                            else "last commit date unreadable in this clone")
                    # The author is printed on every row, never used to
                    # filter one out: a branch nobody in this session owns
                    # is the one most likely to have been sitting there
                    # longest (practice: very-deep-check, pass 4).
                    _who = f", last touched by {r['author']}" if r.get('author') else ""
                    _into = f", merged into {r['into']}" if show_into and r.get('into') else ""
                    print(f"    {r['name']} ({_age}{_who}{_into})")
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
            _elsewhere = scan.get('merged_elsewhere') or []
            _others = [b for b in scan.get('protected', [])
                       if b != scan['target']]
            # Only where a second protected branch exists. A repo whose
            # integration branch IS its default has nowhere else for work to
            # have landed, and a heading offering an empty third list there
            # reads as a check that found nothing rather than one with
            # nothing to ask.
            if _others:
                print("  merged into %s but NOT into %s -- equally proven safe "
                      "to delete;\n  their work is finished elsewhere and is "
                      "not on the integration branch:"
                      % (', '.join(_others), scan['target']))
                if _elsewhere:
                    # The "merged into X" suffix per row only earns its place
                    # when the heading cannot say which X: with one other
                    # protected branch it repeats the line above it.
                    _print_merged(_elsewhere, show_into=len(_others) > 1)
                else:
                    print(f"    {'(none)' if not incomplete else empty}")
            print(f"  NOT merged anywhere -- merge it or close it, one "
                  f"verdict each:")
            if scan['unmerged']:
                for r in scan['unmerged']:
                    age = f", last commit {r['last']}" if r['last'] else ""
                    who = f", last touched by {r['author']}" if r.get('author') else ""
                    print(f"    {r['name']} ({r['ahead']} commit(s) ahead"
                          f"{age}{who})")
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
        if led:
            # A verdict is owed on every branch listed, in both directions:
            # that is what this section asks for, so that is what it counts.
            _owed = sum(len(s.get('merged', []))
                        + len(s.get('merged_elsewhere', []))
                        + len(s.get('unmerged', []))
                        for s in branch_scans.values() if s)
            _incomplete = any((s or {}).get('unreachable')
                              or (s or {}).get('unfetched')
                              for s in branch_scans.values())
            led.end(findings=None if _incomplete else _owed,
                    extra_seconds=_scan_secs)
    elif led:
        led.skipped('BRANCHES -- verdicts owed', '--skip-branch-scan')

    # WHAT LANDED ON THE BASE BRANCH AND NEVER CAME ACROSS (practice:
    # very-deep-check, pass 4). Printed before the endgame rehearsal
    # because it is the cheap half of the same relationship: this is what
    # the two branches have already drifted by, while reconciling it is
    # still a few commits rather than a project. It reports and stops --
    # the session asks before implementing any of it.
    if drift is not None:
        if led:
            led.start('BASE BRANCH DRIFT')
        print(f"BASE BRANCH DRIFT -- what is on origin/{drift['base']} that "
              f"origin/{drift['target']} has never taken\n")
        if drift['status'] in ('cannot-tell', 'error'):
            print(f"  CANNOT TELL: {drift['note']}")
            print(f"  Reported as unknown, never as clean -- a comparison "
                  f"that could not run returns an\n  empty list, which reads "
                  f"exactly like an up-to-date branch.\n")
        elif drift['status'] == 'clean':
            print(f"  Nothing. Every commit on origin/{drift['base']} has a "
                  f"patch-equivalent on the branch.\n")
        else:
            n, shown = drift['total'], len(drift['commits'])
            print(f"  {n} commit(s) on origin/{drift['base']} have no "
                  f"patch-equivalent here, touching "
                  f"{len(drift['files'])} file(s).")
            print(f"  Carried work counts as landed: this is `git cherry`, "
                  f"so a change rewritten into\n  this branch's own shape is "
                  f"NOT listed.\n")
            for c in drift['commits']:
                head = f"      {c['sha']}  {c['date'] or '(no date)'}  {c['subject'] or ''}"
                print(head.rstrip())
                if c['files']:
                    print(f"          {', '.join(c['files'][:6])}"
                          + (f", +{len(c['files']) - 6} more"
                             if len(c['files']) > 6 else ''))
            if drift.get('truncated'):
                print(f"      ... and {drift['truncated']} older commit(s) "
                      f"not detailed (--json for the full list)")
            print(f"\n  ASK, DO NOT IMPLEMENT. None of this is applied "
                  f"automatically, by this tool or by\n  the session reading "
                  f"it: put the list to the person, say for each row whether "
                  f"it\n  belongs on this branch, and take only what they "
                  f"say to take (practice: very-deep-check).")
            print(f"  Some rows will be deliberately not-carried. A row "
                  f"declined once is still listed the\n  next run -- this "
                  f"scan has no memory of a decision; the run record is "
                  f"where that lives.\n")
        if drift['shallow']:
            print(f"  CAVEAT: this clone is shallow, so the merge base may "
                  f"not be the real one. Deepen\n  "
                  f"(`git fetch --unshallow origin`) and re-run before "
                  f"trusting an empty result.\n")
        if led:
            led.end(findings=(None if drift['status'] in
                              ('cannot-tell', 'error') else drift['total']),
                    extra_seconds=_drift_secs)
    elif led:
        led.skipped('BASE BRANCH DRIFT',
                    '--skip-base-drift' if skip_base_drift
                    else 'this checkout has no base branch separate from the '
                         'branch it works on')

    # THE ENDGAME MERGE (practice: very-deep-check, pass 4). Printed with
    # the branch material because it is the same question one level up: the
    # branch sweep asks which branches never landed, this asks what happens
    # when the branch everything lands ON finally lands itself.
    if endgame is not None:
        if led:
            led.start('ENDGAME MERGE')
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
        if led:
            led.end(findings=(None if endgame['status'] in
                              ('cannot-tell', 'error')
                              else len(endgame['dropped'])),
                    extra_seconds=_endgame_secs)
    elif led:
        led.skipped('ENDGAME MERGE', '--skip-endgame-merge')

    # THE OTHER BILL, the one that has actually been hurting. Placed beside
    # the API budget below because they are the same question about two
    # different meters, and read in the same breath.
    if led:
        led.start('ACTIONS FLOOR')
    _ab_days = session_days or _declared_session_window_days(repo_root) or 14
    print(f"ACTIONS FLOOR -- runs x jobs at GitHub's per-job minute floor "
          f"({_ab_days}-day window)\n")
    _ab_total, _ab_measured = 0, False
    if skip_liveness:
        print("  not asked (--skip-liveness).")
    else:
        for _name, _p in _orph_targets:
            if not pathlib.Path(_p).is_dir():
                continue
            _rows, _sub, _note = _actions_bill(_p, days=_ab_days)
            if _note:
                print(f"  {_name}: not measured -- {_note}")
                continue
            _ab_measured = True
            _ab_total += _sub
            print(f"  {_name}:")
            for _rel, _runs, _jobs, _floor, _why in _rows:
                if _floor is None:
                    print(f"      {_rel}: {_why}")
                else:
                    print(f"      {_rel}: {_runs} run(s) x {_jobs} job(s) "
                          f"= {_floor} floor-minute(s)")
            print(f"      subtotal: {_sub} floor-minute(s)")
        if _ab_measured:
            print(f"\n  {_ab_total} floor-minute(s) across every repo in "
                  f"force, over {_ab_days} days.\n  A FLOOR, not an "
                  f"invoice: real minutes are at least this, and whether "
                  f"they are\n  billed at all depends on the repository "
                  f"being private. The lever is job count\n  per workflow "
                  f"-- two workflows on one pull request is two whole "
                  f"minutes for\n  however little work (spec/CI_MINUTES_PLAN.md "
                  f"items 13 and 15).")
        else:
            print("  nothing measured -- no repo in force runs a workflow, "
                  "or GitHub could not\n  be asked.")
    print()
    if led:
        # An estimate is material to read, never a finding to fix: the
        # number is only a problem against a budget nobody has declared
        # here yet.
        led.end(items=_ab_total if _ab_measured else None)

    # WHAT THIS RUN COST, AND WHAT THE ACCOUNT HAS LEFT (practice:
    # github-api-budget). Last, deliberately: the spend figure is only
    # complete once every section that calls the API has finished, and the
    # headroom figure is read off the headers those calls already returned
    # rather than bought with one more (probe=False below).
    #
    # It reports and never refuses. A run that stopped because somebody
    # else's session had spent the pool would be the wrong remedy for the
    # right finding -- the remedy is fewer simultaneous sessions and cheaper
    # tools, and neither is this tool's to apply mid-run.
    if gh_budget is not None:
        if led:
            led.start('GITHUB API BUDGET')
        print('\nGITHUB API BUDGET -- what the account has left, and what '
              'this run spent\n')
        _bf, _bn, _brows = gh_budget.audit(tool='very_deep_check.py',
                                           probe=False)
        gh_budget.render(_bf, _bn, _brows)
        print()
        if led:
            led.end(findings=len(_bf))
    elif led:
        led.skipped('GITHUB API BUDGET',
                    'tools/github_budget.py is not present in this tree')

    if led:
        led.report()

    box['completed'] = True
    return 0


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/FOR_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
