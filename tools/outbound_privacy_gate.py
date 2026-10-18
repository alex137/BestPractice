#!/usr/bin/env python3
"""Refuses a request that would carry the person's private details off the
machine, and logs the refusal (practice: outbound-privacy).

Run by tools/outbound-privacy-gate.sh at PreToolUse, through the fixed
precedent-hooks.sh entry (tools/hook_wiring.json). Reads the hook payload on
stdin: the tool about to run and its input.

WHY (Alex, 2026-10-18, strength: decided: "Do all of the above"). A
research agent fetching encyclopedia pages put the person's email address
in its download script's identification header, "Research/1.0
(<email>)", because the site asks automated tools for contact details and
the agent knew the address. Its context told it never to send that address
anywhere, and it sent it anyway. A written rule had already failed once,
so this refuses the request itself.

WHAT IT REFUSES. A request leaving the machine whose text holds a private
term:
  - WebFetch and WebSearch, always outbound: the URL, the query, the prompt;
  - Bash, when the command reaches the network (curl, wget, an http(s) URL,
    a Python or Node HTTP library, ssh, scp, nc and the like): the whole
    command, scripts written inline included;
  - any MCP tool whose name says it fetches, searches or browses.
Git pushes are not refused: a commit's author address is attribution the
person chose, and the commit goes to their own repository.

THE PRIVATE TERMS, from three places, none of them committed by this file:
  - CLAUDE_CODE_USER_EMAIL, the signed-in person's address, which Claude
    Code puts in every session's environment;
  - .precedent/private_terms.txt, untracked, one term per line, for this
    machine;
  - the file precedent.json names at "private_terms" (repository-relative),
    for terms a private repository keeps for every session.
Matching ignores case. A term under 5 characters is skipped: too short to
mean anything but noise.

THE LOG. Each refusal is one JSON line appended to
.precedent/outbound_refusals.jsonl: the time, the tool, which term (by
number, never its text), and the request with every term masked. The scan
(tools/outbound_privacy_scan.py) reads it beside the transcripts.

FAIL-OPEN ON THE PLUMBING (practice: fail-gracefully): no payload, no terms
or any error lets the call through, with a line on stderr.
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_TERM = 5

NETWORK = re.compile(
    r'\b(?:curl|wget|httpie|http|aria2c|lynx|ssh|scp|sftp|rsync|nc|ncat|telnet|ftp)\b'
    r'|https?://'
    r'|\b(?:requests|httpx|aiohttp|urllib\d?|http\.client|socket|fetch|axios|'
    r'urlopen|playwright|puppeteer|selenium)\b', re.I)
OUTBOUND_TOOLS = {'WebFetch', 'WebSearch'}
OUTBOUND_MCP = re.compile(r'^mcp__.*(?:fetch|search|browse|navigate|http|web)', re.I)


def terms(root=ROOT):
    found = []
    email = os.environ.get('CLAUDE_CODE_USER_EMAIL', '').strip()
    if email:
        found.append(email)
    files = [Path(root) / '.precedent' / 'private_terms.txt']
    try:
        cfg = json.loads((Path(root) / 'precedent.json').read_text(encoding='utf-8'))
        if cfg.get('private_terms'):
            files.append(Path(root) / cfg['private_terms'])
    except (OSError, ValueError):
        pass
    for f in files:
        try:
            for line in f.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    found.append(line)
        except OSError:
            continue
    out = []
    for t in found:
        if len(t) >= MIN_TERM and t.lower() not in (x.lower() for x in out):
            out.append(t)
    return out


def outbound_text(tool, tool_input):
    """The text of a request that would leave the machine, or None."""
    if tool in OUTBOUND_TOOLS or OUTBOUND_MCP.match(tool or ''):
        return json.dumps(tool_input, ensure_ascii=False)
    if tool == 'Bash':
        cmd = str(tool_input.get('command') or '')
        if NETWORK.search(cmd):
            return cmd
    return None


def mask(text, ts):
    for i, t in enumerate(ts, 1):
        text = re.sub(re.escape(t), f'[private term {i}]', text, flags=re.I)
    return text


def check(payload, root=ROOT, log=None):
    """-> (refuse, message). Never raises on bad input."""
    tool = payload.get('tool_name') or ''
    tool_input = payload.get('tool_input') or {}
    text = outbound_text(tool, tool_input)
    if text is None:
        return False, ''
    ts = terms(root)
    hits = [i for i, t in enumerate(ts, 1) if t.lower() in text.lower()]
    if not hits:
        return False, ''
    entry = {'time': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
             'tool': tool, 'terms': hits, 'request': mask(text, ts)[:2000]}
    log = log or (Path(root) / '.precedent' / 'outbound_refusals.jsonl')
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except OSError:
        pass
    return True, (
        'OUTBOUND PRIVACY: this request would send the person\'s private details off the '
        f'machine (private term {", ".join(map(str, hits))}, the person\'s email first). '
        'Take them out and send only what the tool sends by default: answer nothing a site '
        'asks for. If the site will not serve without more, stop and ask the person what to '
        'do (practice: outbound-privacy). The refusal is logged in '
        '.precedent/outbound_refusals.jsonl.')


def main():
    try:
        payload = json.loads(sys.stdin.read() or '{}')
    except ValueError:
        print('outbound_privacy_gate: unreadable payload; let through', file=sys.stderr)
        return 0
    try:
        refuse, msg = check(payload)
    except Exception as e:  # fail open on the plumbing
        print(f'outbound_privacy_gate: {e}; let through', file=sys.stderr)
        return 0
    if refuse:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
