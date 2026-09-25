#!/usr/bin/env python3
"""precedent_push_check.py -- run, before a push, what CI used to run after it.

WHY THIS EXISTS (Morgan, 2026-09-25, strength: decided). Three switches now
keep GitHub Actions from running on most of his pushes: `ci_workflows`
(no workflow installed), `ci_every_hours` and `ci_on_branches` (a `[skip
ci]` line on the commit, spec/CI_CADENCE_PLAN.md). And since 2026-09-21 a
practice source runs no CI at all (practice: source-sets-run-no-ci). Every
one of those decisions was argued on the same premise -- "the local check
runs before the push, so CI is a second opinion" -- and nothing ran the
local check. It was a sentence in AGENTS.md and in go-merge's Rule. His
ask, on being shown that: "it should be the same list of everything we
used to run (just locally we do it, not via the github ci/cd)."

So this is that list, per kind of repository, and one command that runs
all of it. `push-check-gate.sh` (templates/harness/claude-code/hooks/) calls
it with `--gate` before a session's `git push`, and refuses the push on a
failure. Nothing here depends on any one agent harness; the hook is the
thin Claude Code adapter, and any other harness runs this file directly.

WHAT "EVERYTHING WE USED TO RUN" MEANS, kind by kind. Each entry names the
workflow it replaces, so the next person to retire or add a workflow can
see where its local twin lives:

  upstream   BestPractice itself: .github/workflows/deep-check.yml
             (verify_harness, precedent_check, doc_sync), leak-gate.yml,
             and the retired docs.yml (doc_lint). This is also AGENTS.md's
             own "deep check" list, word for word.
  source     a practice set: the retired precedent-check.yml
             (precedent_check, plus its views-drift job, build_views
             --check), leak-gate.yml and doc-lint.yml. Its commit-identity
             steps already moved to commit-identity-push-gate.sh on
             2026-09-21 and are not repeated here.
  consumer   a repo that installs Precedent: leak-gate.yml, light-check.yml
             (precedent_check) and the retired bestpractice-docs.yml
             (doc_lint).

Two deliberate departures from what CI ran, both stronger rather than
weaker. precedent_check runs `--full-sweep`: bare, it runs only this diff's
checks plus a one-in-ten rotation, which is the trap every source set's
AGENTS.md warns about, and a sweep costs seconds. And leak_gate runs whole,
not `--structural-only`: CI could only run the structural half because it
never had the private blocklist, and a local run does.

THE DEEP CHECK'S OWN SUITE RUNS TOO, wherever a repo has one. A set that
maintains check scripts under tools/checks/ keeps a two-direction test for
each and a driver, tools/checks/tests/run_all.sh, that runs them all --
the mechanical half of its `deep-check` practice, in that practice's own
words. No workflow ever ran it; it was run by hand, or not. Morgan,
2026-09-25: "We had a deep_check too." The first run found five of one
set's cases red, fixed the same day. A repo with no driver skips the entry
and says so.

A SHALLOW CLONE IS DEEPENED FIRST, or the push is refused. Every clone in
a cloud session starts shallow, and a check that walks `git log` over a
shallow clone reports SKIPPED -- which this list would then call a pass.
Measured 2026-09-25: all five of that day's clones were shallow, and a
history check in one set had been skipping on every run. `git fetch
--unshallow` took one to five seconds each.

A PASS IS RECORDED AGAINST THE TREE, so the gate does not run the suite
twice. After a clean run with nothing uncommitted, the HEAD tree's hash
goes into .git/precedent-push-check.json. `--gate` finds that record and
exits at once, which is what makes "run the deep check, then push" cost one
run rather than two (practice: slow-steps-report-and-cache). The record
is keyed on the tree and the check list together, so any change to either
invalidates it, and it lives in the git directory, never in the tracked
tree.

AND THE PASS IS SHARED WITH EVERY CHECKOUT (Morgan, 2026-09-25, strength:
decided). The record above lives in one checkout, and a person working in
many windows has one checkout per window: a full run in one window was
invisible to the Promote said in another, which ran the whole suite again
on files it had already passed. So a recorded pass is also published to
origin as a small receipt on the branch precedent-check-receipts --
receipts/<check list>/<tree>.json, naming the files by hash and carrying
none of them, so it publishes no unpushed work. `--gate` fetches that
branch when this checkout has no record of its own. The trade, said
plainly: anyone who can push to origin can write one, and every checkout
then believes it. Only this file writes them, and only after every check
passed -- the trust the local record already asked for, now reaching every
window instead of one. PRECEDENT_NO_SHARED_PASS=1 turns
both halves off.

TWO TIERS, BY BRANCH (spec/BRANCH_TIERS_PLAN.md, Morgan, 2026-09-25,
strength: decided). A push to staging or main runs every check below -- the
FULL tier. A push to pre-staging or any other branch runs only the BASIC
tier: the markdown lint, the leak gate (pushing any branch of a public
repository publishes it) and the commit-author checks, seconds rather than
minutes. The person's `branch_push_checks` setting can raise the other
branches to full; nothing lowers staging or main. Which branch gets which
lives in precedent_branches.py, not here. A full pass satisfies a basic
gate; a basic pass never satisfies a full one.

Run:
  python3 tools/precedent_push_check.py                  # every check, record a pass
  python3 tools/precedent_push_check.py --tier basic     # the basic tier only
  python3 tools/precedent_push_check.py --gate           # skip if this tree passed
  python3 tools/precedent_push_check.py --gate --push-command 'origin pre-staging'
                                  # the tier that push needs (what the hook runs)
  python3 tools/precedent_push_check.py --list           # what would run, and why

Exit status: 0 everything passed; 1 a check failed; 2 nothing could be run
(not a git checkout, or a repository of no kind this file knows).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD = 'precedent-push-check.json'
# The shared receipts live on one branch -- a cloud session's git proxy
# lets it push branches and nothing else, so a hidden ref namespace was
# refused with a 403 (measured 2026-09-25). One small file per pass,
# receipts/<check list>/<tree>.json, the newest RECEIPTS_KEPT of them.
RECEIPT_BRANCH = 'precedent-check-receipts'
RECEIPT_REF = 'refs/precedent/receipts'
RECEIPTS_KEPT = 300
EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
SHARED_ENV = {'GIT_AUTHOR_NAME': 'precedent_push_check',
              'GIT_AUTHOR_EMAIL': 'precedent-push-check@localhost',
              'GIT_COMMITTER_NAME': 'precedent_push_check',
              'GIT_COMMITTER_EMAIL': 'precedent-push-check@localhost'}
TAIL_LINES = 40
# The lines that say WHY a check failed, printed before the tail. A check can
# end on pages of lines that are not the finding -- precedent_check prints its
# VIOLATION block and then every SKIPPED and unverified check after it -- so a
# tail alone can hold nothing but noise. On 2026-09-25 a merge gate refused a
# consumer's pull request over one unbumped version header, and the session it
# refused could not see why: all forty lines it was shown said SKIPPED.
FINDING = re.compile(r'^\s*(VIOLATION|ERROR|FAIL(ED|URE)?)\b')
FINDING_LINES = 30


def _finding_lines(out):
    """The finding headers in `out`, each with the indented lines under it
    (its findings, not the rule text after them), capped at FINDING_LINES."""
    picked, i = [], 0
    while i < len(out) and len(picked) < FINDING_LINES:
        if FINDING.match(out[i]):
            picked.append(out[i])
            i += 1
            while (i < len(out) and out[i].startswith('    ')
                   and len(picked) < FINDING_LINES):
                picked.append(out[i])
                i += 1
            continue
        i += 1
    return picked

# name, argv, and the workflow it stands in for. A python3 script is named
# by its path alone ({engine} is the engine directory); anything else gives
# its interpreter first. ONE list per kind -- this is the registry; nothing
# else restates it (practice: registry-source-of-truth).
DEEP_CHECK_SUITE = ('deep_check', ['bash', 'tools/checks/tests/run_all.sh'],
                    "no workflow -- the deep-check practice's own suite")
# The author and timezone checks, where a repo carries them. They ran in
# precedent-individual's commit-identity.yml and precedent-check.yml until
# 2026-09-21; commit-identity-push-gate.sh runs them too, but only where it
# is wired, and a person running this list by hand should get everything.
# Exit 2 ("could not run here") fails in a repo that carries its own
# identity.json, as it did there; anywhere else it is the expected answer --
# a person's timezone binds only their own individual source (Morgan,
# 2026-09-25: "only use the individual one in the precedent-individual").
SKIP_IS_FINE_WITHOUT_IDENTITY = {'commit_author', 'commit_dates'}
IDENTITY_CHECKS = (
    ('commit_author', ['{engine}/checks/check_commit_author.py'],
     "precedent-individual's commit-identity.yml, retired 2026-09-21"),
    ('commit_dates', ['{engine}/checks/check_buenos_aires_dates.py'],
     "precedent-individual's commit-identity.yml, retired 2026-09-21"),
)
# Every workflow file is the engine's own untouched copy or carries the
# person's approval pinned to its content (practice: ci-workflow-approved).
CI_WORKFLOWS_CHECK = (
    'ci_workflows', ['{engine}/precedent_check.py', '--only',
                     'ci-workflow-approved'],
    'no workflow -- the check that keeps workflows from being added unasked')
# Entries a repo may simply not have: skipped with a note, never a failure.
OPTIONAL = {'deep_check', 'commit_author', 'commit_dates', 'light_check'}
# The BASIC tier: what a push to pre-staging or any other working branch
# runs. Everything else in a kind's list is FULL-only. The leak gate is
# here because a push IS publication in a public repository, and cannot
# wait for promotion (Morgan, 2026-09-25: "Good on nothing private going
# out", strength: assented). Each costs seconds.
# ci_workflows is here because a workflow file starts billing the moment it
# reaches ANY branch GitHub runs it on; light_check is the repo's own fast
# check, and its secret scan wants every push (practice: ci-workflow-approved;
# Morgan, 2026-09-25, "we need to absolutely put a hard stop to this").
BASIC_CHECKS = {'doc_lint', 'leak_gate', 'commit_author', 'commit_dates',
                'ci_workflows', 'light_check'}
BASIC, FULL = 'basic', 'full'
PUSH_CHECKS = {
    'upstream': (
        ('verify_harness', ['{engine}/verify_harness.py', '--as-ci'],
         'deep-check.yml, both verify_harness jobs'),
        ('precedent_check', ['{engine}/precedent_check.py', '--full-sweep'],
         'deep-check.yml, precedent_check + doc_sync job'),
        ('doc_sync', ['{engine}/doc_sync.py'],
         'deep-check.yml, precedent_check + doc_sync job'),
        ('leak_gate', ['{engine}/leak_gate.py'],
         'leak-gate.yml (structural half only in CI)'),
        ('doc_lint', ['{engine}/doc_lint.py'],
         'docs.yml, retired 2026-09-21'),
        DEEP_CHECK_SUITE,
        *IDENTITY_CHECKS,
    ),
    'source': (
        ('precedent_check', ['{engine}/precedent_check.py', '--full-sweep'],
         'precedent-check.yml, retired 2026-09-21'),
        ('build_views', ['{engine}/build_views.py', '--repo', '.', '--check'],
         "precedent-check.yml's views-drift job, retired 2026-09-21"),
        ('leak_gate', ['{engine}/leak_gate.py'],
         'leak-gate.yml, retired 2026-09-21'),
        ('doc_lint', ['{engine}/doc_lint.py'],
         'doc-lint.yml, retired 2026-09-21'),
        CI_WORKFLOWS_CHECK,
        DEEP_CHECK_SUITE,
        *IDENTITY_CHECKS,
    ),
    'consumer': (
        ('precedent_check', ['{engine}/precedent_check.py', '--full-sweep'],
         'light-check.yml'),
        ('leak_gate', ['{engine}/leak_gate.py'],
         'leak-gate.yml (structural half only in CI)'),
        ('doc_lint', ['{engine}/doc_lint.py'],
         'bestpractice-docs.yml, retired 2026-09-21'),
        CI_WORKFLOWS_CHECK,
        # The repo's OWN light check, where it has one: what its
        # light-check.yml ran on GitHub, run here instead of there.
        ('light_check', ['tools/light_check.py'],
         "the repo's own light-check.yml"),
        DEEP_CHECK_SUITE,
        *IDENTITY_CHECKS,
    ),
}


# WHAT A PASS HAS TO SHOW, beyond exit 0. The retired precedent-check.yml
# refused three shapes of "green" that verified nothing, each after it had
# happened for real; they are carried over here rather than lost with it.
def _guard_precedent_check(out, engine):
    m = re.search(r'^precedent_check: (\d+) passed', out, re.M)
    if not m:
        return ('no precedent_check summary line, so nothing says what it '
                'checked')
    if int(m.group(1)) == 0:
        return ('ZERO checks passed -- every one skipped or did not run, and '
                'a skip is not a pass')
    if repo_kind(engine) == 'source':
        # An engine from before binds_publishers skips, in a practice set,
        # the checks whose practice lives upstream, and still exits 0.
        p = subprocess.run(
            [sys.executable, '-c',
             'import sys; sys.path.insert(0, sys.argv[1]); '
             'import precedent_check as pc; '
             'sys.exit(0 if any(c.get("binds_publishers") for c in '
             'pc.CHECKS.values()) else 1)', str(engine)],
            capture_output=True, text=True)
        if p.returncode != 0:
            return ('the vendored engine predates binds_publishers, so in a '
                    'practice set it skips the checks that bind what this '
                    'repo publishes -- refresh it (precedent_vendor_engine.py '
                    'refresh)')
    return None


def _guard_build_views(out, engine):
    if 'NOT VERIFIABLE' in out:
        return ('the loader block is built from sources this machine cannot '
                'reach, so "no drift" was not established')
    return None


GUARDS = {'precedent_check': _guard_precedent_check,
          'build_views': _guard_build_views}


def git(root, *args):
    p = subprocess.run(['git', '-C', str(root), *args],
                       capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def repo_kind(engine=HERE):
    """-> 'upstream' | 'source' | 'consumer' | None. A vendored engine says
    its own kind in ENGINE_MANIFEST.json; BestPractice has no manifest,
    because it is where the engine comes from, and is the only repo
    carrying verify_harness.py (never vendored)."""
    manifest = engine / 'ENGINE_MANIFEST.json'
    if manifest.is_file():
        try:
            kind = json.loads(manifest.read_text(encoding='utf-8')).get('kind')
        except (OSError, ValueError):
            return None
        return kind if kind in PUSH_CHECKS else None
    if (engine / 'verify_harness.py').is_file():
        return 'upstream'
    return None


def plan(root, engine=HERE, tier=FULL):
    """-> (kind, [(name, argv, replaces)]) with {engine} resolved relative
    to `root`, so the commands print the way a person would type them.
    `tier` BASIC keeps only BASIC_CHECKS."""
    kind = repo_kind(engine)
    if kind is None:
        return None, []
    rel = engine.relative_to(root) if engine.is_relative_to(root) else engine
    out = []
    for name, argv, replaces in PUSH_CHECKS[kind]:
        if tier == BASIC and name not in BASIC_CHECKS:
            continue
        argv = [a.replace('{engine}', str(rel)) for a in argv]
        if argv[0].endswith('.py'):
            argv = [sys.executable, *argv]
        out.append((name, argv, replaces))
    return kind, out


def shown_interpreter(argv):
    return 'python3' if argv[0] == sys.executable else argv[0]


def signature(checks):
    return hashlib.sha256(json.dumps(
        [[n, a[1:]] for n, a, _ in checks]).encode()).hexdigest()[:16]


def record_path(root):
    p = git(root, 'rev-parse', '--git-path', RECORD)
    return (root / p) if p else None


def clean_tree(root):
    """-> the HEAD tree hash when nothing tracked is uncommitted, else None.
    A run over uncommitted edits checked something the push will not send,
    so it is never recorded as a pass for the commit."""
    if git(root, 'status', '--porcelain', '--untracked-files=no') != '':
        return None
    return git(root, 'rev-parse', 'HEAD^{tree}')


def already_passed(root, checks, also=()):
    """The record, when this tree's recorded pass covers `checks` -- or any
    of the check lists in `also`, which is how a FULL pass satisfies a BASIC
    gate -- else None. The record names the list it passed by signature, so
    a BASIC pass can never satisfy a FULL gate."""
    tree = clean_tree(root)
    path = record_path(root)
    if not tree or not path or not path.is_file():
        return None
    try:
        rec = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    accepted = {signature(checks), *(signature(c) for c in also)}
    if rec.get('tree') == tree and rec.get('checks') in accepted:
        return rec
    return None


def _shared_off(root):
    return (os.environ.get('PRECEDENT_NO_SHARED_PASS') == '1'
            or not git(root, 'remote', 'get-url', 'origin'))


def _git_env(root, args, timeout, env=None):
    try:
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                              text=True, timeout=timeout,
                              env=dict(os.environ, **(env or {})))
    except (OSError, subprocess.TimeoutExpired):
        return None


def _fetch_receipts(root):
    """-> the receipt branch's tip, fetched into a private ref, or None."""
    f = _git_env(root, ['fetch', '-q', '--no-tags', 'origin',
                        f'+refs/heads/{RECEIPT_BRANCH}:{RECEIPT_REF}'], 30)
    if f is None or f.returncode != 0:
        return None
    return git(root, 'rev-parse', '-q', '--verify', RECEIPT_REF) or None


def shared_pass(root, tree, sigs):
    """The record another checkout published to origin for `tree` under any
    of the check-list signatures `sigs`, else None. Never raises: a remote
    that cannot be reached is a pass not found, and the suite runs."""
    if not tree or _shared_off(root) or not _fetch_receipts(root):
        return None
    for sig in sigs:
        body = git(root, 'cat-file', '-p', f'{RECEIPT_REF}:receipts/{sig}/{tree}.json')
        if body:
            try:
                rec = json.loads(body)
            except ValueError:
                continue
            if rec.get('tree') == tree and rec.get('checks') == sig:
                return rec
    return None


def publish_pass(root, rec):
    """Add a recorded pass to the receipt branch on origin, for every other
    checkout. Best effort: a failure is said and never fails the run that
    passed. Two windows writing at once is a rejected push, retried on the
    newer tip."""
    if _shared_off(root):
        return
    path = f'receipts/{rec["checks"]}/{rec["tree"]}.json'
    index = git(root, 'rev-parse', '--git-path', 'precedent-receipts.index')
    if not index:
        return
    env = dict(SHARED_ENV, GIT_INDEX_FILE=str(
        Path(index) if Path(index).is_absolute() else root / index))
    why = 'no attempt made'
    for _ in range(3):
        tip = _fetch_receipts(root)
        _git_env(root, ['read-tree', tip or '--empty'], 10, env)
        order = (git(root, 'cat-file', '-p', f'{tip}:ORDER') if tip else '') or ''
        order = [l for l in order.splitlines() if l and l != path] + [path]
        blob = subprocess.run(['git', '-C', str(root), 'hash-object', '-w', '--stdin'],
                              input=json.dumps(rec, indent=2, sort_keys=True) + '\n',
                              capture_output=True, text=True).stdout.strip()
        olist = subprocess.run(['git', '-C', str(root), 'hash-object', '-w', '--stdin'],
                               input='\n'.join(order[-RECEIPTS_KEPT:]) + '\n',
                               capture_output=True, text=True).stdout.strip()
        for old in order[:-RECEIPTS_KEPT]:
            _git_env(root, ['update-index', '--force-remove', old], 10, env)
        _git_env(root, ['update-index', '--add', '--cacheinfo',
                        f'100644,{blob},{path}'], 10, env)
        _git_env(root, ['update-index', '--add', '--cacheinfo',
                        f'100644,{olist},ORDER'], 10, env)
        tree = _git_env(root, ['write-tree'], 10, env)
        if tree is None or tree.returncode != 0:
            why = 'could not build the receipt'
            break
        # [skip ci]: a workflow that runs on every branch push must not
        # bill a run for a receipt.
        c = _git_env(root, ['commit-tree', tree.stdout.strip(),
                            *(['-p', tip] if tip else []), '-m',
                            f'[skip ci] receipt: {rec["tier"]} check passed on '
                            f'tree {rec["tree"][:12]}'], 10, SHARED_ENV)
        if c is None or c.returncode != 0:
            why = 'could not build the receipt'
            break
        # --no-verify: a pre-push hook here is this very check.
        p = _git_env(root, ['push', '-q', '--no-verify', 'origin',
                            f'{c.stdout.strip()}:refs/heads/{RECEIPT_BRANCH}'], 60)
        if p is not None and p.returncode == 0:
            _git_env(root, ['update-ref', RECEIPT_REF, c.stdout.strip()], 10)
            print('precedent_push_check: receipt shared with every checkout of '
                  'this repository, so no other window re-runs these files.')
            return
        why = p.stderr.strip()[:200] if p is not None else 'timed out'
    print(f'precedent_push_check: NOTE -- could not share the receipt with '
          f'other checkouts ({why}); they will run the suite themselves.')


def _tier_from_args(root, argv):
    """-> (tier, why). --tier wins; else --push-command names the push and
    precedent_branches.py decides; else FULL, today's behaviour."""
    if '--tier' in argv:
        i = argv.index('--tier')
        value = argv[i + 1] if i + 1 < len(argv) else ''
        if value in (BASIC, FULL):
            return value, f'--tier {value}'
        return FULL, f'--tier {value!r} is not basic or full; running full'
    if '--push-command' in argv:
        i = argv.index('--push-command')
        cmd = argv[i + 1] if i + 1 < len(argv) else ''
        try:
            sys.path.insert(0, str(HERE))
            import precedent_branches
        except ImportError:
            return FULL, ('precedent_branches.py is not beside this file, so '
                          'the branch cannot be read -- running full')
        finally:
            sys.path.pop(0)
        return precedent_branches.tier_for_push(root, cmd)
    return FULL, 'no tier named'



def run(root, checks):
    failed, missing, findings = [], [], {}
    started = time.monotonic()
    for i, (name, argv, replaces) in enumerate(checks, 1):
        script = root / argv[1]
        shown = ' '.join([shown_interpreter(argv), *argv[1:]])
        if not script.is_file() and name in OPTIONAL:
            print(f'[{i}/{len(checks)}] {name}: not here -- this repo has no '
                  f'{argv[1]}', flush=True)
            continue
        if not script.is_file():
            # A check whose tool this repo does not carry cannot be run, and
            # saying so beats a crash. Reported, never silently dropped.
            missing.append(name)
            print(f'[{i}/{len(checks)}] {name}: NOT RUN -- {argv[1]} is not '
                  f'in this repo (stands in for {replaces})', flush=True)
            continue
        print(f'[{i}/{len(checks)}] {name}: {shown}', flush=True)
        t0 = time.monotonic()
        p = subprocess.run(argv, cwd=root, capture_output=True, text=True)
        took = time.monotonic() - t0
        guard = GUARDS.get(name)
        why = guard(p.stdout + p.stderr, HERE) if guard and p.returncode == 0 \
            else None
        if why:
            failed.append(name)
            print(f'      FAILED in {took:.0f}s although it exited 0: {why}',
                  flush=True)
            continue
        if p.returncode == 0:
            print(f'      passed in {took:.0f}s', flush=True)
            continue
        if (p.returncode == 2 and name in SKIP_IS_FINE_WITHOUT_IDENTITY
                and not (root / 'identity.json').is_file()):
            print(f'      stood aside in {took:.0f}s -- not an individual '
                  f'source, so there is no person to hold it to', flush=True)
            continue
        failed.append(name)
        out = (p.stdout + p.stderr).rstrip().splitlines()
        found = _finding_lines(out)
        findings[name] = found
        if found:
            print(f'      FAILED (exit {p.returncode}) in {took:.0f}s; what '
                  f'it found:', flush=True)
            for line in found:
                print(f'      | {line}')
        print(f'      last {TAIL_LINES} lines of its output:', flush=True)
        for line in out[-TAIL_LINES:]:
            print(f'      | {line}')
    total = time.monotonic() - started
    return failed, missing, total, findings


def main(argv):
    root_s = git(HERE, 'rev-parse', '--show-toplevel')
    if not root_s:
        print('precedent_push_check: not inside a git checkout; nothing to '
              'check.', file=sys.stderr)
        return 2
    root = Path(root_s)
    tier, why = _tier_from_args(root, argv)
    kind, checks = plan(root, tier=tier)
    if kind is None:
        print(f'precedent_push_check: cannot tell what kind of repository '
              f'{root} is (no ENGINE_MANIFEST.json kind beside this file, and '
              f'it is not BestPractice), so there is no list to run.',
              file=sys.stderr)
        return 2

    if '--list' in argv:
        print(f'{root.name} is {"an" if kind[0] in "aeiou" else "a"} {kind} '
              f'repository. Before a push to staging or main (full); a push '
              f'to any other branch runs only the checks marked basic:')
        for name, a, replaces in plan(root, tier=FULL)[1]:
            mark = 'basic' if name in BASIC_CHECKS else 'full '
            print(f'  {name:16} [{mark}] {shown_interpreter(a)} {" ".join(a[1:])}')
            print(f'  {"":16}         replaces {replaces}')
        return 0

    also = [plan(root, tier=FULL)[1]] if tier == BASIC else []
    rec = already_passed(root, checks, also) if '--gate' in argv else None
    where = ''
    if '--gate' in argv and not rec:
        sigs = [signature(checks), *(signature(c) for c in also)]
        rec = shared_pass(root, clean_tree(root), sigs)
        if rec:
            where = ', in another checkout'
            path = record_path(root)
            if path:
                path.write_text(json.dumps(
                    {k: v for k, v in rec.items() if k != 'shared'},
                    indent=2) + '\n', encoding='utf-8')
    if rec:
        when = f' at {rec["at"]}' if rec.get('at') else ''
        print(f'precedent_push_check: this exact tree already passed the '
              f'{rec.get("tier", tier)} check{when}{where} ({len(checks)} '
              f'check(s)); nothing to re-run.')
        return 0

    if git(root, 'rev-parse', '--is-shallow-repository') == 'true':
        print('precedent_push_check: this clone is shallow, so every check '
              'that reads history would skip -- deepening it first '
              '(git fetch --unshallow).', flush=True)
        subprocess.run(['git', '-C', str(root), 'fetch', '-q', '--unshallow'],
                       capture_output=True, text=True)
        if git(root, 'rev-parse', '--is-shallow-repository') == 'true':
            print('precedent_push_check: FAILED -- the clone is still shallow '
                  '(the fetch did not complete), so the history checks '
                  'cannot run. Run `git fetch --unshallow` and try again.')
            return 1

    if tier == FULL:
        print(f'precedent_push_check: {kind} repository {root.name}, '
              f'{len(checks)} check(s) -- everything CI used to run, run here '
              f'({why}).', flush=True)
    else:
        print(f'precedent_push_check: {kind} repository {root.name}, the '
              f'basic check, {len(checks)} check(s) ({why}). Staging and main '
              f'get everything.', flush=True)
    failed, missing, total, findings = run(root, checks)
    tree = clean_tree(root)
    if failed:
        # Said again at the very end, because the end is what every caller
        # that truncates -- the push gate, the merge gate -- keeps.
        for name in failed:
            for line in findings.get(name, []):
                print(f'  {name} | {line}')
        print(f'\nprecedent_push_check: FAILED -- {", ".join(failed)} '
              f'({total:.0f}s). Fix the finding and run this again; do not '
              f'push past it.')
        return 1
    if missing:
        print(f'\nprecedent_push_check: passed, but {", ".join(missing)} '
              f'could not run here -- this repo does not carry the tool. '
              f'Refresh the vendored engine to get it.')
    path = record_path(root)
    if tree and path:
        rec = {'tree': tree, 'checks': signature(checks), 'kind': kind,
               'tier': tier, 'at': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
        path.write_text(json.dumps(rec, indent=2) + '\n', encoding='utf-8')
        print(f'\nprecedent_push_check: all passed in {total:.0f}s; recorded '
              f'for tree {tree[:12]} ({tier}), so a push of this commit will '
              f'not re-run them.')
        publish_pass(root, rec)
    else:
        print(f'\nprecedent_push_check: all passed in {total:.0f}s, over a '
              f'working tree with uncommitted changes -- NOT recorded, since '
              f'the push sends the commit, not these edits. Commit, then run '
              f'it again or let the push gate do it.')
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
