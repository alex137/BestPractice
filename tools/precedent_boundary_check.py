#!/usr/bin/env python3
"""precedent_boundary_check.py -- is the contributor boundary actually ON?

WHAT IT ANSWERS. spec/CONTRIBUTOR_ACCESS.md gives a contributor GitHub's
Write role and keeps them out of the machinery with two settings that live
on GitHub, not in the repository: branch protection on the base branch
(require a pull request, required approvals 0, require review from code
owners, no bypass) and a `CODEOWNERS` file. The file is in the tree and
every check can see it. The protection is a setting on a web page, and
until 2026-09-14 nothing read it: a forgotten instantiation step left Write
as unrestricted write, silently, while every document went on describing a
boundary that did not exist. This tool asks GitHub.

THE THREE VERDICTS, and why the third exists (practice: fail-gracefully):

  PASS        protection is on and shaped the way the plan needs, and a
              CODEOWNERS file exists in the tree.
  FAIL        the branch is not protected; or it is, but a pull request is
              not required, code-owner review is not required, or required
              approvals is above 0 (a documents-only pull request would then
              wait for a reviewer, which is the bottleneck the plan exists
              to avoid); or GitHub says protection is not available on this
              repository's plan; or protection is on and no CODEOWNERS file
              is in the tree to give it anything to require.
  UNVERIFIED  it could not ask: no token, a token GitHub refused, a network
              it could not reach. "Could not check" and "checked, it is on"
              never render the same, and --check fails on UNVERIFIED, since
              a gate that passes when it cannot look is not a gate.

WHAT IT READS. `precedent.json`'s `base_branch` (else `main`); the `origin`
remote for owner and repository; a token from the environment, in this
order: `PRECEDENT_GITHUB_TOKEN`, `GITHUB_TOKEN`, `GH_TOKEN`, then whatever
`precedent_source_credentials` names. Reading a branch's protection needs
a token with administration read on the repository (a classic token with
`repo`; a fine-grained one with "Administration: read"); GitHub answers a
lesser token with 403 or 404, and both are reported as UNVERIFIED with the
body, never as "not protected".

THE PLAN QUESTION. Branch protection on a private repository is a
paid-plan feature for personal accounts, as the 2026-09-14 review
understands GitHub (read from no documentation -- docs.github.com is
unreachable from a hosted session). GitHub answers that case with 403 and
a body naming an upgrade, which this reports as FAIL "not available on this
plan" -- the one 403 that is an answer rather than a refusal to answer.

Run:  python3 tools/precedent_boundary_check.py [--repo PATH] [--branch NAME]
      python3 tools/precedent_boundary_check.py --check   # exit 1 on FAIL or UNVERIFIED

The API call is a single function, `fetch_protection`, so a harness case
stubs it and asserts each verdict's own words (practice:
control-asserts-which-failure). Nothing here prints the token.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    import precedent_source_credentials as psc
except Exception:  # noqa: BLE001 -- an engine vendored without it still runs
    psc = None

CODEOWNERS_LOCATIONS = ('.github/CODEOWNERS', 'CODEOWNERS', 'docs/CODEOWNERS')
REMOTE_RE = re.compile(
    r'^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)'
    r'(?P<owner>[^/]+)/(?P<name>[^/]+?)(?:\.git)?/?$')
API = 'https://api.github.com'


def _git(repo, *args):
    p = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def parse_remote(url):
    url = (url or '').strip()
    url = re.sub(r'^(https://)[^/@]*@', r'\1', url)  # never echo a credential
    m = REMOTE_RE.match(url)
    return (m.group('owner'), m.group('name')) if m else (None, None)


def declared_base(repo):
    f = pathlib.Path(repo) / 'precedent.json'
    if f.is_file():
        try:
            b = json.loads(f.read_text(encoding='utf-8')).get('base_branch')
            if isinstance(b, str) and b.strip():
                return b.strip()
        except (OSError, json.JSONDecodeError):
            pass
    return 'main'


def api_token(env):
    for var in ('PRECEDENT_GITHUB_TOKEN', 'GITHUB_TOKEN', 'GH_TOKEN'):
        v = (env.get(var) or '').strip()
        if v:
            return v
    if psc is not None:
        try:
            var = psc.token_var(env)
            v = (env.get(var) or '').strip() if var else ''
            if v:
                return v
        except Exception:  # noqa: BLE001
            pass
    return None


def fetch_protection(owner, name, branch, token):
    """-> (status, body). status is an int, or None when no answer came back
    at all; body is the decoded JSON, or the text, or the error string.
    Stubbed by the harness; the only place the network is touched."""
    req = urllib.request.Request(
        f'{API}/repos/{owner}/{name}/branches/{branch}/protection',
        headers={'Authorization': f'Bearer {token}',
                 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'precedent-boundary-check'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode('utf-8', 'replace')
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', 'replace')
        status = e.code
    except (urllib.error.URLError, OSError) as e:
        return None, str(e)
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, raw


def find_codeowners(repo):
    for rel in CODEOWNERS_LOCATIONS:
        if (pathlib.Path(repo) / rel).is_file():
            return rel
    return None


def classify(status, body, codeowners_present):
    """-> (verdict, reasons list). Pure, so every branch has a stated case."""
    if status is None:
        return 'UNVERIFIED', [f'could not reach GitHub: {body}']
    msg = body.get('message', '') if isinstance(body, dict) else str(body)
    if status == 401:
        return 'UNVERIFIED', ['GitHub refused the token (401); set a token with '
                              'administration read on the repository']
    if status == 403:
        if 'upgrade' in msg.lower() or 'plan' in msg.lower():
            return 'FAIL', [f'branch protection is not available on this '
                            f'repository\'s plan (GitHub: {msg!r}) -- Write is '
                            f'unrestricted write here, and no CODEOWNERS file '
                            f'changes that']
        return 'UNVERIFIED', [f'GitHub answered 403 ({msg!r}); the token cannot '
                              f'read protection settings -- it needs '
                              f'administration read on the repository']
    if status == 404:
        if 'not protected' in msg.lower():
            return 'FAIL', ['the base branch is NOT protected -- a Write '
                            'collaborator can push to it and merge anything; '
                            'turn on branch protection (require a pull request, '
                            'required approvals 0, require review from code '
                            'owners, no bypass)']
        return 'UNVERIFIED', [f'GitHub answered 404 ({msg!r}); either the '
                              f'repository or branch name is wrong or the token '
                              f'cannot see this repository']
    if status != 200 or not isinstance(body, dict):
        return 'UNVERIFIED', [f'unexpected answer from GitHub ({status}): {msg!r}']
    reasons = []
    prr = body.get('required_pull_request_reviews')
    if not isinstance(prr, dict):
        reasons.append('a pull request is not required before merging -- a '
                       'Write collaborator can push straight to the base branch')
    else:
        if not prr.get('require_code_owner_reviews'):
            reasons.append('review from code owners is not required -- '
                           'CODEOWNERS is documentation, not a boundary')
        count = prr.get('required_approving_review_count', 0) or 0
        if count > 0:
            reasons.append(f'required approvals is {count}, not 0 -- a '
                           f'documents-only pull request would wait for a '
                           f'reviewer, which is the bottleneck the plan exists '
                           f'to avoid')
    enforce = body.get('enforce_admins')
    if isinstance(enforce, dict) and not enforce.get('enabled'):
        reasons.append('note: administrators can bypass these settings; the '
                       'plan asks for no bypass, and this is the setting that '
                       'lets a maintainer merge machinery changes unreviewed')
    if not codeowners_present:
        reasons.append('no CODEOWNERS file in the tree at any of '
                       + ', '.join(CODEOWNERS_LOCATIONS)
                       + ' -- protection requires an owner\'s review of nothing')
    hard = [r for r in reasons if not r.startswith('note:')]
    return ('FAIL' if hard else 'PASS'), reasons


def assess(repo, branch=None, env=None, fetch=None):
    env = os.environ if env is None else env
    fetch = fetch_protection if fetch is None else fetch
    branch = branch or declared_base(repo)
    code, url = _git(repo, 'remote', 'get-url', 'origin')
    owner, name = parse_remote(url) if code == 0 else (None, None)
    codeowners = find_codeowners(repo)
    if not owner:
        return {'verdict': 'UNVERIFIED', 'branch': branch, 'repo': None,
                'codeowners': codeowners,
                'reasons': ['origin is not a github.com remote (or there is no '
                            'origin), so there is no protection to read']}
    token = api_token(env)
    if not token:
        return {'verdict': 'UNVERIFIED', 'branch': branch,
                'repo': f'{owner}/{name}', 'codeowners': codeowners,
                'reasons': ['no token in the environment (PRECEDENT_GITHUB_TOKEN, '
                            'GITHUB_TOKEN or GH_TOKEN); the protection setting '
                            'lives on GitHub and cannot be read without one']}
    status, body = fetch(owner, name, branch, token)
    verdict, reasons = classify(status, body, codeowners is not None)
    return {'verdict': verdict, 'branch': branch, 'repo': f'{owner}/{name}',
            'codeowners': codeowners, 'reasons': reasons}


def report(result, out=None):
    # Resolved at call time, not definition time: a default bound to the
    # sys.stdout of import is invisible to any caller redirecting stdout.
    out = sys.stdout if out is None else out
    where = f"{result['repo'] or 'this repository'}, branch {result['branch']}"
    print(f'boundary-check: {result["verdict"]} -- {where}; CODEOWNERS: '
          f'{result["codeowners"] or "none"}', file=out)
    for r in result['reasons']:
        print(f'  - {r}', file=out)
    if result['verdict'] == 'PASS':
        print('  the base branch requires a pull request and a code-owner '
              'review, needs no other approval, and CODEOWNERS is in the '
              'tree -- a contributor can merge their own documents and '
              'nothing else', file=out)
    elif result['verdict'] == 'UNVERIFIED':
        print('  UNVERIFIED is not a pass: nothing above says the boundary '
              'is on, only that this run could not look', file=out)


def main(argv):
    if any(a in ('--help', '-h') for a in argv):
        print((__doc__ or '').strip())
        return 0
    repo = pathlib.Path(os.getcwd())
    branch = None
    check_only = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--repo' and i + 1 < len(argv):
            repo = pathlib.Path(argv[i + 1]).resolve()
            i += 2
        elif a == '--branch' and i + 1 < len(argv):
            branch = argv[i + 1]
            i += 2
        elif a == '--check':
            check_only = True
            i += 1
        else:
            print(f'boundary-check FAIL: unknown argument {a!r}. Takes --repo '
                  f'PATH, --branch NAME, --check.', file=sys.stderr)
            return 2
    result = assess(repo, branch)
    report(result)
    if result['verdict'] == 'PASS':
        return 0
    if result['verdict'] == 'FAIL':
        return 1
    return 1 if check_only else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
