#!/usr/bin/env python3
"""How often the reply gate refuses a turn, per session and per requirement -- read from the ledger the stop hook keeps

How often the reply gate refuses a turn, per session and per requirement.

practice: the-boildown
practice: session-load-budget

WHY THIS EXISTS. The stop hook refuses a reply that misses a requirement in a
source's reply_check.json, and until 2026-11-04 nothing counted the refusals.
The gate's cost was visible on every turn -- the reply written twice -- and its
benefit was a belief, because nobody could say which requirements catch
substance and which catch wording, or whether a session gets refused once a
day or once a turn. A consumer's reduction pass named the gap (S. Alexander
Jacobson, 2026-11-04).

WHAT IT READS. .precedent/reply_refusals.jsonl under the repository, one JSON
line per stop-hook verdict, written by tools/precedent_reply_check.py's
record_outcome(): time, session, repo, turn, outcome (pass or refused), the
kinds of the requirements missed and their messages. The folder is untracked,
so the ledger never reaches git and holds only this machine's sessions.

WHAT IT PRINTS. Per session: turns checked, turns refused, the share. Per
requirement kind: how many refusals it accounts for. Then one line on the
whole window. A session with no ledger prints that there is nothing yet.

WHAT IT DOES NOT DO. It never changes a requirement and never proposes one.
Which refusals were right is a reading of the messages, not of the counts.
"""
import argparse
import collections
import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = '.precedent/reply_refusals.jsonl'


def read_ledger(path):
    """-> [entry]; an unreadable line is skipped, an absent file is []."""
    out = []
    try:
        lines = pathlib.Path(path).read_text(encoding='utf-8').splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get('outcome') in ('pass', 'refused'):
            out.append(e)
    return out


def within(entries, days, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=days)
    kept = []
    for e in entries:
        try:
            t = datetime.datetime.fromisoformat(e.get('time', ''))
        except ValueError:
            continue
        if t.tzinfo is None:
            t = t.replace(tzinfo=datetime.timezone.utc)
        if t >= cutoff:
            kept.append(e)
    return kept


def summarize(entries):
    """-> (per_session, per_kind, total_checked, total_refused)."""
    per_session = collections.OrderedDict()
    per_kind = collections.Counter()
    for e in entries:
        sid = e.get('session') or '(no session id)'
        row = per_session.setdefault(sid, {'checked': 0, 'refused': 0})
        row['checked'] += 1
        if e['outcome'] == 'refused':
            row['refused'] += 1
            for k in e.get('kinds') or ['(unnamed)']:
                per_kind[k or '(unnamed)'] += 1
    checked = sum(r['checked'] for r in per_session.values())
    refused = sum(r['refused'] for r in per_session.values())
    return per_session, per_kind, checked, refused


def report(entries, days, ledger):
    per_session, per_kind, checked, refused = summarize(entries)
    lines = [f'REPLY REFUSALS -- {ledger}', f'  window {days}d']
    if not entries:
        lines.append('  no verdicts recorded yet: the ledger is written by the '
                     'stop hook, one line per turn it checks')
        return '\n'.join(lines)
    lines.append('')
    lines.append(f'  {"session":<40} {"checked":>8} {"refused":>8} {"share":>6}')
    for sid, row in per_session.items():
        share = f"{100 * row['refused'] / row['checked']:.0f}%" if row['checked'] else '-'
        lines.append(f'  {sid[:40]:<40} {row["checked"]:>8} {row["refused"]:>8} {share:>6}')
    lines.append('')
    if per_kind:
        lines.append('  refusals by requirement kind:')
        for kind, n in per_kind.most_common():
            lines.append(f'    {kind:<28} {n:>4}')
        lines.append('')
    share = f'{100 * refused / checked:.0f}%' if checked else '-'
    lines.append(f'  TOTAL {checked} turn(s) checked, {refused} refused ({share}) '
                 f'across {len(per_session)} session(s)')
    lines.append('')
    lines.append('  A count says how often the gate fires, never whether it was '
                 'right: read the messages in the ledger for that.')
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(__doc__ or '').splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default=None,
                    help='the repository whose ledger to read (default: '
                         'CLAUDE_PROJECT_DIR, else this one)')
    ap.add_argument('--ledger', default=None,
                    help=f'a ledger file to read instead of <repo>/{LEDGER}')
    ap.add_argument('--days', type=int, default=14,
                    help='how far back to count (default 14)')
    args = ap.parse_args(argv)
    import os
    repo = pathlib.Path(args.repo or os.environ.get('CLAUDE_PROJECT_DIR') or ROOT)
    ledger = pathlib.Path(args.ledger) if args.ledger else repo / LEDGER
    entries = within(read_ledger(ledger), args.days)
    print(report(entries, args.days, ledger))
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
