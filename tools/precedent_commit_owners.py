#!/usr/bin/env python3
"""Says who made each commit in a range -- a person by author email, a commit signed only by Claude by its session's owner or by whoever merged it -- and lists them by person; the daily report a set ships and Update Vendors' note of what others changed upstream both read it

precedent_commit_owners.py -- whose commit is this?

Two readers need the same answer. Update Vendors says what OTHER people
changed upstream in what an update brings in; a practice set may ship a
daily report of what others landed in a repository. Both sort commits the
same way, so the sorting lives here once, and names no set.

WHAT COUNTS AS SOMEONE ELSE'S. A commit whose author email is not the
person's. A commit signed only by Claude is attributed through its
`Claude-Session:` trailer: a session that also authored commits under a
person's own name is that person's; otherwise the first person who merged
it in owns it (a session's pull request is merged by whoever ran it, in
practice). Measured 2026-10-08 against `get_session`: the two sessions
whose owner the trailer did not settle were the two whose pull requests
someone else merged. What neither rule settles is listed with its session
link, for the session to check. Merge commits are left out by the callers:
merging is not the work, and the merged commits are counted on their own.

Moved out of the others-did report's engine tool on 2026-10-17, when that
report moved into the set that ships it (spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md
part 3).
"""
import re
import subprocess

# The most commit lines one listing prints. The session summarises them; a
# list long enough to push a hook's output past what the harness shows is a
# failure a report of this kind once had.
MAX_LINES = 40


def git(repo, *args):
    """-> (returncode, stdout)."""
    proc = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                          text=True)
    return proc.returncode, proc.stdout.strip()


BOT_EMAILS = {'noreply@anthropic.com'}
SESSION_RE = re.compile(r'Claude-Session:\s*(https://claude\.ai/code/session_\w+)')


def _is_bot(email):
    return (email or '').lower() in BOT_EMAILS


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


LOG_FORMAT = '--format=%H%x1f%ae%x1f%an%x1f%s%x1f%b%x1e'


def records(out):
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


def commit_listing(others, unsure):
    """The commits by person, to choose from: the part of the report the
    morning block and Update Vendors' upstream block share."""
    lines = ['The commits, to choose from -- not to copy into the reply:', '']
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

