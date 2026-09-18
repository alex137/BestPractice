#!/usr/bin/env python3
"""Say whether anyone other than you has pushed to precedent-beta-v01 since
you were last told, and only that once.

WHY THIS IS NOT tools/precedent_upstream_check.py'S WATERMARK, ADAPTED. That
one gates an ACTION: "has `main` been carried onto this branch", and its own
comment is explicit that it must NOT auto-advance -- a person decides when a
carry has happened, so the notice keeps repeating until they run `--record`
themselves. This one gates a NOTIFICATION: "has Morgan been told that
someone else moved this branch". There is no action for him to perform to
make the notice stop -- he has simply been told -- so THIS watermark
auto-advances the moment it reports, in the same run. A notice that keeps
firing after it has already been delivered is exactly the failure
`upstream_watermark.json`'s own header names ("ignored by the second week"),
and the fix here is the mirror image of that file's: advance on report,
not on request.

WHERE THE WATERMARK LIVES, AND WHY NOT HERE. `<individual source>/
beta-branch-watermark.json`, never a file in this repository. It is not
part of `precedent-beta-v01`'s own history -- it is a record of what ONE
PERSON has already seen -- so it belongs beside `identity.json` in Morgan's
own practice source (a private, single-owner repository), not in
`alex137/BestPractice`'s tracked tree, where it would read as churn on every
push that was never his to begin with, and where anyone else reading this
public repository would see a personal read-receipt for no reason.

Raised by Morgan, 2026-09-18: Alex also pushes to this branch, and Morgan
wants to know when -- but not in every reply of a session, only once per
actual change. Two integration points, both calling `check()` /
`remind()` below rather than duplicating its logic:
  - `.claude/hooks/session-start.sh` calls this file directly (like
    `precedent_upstream_check.py`), once per session, and always prints a
    status line -- "unchanged" included -- the same way that script does.
  - `tools/precedent_gate.py`'s `reply` gate calls `remind()`, which is
    SILENT except on a real alert. A per-turn channel that repeated
    "unchanged" on every reply would be exactly the noise this file exists
    to remove; the session-start CLI above is where that status belongs.

Run:
  python3 tools/precedent_beta_watermark_check.py             # session start: always one line
  python3 tools/precedent_beta_watermark_check.py --no-fetch  # compare local refs only
  python3 tools/precedent_beta_watermark_check.py --no-push   # write + commit locally, skip the network push

Exit status is always 0 (practice: fail-gracefully) -- a session start or a
reply that a network hiccup or a missing individual source could block is
worse than the notice it was trying to deliver.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_identity as pi   # noqa: E402
import precedent_time             # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent

# practice: registry-source-of-truth -- the working branch is declared once,
# in upstream_watermark.json, and read from there rather than repeated here
# as a second literal that could drift from it.
UPSTREAM_WATERMARK = REPO / 'tools' / 'upstream_watermark.json'
DEFAULT_BRANCH = 'precedent-beta-v01'

# practice: filename-separator -- the individual source's root already uses
# a hyphen (leak-blocklist.txt), so this file matches it rather than
# introducing a second separator into that directory.
WATERMARK_FILENAME = 'beta-branch-watermark.json'


def _working_branch():
    try:
        data = json.loads(UPSTREAM_WATERMARK.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return DEFAULT_BRANCH
    return data.get('working_branch') or DEFAULT_BRANCH


def _individual_path(user_config=None):
    """Where the individual source is cloned, or None.

    Duplicated from precedent_identity.py's own internal resolution rather
    than imported -- consistent with that file's own header: a person's
    identity needs the individual source's PATH, and precedent_resolve.py
    (the one place that answers this for a consuming repo) is deliberately
    not importable from a module like this one that has to run inside a
    practice SET too, which has no precedent_resolve.py to import.
    """
    cfg_path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(pi.USER_CONFIG_ENV, str(pi.DEFAULT_USER_CONFIG))).expanduser()
    try:
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    except (ValueError, OSError, AttributeError):
        return None
    path = (cfg.get('individual') or {}).get('path')
    return pathlib.Path(path).expanduser() if path else None


def git(repo, *args, check=False):
    """Run git in `repo` and return (returncode, stdout). See
    precedent_upstream_check.py's own `git()` for why the pair matters:
    `git rev-parse` echoes back an unresolved ref instead of failing loudly."""
    proc = subprocess.run(['git', '-C', str(repo), *args],
                           capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.returncode, proc.stdout.strip()


def _load_watermark(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError, OSError):
        return None


def _write_watermark(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                     encoding='utf-8')


def _commit_and_push(individual_path, path, message, no_push):
    """Commit the watermark in the individual source, and push unless asked
    not to. Never raises: a failed push still leaves the watermark advanced
    LOCALLY, which is enough to stop this same session from repeating the
    alert -- cross-session dedup needs the push to actually land, and a
    failure here says so rather than pretending it landed."""
    rel = path.relative_to(individual_path)
    git(individual_path, 'add', str(rel))
    code, _ = git(individual_path, 'commit', '-m', message)
    if code != 0:
        return 'nothing to commit'
    if no_push:
        return 'committed locally only (--no-push)'
    code, out = git(individual_path, 'push', 'origin', 'HEAD')
    if code != 0:
        return (f'committed locally, but the push failed ({out.splitlines()[-1] if out else "see stderr"}) '
                f'-- this will re-alert next session until it can push')
    return 'committed and pushed'


def check(root=None, no_fetch=False, no_push=False, user_config=None):
    """-> (status, lines, alert).

    status is 'ok' (nothing new, or it was all your own commits), 'alert'
    (someone else pushed since the watermark), or 'unknown' (could not
    tell). `lines` is prose for the always-on session-start CLI; `alert` is
    the short paragraph `remind()` surfaces, or None.
    """
    repo = pathlib.Path(root).resolve() if root else REPO
    branch = _working_branch()

    indiv = _individual_path(user_config)
    if indiv is None or not (indiv / '.git').is_dir():
        return 'unknown', ['no individual source resolves, so there is nowhere '
                            'to keep this watermark'], None

    watermark_path = indiv / WATERMARK_FILENAME

    if not no_fetch:
        code, _ = git(repo, 'fetch', '--depth=50', 'origin', branch)
        if code != 0:
            return 'unknown', [f'could not fetch origin/{branch} (offline, or '
                                f'no access) -- this says nothing about who '
                                f'pushed'], None

    code, head = git(repo, 'rev-parse', '--verify', '--quiet', f'origin/{branch}')
    if code != 0 or not head:
        return 'unknown', [f'origin/{branch} does not resolve in this clone'], None

    try:
        me = pi.declared_identity(repo, user_config=user_config)
    except pi.NoDeclaredIdentity:
        return 'unknown', ["no identity is declared, so 'someone other than "
                            "you' cannot be told apart from you"], None

    registry = _load_watermark(watermark_path)
    if registry is None:
        # First run: nothing to compare against. Baseline quietly at the
        # current head rather than reporting every commit already on the
        # branch as if it had just landed.
        registry = {
            '_comment': [
                f'The last commit on origin/{branch} Morgan has already been',
                'told about. Read and written by',
                'tools/precedent_beta_watermark_check.py (BestPractice),',
                'called from that repo\'s SessionStart hook and reply gate.',
                'Lives here rather than in the branch\'s own tree because it',
                'is not that branch\'s history -- it is a record of what ONE',
                'PERSON has seen -- so it stays out of alex137/BestPractice,',
                'which is public and shared.',
                '',
                'Auto-advances the moment it reports something new: unlike',
                'tools/upstream_watermark.json in BestPractice, which a person',
                'moves deliberately because it gates an action, this gates a',
                'notification with nothing left to do once it has been given.',
            ],
            'repo': 'alex137/BestPractice',
            'branch': branch,
        }
        registry['last_seen'] = {'sha': head, 'recorded': precedent_time.today(),
                                  'note': 'baseline -- no prior watermark'}
        _write_watermark(watermark_path, registry)
        outcome = _commit_and_push(indiv, watermark_path,
                                    f'Baseline {branch} watermark at {head[:9]}',
                                    no_push)
        return 'ok', [f'no prior watermark for {branch}; baselined at '
                       f'{head[:9]} ({outcome})'], None

    seen = (registry.get('last_seen') or {}).get('sha')
    if seen == head:
        return 'ok', [f'{branch} unchanged since last check ({head[:9]})'], None

    others = []
    if seen:
        code, log = git(repo, 'log', '--format=%H%x1f%ae%x1f%an%x1f%s',
                         f'{seen}..{head}')
        if code == 0 and log:
            for line in log.splitlines():
                parts = line.split('\x1f')
                if len(parts) != 4:
                    continue
                sha, email, name, subject = parts
                if email != me['email']:
                    others.append((sha[:9], name, subject))

    registry['last_seen'] = {
        'sha': head, 'recorded': precedent_time.today(),
        'note': 'auto-advanced by precedent_beta_watermark_check.py',
    }
    _write_watermark(watermark_path, registry)
    outcome = _commit_and_push(indiv, watermark_path,
                                f'Advance {branch} watermark to {head[:9]}',
                                no_push)

    if not others:
        return 'ok', [f'{branch} moved to {head[:9]}, all your own commits '
                       f'({outcome})'], None

    lines = [f'{len(others)} commit(s) on {branch} since {seen[:9] if seen else "(none recorded)"}, '
              f'not authored by you, up to {head[:9]} ({outcome}):']
    for sha, name, subject in others:
        lines.append(f'  {sha}  {name}: {subject}')
    who = ', '.join(sorted({n for _, n, _ in others}))
    alert = (f'**{who} pushed to `{branch}`** -- {len(others)} commit(s) since '
             f'you last checked, up to `{head[:9]}`. Told once; the watermark '
             f'has moved, so this will not repeat unless the branch moves again.')
    return 'alert', lines, alert


def remind(root=None, user_config=None):
    """For the reply gate: None in the ordinary case, a short paragraph only
    on a real alert. Never reports 'unknown' here -- a per-turn channel that
    nagged about a config problem it cannot fix would be exactly the noise
    this file exists to avoid; `main()` below is where that belongs, once
    per session."""
    try:
        status, _lines, alert = check(root=root, user_config=user_config)
    except Exception:
        return None
    return alert if status == 'alert' else None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--no-fetch', action='store_true',
                         help='compare against local refs only; do not fetch')
    parser.add_argument('--no-push', action='store_true',
                         help='write and commit the watermark locally, skip the push')
    args = parser.parse_args()
    status, lines, _alert = check(no_fetch=args.no_fetch, no_push=args.no_push)
    prefix = {'ok': 'beta-branch watermark',
              'alert': 'BETA-BRANCH WATERMARK',
              'unknown': 'beta-branch watermark UNKNOWN'}[status]
    for i, line in enumerate(lines):
        print(f'{prefix}: {line}' if i == 0 else line)
    return 0


if __name__ == '__main__':
    sys.exit(main())
