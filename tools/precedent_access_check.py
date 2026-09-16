#!/usr/bin/env python3
"""Say, at session start, which repos in force this session can land work in.

Run bare. Prints one line per repo and exits 0 always.

WHY THIS EXISTS, and it is one incident rather than a principle.
`session-text` has said "settle who merges before the work starts" since
2026-09-12, and on 2026-09-10 a session did the opposite: rooted in a private
practice set, it migrated twelve repositories, catalogued their violations,
and built a seven-commit patch for `alex137/BestPractice` -- which it then
could not push, because a session holding one owner's repositories is refused
another owner's. It sat blocked for four days on `root session at
alex137/BestPractice to land the team-set declaration in precedent.json`,
having spent about a hundred dollars reaching a branch nobody could land.
Nothing had lied to it. It simply never asked, and there was no cheap moment
at which asking was the obvious thing to do.

**The rule was already right; what was missing was the moment.** A sentence in
a practice file is read by a session that thinks to read it, and the session
most likely to skip it is the one already deep in work -- which is the one this
costs the most. So the question moves to session start, where nobody has to
remember it and the answer arrives before the first turn.

WHY THE PROBE LIVES HERE RATHER THAN WHERE IT WAS WRITTEN.
`can_land_here` was `very_deep_check.py`'s, from 2026-09-13, and correct. It
could not stay there: `very_deep_check.py` is in neither ENGINE_FILES nor
CONSUMER_ENGINE_FILES, so it is not vendored into a single adopting repo, and
a session-start step importing it would have worked here and silently WARNed
everywhere it actually matters. Copying it instead is how two probes drift
apart. So the definition moved DOWN into the small file that travels, and the
big on-request audit imports it (practice: fix-the-original -- the origin
first, then every copy, and this file is now the origin).

WHAT IT DOES NOT DO. It never gates: a session that cannot start is worse than
any wrong answer it could have been given. It never drops a repo from anything
-- the verdict is information for the session about to work, and a repo needing
a handoff is more expensive rather than unreachable. And `unknown` is kept
distinct from `handoff` all the way to the printed line: a network blip
reported as "you have no access here" sends somebody to spawn a session they
did not need (practice: fail-gracefully).

practice: session-text, durable-fix
"""
import os
import pathlib
import subprocess
import sys
import time

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# The whole-run budget, in seconds. Each probe is a network call capped at 30s
# below, so an unreachable remote and five repos is 150s of a person waiting at
# the door for advisory information. Past the budget the remaining repos are
# named as unchecked rather than skipped silently -- "not asked" and "asked, no
# access" must not look the same, which is this file's entire subject.
BUDGET_SECONDS = float(os.environ.get('PRECEDENT_ACCESS_BUDGET', '45'))

# A ref name nothing uses. The push is a dry run and writes no object, but the
# name still reaches the server's ref-advertisement, so it must not collide
# with anything real.
PROBE_REF = 'refs/heads/precedent-access-probe-do-not-use'

_MARK = {'land': 'LAND    ', 'handoff': 'HANDOFF ', 'unknown': 'UNKNOWN '}


def _origin_url(repo_dir):
    code, out, _ = _run_git(repo_dir, 'remote', 'get-url', 'origin')
    return out if code == 0 else ''


def _credential_args(repo_dir):
    """-> the `git -c` flags that let one network call authenticate, or [].

    THE INCIDENT (2026-09-10, measured in a session where the credential route
    was working exactly as the per-machine setup describes). Every one of four
    private sources failed a tool's freshness gate with "could not read
    Username for 'https://github.com'". The token was fine: the tool shelled
    out to plain `git` while the credential lives in $PRECEDENT_GIT_TOKEN
    behind a helper only one caller was passing. The failure named a missing
    username rather than missing plumbing, which sends the reader to re-set a
    token that was never the problem.

    The secret never reaches an argument list; see
    precedent_source_credentials.credential_args, which builds a helper naming
    the variable. Degrades to [] when that module is absent, since this engine
    is vendored into trees older than it, and to [] for any non-https URL, so
    file:// fixtures are untouched (practice: fail-gracefully).
    """
    try:
        import precedent_source_credentials as psc
    except Exception:                              # noqa: BLE001
        return []
    url = _origin_url(repo_dir)
    if not url:
        return []
    try:
        return psc.credential_args(url)
    except Exception:                              # noqa: BLE001
        return []


def _run_git(repo_dir, *args):
    # Only a network verb gets the credential helper, and `remote get-url` is
    # deliberately not one -- _credential_args calls it, so treating it as a
    # network verb would recurse forever.
    pre = []
    if args and args[0] in ('fetch', 'ls-remote', 'pull', 'push', 'clone'):
        pre = _credential_args(repo_dir)
    try:
        r = subprocess.run(['git', '-C', str(repo_dir), *pre, *args],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return 1, '', 'git unavailable or timed out'
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def can_land_here(repo_dir):
    """-> (verdict, detail). Can THIS session put work into this repo?

    verdict is 'land', 'handoff' or 'unknown'.

    A DIFFERENT QUESTION from a liveness audit, and the difference is the whole
    point. That one asks whether the REPOSITORY accepts work -- is it archived,
    disabled, renamed. This asks whether this SESSION can put work into it,
    which is a fact about the credentials in this container and not about the
    repository at all. A repo can be perfectly live, writable by its owner, and
    unreachable from here.

    MEASURED, not inferred, because a guess here is the expensive kind.
    `git push --dry-run` to a ref name nothing uses asks the server and changes
    nothing: the server answers before any object is written, so a 'land'
    verdict is a real permission answer and a 403 is quotable. The alternative
    -- reasoning from the owner in the URL -- is exactly the inference
    session-text says to stop making.

    NOT USED TO DROP A REPO FROM SCOPE, deliberately. A repo this session
    cannot push to is not unactionable, only more expensive: it needs a woken
    session, which is a route that works.
    """
    if not repo_dir or not pathlib.Path(repo_dir).is_dir():
        return 'unknown', 'no local clone to probe'
    code, stdout, stderr = _run_git(repo_dir, 'push', '--dry-run',
                                    '--porcelain', 'origin', f'HEAD:{PROBE_REF}')
    out = f'{stdout}\n{stderr}'.strip()
    if code == 0:
        return 'land', 'push --dry-run accepted'
    low = out.lower()
    if ('403' in low or 'permission' in low or 'denied' in low
            or 'read-only' in low or 'not authorized' in low):
        first = next((l.strip() for l in out.splitlines() if l.strip()),
                     'no message')
        return 'handoff', first[:160]
    # Could not reach the server, or something else entirely. NOT 'handoff':
    # reporting a network blip as "you have no access here" sends somebody to
    # spawn a session they did not need (practice: fail-gracefully).
    first = next((l.strip() for l in out.splitlines() if l.strip()),
                 'git said nothing')
    return 'unknown', first[:160]


def targets(repo_root):
    """-> [(label, path)] for this checkout and every source in force."""
    out = [('this checkout', str(pathlib.Path(repo_root).resolve()))]
    try:
        import precedent_resolve
        sources = precedent_resolve.load_config(repo_root)
    except SystemExit as exc:
        # load_config EXITS rather than raising for a missing or malformed
        # precedent.json, and SystemExit is not an Exception -- so the clause
        # below does not catch it and the interpreter's code (2) becomes this
        # tool's. Found by verify_harness running every tool with --help in a
        # tools-only tree: a session-start step must never be able to take the
        # session down (practice: fail-gracefully).
        print(f'  note: could not enumerate practice sources (config refused: '
              f'{exc.code}); probed this checkout only', file=sys.stderr)
        return out
    except Exception as exc:                       # noqa: BLE001
        # A source that will not resolve is already reported, loudly, by the
        # session-start step that resolves them. Saying it twice trains a
        # reader to skim both (practice: fail-gracefully).
        print(f'  note: could not enumerate practice sources '
              f'({exc.__class__.__name__}); probed this checkout only',
              file=sys.stderr)
        return out
    seen = {out[0][1]}
    for s in sources or ():
        path = s.get('path')
        if not path:
            continue
        # A repo-local source lives INSIDE this checkout (its path is exactly
        # "local"), so it is the same repository and the same answer. Probing
        # it again would print a second row for one remote.
        if s.get('level') == 'repo-local':
            continue
        resolved = str(pathlib.Path(path).resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append((f"{s.get('level')} source {s.get('name')!r}", resolved))
    return out


def run(repo_root='.', out=sys.stderr):
    """-> exit code, always 0. Prints the table; never raises."""
    rows, unchecked = [], []
    started = time.monotonic()
    for label, path in targets(repo_root):
        if time.monotonic() - started > BUDGET_SECONDS:
            unchecked.append((label, path))
            continue
        try:
            verdict, detail = can_land_here(path)
        except Exception as exc:                   # noqa: BLE001
            verdict, detail = 'unknown', f'probe raised {exc.__class__.__name__}'
        rows.append((label, path, verdict, detail))

    handoff = [r for r in rows if r[2] == 'handoff']
    unknown = [r for r in rows if r[2] == 'unknown']

    if rows and not handoff and not unknown and not unchecked:
        names = ', '.join(r[0] for r in rows)
        print(f'ACCESS: this session can land work in all {len(rows)} repo(s) '
              f'in force ({names}).', file=out)
        return 0

    print('ACCESS -- can THIS session land work in each repo in force?', file=out)
    for label, path, verdict, detail in rows:
        suffix = '' if verdict == 'land' else f' -- {detail}'
        print(f'  {_MARK[verdict]} {label} ({path}){suffix}', file=out)
    for label, path in unchecked:
        print(f'  NOTASKED {label} ({path}) -- probe budget '
              f'({BUDGET_SECONDS:g}s) spent before reaching this one', file=out)

    if handoff:
        print(f'  => {len(handoff)} repo(s) need a handoff. Work destined for '
              f'one of them cannot be pushed from here, however it is written: '
              f'settle who lands it BEFORE doing the work '
              f'(practice: session-text).', file=out)
    if unknown or unchecked:
        print(f'  => {len(unknown) + len(unchecked)} repo(s) unanswered. That '
              f'is NOT the same as refused -- probe one by hand before '
              f'concluding anything: git -C <path> push --dry-run origin '
              f'HEAD:{PROBE_REF}', file=out)
    return 0


USAGE = """usage: precedent_access_check.py [REPO_ROOT]

Probe which repos in force this session can actually PUSH to, and print one
line each. Runs from the session-start hook; run it bare any time.

  REPO_ROOT   the consuming repo to read sources from (default:
              $CLAUDE_PROJECT_DIR, else the working directory)

Verdicts:
  LAND        git push --dry-run was accepted -- work can land here
  HANDOFF     a real permission refusal, quoted. Settle who merges BEFORE
              doing work destined for this repo (practice: session-text)
  UNKNOWN     the probe could not reach the server. NOT the same as refused
  NOTASKED    the probe budget ran out before this repo

Environment:
  PRECEDENT_ACCESS_BUDGET   whole-run probe budget in seconds (default 45)

Always exits 0: a session-start step must never keep a session from starting.
"""


def main():
    args = sys.argv[1:]
    # --help NEVER PROBES. A tool asked to explain itself must not open
    # network connections to do it -- and every tool here answers --help with
    # exit 0, which verify_harness checks by running all of them in a
    # tools-only tree (practice: fail-gracefully).
    if args and args[0] in ('-h', '--help'):
        print(USAGE)
        return 0
    repo_root = args[0] if args else os.environ.get('CLAUDE_PROJECT_DIR', '.')
    return run(repo_root)


if __name__ == '__main__':
    sys.exit(main())
