#!/usr/bin/env python3
"""The name for a session's feature branch, built the same way every time -- `claude/<date>-<slug>-<id>`, the id being the end of the session's ID, or random characters when there is none

precedent_branch_name.py -- the name for a session's feature branch, built
the same way every time.

    claude/2026-10-01-branch-naming-convention-awpkv
    <prefix><date>-<slug>-<id>

  date    the day the branch is made, in the person's zone (precedent_time)
  slug    what the work is, from the words given, lowercased, at most six
  id      the last five characters of the session's ID, lowercased, so the
          branch leads back to the session that made it

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
a local run, another harness -- the id is five random characters instead,
and the tool says so on stderr. The same happens when the name is already
on origin: one session making two branches on the same day with the same
slug is the only realistic way that occurs.

THE PREFIX is `claude/` under Claude Code (CLAUDECODE=1 in its shell) and
`session/` anywhere else; --prefix overrides it. A harness that only lets a
session push to its own prefix needs the name to start with it.

Run:
  python3 tools/precedent_branch_name.py branch naming convention
  git switch -c "$(python3 tools/precedent_branch_name.py branch naming convention)"
  python3 tools/precedent_branch_name.py --no-check some words   # skip asking origin

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
    return 'claude/' if os.environ.get('CLAUDECODE') == '1' else 'session/'


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


def build(words, date=None, prefix=None, tail=None, exists=None):
    """-> (name, notes). `exists(name)` answers True/False/None as on_origin
    does; None skips the check. `tail` None means read the session ID."""
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
        notes.append(f'no session ID found, so the last part ({tail}) is '
                     f'random and leads to no session')
    name = f'{prefix}{date}-{slug}-{tail}'
    if exists is not None:
        found = exists(name)
        if found is None:
            notes.append(f'could not ask origin whether {name} already exists')
        while found:
            extra = random_id()
            notes.append(f'{name} is already on origin; added {extra}')
            name = f'{prefix}{date}-{slug}-{tail}-{extra}'
            found = exists(name)
    return name, notes


# A name the cloud harness gave the session before the task was known:
# two words and a mixed id (`claude/peaceful-ritchie-3u31td`). Left alone,
# per the rule above; the session's own branches are made by build().
_HARNESS_NAME_RE = re.compile(r'(?:claude|session)/[a-z]+-[a-z]+-([a-z0-9]{5,8})')
_TOOL_NAME_RE = re.compile(r'(?:claude|session)/\d{4}-\d{2}-\d{2}-([a-z0-9]+(?:-[a-z0-9]+)+)')


def name_refusal(name, tail=None):
    """-> why `name` is not a branch this tool made, or None when it is (or
    is not a session branch at all). Morgan, 2026-10-06 (strength: decided):
    "how can we make sure that you always use the new format for temporary
    branches?" -- sessions, and the agents they start, typed date-and-topic
    names by hand that lead back to no session, and nothing refused them.
    The push gate asks this of every new branch a push creates.

    Judged: names under `claude/` or `session/`. Passed: a harness-given
    name (two words and an id with a digit in it); a `<date>-<slug>-<id>`
    name whose id is this session's (or, after a clash on origin, whose
    second-to-last part is, as build() writes it). With no session ID to
    compare, any five-character last part passes: build() is random then."""
    if not name.startswith(('claude/', 'session/')):
        return None
    m = _HARNESS_NAME_RE.fullmatch(name)
    if m and any(c.isdigit() for c in m.group(1)):
        return None
    tail = session_id_tail() if tail is None else tail
    m = _TOOL_NAME_RE.fullmatch(name)
    if m:
        parts = m.group(1).split('-')
        if tail:
            if parts[-1] == tail or (len(parts) >= 3 and parts[-2] == tail
                                     and len(parts[-1]) == ID_LEN):
                return None
        elif len(parts[-1]) == ID_LEN:
            return None
    return (f'{name} was not made by tools/precedent_branch_name.py: a session '
            f'branch is named claude/<date>-<what it is>-<the last five '
            f'characters of this session\'s ID>, so it leads back to the '
            f'session. Rename it before pushing: git branch -m {name} '
            f'"$(python3 tools/precedent_branch_name.py <a few words>)"')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('words', nargs='+', help='a few words saying what the work is')
    ap.add_argument('--prefix', help="default: 'claude/' under Claude Code, else 'session/'")
    ap.add_argument('--repo', default='.', help='checkout whose origin is asked')
    ap.add_argument('--no-check', action='store_true', help='do not ask origin')
    args = ap.parse_args(argv)
    exists = None if args.no_check else (lambda n: on_origin(n, args.repo))
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
