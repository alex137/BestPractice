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
A git command that runs on this machine alone (commit, tag, log, add and
every subcommand outside the few that reach a remote) is never outbound,
whatever its message, --author or --trailer say: a commit's author address
is attribution the person chose. A push is read like any network command.

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
import shlex
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


# Git subcommands that talk to a remote. Every other git subcommand runs
# on this machine alone, whatever its arguments say.
_GIT_NETWORK_SUBCOMMANDS = {'push', 'fetch', 'pull', 'clone', 'ls-remote', 'remote',
                            'submodule', 'send-email', 'archive', 'lfs', 'svn', 'p4'}
# git's own options that come before the subcommand and take a value.
_GIT_VALUE_OPTS = {'-C', '-c', '--git-dir', '--work-tree', '--namespace',
                   '--exec-path', '--config-env'}
_HEREDOC = re.compile(r'<<-?[ \t]*([\'"]?)([A-Za-z_]\w*)\1')
_ASSIGNMENT = re.compile(r'^[A-Za-z_]\w*=')


def _segments(cmd):
    """`cmd` split into its simple commands at unquoted `&&`, `||`, `;`,
    `|`, `&` and newlines. Quotes and `$( )` are respected, so a message
    that spans lines stays inside the command it belongs to."""
    out, cur, i, n = [], [], 0, len(cmd)
    quote, depth = None, 0
    while i < n:
        c = cmd[i]
        if quote == "'":
            cur.append(c)
            if c == "'":
                quote = None
        elif c == '\\' and i + 1 < n:
            cur.append(cmd[i:i + 2]); i += 2; continue
        elif quote == '"':
            cur.append(c)
            if c == '"':
                quote = None
        elif c in '\'"':
            quote = c; cur.append(c)
        elif cmd.startswith('$(', i):
            depth += 1; cur.append('$('); i += 2; continue
        elif c == ')' and depth:
            depth -= 1; cur.append(c)
        elif depth == 0 and c in ';&|\n':
            out.append(''.join(cur)); cur = []
            if cmd.startswith(('&&', '||'), i):
                i += 1
        else:
            cur.append(c)
        i += 1
    out.append(''.join(cur))
    return [s for s in out if s.strip()]


def _words(segment):
    try:
        return shlex.split(segment, comments=False)
    except ValueError:
        return segment.split()


def _local_git(segment):
    """True when `segment` is a git command that never leaves the machine:
    git, its own leading options, then a subcommand outside
    _GIT_NETWORK_SUBCOMMANDS."""
    words = _words(segment)
    while words and _ASSIGNMENT.match(words[0]):
        words = words[1:]
    if not words or Path(words[0]).name != 'git':
        return False
    i = 1
    while i < len(words) and words[i].startswith('-'):
        if words[i] in _GIT_VALUE_OPTS:
            i += 1
        i += 1
    return i < len(words) and words[i] not in _GIT_NETWORK_SUBCOMMANDS


def _substitutions(segment):
    """The `$( )` and backtick commands inside `segment`, which run even when
    the command around them is local. `$(cat <<EOF ...)`, the usual way to
    hand git a message, reads nothing from the network and is left out."""
    found, i = [], 0
    while True:
        i = segment.find('$(', i)
        if i < 0:
            break
        depth, j = 1, i + 2
        while j < len(segment) and depth:
            if segment.startswith('$(', j):
                depth += 1; j += 1
            elif segment[j] == ')':
                depth -= 1
            j += 1
        found.append(segment[i + 2:j - 1])
        i = j
    found += re.findall(r'`([^`]*)`', segment)
    return [f for f in found if not re.match(r'\s*cat\s*<<', f)]


def without_local_git(cmd):
    """`cmd` with every git command that runs on this machine alone taken
    out -- its messages, `--author`, `--trailer` and `-c user.email` with it
    -- and the heredoc that feeds one. A git command that reaches a remote
    (push, fetch, clone and the rest of _GIT_NETWORK_SUBCOMMANDS) is kept
    whole, and so is every other command, inline scripts included, and any
    command substitution inside a local git command.

    WHY (2026-11-18; 2026-10-31 and 2026-10-20 before it). Every commit here
    carries a `Claude-Session: https://...` trailer, and the author's
    address goes in `--author` or `-c user.email`. The URL read as "this
    command reaches the network" and the address as a private term, so a
    plain local commit was refused as outbound. The first two fixes blanked
    the message forms seen so far (a heredoc, a one-line -m); the third
    refusal came from a message that spanned lines inside quotes, and
    `--trailer` was never covered at all. Guessing message shapes keeps
    missing one, so this reads what the command DOES instead: a local git
    subcommand sends nothing, whatever text it carries."""
    lines = cmd.split('\n')
    kept, i = [], 0
    while i < len(lines):
        line = lines[i]
        m = _HEREDOC.search(line)
        before = _segments(line[:m.start()]) if m else []
        if m and before and _local_git(before[-1]):
            kept.append(line)
            end = m.group(2)
            i += 1
            while i < len(lines) and lines[i].strip() != end:
                i += 1
            if i < len(lines):
                kept.append(lines[i])
            i += 1
            continue
        kept.append(line)
        i += 1
    out = []
    for seg in _segments('\n'.join(kept)):
        if _local_git(seg):
            out.extend(without_local_git(s) for s in _substitutions(seg))
        else:
            out.append(seg)
    return '\n'.join(out)


def outbound_text(tool, tool_input):
    """The text of a request that would leave the machine, or None."""
    if tool in OUTBOUND_TOOLS or OUTBOUND_MCP.match(tool or ''):
        return json.dumps(tool_input, ensure_ascii=False)
    if tool == 'Bash':
        cmd = str(tool_input.get('command') or '')
        read = without_local_git(cmd)
        if NETWORK.search(read):
            return read
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
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        return 0
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
