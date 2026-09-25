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

Run:
  python3 tools/precedent_push_check.py          # every check, record a pass
  python3 tools/precedent_push_check.py --gate   # skip if this tree passed
  python3 tools/precedent_push_check.py --list   # what would run, and why

Exit status: 0 everything passed; 1 a check failed; 2 nothing could be run
(not a git checkout, or a repository of no kind this file knows).
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD = 'precedent-push-check.json'
TAIL_LINES = 40

# name, argv, and the workflow it stands in for. A python3 script is named
# by its path alone ({engine} is the engine directory); anything else gives
# its interpreter first. ONE list per kind -- this is the registry; nothing
# else restates it (practice: registry-source-of-truth).
DEEP_CHECK_SUITE = ('deep_check', ['bash', 'tools/checks/tests/run_all.sh'],
                    "no workflow -- the deep-check practice's own suite")
# Entries a repo may simply not have: skipped with a note, never a failure.
OPTIONAL = {'deep_check'}
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
        DEEP_CHECK_SUITE,
    ),
    'consumer': (
        ('precedent_check', ['{engine}/precedent_check.py', '--full-sweep'],
         'light-check.yml'),
        ('leak_gate', ['{engine}/leak_gate.py'],
         'leak-gate.yml (structural half only in CI)'),
        ('doc_lint', ['{engine}/doc_lint.py'],
         'bestpractice-docs.yml, retired 2026-09-21'),
        DEEP_CHECK_SUITE,
    ),
}


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


def plan(root, engine=HERE):
    """-> (kind, [(name, argv, replaces)]) with {engine} resolved relative
    to `root`, so the commands print the way a person would type them."""
    kind = repo_kind(engine)
    if kind is None:
        return None, []
    rel = engine.relative_to(root) if engine.is_relative_to(root) else engine
    out = []
    for name, argv, replaces in PUSH_CHECKS[kind]:
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


def already_passed(root, checks):
    tree = clean_tree(root)
    path = record_path(root)
    if not tree or not path or not path.is_file():
        return False
    try:
        rec = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    return rec.get('tree') == tree and rec.get('checks') == signature(checks)


def run(root, checks):
    failed, missing = [], []
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
        if p.returncode == 0:
            print(f'      passed in {took:.0f}s', flush=True)
            continue
        failed.append(name)
        print(f'      FAILED (exit {p.returncode}) in {took:.0f}s; last '
              f'{TAIL_LINES} lines:', flush=True)
        tail = (p.stdout + p.stderr).rstrip().splitlines()[-TAIL_LINES:]
        for line in tail:
            print(f'      | {line}')
    total = time.monotonic() - started
    return failed, missing, total


def main(argv):
    root_s = git(HERE, 'rev-parse', '--show-toplevel')
    if not root_s:
        print('precedent_push_check: not inside a git checkout; nothing to '
              'check.', file=sys.stderr)
        return 2
    root = Path(root_s)
    kind, checks = plan(root)
    if kind is None:
        print(f'precedent_push_check: cannot tell what kind of repository '
              f'{root} is (no ENGINE_MANIFEST.json kind beside this file, and '
              f'it is not BestPractice), so there is no list to run.',
              file=sys.stderr)
        return 2

    if '--list' in argv:
        print(f'{root.name} is {"an" if kind[0] in "aeiou" else "a"} {kind} '
              f'repository. Before a push:')
        for name, a, replaces in checks:
            print(f'  {name:16} {shown_interpreter(a)} {" ".join(a[1:])}')
            print(f'  {"":16} replaces {replaces}')
        return 0

    if '--gate' in argv and already_passed(root, checks):
        print(f'precedent_push_check: this exact tree already passed all '
              f'{len(checks)} check(s); nothing to re-run.')
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

    print(f'precedent_push_check: {kind} repository {root.name}, '
          f'{len(checks)} check(s) -- everything CI used to run, run here.',
          flush=True)
    failed, missing, total = run(root, checks)
    tree = clean_tree(root)
    if failed:
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
        path.write_text(json.dumps({
            'tree': tree, 'checks': signature(checks), 'kind': kind,
            'at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        }, indent=2) + '\n', encoding='utf-8')
        print(f'\nprecedent_push_check: all passed in {total:.0f}s; recorded '
              f'for tree {tree[:12]}, so a push of this commit will not '
              f're-run them.')
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
