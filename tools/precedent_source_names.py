#!/usr/bin/env python3
"""precedent_source_names.py -- answers one question a git command cannot:
is every practice-source repository this repo declares still CALLED what this
repo calls it?

WHY THIS EXISTS, AND THE INCIDENT THAT PRODUCED IT (practice:
cite-the-incident). A team source was renamed on GitHub. A consuming repo
went on declaring it, cloning it, attaching it and materializing from it
under the OLD name, with every check green, for an unknown number of
sessions. Nothing failed, and nothing could have: GitHub redirects a renamed
repository indefinitely, so `git clone` succeeds, `git ls-remote` succeeds,
the sibling clone resolves, and the practices materialize correctly. The
CONTENT is right. Only the name is a ghost -- and every reference to it in
every vendored tree is one repository-settings change away from a 404 that
nobody can date. It surfaced on 2026-09-11 because a person recognised a
name he had retired, which is not a mechanism (practice:
convention-to-audit).

spec/SOURCE_NAMING.md predicted this in as many words -- the repository name
is the one of its four names where "nothing breaks immediately; a later
rename breaks every vendored reference". This is the part of that row that
can be mechanised: not preventing the rename, which no engine can do, but
noticing it afterwards instead of never.

WHAT ACTUALLY ANSWERS IT. Not git, which is exactly the problem: every git
operation follows the redirect silently and reports success. GitHub's REST
API carries the repository's CURRENT `full_name` in the response BODY, and
that is what this reads -- never the status code, never the final URL.
Measured 2026-09-11 in this container against a repository this session
could reach:

    GET /repos/alex137/bestpractice   -> 200, full_name "alex137/BestPractice"
    GET /repos/ALEX137/BESTPRACTICE   -> 200, full_name "alex137/BestPractice"

so the body carries the canonical name whether the request was redirected or
merely spelled differently, and reading the body makes the redirect question
irrelevant to correctness. NOT verified here: the 301 a genuine rename
returns, because this session could reach no renamed repository to try it
on. It does not change what this reads.

The whole tool was run end to end against that same repository on the same
day, through a fixture source whose clone fetched `alex137/bestpractice`: it
reported SPELLING, naming `alex137/BestPractice`, plus the offline DRIFT row
below. A rename differs from that only in how far the two names diverge.

WHY IT IS NOT A precedent_check.py CHECK. Every check there is offline by
construction -- it runs in CI, in a bare checkout, on a plane. This one needs
the network and a credential for a private source, and a check that answers
"could not run" on most of the runs that invoke it teaches people to ignore
the gate (practice: checkable-gets-checked). It is wired instead into the one
moment a session is already online and already reconciling its sources: the
`Update Vendors` sequence (practice: vendor-update-runbook, step 8).

THE FAILURE THIS IS BUILT NOT TO HAVE. "Could not check" and "checked, the
name is current" must never render the same (practice: fail-gracefully). A
source whose API answer did not arrive is UNVERIFIED and says why; it is
never OK, and --check does not fail on it either -- a vendor update must not
be blocked by an unreachable network, and a person who reads UNVERIFIED knows
they have not been told the name is fine.

ONE ENVIRONMENT NOTE THAT WILL OTHERWISE READ AS A RENAME. In a hosted Claude
Code session, api.github.com answers **403** with a body naming `add_repo` for
every repository the session has not attached -- not 404. So "this repo does
not exist" and "this session may not ask" are indistinguishable from the
status code alone, and this tool reports both as UNVERIFIED with the body's
own words rather than guessing. Measured 2026-09-11.

Run:
  python3 tools/precedent_source_names.py            # report
  python3 tools/precedent_source_names.py --check    # exit 1 on a RENAMED source
  python3 tools/precedent_source_names.py --repo PATH [--user-config PATH]
Exit: 0 always, except --check with a source whose name has moved.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

try:
    import precedent_resolve as pr                           # noqa: E402
except Exception as _e:                 # a SOURCE set does not vendor it and
    pr = None                           # has no multi-source config to check
    _resolve_err = f'{type(_e).__name__}: {_e}'
else:
    _resolve_err = None

try:
    import precedent_source_credentials as psc               # noqa: E402
except Exception:                       # pragma: no cover - vendored trees
    psc = None                          # that predate the credentials module

API = 'https://api.github.com/repos/{owner}/{name}'
TIMEOUT = 20

# github.com only. A source on another host has no API this knows how to ask,
# and guessing one would produce a confident answer from the wrong server.
REMOTE_RE = re.compile(
    r'^(?:https://|git@)github\.com[:/](?P<owner>[^/]+)/(?P<name>[^/]+?)(?:\.git)?/?$')


def _git(args):
    """-> (ok, stdout). The exit code is consulted, never inferred from the
    output: `git remote get-url` on a non-repo prints to stderr and exits
    non-zero, and a caller reading stdout alone reads an empty string as an
    answer (AGENTS.md's most-repeated-bug gotcha)."""
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=30)
    except Exception as e:                                   # noqa: BLE001
        return False, f'{type(e).__name__}: {e}'
    return p.returncode == 0, (p.stdout or p.stderr).strip()


def parse_remote(url):
    """-> (owner, name) for a github.com remote, else (None, None).

    A URL carrying credentials -- `https://` then `user:token`, an at-sign,
    then the host -- is stripped of them BEFORE matching, so a tokenised
    remote is parsed rather than silently skipped, and the token never
    reaches a return value that gets printed. (Spelled out in words rather
    than shown: the leak gate reads `<anything>@github.com` as an email
    address, correctly, and an example is not worth a false hit on every
    run.)"""
    url = (url or '').strip()
    url = re.sub(r'^(https://)[^/@]*@', r'\1', url)
    m = REMOTE_RE.match(url)
    return (m.group('owner'), m.group('name')) if m else (None, None)


def api_full_name(owner, name, env=None):
    """-> (full_name, None) or (None, why-it-could-not-be-read).

    Reads `full_name` out of the response BODY. The status code says only
    that an answer came back; the body says what the repository is called
    now."""
    env = os.environ if env is None else env
    req = urllib.request.Request(
        API.format(owner=owner, name=name),
        headers={'Accept': 'application/vnd.github+json',
                 'User-Agent': 'precedent-source-names'})
    # The token is read into a header in this process and never printed,
    # logged or written to disk -- the same standing rule as
    # precedent_source_credentials.py's git helper, which keeps it out of a
    # command line and out of a clone's config. An HTTP header is neither.
    token = _api_token(env)
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = json.load(r)
    except urllib.error.HTTPError as e:
        detail = ''
        try:
            detail = (json.loads(e.read() or b'{}') or {}).get('message', '')
        except Exception:                                    # noqa: BLE001
            pass
        return None, f'GitHub answered HTTP {e.code}' + (f': {detail}' if detail else '')
    except Exception as e:                                   # noqa: BLE001
        return None, f'the API could not be reached ({type(e).__name__}: {e})'
    full = body.get('full_name')
    if not full:
        return None, 'the API answered without a full_name field'
    return full, None


def _api_token(env):
    """The token value for an API call, or None.

    Deliberately NOT precedent_source_credentials.credential_helper(): that
    one hands git a snippet naming the variable, so the secret is never read
    here. An HTTPS header has no such indirection, so this reads the value --
    and nothing in this module ever puts it in a message."""
    if psc is None:
        return (env.get('PRECEDENT_GIT_TOKEN') or '').strip() or None
    var = psc.token_var(env)
    return (env.get(var) or '').strip() if var else None


def sources_to_check(repo, user_config=None):
    """-> [{level, name, path}] for every declared source that is a SEPARATE
    repository.

    A source whose resolved path is INSIDE the consuming repo is not one: a
    repo-local source is a directory in this tree, and this repo's own
    universal source is this repo. Neither has a name of its own on GitHub
    to have been renamed."""
    if pr is None:
        raise RuntimeError(
            f'precedent_resolve is not available here ({_resolve_err}), so the '
            f'declared sources could not be read. That module is vendored into '
            f'CONSUMING repos only -- a practice SET resolves no catalogue and '
            f'has no separate source repository to check.')
    root = pathlib.Path(repo).resolve()
    out = []
    # user_config is threaded through rather than left to the default,
    # because the default reads the machine's own ~/.config/precedent: a
    # fixture that does not pass one silently inherits the real individual
    # source and grades it (practice: fixture-owns-its-state -- and this
    # module's own harness case did exactly that before the argument
    # existed).
    for src in pr.load_config(repo, user_config=user_config):
        path = pathlib.Path(src['path']).resolve()
        if path == root or root in path.parents:
            continue
        out.append(src)
    return out


def assess(repo, env=None, user_config=None):
    """-> [row], one per separate-repository source, each carrying its own
    verdict. Never raises: a name check degrades the report, it does not take
    an update down (practice: fail-gracefully)."""
    env = os.environ if env is None else env
    rows = []
    for src in sources_to_check(repo, user_config=user_config):
        row = {'level': src['level'], 'declared': src['name'],
               'path': src['path'], 'verdict': 'UNVERIFIED', 'detail': ''}
        rows.append(row)
        clone = pathlib.Path(src['path'])
        if not (clone / '.git').exists():
            row['detail'] = (f'no clone at {src["path"]}, so there is no '
                             f'remote to ask about')
            continue
        ok, url = _git(['git', '-C', str(clone), 'remote', 'get-url', 'origin'])
        if not ok:
            row['detail'] = f'the clone has no origin remote ({url})'
            continue
        owner, name = parse_remote(url)
        if not owner:
            row['detail'] = ('its origin is not a github.com remote, and no '
                             'other host has an API this knows how to ask')
            continue
        row['origin'] = f'{owner}/{name}'
        # The OFFLINE half, reported whether or not the API answers: the
        # declared name and the clone's own remote disagreeing is a drift
        # nothing else prints, and it costs no network to see.
        if src['level'] in ('team', 'individual') and name != src['name']:
            row['declared_drift'] = (
                f'precedent.json (or the user config) declares {src["name"]!r} '
                f'while the clone fetches from {owner}/{name}')
        full, why = api_full_name(owner, name, env)
        if full is None:
            row['detail'] = why
            continue
        row['current'] = full
        cur_name = full.split('/', 1)[-1]
        cur_owner = full.split('/', 1)[0]
        if (cur_name, cur_owner) == (name, owner):
            row['verdict'] = 'OK'
            row['detail'] = f'still {full}'
        elif cur_name.lower() == name.lower() and cur_owner.lower() == owner.lower():
            row['verdict'] = 'SPELLING'
            row['detail'] = (f'the same repository, spelled {full} -- git does '
                             f'not care and a reader might')
        else:
            row['verdict'] = 'RENAMED'
            row['detail'] = (f'this repo fetches {owner}/{name}; GitHub calls '
                             f'it {full} now. The redirect is why nothing has '
                             f'failed, and why nothing will say so.')
    return rows


def report(rows, out=sys.stdout):
    for r in rows:
        line = (f"{r['verdict']:<11}{r['level']}/{r['declared']} -- "
                f"{r['detail']}")
        print(line, file=out)
        if r.get('declared_drift'):
            print(f"{'DRIFT':<11}{r['level']}/{r['declared']} -- "
                  f"{r['declared_drift']}", file=out)
    renamed = [r for r in rows if r['verdict'] == 'RENAMED']
    unver = [r for r in rows if r['verdict'] == 'UNVERIFIED']
    if not rows:
        print('precedent_source_names: this repo declares no source that is a '
              'separate repository, so there is no name to check.', file=out)
        return
    print(f"precedent_source_names: {len(rows)} separate-repository source(s), "
          f"{len(renamed)} renamed, {len(unver)} NOT checked (an unchecked "
          f"source is not a passing one).", file=out)


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--repo', default=str(ROOT))
    ap.add_argument('--user-config', default=None)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--help', '-h', action='store_true')
    args = ap.parse_args()
    if args.help:
        print((__doc__ or '').strip())
        return 0
    try:
        rows = assess(args.repo, user_config=args.user_config)
    except Exception as e:                                   # noqa: BLE001
        print(f'precedent_source_names: could not read this repo\'s sources '
              f'({type(e).__name__}: {e}), so no name was checked.',
              file=sys.stderr)
        return 0
    report(rows)
    if args.check and any(r['verdict'] == 'RENAMED' for r in rows):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
