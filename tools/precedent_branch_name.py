#!/usr/bin/env python3
"""The name for a session's feature branch, built the same way every time -- `<date>-<username>-<slug>-<session>-<random>`, the session part being the end of the session's ID

precedent_branch_name.py -- the name for a session's feature branch, built
the same way every time.

    2026-10-11-themorgan-branch-naming-convention-awpkv-q7m2x
    <date>-<username>-<slug>-<session>-<random>

  date     the day the branch is made, in the person's zone (precedent_time)
  username the person's GitHub username, lowercased, as declared in their
           identity.json ("github") or PRECEDENT_GITHUB_USER
  slug     what the work is, from the words given, lowercased, at most six
  session  the last five characters of the session's ID, lowercased, so the
           branch leads back to the session that made it
  random   five random characters, on every name, so two branches one
           session makes on the same day with the same slug never clash

EVERY NAME ENDS IN BOTH (Morgan, 2026-10-11, strength: decided: "we should
update the structure, the formula from date slug session ID to date slug
session ID, random characters"). Until then a name ended at the session
part, and five random characters were added only when that name was
already taken -- so a session's first Promote copy of the day was
`...-promote-to-main-y1ktn` and every later one `...-promote-to-main-y1ktn-
mijf2`, two shapes in use for the same kind of branch. Now there is one
shape, and a name that is somehow taken anyway gets fresh random
characters in the same place, never a third group.

THE RULE (Morgan, 2026-10-01, strength: decided): a branch's name should say
when it is from, what it is about, and which session made it. Until then a
session either took the name the harness gave it when it opened, before
anyone knew the task (`claude/hopeful-carson-yy42sb`), or typed its own
"random" suffix, and three branches in BestPractice ended up with the same
one (`-7qk2`). A model choosing random characters repeats itself; this tool
is the one place the name is built, so it cannot drift.

WHERE THE ID COMES FROM. Claude Code's cloud sessions carry it in
CLAUDE_CODE_REMOTE_SESSION_ID, read by precedent_detect.this_session_id()
(the same ID a commit's session trailer carries). Anywhere it is missing --
a local run, another harness -- the session part is five random characters
instead, and the tool says so on stderr. A name already taken, on origin
or by a local branch, gets new random characters in the last part. Local
branches count too (2026-10-11): a rollout made an update branch, merged
it, and the next day's run got the same name back from origin's silence --
and `git switch -c` refused it, because the merged branch was still there
locally.

THE USERNAME, RIGHT AFTER THE DATE (Morgan, 2026-10-11, strength:
decided: "what if we add to the branch name convention the name of the
user ... I think the username should be first"). A branch list then reads
when, who, what, and `branches/all?query=themorgan` finds one person's
branches. Git never knows a GitHub username -- a commit carries a name and
an address -- so it is read from the person's declaration
(precedent_identity). With none declared, the name leaves that part out,
and the tool asks GitHub who this session is signed in as and says how to
record it: `--set-github LOGIN` writes it into the individual set's
identity.json, once the person agrees (Morgan, the same day: "add in the
tool to look it up with github's 'who am I' and offer to write it into
the identity.json").

ONLY ON THE LADDER (Morgan, 2026-10-11, strength: decided: "Our branch
naming conventions should be in force for people who use ladders, not
everyone else"). The rule is the ladder's (precedent-shared-ladder's act);
so the push check's refusal and notes, and the first-commit note below,
say nothing to a person off it (conventions_in_force). The tool itself
still names a branch for anyone who runs it, and for the engine's own
branches (Update Vendors, Promote), which need some unique name.

THE HARNESS'S OWN BRANCH. Claude Code on the web opens a session on a
branch it named before the task was known: two random words
(`claude/eager-volta-hfk5k3`) or, when the session starts from a task, a
few words of it (`claude/branch-naming-enforcement-cjm44t`), then six
characters. Both are let through (a session that kept one can always
push), and both are said: at the first commit on one, once per branch
(commit_note, from branch-name-commit-note.sh), and at every push to one
(harness_name_note). The first commit is the moment every building session
passes through, whatever word started the building; on 2026-10-11 a whole
feature in a consumer went up and landed on claude/eager-volta-hfk5k3
after a go-ahead ("Great") that never loaded act.

NO PREFIX (Morgan, 2026-10-07, strength: decided: "many of your temp github
[branches] you create start with 'claude/' - I think update the rule to
eliminate that prefix"). Until then a name began `claude/` under Claude Code
and `session/` elsewhere, on the theory that a harness might only let a
session push to its own prefix. Claude Code's cloud harness does not: a
Promote has pushed `to-main-DATE`, `pre-staging` and `staging` from it all
along. The date leads, so a branch list sorts by day. --prefix still adds
one, for a harness that does restrict pushes.

Run:
  python3 tools/precedent_branch_name.py branch naming convention
  git switch -c "$(python3 tools/precedent_branch_name.py branch naming convention)"
  python3 tools/precedent_branch_name.py --no-check some words   # skip asking origin and local branches
  python3 tools/precedent_branch_name.py --set-github LOGIN      # record the username, once the person agrees
  python3 tools/precedent_branch_name.py --commit-note           # the first-commit note, if one is due

Exit status: 0 a name was printed (any note is on stderr); 2 no usable slug.
"""
import argparse
import json
import os
import re
import secrets
import string
import subprocess
import sys
from pathlib import Path

ID_LEN = 5
MAX_SLUG_WORDS = 6
ALPHABET = string.ascii_lowercase + string.digits


def slugify(words):
    """-> 'branch-naming-convention' from any mix of words and punctuation,
    '' when nothing usable is left. Lowercase only: git keeps branches as
    files, and on a case-insensitive disk (a Mac's default) two names that
    differ only by case collide."""
    parts = re.split(r'[^a-z0-9]+', ' '.join(words).lower())
    return '-'.join([p for p in parts if p][:MAX_SLUG_WORDS])


def random_id(n=ID_LEN):
    return ''.join(secrets.choice(ALPHABET) for _ in range(n))


def session_id_tail(n=ID_LEN):
    """-> the last n characters of this session's ID, lowercased, or '' when
    the harness does not say. Reads the ID where precedent_detect does, so
    there is one place that knows where a session ID lives."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from precedent_detect import this_session_id
        sid = this_session_id()
    except Exception:  # a partial engine copy: fall back, never fail
        raw = os.environ.get('CLAUDE_CODE_REMOTE_SESSION_ID', '').strip()
        sid = raw[4:] if raw.startswith('cse_') else raw
    sid = sid[len('session_'):] if sid.startswith('session_') else sid
    tail = sid[-n:].lower()
    return tail if len(tail) == n and all(c in ALPHABET for c in tail) else ''


def _today():
    """The person's date, never the container's (practice:
    timestamps-carry-offset)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import precedent_time  # noqa: E402
    return precedent_time.today()


def default_prefix():
    return ''


_USERNAME_RE = re.compile(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?')


def github_user(repo='.'):
    """-> the person's GitHub username, lowercased, from their declaration
    (precedent_identity: PRECEDENT_GITHUB_USER, then this repo's or the
    individual set's identity.json), or '' when none is declared. Never
    from git: git knows a name and an address, never a username."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    user = ''
    try:
        import precedent_identity
        user = precedent_identity.declared_identity(repo).get('github') or ''
    except Exception:  # NoDeclaredIdentity, or a partial engine copy
        pass
    user = (user or os.environ.get('PRECEDENT_GITHUB_USER', '')).strip()
    user = user.lstrip('@').lower()
    return user if _USERNAME_RE.fullmatch(user) else ''


def github_login_from_github():
    """-> the login GitHub says this session's credential belongs to (its
    "who am I", GET /user), or '' when it cannot be asked. One call, made
    only when no username is declared, through github_budget so it is
    counted."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import github_budget
        data, err = github_budget.call('user')
    except Exception:
        return ''
    login = (data or {}).get('login') if isinstance(data, dict) else ''
    login = str(login or '').strip().lower()
    return login if _USERNAME_RE.fullmatch(login) else ''


def identity_file(repo='.'):
    """-> the identity.json a username belongs in: this repository's own
    when it is an individual set, else the individual set the user-level
    config names; None when neither is there."""
    own = Path(repo).resolve() / 'identity.json'
    if own.is_file():
        return own
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import precedent_identity as pi
        cfg_path = Path(os.environ.get(pi.USER_CONFIG_ENV,
                                       str(pi.DEFAULT_USER_CONFIG))).expanduser()
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
        path = (cfg.get('individual') or {}).get('path')
    except Exception:
        return None
    f = Path(path).expanduser() / 'identity.json' if path else None
    return f if f and f.is_file() else None


def set_github(login, repo='.'):
    """Writes "github": login into identity_file(repo). -> (path, error).
    Run only once the person has agreed: it is their declaration."""
    login = (login or '').strip().lstrip('@').lower()
    if not _USERNAME_RE.fullmatch(login):
        return None, f'{login!r} is not a GitHub username'
    f = identity_file(repo)
    if f is None:
        return None, ('no identity.json found -- neither in this repository '
                      'nor in an individual set the user-level config names')
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        return None, f'{f} did not read ({e})'
    if not isinstance(data, dict):
        return None, f'{f} is not a JSON object'
    data['github'] = login
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                 encoding='utf-8')
    return f, None


def missing_user_note(login=''):
    """-> what to say when no username is declared; `login` is what GitHub
    answered, when it was asked."""
    if login:
        found = (f'GitHub says this session is signed in as {login}. Offer to '
                 f'record it, and once the person agrees: python3 '
                 f'tools/precedent_branch_name.py --set-github {login} '
                 f'(then commit and push identity.json where it lives)')
    else:
        found = ('Find it with GitHub\'s "who am I" (get_me), offer to record '
                 'it, and once the person agrees: python3 '
                 'tools/precedent_branch_name.py --set-github <username>')
    return (f'no GitHub username is declared, so this name leaves it out. '
            f'{found}.')


def conventions_in_force(repo='.'):
    """-> True when this naming rule binds the person working in `repo`:
    the ladder is in force for them (precedent_ladder). An engine copy with
    no precedent_ladder.py predates the opt-in and keeps the old answer."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import precedent_ladder
    except ImportError:
        return True
    try:
        return bool(precedent_ladder.ladder_in_force(repo))
    except Exception:
        return True


def on_origin(name, repo='.', remote='origin'):
    """-> True the branch exists on the remote, False it does not, None the
    remote could not be asked. `ls-remote --exit-code` says 2 for "no such
    branch", which is what tells an absent branch from an unreachable remote
    (practice: fresh-before-write records the same distinction)."""
    try:
        r = subprocess.run(['git', '-C', str(repo), 'ls-remote', '--exit-code',
                            '--heads', remote, f'refs/heads/{name}'],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode == 0:
        return True
    return False if r.returncode == 2 else None


def local_branch(name, repo='.'):
    """-> True when this checkout already has a local branch called `name`."""
    try:
        r = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', '-q',
                            f'refs/heads/{name}'], capture_output=True, text=True,
                           timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


def taken(name, repo='.', remote='origin'):
    """-> True a local branch or the remote already has `name`, False
    neither does, None the remote could not be asked and nothing local has
    it. Every caller that names a branch asks this, never on_origin alone."""
    if local_branch(name, repo):
        return True
    return on_origin(name, repo, remote)


MAX_DRAWS = 20


def build(words, date=None, prefix=None, tail=None, exists=None, rand=None,
          user=None):
    """-> (name, notes). `exists(name)` answers True/False/None as taken()
    does; None skips the check. `tail` None means read the session ID;
    `user` None means read the declared username ('' leaves it out);
    `rand` None means draw the last part at random (a test passes one)."""
    slug = slugify(words)
    if not slug:
        raise ValueError('no usable words for the slug -- give a few words '
                         'saying what the work is')
    date = date or _today()
    prefix = default_prefix() if prefix is None else prefix
    notes = []
    tail = session_id_tail() if tail is None else tail
    if not tail:
        tail = random_id()
        notes.append(f'no session ID found, so the session part ({tail}) is '
                     f'random and leads to no session')
    user = github_user() if user is None else user
    if user:
        slug = f'{user}-{slug}'
    name = f'{prefix}{date}-{slug}-{tail}-{rand or random_id()}'
    if exists is not None:
        found = exists(name)
        if found is None:
            notes.append(f'could not ask origin whether {name} already exists '
                         f'(no local branch has it)')
        for _ in range(MAX_DRAWS):
            if not found:
                break
            taken_name = name
            name = f'{prefix}{date}-{slug}-{tail}-{random_id()}'
            notes.append(f'{taken_name} is already taken (a local branch or '
                         f'origin has it); drew {name.rsplit("-", 1)[1]} instead')
            found = exists(name)
        else:
            if found:
                raise ValueError(f'every name drawn for {date}-{slug}-{tail} was '
                                 f'taken -- the existence check is answering '
                                 f'"taken" for everything')
    return name, notes


# A name the cloud harness gave the session before the task was known:
# words and six characters -- two random words (`claude/peaceful-ritchie-
# 3u31td`) or a few words of the task (`claude/branch-naming-enforcement-
# cjm44t`). Left alone, per the rule above; the session's own branches are
# made by build(). Until 2026-10-11 only the two-word shape with a digit in
# its last part counted, so the push check refused the task-word names --
# this very session's among them -- and the one random ending in seven with
# no digit in it.
_HARNESS_NAME_RE = re.compile(
    r'(?:claude|session)/(?!\d{4}-\d{2}-\d{2}-)[a-z0-9]+(?:-[a-z0-9]+)+-[a-z0-9]{6}')
_TOOL_NAME_RE = re.compile(r'\d{4}-\d{2}-\d{2}-([a-z0-9]+(?:-[a-z0-9]+)+)')
# What is judged at all: the old prefixes, and any name that opens with a
# date, the shape build() writes.
_JUDGED_RE = re.compile(r'(?:claude/|session/|\d{4}-\d{2}-\d{2}-)')


def is_harness_name(name):
    """True for a branch name the cloud harness gave a session."""
    return bool(_HARNESS_NAME_RE.fullmatch(name or ''))


def name_refusal(name, tail=None, user=None):
    """-> why `name` is not a branch this tool made, or None when it is (or
    is not a session branch at all). Morgan, 2026-10-06 (strength: decided):
    "how can we make sure that you always use the new format for temporary
    branches?" -- sessions, and the agents they start, typed date-and-topic
    names by hand that lead back to no session, and nothing refused them.
    The push gate asks this of every new branch a push creates, on the
    ladder only (conventions_in_force).

    Judged: names that open with a date, or sit under `claude/` or
    `session/`. Passed: a harness-given name; a
    `<date>-<username>-<slug>-<session>-<random>` name whose username is
    this person's, whose session part is this session's and whose last part
    is five characters. With no session ID to compare, any two
    five-character last parts pass: build() is random then. With no
    username declared, a name without one passes. Refused since 2026-10-11:
    the older shape that ended at the session part, which build() no longer
    writes, and, where a username is declared, a name without it. A
    `claude/<date>-...` name is refused since 2026-10-07: build() no longer
    writes the prefix, so a name carrying it was typed."""
    if not _JUDGED_RE.match(name):
        return None
    if is_harness_name(name):
        return None
    tail = session_id_tail() if tail is None else tail
    user = github_user() if user is None else user
    m = _TOOL_NAME_RE.fullmatch(name)
    if m:
        rest = m.group(1)
        if not user or rest.startswith(f'{user}-'):
            parts = rest[len(user) + 1:].split('-') if user else rest.split('-')
            if len(parts) >= 3 and len(parts[-1]) == ID_LEN and (
                    parts[-2] == tail if tail else len(parts[-2]) == ID_LEN):
                return None
    who = '<your GitHub username>-' if not user else f'{user}-'
    return (f'{name} was not made by tools/precedent_branch_name.py: a session '
            f'branch is named <date>-{who}<what it is>-<the last five '
            f'characters of this session\'s ID>-<five random characters>, so '
            f'it leads back to the person and the session. Rename it before '
            f'pushing: git branch -m {name} '
            f'"$(python3 tools/precedent_branch_name.py <a few words>)"')


def harness_name_note(name):
    """-> what to say about a push to the branch the harness named when the
    session opened, or None for any other name.

    Never a refusal: a session that kept that name must still be able to
    push its work (name_refusal lets it through for that reason). But act's
    Rule has the session make its own named branch, and a session that
    forgot was told nothing: on 2026-10-11 a whole build went up under
    claude/amazing-lamport-l5eivc, and Morgan asked why. So every push to
    one says so, once per push, in words the push gate hands the session."""
    if not is_harness_name(name):
        return None
    return (f'{name} is the name the harness gave this session when it '
            f'opened, before the task was known. act\'s Rule: make the '
            f'session\'s named branch and work there -- git switch -c '
            f'"$(python3 tools/precedent_branch_name.py <a few words>)" -- '
            f'then push that. This push goes ahead.')


COMMIT_NOTE_MARKS = 'precedent-branch-name-noted'


def _git(repo, *args):
    try:
        r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return ''
    return r.stdout.strip() if r.returncode == 0 else ''


def commit_note(repo='.', branch=None):
    """-> what to say before the first commit on the harness's branch, or
    None. Said once per branch (a marker under the checkout's .git), only
    where a session ID says a cloud session is running, and only on the
    ladder. Never a refusal: the commit goes ahead, and `git switch -c`
    afterwards carries every commit made so far onto the named branch.

    Why the first commit (2026-10-11): act loads when a person says "Act"
    or "Build", and a go-ahead in other words ("Great") never loads it; the
    push note comes after the work is built. Every building session
    commits, whatever word started it."""
    if not session_id_tail():
        return None
    branch = branch or _git(repo, 'symbolic-ref', '--short', '-q', 'HEAD')
    if not is_harness_name(branch):
        return None
    if not conventions_in_force(repo):
        return None
    git_dir = _git(repo, 'rev-parse', '--absolute-git-dir')
    if not git_dir:
        return None
    mark = Path(git_dir) / COMMIT_NOTE_MARKS / branch.replace('/', '__')
    if mark.exists():
        return None
    try:
        mark.parent.mkdir(parents=True, exist_ok=True)
        mark.write_text(branch + '\n', encoding='utf-8')
    except OSError:
        pass
    return (f'This commit is going onto {branch}, the branch the harness '
            f'named when this session opened, before the task was known. On '
            f'the ladder a session works on its own named branch (act): '
            f'git switch -c "$(python3 tools/precedent_branch_name.py <a few '
            f'words>)" -- run it now, and every commit made so far comes '
            f'with it. This commit goes ahead; this note is said once per '
            f'branch.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('words', nargs='*', help='a few words saying what the work is')
    ap.add_argument('--prefix', default='', help="default: none; the name opens with the date")
    ap.add_argument('--repo', default='.', help='checkout whose origin is asked')
    ap.add_argument('--no-check', action='store_true', help='do not ask origin')
    ap.add_argument('--set-github', metavar='LOGIN',
                    help='write "github": LOGIN into the identity.json the '
                         'username belongs in, once the person agrees')
    ap.add_argument('--commit-note', action='store_true',
                    help='print the first-commit note for this checkout, if '
                         'one is due (branch-name-commit-note.sh)')
    args = ap.parse_args(argv)
    if args.set_github:
        path, err = set_github(args.set_github, args.repo)
        if err:
            print(f'precedent_branch_name: {err}', file=sys.stderr)
            return 1
        print(f'precedent_branch_name: wrote "github": '
              f'"{args.set_github.strip().lstrip("@").lower()}" into {path}; '
              f'commit and push it there.', file=sys.stderr)
        return 0
    if args.commit_note:
        note = commit_note(args.repo)
        if note:
            print(note)
        return 0
    if not args.words:
        ap.error('give a few words saying what the work is')
    exists = None if args.no_check else (lambda n: taken(n, args.repo))
    user = github_user(args.repo)
    try:
        name, notes = build(args.words, prefix=args.prefix, exists=exists,
                            user=user)
    except ValueError as e:
        print(f'precedent_branch_name: {e}', file=sys.stderr)
        return 2
    if not user:
        notes.append(missing_user_note(github_login_from_github()))
    for n in notes:
        print(f'precedent_branch_name: {n}', file=sys.stderr)
    print(name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
