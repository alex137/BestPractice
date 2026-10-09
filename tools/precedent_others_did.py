#!/usr/bin/env python3
"""Once a day, from the first session after 07:00 in the person's own timezone, says what OTHER people landed in this repository since that person was last told -- every commit on its shared branches that is not theirs -- and hands the session a block to open its first reply with; the per-person mark lives on origin's refs/precedent/others-did, outside every branch, and is written there without touching the checkout

Say what other people did here since you were last told, once a day.

WHY IT EXISTS (Morgan, 2026-10-08). Alex changed how merges to `main` work
and Morgan found out only when something confusing happened. WHATS_NEW.md
did not help: it carries the three or four most important things done by
anyone each day, and most days that is mostly Morgan's own work. What he
asked for is the opposite view -- only what OTHERS did -- delivered before
his first question of the day is answered, without him having to ask.

IT REPLACES the beta-branch watermark check, which did a narrower
version of the same job (anyone else pushing to one branch, staging) and,
measured the day this was written, did not deliver it: it found Alex's ten
commits at that session's start, and (1) its notice sat inside a
SessionStart output over the size the harness shows, so the session never
saw it, and (2) it could write its mark only into a checkout sitting idle
on staging, which a session on a feature branch never is, so the mark went
to a per-container note and every new container would have said it again.
This file fixes both: the notice reaches the session through the reply
gate on the first prompt, and the mark is committed with git plumbing,
never through the working tree, the index or HEAD.

WHERE THE MARK LIVES: refs/precedent/others-did on origin (2026-10-08),
a ref outside refs/heads, holding one file, others_did_watermark.json,
with its own history. It is fetched and pushed by name, so it is not a
branch: it never appears in a branch list, never rides a Promote, and
never lands on a tier. Until then the mark was a commit on the landing
branch itself, and a status check run in a session's first reply pushed
"Others-did mark ... [skip ci]" straight onto a consuming repository's
pre-staging, from where the next Produce carried it up to main. A
repository that still has only the old file, tools/others_did_watermark.json
on its landing branch, is READ from there once, to carry its marks over;
nothing is written there again.

WHO IT IS FOR. The whole five-stage ladder set turns it on
(`precedent_ladder.ladder_in_force`): a person off the ladder hears
nothing. It ships with the engine, so every repository with Precedent
installed carries it for every person in it, each keyed separately.

WHAT COUNTS AS SOMEONE ELSE'S. A commit whose author email is not the
declared identity's. A commit signed only by Claude is attributed through
its `Claude-Session:` trailer: a session that also authored commits under a
person's own name is that person's; otherwise the first person who merged
it in owns it (a session's pull request is merged by whoever ran it, in
practice). Measured 2026-10-08 against `get_session` from Morgan's account:
the two sessions that did not open there were the two whose pull requests
Alex merged. What neither rule settles is listed with its session link, and
the session checks the link before it writes the summary. Merge commits
are left out: merging is not the work, and the merged commits are counted
on their own.

WHEN. At most one report a day: none before the person's hour (07:00 by
default, `others_did_hour` in identity.json overrides), and none once they
have been told since that hour today. A report advances the mark; a run
that finds nothing from anyone else writes nothing and says one line, so a
quiet day leaves no commits behind.

Run:
  python3 tools/precedent_others_did.py              # session start: one status line
  python3 tools/precedent_others_did.py --no-fetch   # compare local refs only
  python3 tools/precedent_others_did.py --no-push    # never write the shared mark

Exit status is always 0 (practice: fail-gracefully): a session start that
a network hiccup could block is worse than the notice it was carrying.
"""
import argparse
import datetime
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

# The ref the shared mark lives on, on origin and in every clone that has
# fetched it, and the one file its tree holds.
MARK_REF = 'refs/precedent/others-did'
MARK_FILE = 'others_did_watermark.json'
# Where the mark lived before 2026-10-08, on the landing branch: read once,
# for migration, never written.
WATERMARK_PATH = 'tools/others_did_watermark.json'
LOCAL_NOTE = '.precedent/others-did-local.json'
PENDING = '.precedent/others-did-pending.md'
DEFAULT_HOUR = 7
HOUR_SETTING = 'others_did_hour'
# The most commit lines one report prints. The session summarises them; a
# list long enough to push the hook output past what the harness shows is
# the failure this file was written to end.
MAX_LINES = 40

BOT_EMAILS = {'noreply@anthropic.com'}
SESSION_RE = re.compile(r'Claude-Session:\s*(https://claude\.ai/code/session_\w+)')


def git(repo, *args, env=None, input=None):
    """-> (returncode, stdout). `env` adds to the environment, never replaces it."""
    full = None
    if env:
        full = dict(os.environ)
        full.update(env)
    proc = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                          text=True, env=full, input=input)
    return proc.returncode, proc.stdout.strip()


def identity_key(identity):
    """A slug of the declared NAME, never the email: the leak gate refuses an
    email anywhere in a tracked file, and this one is public."""
    slug = re.sub(r'[^a-z0-9]+', '-',
                  (identity.get('name') or identity.get('email') or '').lower())
    return slug.strip('-') or 'unknown'


def _is_bot(email):
    return (email or '').lower() in BOT_EMAILS


# ---------------------------------------------------------------- branches

def watched_branches(repo):
    """The tier branches this repository has: main, its staging branch,
    pre-staging and whatever precedent.json names as base_branch."""
    names = ['main', 'staging', 'pre-staging']
    try:
        import precedent_branches as pb
        for extra in (pb.base_branch(repo), pb.staging_branch(repo)):
            if extra and extra not in names:
                names.append(extra)
    except Exception:                                             # noqa: BLE001
        pass
    return names


def landing(repo, user_config=None):
    try:
        import precedent_branches as pb
        return pb.landing_branch(repo, user_config)[0]
    except Exception:                                             # noqa: BLE001
        return 'main'


def _fetch(repo, branches):
    """Fetch the branches origin actually has. -> the ones that resolve."""
    code, out = git(repo, 'ls-remote', '--heads', 'origin')
    if code != 0:
        return None
    present = {ln.split('refs/heads/', 1)[1] for ln in out.splitlines()
               if 'refs/heads/' in ln}
    wanted = [b for b in branches if b in present]
    if not wanted:
        return []
    _, shallow = git(repo, 'rev-parse', '--is-shallow-repository')
    depth = ['--depth=200'] if shallow == 'true' else []
    refspecs = [f'+refs/heads/{b}:refs/remotes/origin/{b}' for b in wanted]
    code, _ = git(repo, 'fetch', '-q', *depth, 'origin', *refspecs)
    return wanted if code == 0 else None


def _heads(repo, branches):
    heads = {}
    for b in branches:
        code, sha = git(repo, 'rev-parse', '--verify', '--quiet', f'origin/{b}^{{commit}}')
        if code == 0 and sha:
            heads[b] = sha
    return heads


# ---------------------------------------------------------------- the mark

def _fetch_mark(repo):
    """Bring origin's mark ref into this clone, at the same name. -> True
    fetched, False origin has none yet (the local ref is dropped, so a stale
    one is never built on), None origin could not be reached."""
    code, _ = git(repo, 'fetch', '-q', '--no-tags', 'origin',
                  f'+{MARK_REF}:{MARK_REF}')
    if code == 0:
        return True
    code, _ = git(repo, 'ls-remote', '--exit-code', 'origin', MARK_REF)
    if code == 2:
        git(repo, 'update-ref', '-d', MARK_REF)
        return False
    return None


def _read_shared(repo, land):
    """The registry as origin's mark ref holds it (last fetched). Where no
    mark ref exists yet, the registry the landing branch held before the
    mark moved (read only; MIGRATION), else the working tree's copy of it."""
    code, text = git(repo, 'show', f'{MARK_REF}:{MARK_FILE}')
    if code != 0:
        code, text = git(repo, 'show', f'origin/{land}:{WATERMARK_PATH}')
    if code != 0:
        try:
            text = (pathlib.Path(repo) / WATERMARK_PATH).read_text(encoding='utf-8')
        except OSError:
            return {}
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_local(repo):
    try:
        data = json.loads((pathlib.Path(repo) / LOCAL_NOTE).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _ignored(repo, rel):
    """Only write under .precedent/ where git can be SHOWN to ignore it: an
    untracked file elsewhere is dirt that reads as work existing nowhere."""
    return git(repo, 'check-ignore', '--quiet', rel)[0] == 0


def _write_local(repo, rel, text):
    if not _ignored(repo, rel):
        return False
    path = pathlib.Path(repo) / rel
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    except OSError:
        return False
    return True


def _parse_time(value):
    try:
        return datetime.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _later_row(a, b):
    """The row told more recently, so a container that told the person
    something the shared file could not record does not tell it again."""
    ta, tb = _parse_time((a or {}).get('told_at')), _parse_time((b or {}).get('told_at'))
    if ta and tb:
        return b if tb > ta else a
    return a if ta else b


def _session_trailer():
    url = (os.environ.get('PRECEDENT_SESSION_URL') or '').strip()
    return f'Session: {url}' if url else \
        'Session: none available (tools/precedent_others_did.py)'


def publish(repo, land, registry, identity, message):
    """Commit the registry onto origin's MARK_REF and push it there, by name,
    WITHOUT the working tree, the index or HEAD: a blob, a one-file tree, a
    commit on the mark's own last commit. Never onto a branch -- `land` is
    not written, whatever it is -- so the mark cannot ride a Promote or sit
    on a tier. The session's own work cannot be swept into it, and nothing is
    left behind locally if the push fails.

    -> (ok, phrase). One retry on a rejected push, after a fresh fetch: a
    second session recording at the same moment is the expected race."""
    del land  # where the mark used to go; kept in the signature for callers
    body = json.dumps(registry, indent=2, ensure_ascii=False) + '\n'
    env = {}
    if identity.get('name'):
        env['GIT_AUTHOR_NAME'] = env['GIT_COMMITTER_NAME'] = identity['name']
    if identity.get('email'):
        env['GIT_AUTHOR_EMAIL'] = env['GIT_COMMITTER_EMAIL'] = identity['email']
    last = ''
    for _attempt in range(2):
        if _fetch_mark(repo) is None:
            return False, 'could not reach origin'
        code, parent = git(repo, 'rev-parse', '--verify', '--quiet',
                           f'{MARK_REF}^{{commit}}')
        parent = parent if code == 0 else ''
        code, blob = git(repo, 'hash-object', '-w', '--stdin', input=body)
        if code != 0:
            return False, 'could not write the mark into git'
        code, tree = git(repo, 'mktree', input=f'100644 blob {blob}\t{MARK_FILE}\n')
        if code != 0 or not tree:
            return False, 'could not build the tree'
        if parent and git(repo, 'rev-parse', f'{parent}^{{tree}}')[1] == tree:
            return True, 'already recorded'
        code, commit = git(repo, 'commit-tree', tree,
                           *(['-p', parent] if parent else []),
                           '-m', message, '-m', _session_trailer(), env=env)
        if code != 0:
            return False, 'could not build the commit'
        code, out = git(repo, 'push', '-q', 'origin', f'{commit}:{MARK_REF}')
        if code == 0:
            git(repo, 'update-ref', MARK_REF, commit)
            return True, f'recorded on origin\'s {MARK_REF}'
        last = out
    return False, f'the push to origin\'s {MARK_REF} was refused{": " + last if last else ""}'


# ---------------------------------------------------------------- attribution

def _session_owners(repo, refs):
    """-> {session url: set of human author emails} over recent history: a
    session that committed under a person's own name is that person's."""
    code, out = git(repo, 'log', '-n', '4000', '--format=%ae%x1f%B%x1e', *refs)
    owners = {}
    if code != 0:
        return owners
    for rec in out.split('\x1e'):
        email, _, body = rec.strip().partition('\x1f')
        if not email or _is_bot(email):
            continue
        for url in SESSION_RE.findall(body):
            owners.setdefault(url, set()).add(email.lower())
    return owners


def _merger(repo, sha, heads):
    """-> (email, name) of the first person whose merge brought `sha` into a
    watched branch, skipping merges a session made on its own branch."""
    for head in heads.values():
        if git(repo, 'merge-base', '--is-ancestor', sha, head)[0] != 0:
            continue
        code, out = git(repo, 'log', '--merges', '--ancestry-path', '--reverse',
                        '--format=%ae%x1f%an', f'{sha}..{head}')
        for line in out.splitlines() if code == 0 else []:
            email, _, name = line.partition('\x1f')
            if email and not _is_bot(email):
                return email.lower(), name
    return None, None


def classify(repo, commits, me_email, heads):
    """-> (others, unsure). others: [(sha, who, subject)], a Claude
    session's subject marked as one; unsure: commits signed only by Claude
    whose session nothing here settles, with its link."""
    me_email = (me_email or '').lower()
    owners = None
    names = {}
    others, unsure = [], []
    for sha, email, name, subject, body in commits:
        email = (email or '').lower()
        if not _is_bot(email):
            names.setdefault(email, name)
            if email != me_email:
                others.append((sha, name, subject))
            continue
        if owners is None:
            owners = _session_owners(repo, list(heads.values()))
        url = (SESSION_RE.findall(body) or [None])[0]
        who = owners.get(url, set()) if url else set()
        if me_email in who:
            continue
        if who:
            owner = sorted(who)[0]
            others.append((sha, names.get(owner, owner.split('@')[0]),
                           f'{subject} (a Claude session)'))
            continue
        m_email, m_name = _merger(repo, sha, heads)
        if m_email == me_email:
            continue
        if m_email:
            others.append((sha, m_name, f'{subject} (a Claude session they merged)'))
        else:
            unsure.append((sha, url, subject))
    return others, unsure


def _new_commits(repo, heads, tips, told_at):
    """Every non-merge commit on a watched branch that no tip the person was
    told about already reaches."""
    known = [t for t in tips.values()
             if t and git(repo, 'cat-file', '-e', f'{t}^{{commit}}')[0] == 0]
    args = ['log', '--no-merges', '--format=%H%x1f%ae%x1f%an%x1f%s%x1f%b%x1e',
            *sorted(set(heads.values()))]
    if known:
        args += ['--not', *known]
    if len(known) < len([t for t in tips.values() if t]) and told_at:
        # A tip this clone does not hold (a shallow clone, a rewritten
        # branch): bound the window by time instead of reading all history.
        args.insert(1, f'--since={told_at}')
    code, out = git(repo, *args)
    if code != 0:
        return None
    commits = []
    for rec in out.split('\x1e'):
        parts = rec.strip('\n').split('\x1f')
        # git() strips its output, and Python counts \x1e and \x1f as
        # whitespace: the LAST commit, when its body is empty, arrives
        # without its trailing separator, and was dropped (2026-10-08, a
        # one-commit report of a colleague's commit with no body said
        # "nobody else changed anything").
        if len(parts) == 4:
            parts.append('')
        if len(parts) == 5 and parts[0]:
            commits.append(tuple(parts))
    return commits


# ---------------------------------------------------------------- the report

def _block(repo_name, since, others, unsure):
    """The text the reply gate hands the session on its first prompt."""
    lines = [f'WHAT OTHERS DID IN {repo_name} since you were last told '
             f'({since.strftime("%A %Y-%m-%d %H:%M") if since else "the first record"}) '
             f'-- {len(others) + len(unsure)} commit(s) by people other than you.',
             '',
             'OPEN YOUR FIRST REPLY WITH THIS, before answering the question: a '
             "short summary in What's New style -- about three bullets, each "
             'opening with its key phrase in bold, saying who did it and what '
             'it changes for the person, any change to a rule or to how sessions '
             'behave always named -- then answer. Say it once; it is not repeated '
             'in later replies (the others-did practice, in the ladder set).',
             '']
    by_who = {}
    for sha, who, subject in others:
        by_who.setdefault(who, []).append((sha, subject))
    # Each person gets a fair share of the lines, never fewer than five, so
    # one busy colleague cannot crowd a quieter one out of the report.
    share = max(5, MAX_LINES // max(1, len(by_who)))
    for who, items in by_who.items():
        lines.append(f'{who} -- {len(items)} commit(s):')
        for sha, subject in items[:share]:
            lines.append(f'  {sha[:9]}  {subject}')
        if len(items) > share:
            lines.append(f'  ... and {len(items) - share} more; `git log` names them all')
    if unsure:
        lines += ['', 'Signed only by Claude, owner not settled here -- open each '
                  'session link with get_session first: one that opens from this '
                  "account is the person's own, so leave it out; one that does "
                  "not is someone else's:"]
        for sha, url, subject in unsure[:MAX_LINES]:
            lines.append(f'  {sha[:9]}  {subject}  ({url or "no session link"})')
    return '\n'.join(lines) + '\n'


def check(root=None, no_fetch=False, no_push=False, user_config=None, now=None,
          land=None):
    """-> (status, lines). status: 'alert' (a report is pending for the
    first prompt), 'ok' (nothing to tell, or not yet), 'unknown'."""
    repo = pathlib.Path(root).resolve() if root else REPO
    try:
        me = pi.declared_identity(repo, user_config=user_config)
    except pi.NoDeclaredIdentity:
        return 'unknown', ["no identity is declared, so other people's work "
                           "cannot be told apart from yours"]
    now = now or precedent_time.now(repo)
    land = land or landing(repo, user_config)
    branches = watched_branches(repo)
    if not no_fetch:
        fetched = _fetch(repo, branches)
        if fetched is None or _fetch_mark(repo) is None:
            return 'unknown', ['could not reach origin -- what others did is '
                               'unknown this session']
    heads = _heads(repo, branches)
    if not heads:
        return 'unknown', ['none of ' + ', '.join(branches) + ' resolves here']

    registry = _read_shared(repo, land)
    seen_by = registry.setdefault('seen_by', {})
    key = identity_key(me)
    local = _read_local(repo).get(key)
    row = _later_row(seen_by.get(key), local)

    def record(note):
        new = {'told_at': now.isoformat(timespec='seconds'), 'tips': dict(heads),
               'note': note}
        seen_by[key] = new
        registry['_comment'] = [
            'What each person was last told about other people\'s commits,',
            'keyed by a slug of their declared name (never their email: this',
            'file is public). told_at is when; tips are the branch tips that',
            'report covered. Written by tools/precedent_others_did.py onto',
            f'origin\'s {MARK_REF}, outside every branch, never through',
            'anyone\'s working tree.',
        ]
        if not no_push:
            ok, phrase = publish(repo, land, registry, me,
                                 f'Others-did mark: {me.get("name") or key} told '
                                 f'through {now.strftime("%Y-%m-%d %H:%M")}')
            if ok:
                return phrase
        else:
            phrase = '--no-push'
        notes = _read_local(repo)
        notes[key] = new
        saved = _write_local(repo, LOCAL_NOTE, json.dumps(notes, indent=2) + '\n')
        return (f'{phrase}; kept in this container only'
                if saved else f'{phrase}; not recorded, so it may repeat')

    if not row:
        outcome = record('baseline -- first run for this person')
        return 'ok', [f'first run for {me.get("name") or key}: baselined at '
                      f'the current tips ({outcome}); reports start tomorrow']

    hour = me.get(HOUR_SETTING, DEFAULT_HOUR)
    try:
        hour = int(hour)
    except (TypeError, ValueError):
        hour = DEFAULT_HOUR
    start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    told_at = _parse_time(row.get('told_at'))
    if now < start:
        return 'ok', [f'before {hour:02d}:00 -- the day\'s report waits until then']
    if told_at and told_at >= start:
        return 'ok', [f'already told today at {told_at.strftime("%H:%M")}']

    commits = _new_commits(repo, heads, row.get('tips') or {}, row.get('told_at'))
    if commits is None:
        return 'unknown', ['could not read the history since the last report']
    others, unsure = classify(repo, commits, me.get('email'), heads)
    since = told_at.strftime('%Y-%m-%d %H:%M') if told_at else 'the first record'
    if not others and not unsure:
        # Nothing is written: the mark records what the person was TOLD.
        return 'ok', [f'nobody else changed anything since {since}']

    _, url = git(repo, 'remote', 'get-url', 'origin')
    repo_name = re.sub(r'\.git$', '', url.rstrip('/').split('github.com/')[-1]) \
        if url else repo.name
    block = _block(repo_name, told_at, others, unsure)
    pending_ok = _write_local(repo, PENDING, block)
    outcome = record('reported') if pending_ok else 'not recorded: no pending file'
    who = ', '.join(sorted({w for _, w, _ in others})) or 'unsettled Claude sessions'
    lines = [f'{len(others) + len(unsure)} commit(s) by others since {since} '
             f'({who}); the first reply opens with them ({outcome})']
    if not pending_ok:
        lines.append(block)
    return 'alert', lines


def remind(root=None, user_config=None):
    """For the reply gate: the pending block, once, then gone. Reads one local
    file; never fetches, so a reply costs nothing when there is no news."""
    repo = pathlib.Path(root).resolve() if root else REPO
    if off_ladder(repo, user_config):
        return None
    path = repo / PENDING
    try:
        text = path.read_text(encoding='utf-8')
        path.unlink()
    except OSError:
        return None
    return text.strip() or None


def off_ladder(root, user_config=None):
    """True for a person off the ladder: the ladder set is what turns this on."""
    try:
        import precedent_ladder
        return precedent_ladder.ladder_in_force(root, user_config) is False
    except Exception:                                             # noqa: BLE001
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--no-fetch', action='store_true')
    parser.add_argument('--no-push', action='store_true')
    args = parser.parse_args()
    if off_ladder(REPO):
        return 0
    try:
        status, lines = check(no_fetch=args.no_fetch, no_push=args.no_push)
    except Exception as exc:                                      # noqa: BLE001
        status, lines = 'unknown', [f'did not run ({exc})']
    prefix = {'ok': 'others-did', 'alert': 'OTHERS-DID',
              'unknown': 'others-did UNKNOWN'}[status]
    for i, line in enumerate(lines):
        print(f'{prefix}: {line}' if i == 0 else line)
    return 0


if __name__ == '__main__':
    sys.exit(main())
