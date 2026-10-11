#!/usr/bin/env python3
"""The name for a session's feature branch, built the same way every time -- `<date>-<slug>-<session>-<random>`, the session part being the end of the session's ID

precedent_branch_name.py -- the name for a session's feature branch, built
the same way every time.

    2026-10-01-branch-naming-convention-awpkv-q7m2x
    <date>-<slug>-<session>-<random>

  date     the day the branch is made, in the person's zone (precedent_time)
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

Exit status: 0 a name was printed (any note is on stderr); 2 no usable slug.
"""
import argparse
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


def build(words, date=None, prefix=None, tail=None, exists=None, rand=None):
    """-> (name, notes). `exists(name)` answers True/False/None as taken()
    does; None skips the check. `tail` None means read the session ID;
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
# two words and a mixed id (`claude/peaceful-ritchie-3u31td`). Left alone,
# per the rule above; the session's own branches are made by build().
_HARNESS_NAME_RE = re.compile(r'(?:claude|session)/[a-z]+-[a-z]+-([a-z0-9]{5,8})')
_TOOL_NAME_RE = re.compile(r'\d{4}-\d{2}-\d{2}-([a-z0-9]+(?:-[a-z0-9]+)+)')
# What is judged at all: the old prefixes, and any name that opens with a
# date, the shape build() writes.
_JUDGED_RE = re.compile(r'(?:claude/|session/|\d{4}-\d{2}-\d{2}-)')


def name_refusal(name, tail=None):
    """-> why `name` is not a branch this tool made, or None when it is (or
    is not a session branch at all). Morgan, 2026-10-06 (strength: decided):
    "how can we make sure that you always use the new format for temporary
    branches?" -- sessions, and the agents they start, typed date-and-topic
    names by hand that lead back to no session, and nothing refused them.
    The push gate asks this of every new branch a push creates.

    Judged: names that open with a date, or sit under `claude/` or
    `session/`. Passed: a harness-given name (two words and an id with a
    digit in it); a `<date>-<slug>-<session>-<random>` name whose session
    part is this session's and whose last part is five characters. With no
    session ID to compare, any two five-character last parts pass: build()
    is random then. Refused since 2026-10-11: the older shape that ended at
    the session part, which build() no longer writes. A `claude/<date>-...`
    name is refused since 2026-10-07: build() no longer writes the prefix,
    so a name carrying it was typed."""
    if not _JUDGED_RE.match(name):
        return None
    m = _HARNESS_NAME_RE.fullmatch(name)
    if m and any(c.isdigit() for c in m.group(1)):
        return None
    tail = session_id_tail() if tail is None else tail
    m = _TOOL_NAME_RE.fullmatch(name)
    if m:
        parts = m.group(1).split('-')
        if len(parts) >= 3 and len(parts[-1]) == ID_LEN and (
                parts[-2] == tail if tail else len(parts[-2]) == ID_LEN):
            return None
    return (f'{name} was not made by tools/precedent_branch_name.py: a session '
            f'branch is named <date>-<what it is>-<the last five '
            f'characters of this session\'s ID>-<five random characters>, so '
            f'it leads back to the session. Rename it before pushing: git '
            f'branch -m {name} '
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
    m = _HARNESS_NAME_RE.fullmatch(name)
    if not (m and any(c.isdigit() for c in m.group(1))):
        return None
    return (f'{name} is the name the harness gave this session when it '
            f'opened, before the task was known. act\'s Rule: make the '
            f'session\'s named branch and work there -- git switch -c '
            f'"$(python3 tools/precedent_branch_name.py <a few words>)" -- '
            f'then push that. This push goes ahead.')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('words', nargs='+', help='a few words saying what the work is')
    ap.add_argument('--prefix', default='', help="default: none; the name opens with the date")
    ap.add_argument('--repo', default='.', help='checkout whose origin is asked')
    ap.add_argument('--no-check', action='store_true', help='do not ask origin')
    args = ap.parse_args(argv)
    exists = None if args.no_check else (lambda n: taken(n, args.repo))
    try:
        name, notes = build(args.words, prefix=args.prefix, exists=exists)
    except ValueError as e:
        print(f'precedent_branch_name: {e}', file=sys.stderr)
        return 2
    for n in notes:
        print(f'precedent_branch_name: {n}', file=sys.stderr)
    print(name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
