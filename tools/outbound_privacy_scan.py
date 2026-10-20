#!/usr/bin/env python3
"""Finds requests that already left the machine carrying the person's
private details, in a session's own record of its tool calls (practice:
outbound-privacy).

    python3 tools/outbound_privacy_scan.py              every session transcript under ~/.claude/projects
    python3 tools/outbound_privacy_scan.py FILE...      these transcripts
    python3 tools/outbound_privacy_scan.py --hook       Stop hook: this session and its agents

The gate (tools/outbound_privacy_gate.py) refuses such a request before it
runs; this is the check behind it, for whatever reached the network another
way: a session without the gate, a tool the gate does not see, a term added
after the fact. It reads each tool call in the transcript and in the
transcripts of the agents the session started (<session>/subagents/), and
reports every outbound one holding a private term, the term masked, the
same way the gate decides what is outbound and what is private.

As a Stop hook it speaks once per finding: a finding it has reported is
recorded in .precedent/outbound_scan_seen.json, and the next stop is quiet
unless a new one appears. A new finding ends the turn with exit 2, so the
session tells the person in its reply what went out, where and when.

WHY (Alex, 2026-10-18: "Or at least better track when this happens?"). The
first such leak was found only because the agent mentioned it in its report.

FAIL-OPEN (practice: fail-gracefully): an unreadable transcript or line is
skipped; the hook never blocks on its own plumbing.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import outbound_privacy_gate as gate  # noqa: E402

ROOT = gate.ROOT
SEEN = ROOT / '.precedent' / 'outbound_scan_seen.json'


# What a tool call's result says when the call never ran: the gate's own
# refusal, or the person declining it. Such a call sent nothing.
NEVER_RAN = ('OUTBOUND PRIVACY: this request would send',
             "doesn't want to proceed with this tool use")


def _result_text(item):
    c = item.get('content')
    if isinstance(c, list):
        return ' '.join(str(x.get('text') or '') for x in c if isinstance(x, dict))
    return str(c or '')


def tool_calls(path):
    """(id, tool, input, time) for every tool call recorded in a transcript
    that actually ran.

    WHY THE SKIP (2026-10-20). A call the gate refused is still in the
    transcript as a tool call, with the refusal as its result. Read as one
    that ran, it was reported to the person as private details that "left
    this machine" -- twice in one session, about a commit command the gate
    had stopped -- when nothing went anywhere."""
    try:
        lines = Path(path).read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return
    calls, refused = [], set()
    for line in lines:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        msg = rec.get('message') if isinstance(rec, dict) else None
        content = msg.get('content') if isinstance(msg, dict) else None
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get('type') == 'tool_use':
                calls.append((item.get('id') or '', item.get('name') or '',
                              item.get('input') or {}, rec.get('timestamp') or ''))
            elif item.get('type') == 'tool_result' and item.get('is_error') \
                    and any(m in _result_text(item) for m in NEVER_RAN):
                refused.add(item.get('tool_use_id') or '')
    for call in calls:
        if call[0] not in refused:
            yield call


def transcripts_for(session_path):
    p = Path(session_path)
    out = [p]
    sub = p.with_suffix('') / 'subagents'
    if sub.is_dir():
        out += sorted(sub.glob('*.jsonl'))
    return out


def scan(paths, root=ROOT):
    ts = gate.terms(root)
    if not ts:
        return []
    found = []
    for path in paths:
        for cid, tool, tool_input, when in tool_calls(path):
            text = gate.outbound_text(tool, tool_input)
            if text is None:
                continue
            hits = [i for i, t in enumerate(ts, 1) if t.lower() in text.lower()]
            if hits:
                found.append({'id': cid, 'tool': tool, 'time': when, 'terms': hits,
                              'transcript': str(path), 'request': gate.mask(text, ts)[:400]})
    return found


def report(found):
    lines = [f'OUTBOUND PRIVACY: {len(found)} request(s) left this machine carrying the '
             'person\'s private details (practice: outbound-privacy). Tell the person what '
             'went out, to which service and when:']
    for f in found:
        lines.append(f"  - {f['time'] or 'time unknown'} · {f['tool']} · private term "
                     f"{', '.join(map(str, f['terms']))} · {f['request'][:200]}")
    return '\n'.join(lines)


def hook():
    try:
        payload = json.loads(sys.stdin.read() or '{}')
    except ValueError:
        return 0
    tp = payload.get('transcript_path')
    if not tp:
        return 0
    try:
        found = scan(transcripts_for(tp))
        seen = set(json.loads(SEEN.read_text(encoding='utf-8'))) if SEEN.exists() else set()
        new = [f for f in found if f['id'] and f['id'] not in seen]
        if not new:
            return 0
        SEEN.parent.mkdir(parents=True, exist_ok=True)
        SEEN.write_text(json.dumps(sorted(seen | {f['id'] for f in new})), encoding='utf-8')
    except Exception as e:  # fail open on the plumbing
        print(f'outbound_privacy_scan: {e}', file=sys.stderr)
        return 0
    print(report(new), file=sys.stderr)
    return 2


def main(argv):
    if argv[1:2] == ['--hook']:
        return hook()
    if argv[1:2] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    paths = argv[1:] or sorted(Path.home().glob('.claude/projects/**/*.jsonl'))
    found = scan(paths)
    if not found:
        print('outbound_privacy_scan: nothing private went out in the transcripts read '
              f'({len(paths)} file(s)).')
        return 0
    print(report(found))
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
