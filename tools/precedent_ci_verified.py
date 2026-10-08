#!/usr/bin/env python3
"""Did CI actually run, and pass, on the commit about to be merged — advisory, one API call

precedent_ci_verified.py -- did CI actually run on the commit about to be
merged, and did it pass?

THE FAILURE THIS ANSWERS, 2026-09-23 in alex137/BestPractice. A pull request
showed a green tick. One workflow of the two had run on its head commit; the
other, the one carrying verify_harness/precedent_check/doc_sync, never fired
at all. Its `pull_request:` trigger had produced a run for the four previous
pull requests on that same branch and silently produced none for the fifth,
with no configuration difference. Nothing on the pull request page said so:
GitHub re-attaches a branch's historical workflow runs to whatever pull
request is currently open on it, so four green runs earned by EARLIER pull
requests on the same branch name were displayed as this one's history.

So "the pull request is green" is not the question. The question is whether
a successful run exists FOR THIS EXACT COMMIT, for every workflow that was
supposed to produce one. That is what this answers.

ADVISORY, NEVER A REFUSAL, and that is a deliberate limit rather than
timidity. It asks GitHub unauthenticated, which is 60 requests an hour per
IP shared across every session on this machine (practice:
github-api-budget). A gate that blocked a merge on somebody else's rate
limit, or on a proxy hiccup, would be routed around within a week and then
believed by nobody. It reports; the person or session decides.

ONE REQUEST per invocation: GET /repos/{slug}/actions/runs?head_sha={sha}.
The workflow-RUNS endpoint rather than the check-RUNS one deliberately --
check runs are named for JOBS ("precedent_check + doc_sync + verify_harness --as-ci"), which
cannot be matched against the workflow files on disk; workflow runs carry
the workflow's own `name:`, which can.

WHAT IT CANNOT SEE, stated because a checker that looks complete is worse
than one that says where it stops:
  - whether a workflow that did not run was SUPPOSED to, in any case
    subtler than its trigger block. The expected set is read from the
    workflow files and over-reports rather than under-reports: a workflow
    narrowed by `paths:` or by a glob branch pattern is expected here even
    where GitHub would skip it.
  - a private repository. Unauthenticated, GitHub answers 404 for private
    and for deleted alike, so that resolves to UNVERIFIED, never to clean.
  - whether the run tested what it claimed. A green run of a workflow whose
    job silently skipped its real work still reads as success here.
"""
import json, os, pathlib, re, subprocess, sys, urllib.error, urllib.request

API = 'https://api.github.com'
TIMEOUT = 15

VERIFIED, FAILED, NOT_RUN, RUNNING, UNVERIFIED, NEVER_STARTED = (
    'verified', 'failed', 'not_run', 'running', 'unverified', 'never_started')


def _git(root, *args):
    """-> (ok, stdout). Never raises: this whole module degrades to
    UNVERIFIED rather than taking a gate down (practice: fail-gracefully)."""
    try:
        p = subprocess.run(['git', '-C', str(root), *args],
                           capture_output=True, text=True)
    except OSError:
        return False, ''
    return p.returncode == 0, p.stdout.strip()


def repo_slug(root):
    """-> 'owner/repo' from origin, or '' when it cannot be read."""
    ok, url = _git(root, 'config', '--get', 'remote.origin.url')
    if not ok or not url:
        return ''
    m = re.search(r'github\.com[:/]+([^/]+)/(.+?)(?:\.git)?/?$', url)
    return f'{m.group(1)}/{m.group(2)}' if m else ''


def _branch_filter(block):
    """-> the branch names a trigger block's inline `branches: [..]` lists,
    or None when it has no such filter (every branch)."""
    filt = re.search(r'branches:[ \t]*\[(.*?)\]', block or '')
    if not filt:
        return None
    return [b.strip().strip('"\'') for b in filt.group(1).split(',') if b.strip()]


def expected_workflows(root, branch='', base=''):
    """-> {workflow name} for every workflow that should produce a run for a
    commit on `branch`, merged by a pull request into `base`.

    Read off the tree rather than hardcoded, so adding a workflow is enough
    to make it expected and nothing has to remember to update a list
    (practice: registry-source-of-truth).

    A workflow counts when its `on:` declares `pull_request:` whose branch
    filter the pull request's `base` satisfies, or `push:` whose branch
    filter this branch satisfies -- an ABSENT filter meaning every branch,
    and an unknown `base` counting as a match (over-report, never miss).

    THE BASE WAS IGNORED until 2026-09-30: any `pull_request:` counted, so
    deep-check.yml (`pull_request: branches: [main]`) was expected on every
    pull request into pre-staging, where it never fires, and the merge gate
    said "CI DID NOT RUN" and advised a workflow_dispatch run that would
    have spent Actions minutes for nothing. Both shapes
    are live in this repository: deep-check.yml is pull_request plus push on
    main, leak-gate.yml is push on every branch and no
    pull_request at all.

    THE NAIVE VERSION WAS WRONG and its own output caught it: testing for
    the substring `pull_request:` anywhere in the `on:` block reported
    leak-gate.yml as pull-request-triggered, because that block carries a
    COMMENT explaining why the trigger was removed. Anchored to the start of
    a line, past indentation, a comment cannot pose as a key.

    Blind to `paths:`/`paths-ignore:` filters and to glob branch patterns; a
    workflow scoped by either is over-reported rather than missed, which is
    the safe direction for a thing that only ever advises."""
    names = set()
    d = pathlib.Path(root) / '.github' / 'workflows'
    if not d.is_dir():
        return names
    for f in sorted(list(d.glob('*.yml')) + list(d.glob('*.yaml'))):
        try:
            text = f.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        name = re.search(r'^name:[ \t]*(.+?)[ \t]*$', text, re.M)
        if not name:
            continue
        # The `on:` block, to its first unindented key after it.
        on = re.search(r'^on:[ \t]*\n(.*?)(?=^\S)', text, re.S | re.M)
        body = on.group(1) if on else ''
        pr = re.search(r'^\s*pull_request:[ \t]*\n?(.*?)(?=^\s{0,2}\w|\Z)',
                       body, re.S | re.M)
        wanted = False
        if pr:
            only = _branch_filter(pr.group(1))
            wanted = only is None or not base or base in only
        push = re.search(r'^\s*push:[ \t]*\n(.*?)(?=^\s{0,2}\w|\Z)',
                         body, re.S | re.M)
        if push and not wanted:
            only = _branch_filter(push.group(1))
            if only is None:
                wanted = True
            elif branch:
                wanted = branch in only
        if wanted:
            names.add(name.group(1).strip().strip('"\''))
    return names


def _fetch_runs(slug, sha):
    """-> (runs, error). Never raises."""
    return _get(f'{API}/repos/{slug}/actions/runs?head_sha={sha}&per_page=100',
                'workflow_runs')


def _fetch_jobs(jobs_url):
    """-> (jobs, error) for one workflow run. Never raises. Asked only for a
    run that did not pass, so a green merge still costs one request."""
    return _get(f'{jobs_url}?per_page=100', 'jobs')


def never_started(jobs):
    """True when every job of a run that did not pass was cancelled without a
    runner ever picking it up: GitHub had no machine for it, so no check ran
    and nothing was found.

    THE INCIDENT (2026-10-05). For about an hour, roughly half of all jobs in
    this repository, on every branch and workflow, sat queued for fifteen
    minutes and were cancelled with `runner_id: 0` and no log. The run's own
    conclusion read `failure`, so this tool said "CI FAILED", and a session
    spent three quarters of an hour looking for a finding that did not exist
    (gotchas/gotcha-2026-10-05-a-ci-run-that-never-got-a-runner-reads-as-ci-failed.md)."""
    bad = [j for j in jobs or []
           if j.get('conclusion') not in ('success', 'skipped', 'neutral')]
    return bool(bad) and all(
        j.get('conclusion') == 'cancelled' and not j.get('runner_name')
        and not j.get('runner_id') for j in bad)


def _get(url, key):
    """-> (the list under `key`, error). Never raises."""
    req = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'precedent-ci-verified'})
    token = (os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN'))
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as f:
            return json.load(f).get(key, []), ''
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return None, ('GitHub answered 403 -- the unauthenticated rate '
                          'limit is 60/hour per IP and is shared across every '
                          'session on this machine')
        if e.code == 404:
            return None, ('GitHub answered 404 -- unauthenticated, a private '
                          'repository and a deleted one answer alike, so this '
                          'proves nothing either way')
        return None, f'GitHub answered {e.code}'
    except Exception as e:                                    # noqa: BLE001
        return None, f'{type(e).__name__}: {e}'


def merge_base_branch(root, branch):
    """-> the branch a pull request from `branch` merges into, as this
    repository's tiers make it: a Promote's to-main copy and staging go
    into main, pre-staging into staging, anything else into the person's
    landing branch. '' when that cannot be read."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_branches as pb
        staging = pb.staging_branch(root)
        if pb.is_main_copy(branch) or branch == staging:
            return pb.MAIN
        if branch == pb.PRE_STAGING:
            return staging
        return pb.landing_branch(root)[0]
    except Exception:                                         # noqa: BLE001
        return ''


def verdict(root='.', base=None):
    """-> (state, [line, ...]). The lines are for a person; the state is for
    anything deciding on it."""
    slug = repo_slug(root)
    if not slug:
        return UNVERIFIED, ['no github.com origin could be read from this '
                            'checkout']
    ok, sha = _git(root, 'rev-parse', 'HEAD')
    if not ok or not sha:
        return UNVERIFIED, ['HEAD could not be read']
    short = sha[:12]

    # Not on origin at all -> nothing could have run on it, and no request is
    # worth spending to confirm that.
    ok_r, remotes = _git(root, 'branch', '-r', '--contains', sha)
    if ok_r and not remotes.strip():
        return NOT_RUN, [f'{short} is on no remote branch -- it has not been '
                         f'pushed, so nothing has run on it']

    ok_b, branch = _git(root, 'rev-parse', '--abbrev-ref', 'HEAD')
    branch = branch if ok_b else ''
    if base is None:
        base = merge_base_branch(root, branch)
    expected = expected_workflows(root, branch, base)
    runs, err = _fetch_runs(slug, sha)
    if runs is None:
        return UNVERIFIED, [f'could not ask about {short}: {err}']

    by_name = {}
    for r in runs:
        name = r.get('name') or '?'
        # Keep the newest per workflow: a re-run supersedes what it re-ran.
        prev = by_name.get(name)
        if prev is None or (r.get('run_number') or 0) >= (prev.get('run_number') or 0):
            by_name[name] = r

    lines, missing, bad, pending, idle = [], [], [], [], []
    for name in sorted(expected):
        r = by_name.get(name)
        if r is None:
            missing.append(name)
            lines.append(f'  {name}: NO RUN for {short}')
            continue
        status, concl = r.get('status'), r.get('conclusion')
        if status != 'completed':
            pending.append(name)
            lines.append(f'  {name}: {status}')
        elif concl != 'success':
            jobs = (_fetch_jobs(r['jobs_url'])[0] if r.get('jobs_url')
                    else None)
            if never_started(jobs):
                idle.append(name)
                lines.append(f'  {name}: never started -- no GitHub machine '
                             f'picked it up, so it was cancelled ({concl})')
            else:
                bad.append(name)
                lines.append(f'  {name}: {concl}')
        else:
            lines.append(f'  {name}: success')
    for name in sorted(set(by_name) - expected):
        lines.append(f'  {name}: {by_name[name].get("conclusion")} '
                     f'(not in the expected set)')
    if not expected:
        return UNVERIFIED, [f'no workflow in this tree declares '
                            f'`pull_request:`, so there is nothing to expect '
                            f'for {short}'] + lines

    if bad:
        return FAILED, [f'{short}: ' + ', '.join(bad) + ' did not pass'] + lines
    if missing:
        return NOT_RUN, [f'{short}: ' + ', '.join(missing) +
                         ' produced no run at all'] + lines
    if idle:
        return NEVER_STARTED, [f'{short}: ' + ', '.join(idle) +
                               ' never started -- GitHub had no machine for '
                               'it, so no check ran and nothing was found'] + lines
    if pending:
        return RUNNING, [f'{short}: ' + ', '.join(pending) +
                         ' has not finished'] + lines
    return VERIFIED, [f'{short}: every expected workflow ran and passed'] + lines


def remind(root='.', prefix='precedent', base=None):
    """-> a block to print, or '' when the commit is verified.

    Silent on success, like every other gate notice here: a reminder that
    speaks when there is nothing to say is one nobody reads."""
    try:
        state, lines = verdict(root, base)
    except Exception as e:                                    # noqa: BLE001
        return (f'{prefix}: could not check whether CI ran on this commit '
                f'({type(e).__name__}) -- treat it as UNVERIFIED')
    if state == VERIFIED:
        return ''
    head = {
        FAILED: 'CI FAILED on the commit you are about to merge',
        NOT_RUN: 'CI DID NOT RUN on the commit you are about to merge',
        RUNNING: 'CI has not finished on the commit you are about to merge',
        NEVER_STARTED: 'CI NEVER STARTED on the commit you are about to merge',
        UNVERIFIED: 'could not verify CI on the commit you are about to merge',
    }[state]
    out = [f'{prefix}: {head} --', *lines]
    if state == NOT_RUN:
        out.append('  A pull request page can show green runs earned by an '
                   'EARLIER pull request on the same branch.')
        out.append('  Re-run it before merging: the workflow\'s own '
                   '`workflow_dispatch`, never a close-and-reopen.')
    if state == NEVER_STARTED:
        out.append('  Not a finding: GitHub assigned no machine. Run the same '
                   'check here (`python3 tools/precedent_push_check.py`; the '
                   'leak gate here is a superset of its CI half) and decide on '
                   'that. One re-run at most; other branches stuck the same '
                   'way confirm it is GitHub, not this change.')
    return '\n'.join(out)


def main():
    argv = sys.argv[1:]
    if '--help' in argv or '-h' in argv:
        print(__doc__)
        return 0
    root = '.'
    if '--repo' in argv:
        i = argv.index('--repo')
        if i + 1 < len(argv):
            root = argv[i + 1]
    base = None
    if '--base' in argv:
        i = argv.index('--base')
        if i + 1 < len(argv):
            base = argv[i + 1]
    state, lines = verdict(root, base)
    print(f'ci verified: {state.upper()}')
    for line in lines:
        print(line)
    if '--exit-code' in argv:
        return 0 if state == VERIFIED else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
