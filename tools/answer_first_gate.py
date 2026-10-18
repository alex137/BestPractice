#!/usr/bin/env python3
"""Refuses a change while the person's latest message asks something the
session has not answered yet in words (practice:
answer-first-ask-before-long-work, clause 1).

Run by tools/answer-first-gate.sh at PreToolUse, through the fixed
precedent-hooks.sh entry (tools/hook_wiring.json). Reads the hook payload
on stdin: the tool about to run, and the session's transcript.

WHY (Morgan, 2026-10-17, strength: decided). He asked for the details of a
workflow change in the same message that approved a landing; the session
wrote "Landing first, since you approved it." and landed, and he got the
answer 18 minutes later. His words: "if I ask a question, you answer it
BEFORE you implement a change? THAT IS IMPORTANT, SO I CAN THINK ABOUT YOUR
ANSWER ****WHILE**** YOU MAKE THE CHANGE SO WE DON'T LOSE OR WASTE TIME.
Make that change enforcement stronger". The rule was prose only.

WHAT IT REFUSES. A change -- an edit to a file outside /tmp, a commit, a
push, a merge, a landing or a Produce, a pull request opened or merged, a
file written to GitHub -- while the person's latest message reads as a
question (a question mark, or "explain", "tell me", "give me", "show me",
"details" and the like) and the session has written fewer than
MIN_ANSWER_WORDS words to them since. Reading, searching and running
checks are never refused: they are how an answer gets found. A sentence
announcing the work ("Landing first") is not an answer, which is why a few
words do not clear it.

The person's messages are the transcript's records whose origin is
"human": a message typed at the prompt, and one sent while the session was
working (queued_command). Notices, tool results and other sessions'
messages are not theirs.

FAIL-OPEN (practice: fail-gracefully): no transcript, an unreadable line,
an unknown tool or any error lets the call through.
"""
import json
import re
import sys

MIN_ANSWER_WORDS = 50

ASKS = re.compile(
    r'\?|\b(?:explain|tell me|give me|show me|walk me through|details?|'
    r'describe|clarify|what do you think|my options)\b', re.I)

CHANGING_TOOLS = re.compile(
    r'mcp__.*__(?:merge_pull_request|create_pull_request|update_pull_request|'
    r'push_files|create_or_update_file|delete_file|create_branch)')
EDIT_TOOLS = {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}
CHANGING_COMMAND = re.compile(
    r'(?:^|[;&|(]\s*|\s)git\s+(?:-C\s+\S+\s+)?(?:commit|push|merge(?!\s+--abort))\b'
    r'|precedent_branches\.py\b[^\n]*--(?:land|promote)\b')


def is_change(tool, tool_input):
    if tool in EDIT_TOOLS:
        path = str(tool_input.get('file_path') or tool_input.get('notebook_path') or '')
        return not path.startswith('/tmp/')
    if tool == 'Bash':
        return bool(CHANGING_COMMAND.search(str(tool_input.get('command') or '')))
    return bool(CHANGING_TOOLS.fullmatch(tool or ''))


def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(str(b.get('text') or '') for b in content
                         if isinstance(b, dict) and b.get('type') == 'text')
    return ''


def person_message(rec):
    """-> the text of a message the person sent, or None."""
    if rec.get('type') == 'user' and (rec.get('origin') or {}).get('kind') == 'human':
        return _text((rec.get('message') or {}).get('content'))
    att = rec.get('attachment') if rec.get('type') == 'attachment' else None
    if isinstance(att, dict) and att.get('type') == 'queued_command' \
            and (att.get('origin') or {}).get('kind') == 'human':
        return str(att.get('prompt') or '')
    return None


def assistant_words(rec):
    if rec.get('type') != 'assistant':
        return 0
    return len(_text((rec.get('message') or {}).get('content')).split())


def unanswered(lines):
    """-> the person's latest message when it asks something and fewer than
    MIN_ANSWER_WORDS words have gone to them since, else None."""
    asked, words = None, 0
    for line in lines:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if not isinstance(rec, dict) or rec.get('isSidechain'):
            continue
        said = person_message(rec)
        if said is not None:
            asked, words = said, 0
            continue
        words += assistant_words(rec)
    if asked and ASKS.search(asked) and words < MIN_ANSWER_WORDS:
        return asked
    return None


def refusal(payload):
    """-> the refusal text for this PreToolUse payload, or None."""
    tool = payload.get('tool_name') or ''
    if not is_change(tool, payload.get('tool_input') or {}):
        return None
    path = payload.get('transcript_path')
    if not path:
        return None
    try:
        with open(path, encoding='utf-8') as fh:
            asked = unanswered(fh)
    except OSError:
        return None
    if not asked:
        return None
    quoted = ' '.join(asked.split())
    if len(quoted) > 160:
        quoted = quoted[:157] + '...'
    return (f'ANSWER FIRST: the person\'s latest message asks something, and it '
            f'has not been answered yet: "{quoted}". Write them the answer now, '
            f'in plain words, then make this change: they think about the '
            f'answer while the work runs (practice: '
            f'answer-first-ask-before-long-work). Reading and checking are not '
            f'held; only changes are.')


def main():
    if sys.argv[1:2] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
    try:
        payload = json.loads(sys.stdin.read() or '{}')
        why = refusal(payload) if isinstance(payload, dict) else None
    except Exception as exc:  # noqa: BLE001 -- fail open on the plumbing
        print(f'answer_first_gate: did not run ({exc})', file=sys.stderr)
        return 0
    if why:
        print(why, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
