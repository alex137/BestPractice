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

WHAT MOVES THE WATERMARK: AN ALERT, NOT A PUSH. Until 2026-09-22 this
file wrote and committed the watermark the moment `origin/<branch>` moved
at all -- above the `if not others` return, so the path that reports
NOTHING advanced and committed exactly like the path that reports someone
else's commits. Measured on `precedent-beta-v01` the same day: of the last
300 commits, 293 are Morgan's own, 5 a session's and 2 Alex's. So very
nearly every watermark commit ever written recorded the delivery of a
notice that was never delivered, and the registry's own `_comment` --
"gates a notification with nothing left to do once it has been given" --
described a contract the code did not keep. Counted in this container's
own clone of the individual source the same day: 32 watermark commits
across four days, 13 of them on 2026-09-21 alone, and 8 of the 32 still
sitting unpushed. The open item is
todo-2026-09-21-watermark-commits-pile-up-where-they-cannot-be-pushed
under todo/.

The write and the commit now sit BELOW that return. Nothing at all is
written on the quiet path -- not a commit, and not an uncommitted edit
either, which would leave that clone permanently dirty and stop
`.claude/hooks/freshness-guard.sh` fast-forwarding it: a stuck checkout
in place of a diverged one. Letting the watermark go stale there is
harmless and is the point: `others` is computed over `seen..head`, so a
watermark that stayed put simply widens the window the next run reads, and
a commit nobody was told about is still found and still reported.

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


def git(repo, *args, check=False, env=None):
    """Run git in `repo` and return (returncode, stdout). See
    precedent_upstream_check.py's own `git()` for why the pair matters:
    `git rev-parse` echoes back an unresolved ref instead of failing loudly.

    `env` ADDS to this process's environment rather than replacing it --
    a bare dict handed to subprocess would drop PATH, HOME and the proxy
    settings, and the caller only ever wants to set a couple of GIT_*
    variables on top of what is already there."""
    _env = None
    if env:
        _env = dict(os.environ)
        _env.update(env)
    proc = subprocess.run(['git', '-C', str(repo), *args],
                           capture_output=True, text=True, env=_env)
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


def _identity_args(identity):
    """-> ['-c', 'user.name=...', '-c', 'user.email=...'] for the DECLARED
    identity, and an env carrying a date in that person's own timezone.

    WHY THIS EXISTS (2026-09-21). `_commit_and_push` used to run a bare
    `git commit -m`, trusting whatever `git config` held in the clone it was
    writing to. That clone is in a DIFFERENT REPOSITORY from the one this
    script runs in: the script runs in BestPractice and commits into the
    individual source. `commit-identity.sh` does reach sibling repos, and
    earlier in the same hook -- but when it cannot, it says so in a WARN and
    keeps going, and this ran anyway against an unconfigured clone.

    The trail is what forced the fix. Nineteen watermark commits on the
    individual source's `main` came out in THREE states, not two: authored
    correctly with the right offset; authored as the container with `+0000`;
    and -- twice -- authored as the container with the RIGHT offset. That
    third state is the proof the two halves are independent. The offset
    comes from the `env` block in settings.json, which follows a session
    into every repo it touches; the author comes from `git config` in one
    specific clone, which is the thing that has to be reached. Trusting an
    earlier step to have configured somebody else's repository is not a
    guarantee, so this stops trusting it and states the author on the
    command that writes the commit (practice: durable-fix).

    Degrades rather than fails: no identity, or an unreadable timezone, and
    the caller commits exactly as it did before. A watermark that cannot be
    written is a notice that repeats forever, which is worse than one
    carrying the wrong name.
    """
    if not identity:
        return [], None
    args = []
    if identity.get('name'):
        args += ['-c', f'user.name={identity["name"]}']
    if identity.get('email'):
        args += ['-c', f'user.email={identity["email"]}']
    env = None
    zone = identity.get('timezone')
    if zone:
        try:
            import datetime
            import zoneinfo
            when = datetime.datetime.now(
                zoneinfo.ZoneInfo(zone)).strftime('%Y-%m-%dT%H:%M:%S%z')
        except Exception:                                     # noqa: BLE001
            pass          # a bad zone name is not worth losing the commit
        else:
            env = {'GIT_AUTHOR_DATE': when, 'GIT_COMMITTER_DATE': when}
    return args, env


def _commit_and_push(individual_path, path, message, no_push, branch,
                     identity=None):
    """Commit the watermark in the individual source, and push unless asked
    not to. Never raises: a failed push still leaves the watermark advanced
    LOCALLY, which is enough to stop this same session from repeating the
    alert -- cross-session dedup needs the push to actually land, and a
    failure here says so rather than pretending it landed.

    `branch` is only for the failure message below -- naming the branch this
    watermark is FOR, not the repository this push actually targets (that's
    always the individual source, never `branch`'s own repo).

    `identity` is the DECLARED identity, stated on the commit rather than
    read out of the target clone's config -- see `_identity_args` for the
    measurement that made that necessary."""
    rel = path.relative_to(individual_path)
    git(individual_path, 'add', str(rel))
    _id_args, _id_env = _identity_args(identity)
    code, _ = git(individual_path, *_id_args, 'commit', '-m', message,
                  env=_id_env)
    if code != 0:
        return 'nothing to commit'
    if no_push:
        return 'committed locally only (--no-push)'
    code, out = git(individual_path, 'push', 'origin', 'HEAD')
    if code != 0:
        # Names the individual source and calls this "the note" -- the
        # caller embeds this string right after reporting on `branch`'s own
        # commits, in the same sentence, and a bare "the push failed" there
        # reads as if THOSE commits failed to push. They didn't; this is a
        # separate push, of a bookkeeping file, to a different repository
        # (individual_path's own remote, not branch's).
        return (f'this note about it failed to sync to the individual source '
                f'({out.splitlines()[-1] if out else "see stderr"}) -- not a '
                f'failure to push {branch} itself. The commit stays in this '
                f'container: the local watermark now equals the head, so the '
                f'next session here short-circuits before reaching this push '
                f'and nothing retries it. It reaches the individual source '
                f'only when a session that can push there sends it')
    return 'committed and pushed'


def check(root=None, no_fetch=False, no_push=False, user_config=None,
          individual_path=None):
    """-> (status, lines, alert).

    status is 'ok' (nothing new, or it was all your own commits), 'alert'
    (someone else pushed since the watermark), or 'unknown' (could not
    tell). `lines` is prose for the always-on session-start CLI; `alert` is
    the short paragraph `remind()` surfaces, or None.

    `individual_path`, given explicitly, skips config-file resolution
    entirely. Needed for a session whose PRIMARY repo IS the individual
    source: nothing wrote it a `~/.config/precedent/config.json` pointing
    at itself (that file is for a repo that resolves someone ELSE's
    individual set), so `_individual_path()` would find nothing to
    resolve even though the right directory is sitting right there.
    """
    repo = pathlib.Path(root).resolve() if root else REPO
    branch = _working_branch()

    indiv = pathlib.Path(individual_path).expanduser() if individual_path \
        else _individual_path(user_config)
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
                'Advances the moment it reports SOMEBODY ELSE\'S commits,',
                'and only then -- a run that finds none writes nothing here.',
                'Unlike tools/upstream_watermark.json in BestPractice, which',
                'a person moves deliberately because it gates an action, this',
                'gates a notification with nothing left to do once it has',
                'been given.',
            ],
            'repo': 'alex137/BestPractice',
            'branch': branch,
        }
        registry['last_seen'] = {'sha': head, 'recorded': precedent_time.today(),
                                  'note': 'baseline -- no prior watermark'}
        _write_watermark(watermark_path, registry)
        outcome = _commit_and_push(indiv, watermark_path,
                                    f'Baseline {branch} watermark at {head[:9]}',
                                    no_push, branch, identity=me)
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

    if not others:
        # NOTHING IS WRITTEN AND NOTHING IS COMMITTED ON THIS PATH. See
        # "WHAT MOVES THE WATERMARK" in this file's header: the watermark
        # records what Morgan has been TOLD, and he has just been told
        # nothing, so there is nothing to record -- and no commit to write
        # into a different person's repository for a notice never given.
        return 'ok', [f'{branch} moved to {head[:9]}, all your own commits -- '
                       f'nothing to tell you, so the watermark stays at '
                       f'{seen[:9] if seen else "(none recorded)"}'], None

    registry['last_seen'] = {
        'sha': head, 'recorded': precedent_time.today(),
        'note': 'auto-advanced by precedent_beta_watermark_check.py',
    }
    _write_watermark(watermark_path, registry)
    outcome = _commit_and_push(indiv, watermark_path,
                                f'Advance {branch} watermark to {head[:9]}',
                                no_push, branch, identity=me)

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
    parser.add_argument('--individual-path', default=None,
                         help='the individual source directory, when this session '
                              'IS that source and has no config.json pointing at '
                              'someone else\'s')
    args = parser.parse_args()
    status, lines, _alert = check(no_fetch=args.no_fetch, no_push=args.no_push,
                                   individual_path=args.individual_path)
    prefix = {'ok': 'beta-branch watermark',
              'alert': 'BETA-BRANCH WATERMARK',
              'unknown': 'beta-branch watermark UNKNOWN'}[status]
    for i, line in enumerate(lines):
        print(f'{prefix}: {line}' if i == 0 else line)
    return 0


if __name__ == '__main__':
    sys.exit(main())
