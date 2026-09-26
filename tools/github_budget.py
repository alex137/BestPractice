#!/usr/bin/env python3
"""What this account has left of GitHub's API allowances, measured.

TWO THINGS THIS MODULE IS FOR, and they are different questions:

  * **Headroom** -- how much of the account's hourly REST allowance is
    already spent, right now, across every session and tool using this
    credential.
  * **Spend** -- how many calls the tool that imported this module made on
    its own run, and whether that is more than the budget declared for it in
    [tools/github_api_budgets.json](github_api_budgets.json).

The second is the one nothing measured before. "Is normal usage overusing
the API" cannot be answered by a number that mixes a fleet of sessions
together; it is answered by each tool knowing its own bill.

**MEASURED FROM RESPONSE HEADERS, NEVER FROM `/rate_limit`** -- and that is
a repair, not a style preference (practice: diagnosis-is-measured). Measured
2026-09-14 from inside a Claude Code container, with a token that had just
made several dozen counted calls:

    GET /rate_limit          -> core used 0 of 15000, reset 60.0m away
    GET /repos/<owner>/<name> -> X-RateLimit-Used: 74, Remaining: 14926

Both answers arrived seconds apart, on the same credential. The endpoint
reported a pristine window and moved its own reset forward on every ask; the
headers on an ordinary call reported the truth. A budget check built on the
endpoint would have been green on the day the account ran out, which is the
one day it exists for. So every number here comes off the headers of a call
somebody was making anyway, and the endpoint is not consulted at all.

**WHAT A SESSION CANNOT MEASURE FROM HERE, said out loud rather than left
as a clean-looking zero** (practice: fail-gracefully). The agent proxy binds
a session to its configured repositories: `/search/*` and `/graphql` answer
403 with `This GitHub API path is not available` before they ever reach
GitHub. So the two tightest allowances on the account -- search at 30
requests per MINUTE, GraphQL at 5,000 points per hour -- cannot be probed
from inside a container at all, and the calls that DO spend them come from
the harness's own `mcp__github__*` tools, which run outside it. Those are
declared in the budgets file with their published figures and reported as
unmeasurable here, never as clean.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
BUDGETS = HERE / 'github_api_budgets.json'

API = 'https://api.github.com/'
TIMEOUT = 20

# Every call this process made, so a tool can report its own bill. Counted
# here rather than in each caller: two counters drift, and the one that
# matters is the one the HTTP call itself increments.
_SPEND = {'calls': 0, 'cache_hits': 0, 'errors': 0}
_CACHE = {}
# The last rate-limit headers seen, per resource AND per pool -- because
# there is more than one pool, which is the thing nobody here knew before
# 2026-09-14. Measured that day, seconds apart, on the same session:
#
#     GET /repos/alex137/BestPractice   -> limit 15000, used 133
#     GET /repos/<owner>/<a-private-one> -> limit  5200, used   1
#     GET /repos/<owner>/<another>       -> limit  5200, used  19
#
# Same credential variable, three different allowances with three different
# reset clocks. The harness attaches a per-repository credential, so "how
# much is left" is a question about a repository, not about the account, and
# a single `core` row would have reported whichever call happened to run
# last. Keyed by the owner/name the call was about, or `account` for a path
# that names no repository.
_LIMITS = {}

_HEADER_RE = re.compile(r'^([A-Za-z0-9-]+):\s*(.*)$')


def token_var():
    """-> the environment variable holding a usable token, or None.

    Delegated to precedent_source_credentials so there is ONE answer to "is
    there a credential here" (it also resolves PRECEDENT_GIT_TOKEN=inherit).
    Degrades to no token where that module is absent: this engine is vendored
    into trees older than it.
    """
    try:
        sys.path.insert(0, str(HERE))
        import precedent_source_credentials as psc
        return psc.token_var()
    except Exception:                       # noqa: BLE001 -- reported, never raised
        return None


def token():
    """-> (value, var_name), or (None, var_name/None).

    A token carrying a quote, a backslash or a newline is refused rather than
    escaped: it is passed to curl through a config file on STDIN, which is a
    quoted format, and such a value would either break the parse or smuggle a
    second directive into it. No GitHub token looks like that; a mis-set
    variable (a whole `export` line pasted in) does.
    """
    var = token_var()
    if not var:
        return None, None
    value = (os.environ.get(var) or '').strip()
    if not value or any(c in value for c in '"\\\n\r'):
        return None, var
    return value, var


def _parse_headers(text):
    out = {}
    for line in text.splitlines():
        m = _HEADER_RE.match(line.strip())
        if m:
            out[m.group(1).lower()] = m.group(2).strip()
    return out


_REPO_PATH_RE = re.compile(r'^repos/([^/]+)/([^/?#]+)')


def pool_of(path):
    """-> which allowance a call on `path` is charged against.

    A repository path is charged to that repository's own credential; every
    other path to whatever this session's default credential is. See _LIMITS
    for the measurement behind this.
    """
    m = _REPO_PATH_RE.match(path.lstrip('/'))
    return f'{m.group(1)}/{m.group(2)}' if m else 'account'


def _record_limits(headers, path):
    """Keep the rate-limit headers of the call that just happened."""
    resource = headers.get('x-ratelimit-resource')
    if not resource:
        return
    row = {}
    for field in ('limit', 'remaining', 'used', 'reset'):
        raw = headers.get(f'x-ratelimit-{field}')
        if raw is None or not raw.lstrip('-').isdigit():
            return          # a partial row is worse than none: it reads as measured
        row[field] = int(raw)
    row['pool'] = pool_of(path)
    _LIMITS[f'{resource} @ {row["pool"]}'] = row


def call(path, timeout=TIMEOUT, auth=True, cache=True):
    """-> (parsed_json, error). Never raises: the caller reports, it does not crash.

    CACHED BY DEFAULT. Read-only GETs about repository metadata do not change
    within one run of a tool, so a second ask is waste every time. What that
    is worth today is small and honest to state: a very-deep-check run
    measured 2026-09-14 made 45 calls and the cache served none of them,
    because the visibility audit reads ONE tree per run and already dedupes
    within it. The overlap is across trees -- the same five repos in force
    name 62 repositories between them, of which 46 are distinct -- so the
    cache pays the day that audit runs per source, and costs nothing before
    then.

    AUTHENTICATES WHEN A TOKEN IS SET, because unauthenticated is a different
    question rather than a milder one: the API answers `Not Found` for a
    private repository and a deleted one alike. The token goes through a curl
    config on STDIN, not an `-H` argument -- an argument list is world-readable
    in /proc, and this one would carry the credential.
    """
    key = (path, bool(auth))
    if cache and key in _CACHE:
        _SPEND['cache_hits'] += 1
        return _CACHE[key]

    value, _var = token() if auth else (None, None)
    # HEADERS TO THEIR OWN FILE, never merged into stdout. `-D -` alongside
    # `-o -` interleaves both into one stream, and splitting them again means
    # guessing at a blank line -- which fails on the first body that contains
    # one. Measured 2026-09-14: the split read a repository's own JSON as the
    # header block and returned `not JSON` for a call that had succeeded, on
    # 10 of 45 calls in one very-deep-check run. A temporary file has no
    # ambiguity to get wrong.
    headers_fd, headers_path = tempfile.mkstemp(prefix='gh-budget-hdr-')
    os.close(headers_fd)
    argv = ['curl', '-s', '-D', headers_path, '--max-time', str(timeout),
            '-H', 'Accept: application/vnd.github+json']
    if value:
        argv += ['-K', '-']
    argv.append(API + path.lstrip('/'))
    _SPEND['calls'] += 1
    try:
        r = subprocess.run(
            argv, input=(f'header = "Authorization: Bearer {value}"\n'
                         if value else ''),
            capture_output=True, text=True, timeout=timeout + 10)
    except Exception as e:                  # noqa: BLE001 -- reported
        _SPEND['errors'] += 1
        return None, f'curl failed: {e}'
    finally:
        try:
            # A proxied request writes more than one header block (its own
            # `200 Connection Established` first). The LAST one is the real
            # response's, and it is the one carrying the rate-limit headers.
            raw = pathlib.Path(headers_path).read_text(errors='ignore')
            for block in reversed(raw.split('\r\n\r\n')):
                got = _parse_headers(block)
                if any(k.startswith('x-ratelimit-') for k in got):
                    _record_limits(got, path)
                    break
        except OSError:
            pass
        try:
            os.unlink(headers_path)
        except OSError:
            pass
    if r.returncode != 0:
        _SPEND['errors'] += 1
        return None, f'curl exited {r.returncode}: {r.stderr.strip()[:120]}'
    try:
        parsed = json.loads(r.stdout)
    except ValueError:
        _SPEND['errors'] += 1
        return None, f'not JSON: {r.stdout.strip()[:120]}'
    result = (parsed, None)
    if cache:
        _CACHE[key] = result
    return result


def post(path, payload, timeout=TIMEOUT):
    """-> (ok, error) for a POST of `payload` as JSON. Never raises.

    Added 2026-09-26 for one caller: precedent_branches.py pressing a
    workflow's `workflow_dispatch` button, which answers 204 with no body --
    so success is read off the status code, not off a parse of the body the
    way call() reads it. Counted, and its rate-limit headers kept, exactly
    as call() does. The token still travels on STDIN; the body, which holds
    nothing secret, goes through a temporary file."""
    value, _var = token()
    if not value:
        return False, 'no GitHub token is set here, so nothing can be started'
    fd, body_path = tempfile.mkstemp(prefix='gh-budget-body-')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(payload, f)
    headers_fd, headers_path = tempfile.mkstemp(prefix='gh-budget-hdr-')
    os.close(headers_fd)
    argv = ['curl', '-s', '-o', os.devnull, '-w', '%{http_code}',
            '-D', headers_path, '--max-time', str(timeout), '-X', 'POST',
            '-H', 'Accept: application/vnd.github+json',
            '-H', 'Content-Type: application/json',
            '--data-binary', f'@{body_path}', '-K', '-', API + path.lstrip('/')]
    _SPEND['calls'] += 1
    try:
        r = subprocess.run(argv, input=f'header = "Authorization: Bearer {value}"\n',
                           capture_output=True, text=True, timeout=timeout + 10)
    except Exception as e:                  # noqa: BLE001 -- reported
        _SPEND['errors'] += 1
        return False, f'curl failed: {e}'
    finally:
        try:
            raw = pathlib.Path(headers_path).read_text(errors='ignore')
            for block in reversed(raw.split('\r\n\r\n')):
                got = _parse_headers(block)
                if any(k.startswith('x-ratelimit-') for k in got):
                    _record_limits(got, path)
                    break
        except OSError:
            pass
        for leftover in (headers_path, body_path):
            try:
                os.unlink(leftover)
            except OSError:
                pass
    code = r.stdout.strip()
    if r.returncode != 0 or not code.startswith('2'):
        _SPEND['errors'] += 1
        return False, f'GitHub answered {code or "nothing"} (curl exit {r.returncode})'
    return True, None


def spend():
    """-> a copy of this process's own call counters."""
    return dict(_SPEND)


def limits():
    """-> {resource: {limit, remaining, used, reset}} as last reported."""
    return {k: dict(v) for k, v in _LIMITS.items()}


def reset_counters():
    """Only for tests and for a tool measuring one phase at a time."""
    _SPEND.update({'calls': 0, 'cache_hits': 0, 'errors': 0})
    _CACHE.clear()
    _LIMITS.clear()


def budgets(path=None):
    """-> (config, error). A missing or malformed file is a NOTE, not a crash:
    the audit's job is to report, and a budget nobody could read is itself
    worth reporting."""
    p = pathlib.Path(path or BUDGETS)
    try:
        return json.loads(p.read_text(encoding='utf-8')), None
    except OSError as e:
        return None, f'{p} could not be read ({e})'
    except ValueError as e:
        return None, f'{p} is not valid JSON ({e})'


def _pct(part, whole):
    return (100.0 * part / whole) if whole else 0.0


def audit(tool=None, budget_path=None, probe=True):
    """-> (findings, notes, rows). Findings are real; notes are what could not run.

    `tool` names the caller as it appears in the budgets file's `run_budgets`,
    e.g. 'very_deep_check.py'. Pass probe=False when the caller has already
    made real calls this run -- their headers are the measurement, and one
    more call to take it would be the check spending what it is auditing.
    """
    findings, notes, rows = [], [], []
    cfg, err = budgets(budget_path)
    if err:
        notes.append(f'{err} -- no floor or run budget was applied, so the '
                     f'numbers below are reported and not judged.')
        cfg = {}

    value, var = token()
    if not value:
        notes.append(
            'no GitHub credential is set'
            + (f' ({var} is empty)' if var else '')
            + ' -- headroom was NOT measured. This is an unrun check, not a '
              'clean one: a session without a token cannot see what the '
              'account has spent.')
        return findings, notes, rows

    if probe and not _LIMITS:
        # The cheapest authenticated call there is, and it is charged to the
        # same `core` resource everything else here spends.
        _data, perr = call('user')
        if perr:
            notes.append(f'the GitHub API could not be reached ({perr}) -- '
                         f'headroom was NOT measured.')
            return findings, notes, rows

    if not _LIMITS:
        notes.append('no X-RateLimit-* headers came back on any call this run '
                     '-- headroom was NOT measured. Something between this '
                     'session and GitHub is answering without them.')

    # `_`-prefixed keys in the budgets file are its own commentary -- the
    # registry carries the reason for every number beside it, and a reader
    # skipping those is the only difference between the two.
    floors = {k: v for k, v in (cfg.get('floors') or {}).items()
              if not k.startswith('_')}
    for resource, row in sorted(_LIMITS.items()):
        left = _pct(row['remaining'], row['limit'])
        mins = max(0.0, (row['reset'] - time.time()) / 60.0)
        rows.append({'resource': resource, 'measured': True, **row,
                     'remaining_pct': round(left, 1),
                     'resets_in_minutes': round(mins, 1)})
        floor = floors.get(resource.split(' @ ')[0])
        if floor is None:
            continue
        if left < float(floor):
            findings.append(
                f'the `{resource}` allowance is {left:.1f}% remaining '
                f'({row["used"]} of {row["limit"]} spent, resets in '
                f'{mins:.0f}m), below the {floor}% floor declared in '
                f'{pathlib.Path(budget_path or BUDGETS).name}. NOBODY OWNS '
                f'THIS POOL ALONE: every session, hook and tool drawing on '
                f'the same credential spends it, so the next one to need the '
                f'API is the one that gets refused, and it will not be the '
                f'one that spent it.')

    for resource, row in sorted((cfg.get('unmeasurable') or {}).items()):
        if resource.startswith('_') or not isinstance(row, dict):
            continue
        rows.append({'resource': resource, 'measured': False, **row})
        notes.append(
            f'`{resource}`: '
            + (f'{row.get("limit")} per {row.get("window", "hour")} '
               if row.get('limit') is not None else 'no published figure recorded ')
            + f'-- NOT measurable from a session ({row.get("why", "no reason recorded")}). '
            f'{row.get("spent_by", "")}'.strip())

    if tool:
        budget = (cfg.get('run_budgets') or {}).get(tool)
        if isinstance(budget, str):
            budget = None
        s = spend()
        rows.append({'resource': f'this run ({tool})', 'measured': True,
                     'calls': s['calls'], 'cache_hits': s['cache_hits'],
                     'errors': s['errors'], 'budget': budget})
        if budget is not None and s['calls'] > int(budget):
            findings.append(
                f'{tool} made {s["calls"]} API call(s) this run, over the '
                f'{budget} declared for it in '
                f'{pathlib.Path(budget_path or BUDGETS).name}. A tool whose '
                f'bill grows quietly is how an account-wide pool is spent by '
                f'something nobody was watching -- either the growth is '
                f'justified and the budget moves with a reason beside it, or '
                f'the tool caches, narrows its scope, or stops asking.')
    return findings, notes, rows


def render(findings, notes, rows, out=None):
    out = out or sys.stdout
    for r in rows:
        if r.get('resource', '').startswith('this run'):
            budget = r.get('budget')
            print(f"  {r['resource']}: {r['calls']} call(s), "
                  f"{r['cache_hits']} served from cache, {r['errors']} error(s)"
                  + (f", budget {budget}" if budget is not None else
                     ", no budget declared"), file=out)
        elif r.get('measured'):
            print(f"  {r['resource']}: {r['used']} of {r['limit']} spent "
                  f"({r['remaining_pct']}% left), resets in "
                  f"{r['resets_in_minutes']:.0f}m", file=out)
        else:
            # A limit nobody recorded prints as such. `None per hour` reads
            # like a measurement of zero (practice: no-invented-specifics).
            cap = (f"{r['limit']} per {r.get('window', 'hour')}"
                   if r.get('limit') is not None else 'no published figure recorded')
            print(f"  {r['resource']}: {cap} -- not measurable here", file=out)
    for f in findings:
        print(f'  FINDING: {f}', file=out)
    for n in notes:
        print(f'  note: {n}', file=out)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    tool = None
    if '--tool' in argv:
        i = argv.index('--tool')
        if i + 1 >= len(argv):
            print('github_budget: --tool needs a value.', file=sys.stderr)
            return 2
        tool = argv[i + 1]
    as_json = '--json' in argv
    findings, notes, rows = audit(tool=tool)
    if as_json:
        print(json.dumps({'findings': findings, 'notes': notes, 'rows': rows},
                         indent=2))
    else:
        print('GITHUB API BUDGET -- measured from response headers, not '
              '/rate_limit\n')
        render(findings, notes, rows)
    # Prints rather than fails. This is scope information for the session
    # about to work, not a gate -- and a tool that refused to run because
    # somebody else's session had spent the pool would be the wrong remedy
    # for the right finding.
    return 0


if __name__ == '__main__':
    # `--help` is what anyone types first, and this project's tools answer it
    # with the module docstring and exit 0 -- verify_harness.py asserts it of
    # every one of them. The docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
