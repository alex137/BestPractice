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

WHERE THE WATERMARK LIVES: `tools/beta-branch-watermark.json`, HERE, since
2026-09-22. It lived at the root of the individual source until then, on
the argument that a record of what one person has already seen is not part
of this branch's history and would read as a personal read-receipt in a
public tree. Morgan overruled that, in those terms: the file holds a public
repository name, a public branch, a public commit SHA and a date; his own
my-identity-is-not-private practice covers his name appearing; and the
placement was tidiness, not privacy. It is keyed by identity inside, so a
second person on this branch is a second key rather than a second file --
"the last commit already reported" is true of a PERSON, not of a repo, and
one shared row would have each of them eating the other's notification.

WHAT THE MOVE COST, since it is not free. The write now lands in the very
checkout the session is about to work in, which the old placement made
impossible by construction. Two guards carry that: `_is_quiet` refuses to
write history into a checkout that is ahead of origin or has anything
staged, so a session-start hook can never publish work in progress or
author somebody's half-made commit; and `_commit_and_push` commits the one
path explicitly rather than whatever the index holds.

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

AND WHERE IT MOVES: NEVER WHERE IT CANNOT BE PUSHED. Moving the trigger
left the rarer half of the problem behind -- an alert still wrote a commit
into the individual source, and from a session rooted here that push could
not land: the git proxy serves fetches of that clone and refuses pushes on
repository scope, measured repeatedly on 2026-09-22 with the credential
helper present and the token in the environment. Eight unpushable commits
piled up there before the probe went in.

Relocating the file removes that particular wall and NOT the rule. The
alert path still probes with `push --dry-run` -- a real
authenticate-and-negotiate round trip that writes nothing -- because a
checkout that is offline, behind or diverged still cannot push, and a
commit written where it cannot be pushed is the whole failure. Where the
probe says no, or the checkout is not idle, nothing is written to the
shared file: the head just reported goes into this repository's gitignored
`.precedent/`, per container. That is all the shared watermark buys once it
cannot be written -- it stops the alert repeating HERE and claims nothing
about any other container -- and the note is written only where git can be
SHOWN to ignore it, because an untracked file in a source clone is the dirt
that skips that clone's refresh and reads as work existing nowhere else.

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
                                                             # (this repo's own tools/, since 2026-09-22)

Exit status is always 0 (practice: fail-gracefully) -- a session start or a
reply that a network hiccup or a missing individual source could block is
worse than the notice it was trying to deliver.
"""
import argparse
import json
import os
import pathlib
import re
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

# practice: filename-separator -- every .json in tools/ uses underscores
# (upstream_watermark.json, session_load_budgets.json, glossary_terms.json),
# so this one does too. It arrived here as beta-branch-watermark.json,
# carrying the hyphen from the individual source's root where it used to
# live, and the planted filename-separator case refused it within the hour.
WATERMARK_FILENAME = 'beta_branch_watermark.json'


def _identity_key(identity):
    """The key one person's row is stored under -- a slug of their DECLARED
    NAME, never their email.

    The email is the identity this tool actually compares commits against,
    and it is the obvious key. It cannot be used: `tools/leak_gate.py`
    refuses any email address anywhere in the tracked tree, and that rule is
    right -- this branch is public, a push is a publication, and a
    bookkeeping file is not the place to carve out an exception. Measured
    rather than reasoned: keying by email failed the gate on the first run
    after the file moved here, 2026-09-22.

    A name slug is stable enough for what this holds. If somebody's declared
    name changes, their row is re-baselined once, in silence, which costs
    nothing -- a baseline reports nothing by construction."""
    slug = re.sub(r'[^a-z0-9]+', '-',
                  (identity.get('name') or identity.get('email') or '').lower())
    return slug.strip('-') or 'unknown'


def _watermark_path(repo):
    """The shared watermark, in THIS repository's tools/.

    It used to live at the root of the individual source, on the argument
    that a record of what one person has seen does not belong in a public
    shared tree. Morgan overruled that 2026-09-22: it holds a public repo
    name, a public branch, a public SHA and a date, his own
    my-identity-is-not-private practice covers his name, and the placement
    was tidiness rather than privacy. Keyed by identity inside, so a second
    person is a second key rather than a second file."""
    return pathlib.Path(repo) / 'tools' / WATERMARK_FILENAME


def _working_branch():
    try:
        data = json.loads(UPSTREAM_WATERMARK.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return DEFAULT_BRANCH
    return data.get('working_branch') or DEFAULT_BRANCH


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


LOCAL_NOTE_DIRNAME = '.precedent'
LOCAL_NOTE_FILENAME = 'beta-branch-watermark-local.json'


def _can_push(repo):
    """-> True when a push of this checkout's current branch would land.

    WHY PROBE AT ALL, now that the write is same-repo. Until 2026-09-22 the
    watermark was committed into a DIFFERENT repository -- the individual
    source -- and from a session rooted here that push could not land: the
    git proxy serves fetches and refuses pushes on repository scope. Eight
    unpushable commits piled up in that clone before the probe went in.
    Moving the file here removes that particular wall, and the probe stays
    because the general case has not changed: a checkout that is offline,
    behind, or diverged still cannot push, and a commit written where it
    cannot be pushed is the failure this whole area is made of.

    `push --dry-run` is a real authenticate-and-negotiate round trip that
    writes nothing, so it answers the question that matters: WOULD this
    land."""
    code, _ = git(repo, 'push', '--dry-run', '--quiet', 'origin', 'HEAD')
    return code == 0


def _is_quiet(repo, branch):
    """-> True when this checkout is level with origin and nothing is staged.

    THE HAZARD THE MOVE INTRODUCED, and the reason this exists. While the
    watermark lived in another repository, a session-start commit there
    could not touch the session's own work. Now the hook writes into the
    very checkout the session is about to work in -- so a push would carry
    whatever else is sitting ahead of origin, and a commit would sweep up
    anything already staged. A session-start hook must never publish a
    session's work in progress, and must never author a commit a person was
    still composing.

    So the hook writes history only into a checkout that is demonstrably
    idle. Anything else, and the per-container note takes it instead: the
    alert is still delivered, and nobody's work moves."""
    code, ahead = git(repo, 'rev-list', '--count', f'origin/{branch}..HEAD')
    if code != 0 or ahead.strip() != '0':
        return False
    code, staged = git(repo, 'diff', '--cached', '--name-only')
    return code == 0 and not staged.strip()


def _local_note_path(repo):
    """Where a container that cannot push records what it has already said.

    Inside THIS repository's `.precedent/`, which is gitignored here, and
    never inside the individual source. A file in that clone -- tracked,
    untracked or otherwise -- is the thing being avoided: an untracked one
    is dirt that skips the clone's refresh and, since the container scanner
    landed, reads as work that exists nowhere else.
    """
    return pathlib.Path(repo) / LOCAL_NOTE_DIRNAME / LOCAL_NOTE_FILENAME


def _note_is_ignored(repo, path):
    """True only when git in `repo` really ignores `path`.

    Checked, never assumed. This repository's .gitignore carries
    `.precedent/`, but `check()` also runs with `root` set to a practice set
    -- and writing a non-ignored file there would create exactly the
    untracked dirt this note exists to avoid. No proof, no note."""
    code, _ = git(repo, 'check-ignore', '--quiet', str(path))
    return code == 0


def _read_local_note(repo):
    try:
        data = json.loads(_local_note_path(repo).read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError, OSError):
        return None
    sha = (data or {}).get('reported_head')
    return sha if isinstance(sha, str) and sha else None


def _write_local_note(repo, head, branch):
    """-> a phrase for the session-start line, saying what was recorded."""
    path = _local_note_path(repo)
    if not _note_is_ignored(repo, path):
        return ('and nothing recorded it -- this repo does not ignore '
                f'{LOCAL_NOTE_DIRNAME}/, so the same alert repeats next session')
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            '_comment': [
                'What THIS CONTAINER has already told Morgan about',
                f'origin/{branch}, when it could not push the shared',
                'watermark to the individual source. Gitignored and',
                'per-container on purpose: it stops the same alert',
                'repeating here without leaving an unpushable commit in',
                'somebody else\'s repository. Written by',
                'tools/precedent_beta_watermark_check.py.',
            ],
            'branch': branch,
            'reported_head': head,
            'recorded': precedent_time.today(),
        }, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    except OSError as exc:
        return f'and the local note could not be written ({exc})'
    return ('recorded in this container only, so it will not repeat here; '
            'another container has not been told')


def _later_of(repo, a, b):
    """The more recent of two commits on the same branch, or `a` when that
    cannot be established. Used to fold the local note into the shared
    watermark: a container that has already reported up to X must not report
    X again just because the file it could not push still says something
    older."""
    if not b:
        return a
    if not a:
        return b
    if a == b:
        return a
    code, _ = git(repo, 'merge-base', '--is-ancestor', a, b)
    if code == 0:
        return b
    code, _ = git(repo, 'merge-base', '--is-ancestor', b, a)
    return a if code == 0 else a


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


def _commit_and_push(repo, path, message, no_push, branch, identity=None):
    """Commit the watermark in THIS repository, and push unless asked not to.

    Never raises: a failed push still leaves the watermark advanced locally,
    which is enough to stop this same session repeating the alert.

    `commit -- <path>` COMMITS THAT PATH ALONE, whatever the index holds.
    A bare `git commit -m` after `git add` takes everything staged, and
    since 2026-09-22 this runs inside the checkout a person is working in --
    so the narrow form is the difference between a bookkeeping commit and
    quietly authoring somebody's half-staged edit. `_is_quiet` already
    refuses a staged index; this is the belt to that brace.

    `identity` is the DECLARED identity, stated on the commit rather than
    read out of the clone's config -- see `_identity_args` for the
    measurement that made that necessary. Its original reason was that this
    wrote into a repository it did not configure, which no longer holds;
    the explicit author stays because it is correct and costs nothing."""
    rel = path.relative_to(pathlib.Path(repo))
    git(repo, 'add', str(rel))
    _id_args, _id_env = _identity_args(identity)
    code, _ = git(repo, *_id_args, 'commit', '-m', message, '--', str(rel),
                  env=_id_env)
    if code != 0:
        return 'nothing to commit'
    if no_push:
        return 'committed locally only (--no-push)'
    code, out = git(repo, 'push', 'origin', f'HEAD:{branch}')
    if code != 0:
        return (f'committed here, and the push to origin/{branch} failed '
                f'({out.splitlines()[-1] if out else "see stderr"}). Nothing '
                f'retries it: the local watermark now equals the head, so the '
                f'next session here short-circuits before reaching this push. '
                f'It travels with whatever this session pushes next')
    return 'committed and pushed'


def check(root=None, no_fetch=False, no_push=False, user_config=None):
    """-> (status, lines, alert).

    status is 'ok' (nothing new, or it was all your own commits), 'alert'
    (someone else pushed since the watermark), or 'unknown' (could not
    tell). `lines` is prose for the always-on session-start CLI; `alert` is
    the short paragraph `remind()` surfaces, or None.

    Took an `individual_path` until 2026-09-22, for a session whose PRIMARY
    repo was the individual source. The watermark lives in this repository
    now, so there is no second repository to point at and no case where it
    is somewhere this script cannot find.
    """
    repo = pathlib.Path(root).resolve() if root else REPO
    branch = _working_branch()
    watermark_path = _watermark_path(repo)

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

    # KEYED BY IDENTITY, not one record for the file. Two people work on
    # this branch, and "the last commit already reported" is true of a
    # PERSON, not of the repository -- a single shared record would have
    # one of them silently consuming the other's notification.
    registry = _load_watermark(watermark_path) or {}
    seen_by = registry.setdefault('seen_by', {})
    mine = seen_by.get(_identity_key(me)) or {}

    def _record(note):
        """Write this person's row and try to land it. -> an outcome phrase."""
        seen_by[_identity_key(me)] = {'sha': head, 'recorded': precedent_time.today(),
                                 'note': note}
        registry.setdefault('_comment', [
            f'The last commit on origin/{branch} each person has already been',
            'told about, keyed by a slug of the name their identity declares',
            '(never their email -- the leak gate refuses one in a tracked',
            'file, and this branch is public). Read and',
            'written by tools/precedent_beta_watermark_check.py, called from',
            "this repo's SessionStart hook and reply gate.",
            '',
            'Advances the moment it reports SOMEBODY ELSE\'S commits, and',
            'only then -- a run that finds none writes nothing here. Unlike',
            'tools/upstream_watermark.json beside it, which a person moves',
            'deliberately because it gates an action, this gates a',
            'notification with nothing left to do once it has been given.',
        ])
        registry.setdefault('repo', 'alex137/BestPractice')
        registry['branch'] = branch
        if not (no_push or (_is_quiet(repo, branch) and _can_push(repo))):
            # Not an idle checkout, or a push that would not land. Writing
            # history here would either publish a session's work in progress
            # or leave a commit nothing can send; the per-container note
            # carries the dedup instead and nobody's work moves.
            return ('nothing written to the shared watermark -- this checkout '
                    'is mid-work or cannot push; '
                    + _write_local_note(repo, head, branch))
        _write_watermark(watermark_path, registry)
        return _commit_and_push(repo, watermark_path,
                                 f'Advance {branch} watermark to {head[:9]}',
                                 no_push, branch, identity=me)

    if not mine:
        # First run for this person: nothing to compare against. Baseline
        # quietly at the current head rather than reporting every commit
        # already on the branch as if it had just landed.
        outcome = _record('baseline -- no prior watermark for this identity')
        return 'ok', [f'no prior watermark for {branch}; baselined at '
                       f'{head[:9]} ({outcome})'], None

    seen = mine.get('sha')
    # A container that could not write the shared watermark keeps its own
    # note of what it has already said. Fold it in before deciding what is
    # new, or this container re-reports commits it reported yesterday
    # purely because the shared file still names an older head.
    seen = _later_of(repo, seen, _read_local_note(repo))
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
        # records what its person has been TOLD, and they have just been
        # told nothing, so there is nothing to record and no commit to write.
        return 'ok', [f'{branch} moved to {head[:9]}, all your own commits -- '
                       f'nothing to tell you, so the watermark stays at '
                       f'{seen[:9] if seen else "(none recorded)"}'], None

    outcome = _record('auto-advanced by precedent_beta_watermark_check.py')

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
