#!/usr/bin/env python3
"""precedent_whats_new.py -- the mechanics behind "What's new?".

A project keeps one running log of what changed in it, newest first:
WHATS_NEW.md at the root, or wherever precedent.json's `whats_new_path`
puts it. One entry per finished calendar day on which the production
branch (`main`) changed. The session writes the entries (that is judgment:
what was noteworthy, said plainly); this file does the mechanical half.

    python3 tools/precedent_whats_new.py            # status: where the log is,
                                                    # how far it runs, what is missing
    python3 tools/precedent_whats_new.py --days     # each finished day the log lacks,
                                                    # with what changed on main that day
                                                    # (add --full for each commit's first
                                                    # paragraph; `git show SHA` for the rest)
    python3 tools/precedent_whats_new.py --today    # what has changed on main today so far
    python3 tools/precedent_whats_new.py --mark YYYY-MM-DD
                                                    # the log now covers every day through
                                                    # this one (creates the file if needed)
    python3 tools/precedent_whats_new.py --check    # entries name no approver

THE ONE PIECE OF STATE is the log's own front matter, `checked_through:
<date>`. It answers both questions a run asks: which days to write, and
whether a run already happened today (checked through yesterday means it
did). It is read from the log as the production branch has it when that
is newer than this checkout's, so two sessions do not both write the same
days off a checkout that is behind.

A DAY is a calendar day in the REPOSITORY's timezone (precedent.json
`fallback_timezone`), never the person's: the log is shared, so its day
has to end at the same moment whoever writes it. It changed when the tip
of `main`'s first-parent line at that day's midnight differs from the tip
at the midnight before, and a commit that touches only the log itself
does not count -- the log landing on main would otherwise be news every
day after it. The first run, with no log yet, covers the last seven
finished days.

Standard library and precedent_time only, so it runs in any repo that
vendors the engine (practice: whats-new).
"""
import datetime
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # noqa: E402

DEFAULT_PATH = 'WHATS_NEW.md'
PRODUCTION = 'main'
FIRST_RUN_DAYS = 7
BODY_CHARS = 400
HEADER = ("# What's new\n\n"
          "A running log of what changed in this project, newest first: one "
          "entry per day on which something did.\n")

# Words that name an approval. An entry says what changed, never who
# approved or signed off on it.
APPROVAL = re.compile(r"\b(approved|approval|approver|signed[ -]off|sign-off|"
                      r"strength:|decided by|assented)\b", re.I)


def _git(root, *args, timeout=60):
    try:
        p = subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ''


def feed_path(root):
    """-> the log's path relative to `root`: precedent.json's
    `whats_new_path`, else WHATS_NEW.md."""
    try:
        data = json.loads((pathlib.Path(root) / 'precedent.json').read_text(encoding='utf-8'))
        rel = data.get('whats_new_path')
        if isinstance(rel, str) and rel.strip():
            return rel.strip()
    except (OSError, ValueError, AttributeError):
        pass
    return DEFAULT_PATH


def repo_zone(root):
    """-> (tzinfo, name): the repository's declared zone, else the zone
    precedent_time resolves, said as such."""
    name = precedent_time._repo_fallback_zone(root)
    if name and precedent_time.ZoneInfo is not None:
        try:
            return precedent_time.ZoneInfo(name), name
        except Exception:                                    # noqa: BLE001
            pass
    tz, name, _src = precedent_time.resolved(root)
    return tz, name


def production_ref(root):
    """-> 'origin/main' when this clone has it, else 'main', else None."""
    for ref in (f'origin/{PRODUCTION}', PRODUCTION):
        if _git(root, 'rev-parse', '--verify', '--quiet', ref)[0] == 0:
            return ref
    return None


def checked_through(text):
    """-> the `checked_through` date in a log's front matter, or None."""
    m = re.match(r'---\n(.*?)\n---(?:\n|$)', text or '', re.S)
    if not m:
        return None
    d = re.search(r'^checked_through:\s*(\d{4}-\d{2}-\d{2})\s*$', m.group(1), re.M)
    return datetime.date.fromisoformat(d.group(1)) if d else None


def read_state(root):
    """-> (text of the log here or '', checked_through): the later of this
    checkout's log and the production branch's."""
    rel = feed_path(root)
    path = pathlib.Path(root) / rel
    here = path.read_text(encoding='utf-8') if path.is_file() else ''
    best = checked_through(here)
    ref = production_ref(root)
    if ref:
        rc, there = _git(root, 'show', f'{ref}:{rel}')
        other = checked_through(there) if rc == 0 else None
        if other and (best is None or other > best):
            best = other
    return here, best


def _midnight(day, tz):
    return datetime.datetime.combine(day, datetime.time(0, 0), tzinfo=tz)


def _tip_before(root, ref, moment):
    rc, out = _git(root, 'rev-list', '-1', '--first-parent',
                   f'--before={moment.isoformat()}', ref)
    return out if rc == 0 and out else None


def _touches_only(root, sha, rel):
    rc, files = _git(root, 'diff-tree', '--no-commit-id', '--name-only', '-r',
                     '-m', '--first-parent', sha)
    names = {f for f in files.splitlines() if f.strip()}
    return bool(names) and names <= {rel}


def changes_between(root, ref, start, end):
    """-> {'commits': [(short, subject, body)], 'added': [paths]} for the
    first-parent line of `ref` between two moments, the log's own commits
    left out; None when nothing else changed."""
    rel = feed_path(root)
    old, new = _tip_before(root, ref, start), _tip_before(root, ref, end)
    if not new or old == new:
        return None
    rng = f'{old}..{new}' if old else new
    # The day is bounded on main's first-parent line, but on a tiered repo
    # every commit there is a Promote ("Promote staging into main (20
    # commits)"), which says nothing. What changed is every commit those
    # merges brought, so the listing reads them, merges left out.
    rc, log = _git(root, 'log', '--no-merges', '--format=%H%x1f%s%x1f%b%x1e', rng)
    commits = []
    for entry in (log.split('\x1e') if rc == 0 else []):
        parts = entry.strip('\n').split('\x1f')
        if len(parts) < 2 or not parts[0]:
            continue
        sha, subject = parts[0], parts[1]
        body = _prose(parts[2] if len(parts) > 2 else '')
        if _touches_only(root, sha, rel):
            continue
        commits.append((sha[:9], subject, body))
    if not commits:
        return None
    added = []
    if old:
        rc, names = _git(root, 'diff', '--name-only', '--diff-filter=A', old, new)
        added = [n for n in names.splitlines() if n and n != rel] if rc == 0 else []
    # A new document is often the day's news (a new guide, a philosophy
    # note) without a commit message saying so; list those first.
    added.sort(key=lambda n: (not n.endswith('.md'), n))
    return {'commits': commits, 'added': added}


TRAILER = re.compile(r'^(Session|Claude-Session|Co-Authored-By|Signed-off-by):', re.I)


def _prose(body):
    """-> a commit body's first paragraph, trailers dropped, capped."""
    lines = [l for l in body.strip().splitlines() if not TRAILER.match(l.strip())]
    para = []
    for l in lines:
        if not l.strip():
            if para:
                break
            continue
        para.append(l.strip())
    text = ' '.join(para)
    return text if len(text) <= BODY_CHARS else text[:BODY_CHARS].rstrip() + ' ...'


def missing_days(root, today=None):
    """-> (tz name, checked_through, [(date, changes)]): every finished day
    after checked_through (or the last FIRST_RUN_DAYS, with no log yet) on
    which the production branch changed."""
    tz, name = repo_zone(root)
    today = today or datetime.datetime.now(tz).date()
    _text, through = read_state(root)
    ref = production_ref(root)
    first = (through + datetime.timedelta(days=1)) if through else \
        today - datetime.timedelta(days=FIRST_RUN_DAYS)
    out = []
    if ref is None:
        return name, through, out
    day = first
    while day < today:
        ch = changes_between(root, ref, _midnight(day, tz),
                             _midnight(day + datetime.timedelta(days=1), tz))
        if ch:
            out.append((day, ch))
        day += datetime.timedelta(days=1)
    return name, through, out


def mark(root, day, today=None):
    """Record that the log covers every finished day through `day`.
    -> (ok, message). Never a day that has not finished."""
    tz, _name = repo_zone(root)
    today = today or datetime.datetime.now(tz).date()
    if day >= today:
        return False, f'{day} has not finished yet; only a finished day can be covered'
    path = pathlib.Path(root) / feed_path(root)
    text = path.read_text(encoding='utf-8') if path.is_file() else ''
    front = f'---\nchecked_through: {day.isoformat()}\n---\n'
    if checked_through(text) is not None:
        text = re.sub(r'^---\n.*?\n---\n', lambda _m: front, text, count=1, flags=re.S)
    elif text:
        text = front + text
    else:
        text = front + HEADER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return True, f'{path.relative_to(root)} now covers every day through {day}'


def approval_lines(text):
    """-> [(line number, line)] of entries that name an approval."""
    body_start = 0
    m = re.match(r'---\n.*?\n---\n', text or '', re.S)
    if m:
        body_start = text[:m.end()].count('\n')
    return [(i + 1, line) for i, line in enumerate((text or '').splitlines())
            if i >= body_start and APPROVAL.search(line)]


def _print_changes(ch, full=False):
    print(f"  {len(ch['commits'])} commit(s):")
    for short, subject, body in ch['commits']:
        print(f'  {short}  {subject}')
        if full and body:
            print(f'           {body}')
    if ch['added']:
        docs = [n for n in ch['added'] if n.endswith('.md')]
        rest = len(ch['added']) - len(docs)
        shown = ', '.join(docs[:20]) + (' ...' if len(docs) > 20 else '')
        print(f"  new documents: {shown or 'none'}"
              f"{f'; and {rest} other new file(s)' if rest else ''}")


def main(argv):
    if '--help' in argv or '-h' in argv:
        print(__doc__.strip())
        return 0
    root = pathlib.Path(_git('.', 'rev-parse', '--show-toplevel')[1] or '.')
    rel = feed_path(root)
    ref = production_ref(root)
    if ref and ref.startswith('origin/'):
        _git(root, 'fetch', '--quiet', 'origin', PRODUCTION, timeout=30)

    if '--mark' in argv:
        i = argv.index('--mark')
        try:
            day = datetime.date.fromisoformat(argv[i + 1])
        except (IndexError, ValueError):
            print('precedent_whats_new: --mark takes a date, YYYY-MM-DD', file=sys.stderr)
            return 2
        ok, msg = mark(root, day)
        print(f'precedent_whats_new: {msg}')
        return 0 if ok else 1

    if '--check' in argv:
        path = root / rel
        text = path.read_text(encoding='utf-8') if path.is_file() else ''
        hits = approval_lines(text)
        for n, line in hits:
            print(f'{rel}:{n}: names an approval -- an entry says what changed, '
                  f'never who approved it: {line.strip()[:120]}')
        print(f'precedent_whats_new: {len(hits)} entry line(s) naming an approval')
        return 1 if hits else 0

    if '--today' in argv:
        tz, name = repo_zone(root)
        now = datetime.datetime.now(tz)
        ch = changes_between(root, ref, _midnight(now.date(), tz), now) if ref else None
        if not ch:
            print(f'Nothing has changed on {PRODUCTION} yet today ({now.date()}, {name}).')
            return 0
        print(f'Today so far on {PRODUCTION} ({now.date()}, {name}):')
        _print_changes(ch, '--full' in argv)
        return 0

    name, through, days = missing_days(root)
    if ref is None:
        print(f'precedent_whats_new: no {PRODUCTION} branch here, so there is '
              f'nothing to log.')
        return 0
    if '--days' in argv:
        if not days:
            print(f'precedent_whats_new: {rel} is current through '
                  f'{through or "(no log yet)"}; no finished day is missing.')
            return 0
        for day, ch in reversed(days):
            print(f'\n## {day.isoformat()} ({name})')
            _print_changes(ch, '--full' in argv)
        last = max(d for d, _ in days)
        print(f'\nWrite one entry per day above, newest first, then run: '
              f'python3 tools/precedent_whats_new.py --mark {last}')
        return 0

    exists = (root / rel).is_file()
    print(f'log: {rel}{"" if exists else " (not written yet)"}')
    print(f'checked through: {through or "nothing yet"} ({name})')
    if days:
        print(f'missing: {len(days)} finished day(s) with changes -- '
              f'{", ".join(d.isoformat() for d, _ in days)}')
    else:
        print('missing: none -- the log is current through yesterday')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
