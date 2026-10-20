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

THE TRANSCRIPT TRAILS THE TURN (measured 2026-10-18). Claude Code writes
an assistant message -- the text and the tool call it ends in -- to the
transcript after PreToolUse runs, usually within a second, sometimes not
for several. So the answer written just before the change being guarded is
not there when the gate first reads; that day a session answered in about a
hundred words, the gate counted 11 and refused its merge three times. When
the count falls short and the payload names its tool_use_id, the gate waits
up to CATCH_UP_SECONDS for that call to be recorded -- its text lands first
-- and counts again. Still not recorded: the transcript provably lags, and
the call goes through. No tool_use_id: nothing to prove lag with, so the
first count stands.

ONE REFUSAL PER QUESTION (Morgan, 2026-10-19, strength: decided: "okay,
go fix"). The lag above was not the whole story. A text the session writes
mid-turn of about forty-five words or more is never written to the
transcript at all: shorter ones are, and the turn's final reply is, but a
mid-turn answer the length this gate asks for is not, minutes later or
ever (gotchas/gotcha-2026-10-18-the-answer-first-gate-cannot-see-text-
written-between-tool-calls.md). A session that had answered in two hundred
words was refused four times running, with nothing it could write ever
reaching the gate. The person had the answer the moment it was written;
only the work they asked for was held. So the refusal is a nudge, given
once: when the transcript already carries this gate's refusal since the
person's latest message, the next change goes through, saying so. Morgan:
"if you write a longer answer for me, IS THERE A REASON TO NOT GIVE IT TO
ME IMMEDIATELY? WHY WAIT OR WHY REFUSE?"

SLOW WORK NOBODY ASKED FOR IS HELD TOO (Morgan, 2026-10-20: "Can you
make the enforcement of that stronger?"). He asked whether BestPractice
had a process for vendoring itself; the session found the answer in two
commands, then spent minutes rebuilding and publishing the branch cleanup
page for its closing archive line before writing a word of it. Neither step
was a change by the list above -- the build writes under /tmp, and a
publish is no file edit -- so nothing held them. Now a publish with the
Artifact tool (any call but a read, list or open) and a run of
precedent_stale_branches.py are held the same way: the answer goes first,
the page after.

CODE IS NOT A QUESTION, AND A HANDOFF IS WORK (2026-10-20). A session
seeded with a prompt full of regex -- non-capturing groups and lookbehinds,
each written with a question mark -- had its first file write refused, the
prompt read as a question nobody had answered. A question mark inside a
code span or a fenced block, or opening a regex group, is not a question;
and a message that opens with the seeded-prompt origin line ("Sent
automatically by the session ...") hands over work, so it holds nothing.

FAIL-OPEN (practice: fail-gracefully): no transcript, an unreadable line,
an unknown tool, a transcript that has not caught up with the call, or any
error lets the call through.
"""
import json
import re
import sys
import time

MIN_ANSWER_WORDS = 50
CATCH_UP_SECONDS = 3.0

ASKS = re.compile(
    r'(?<!\()\?|\b(?:explain|tell me|give me|show me|walk me through|details?|'
    r'describe|clarify|what do you think|my options)\b', re.I)
CODE = re.compile(r'```.*?(?:```|\Z)|~~~.*?(?:~~~|\Z)|`[^`\n]*`', re.S)
HANDOFF = re.compile(r'\A\s*Sent automatically by the session\b')


def asks(text):
    """True when the person's message reads as a question: code and a
    seeded handoff do not."""
    if HANDOFF.match(text):
        return False
    return bool(ASKS.search(CODE.sub(' ', text)))

CHANGING_TOOLS = re.compile(
    r'mcp__.*__(?:merge_pull_request|create_pull_request|update_pull_request|'
    r'push_files|create_or_update_file|delete_file|create_branch)')
EDIT_TOOLS = {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}
CHANGING_COMMAND = re.compile(
    r'(?:^|[;&|(]\s*|\s)git\s+(?:-C\s+\S+\s+)?(?:commit|push|merge(?!\s+--abort))\b'
    r'|precedent_branches\.py\b[^\n]*--(?:land|promote)\b'
    r'|precedent_stale_branches\.py\b')
ARTIFACT_READS = {'read', 'list', 'open', 'quickstart'}


def is_change(tool, tool_input):
    if tool == 'Artifact':
        return str(tool_input.get('action') or 'publish') not in ARTIFACT_READS
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


REFUSED_MARK = 'ANSWER FIRST:'


def refused_already(rec):
    """True for a tool result carrying this gate's own refusal."""
    if rec.get('type') != 'user':
        return False
    content = (rec.get('message') or {}).get('content')
    if not isinstance(content, list):
        return False
    return any(isinstance(b, dict) and b.get('type') == 'tool_result'
               and REFUSED_MARK in str(b.get('content'))
               for b in content)


def unanswered(lines, once=None):
    """-> the person's latest message when it asks something and fewer than
    MIN_ANSWER_WORDS words have gone to them since, else None. When this
    gate has already refused since that message, None as well, and `once`
    (a list) gets the message appended: ONE REFUSAL PER QUESTION."""
    asked, words, refused = None, 0, False
    for line in lines:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if not isinstance(rec, dict) or rec.get('isSidechain'):
            continue
        said = person_message(rec)
        if said is not None:
            asked, words, refused = said, 0, False
            continue
        refused = refused or refused_already(rec)
        words += assistant_words(rec)
    if asked and asks(asked) and words < MIN_ANSWER_WORDS:
        if refused:
            if once is not None:
                once.append(asked)
            return None
        return asked
    return None


def recorded(path, call, seconds):
    """-> True once the transcript at path carries tool call `call`, waiting
    up to `seconds` for it. The text written with the call lands first."""
    deadline = time.monotonic() + seconds
    while True:
        with open(path, encoding='utf-8') as fh:
            if call in fh.read():
                return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)


def refusal(payload):
    """-> the refusal text for this PreToolUse payload, or None."""
    tool = payload.get('tool_name') or ''
    if not is_change(tool, payload.get('tool_input') or {}):
        return None
    path = payload.get('transcript_path')
    if not path:
        return None
    once = []
    try:
        with open(path, encoding='utf-8') as fh:
            asked = unanswered(fh, once)
        if once:
            print('answer_first_gate: refused once already for this question; '
                  'an answer written mid-turn may never reach the transcript, '
                  'so this change goes through', file=sys.stderr)
            return None
        call = payload.get('tool_use_id')
        if asked and call:
            if not recorded(path, call, CATCH_UP_SECONDS):
                print(f'answer_first_gate: the transcript has not recorded '
                      f'{call} after {CATCH_UP_SECONDS:g}s, so it may lack the '
                      f'answer written with it; letting the call through',
                      file=sys.stderr)
                return None
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
            f'held; only changes, a page publish and the branch page build are.')


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
