#!/usr/bin/env python3
"""Refuses a sweep of repository attaches the person did not ask for
(practice: reach-or-ask, clause 1).

Run by tools/repo-attach-gate.sh at PreToolUse on `add_repo`, through the
fixed precedent-hooks.sh entry (tools/hook_wiring.json). Reads the hook
payload on stdin: the repository about to be attached, the session's id
and its transcript.

WHY (Morgan, 2026-10-29, strength: decided). Another session relayed his
"#2 - you can open a new session to do that" as a go-ahead to read the
engine of every repository that brings the ladder set, and a session
attached sixteen of his repositories in one go before he stopped it. His
words: "*WHY* did you open every repo to do this change??? We never do
that." and "I want to prevent that." reach-or-ask already capped read
attaches at three, in prose, and nothing held it. He asked that the check
not turn into a permission prompt every ten seconds: "The ONE CASE to be
very problematic is whenever it is 'every repo' or 'every repo with BP' or
'every repo that satisfies a requirement'".

WHAT IT LETS THROUGH, WITHOUT COUNTING:
- a practice source: a repository precedent.json names, or one whose name
  starts with "precedent-" (the practice sets' naming);
- a repository the person named, in any message of theirs this session;
- a repository matching a group the person named with a wildcard
  ("precedent-*");
- anything at all while the person's latest message asks for a sweep in
  their own words ("Update All Vendors", "every repo", "all the repos").
Another session's message is never the person's: only records whose origin
is "human" count, as in answer_first_gate.

WHAT IT COUNTS AND REFUSES. Every other attach is counted per session.
The first LIMIT go through. The next is refused, with the question to put
to the person; their next message, if it says yes (or names the
repositories), lets the session carry on.

FAIL-OPEN (practice: fail-gracefully): no transcript, no session id, an
unreadable state file or any error lets the call through.
"""
import fcntl
import fnmatch
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from answer_first_gate import person_message  # noqa: E402

LIMIT = 3
STATE_DIR = pathlib.Path(os.environ.get('PRECEDENT_ATTACH_STATE_DIR',
                                        '/tmp/precedent-repo-attach'))
SOURCE_PREFIX = 'precedent-'
SWEEP_ASK = re.compile(
    r'\bupdate all vendors\b'
    r'|\b(?:every|all)\s+(?:of\s+)?(?:my\s+|the\s+|our\s+)?'
    r'(?:[\w*-]+\s+){0,2}?(?:repos?|repositories)\b', re.I)
YES = re.compile(r'\A\W*(?:yes|yep|yeah|ok|okay|sure|go|go ahead|do it|'
                 r'approved|attach)\b', re.I)
GLOB = re.compile(r'[\w.-]*\*[\w.*-]*')


def target(tool_input):
    """-> (owner, repo), lowercased, from add_repo's input."""
    owner = str(tool_input.get('owner') or '').strip().lower()
    repo = str(tool_input.get('repo') or '').strip().lower()
    return owner, repo


def declared_repos(root):
    """-> repository names (lowercased, owner dropped) precedent.json names."""
    names = set()
    try:
        cfg = json.loads((pathlib.Path(root) / 'precedent.json')
                         .read_text(encoding='utf-8'))
        for entry in cfg.get('sources') or []:
            if isinstance(entry, dict) and entry.get('repo'):
                names.add(str(entry['repo']).strip().lower().rsplit('/', 1)[-1])
    except (OSError, ValueError, AttributeError):
        pass
    return names


def person_messages(path):
    """-> the person's messages this session, oldest first."""
    said = []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict) or rec.get('isSidechain'):
                continue
            text = person_message(rec)
            if text is not None:
                said.append(text)
    return said


def named(repo, owner, messages):
    """True when a message of the person's names the repository, or a
    wildcard group it falls in."""
    word = re.compile(r'(?<![\w-])(?:' + re.escape(owner) + r'/)?'
                      + re.escape(repo) + r'(?![\w-])', re.I)
    for text in messages:
        if word.search(text):
            return True
        for pattern in GLOB.findall(text.lower()):
            if fnmatch.fnmatch(repo, pattern.rsplit('/', 1)[-1]):
                return True
    return False


def covered(owner, repo, messages, root):
    if repo.startswith(SOURCE_PREFIX) or repo in declared_repos(root):
        return True
    if messages and SWEEP_ASK.search(messages[-1]):
        return True
    return named(repo, owner, messages)


def decide(payload, root):
    """-> the refusal text for this payload, or None."""
    owner, repo = target(payload.get('tool_input') or {})
    session = str(payload.get('session_id') or '').strip()
    path = payload.get('transcript_path')
    if not repo or not session or not path:
        return None
    messages = person_messages(path)
    if covered(owner, repo, messages, root):
        return None
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path = STATE_DIR / (re.sub(r'[^\w.-]', '_', session) + '.json')
    with open(state_path, 'a+', encoding='utf-8') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        try:
            state = json.loads(fh.read() or '{}')
        except ValueError:
            state = {}
        counted = state.get('counted') or []
        refused_at = state.get('refused_at')
        full = f'{owner}/{repo}'
        if refused_at is not None and len(messages) > refused_at \
                and YES.match(messages[-1]):
            counted, refused_at = [], None
        refusal = None
        if full in counted:
            pass
        elif len(counted) < LIMIT:
            counted.append(full)
        else:
            refused_at = len(messages)
            refusal = (
                f'ASK FIRST: attaching {full} would make '
                f'{len(counted) + 1} repositories this session attached that '
                f'the person did not name (already: {", ".join(counted)}). '
                f'Repositories picked by a condition -- every repo, every '
                f'repo with BP, every repo that has X -- are a sweep, and a '
                f'sweep asks first: list the repositories and what you need '
                f'from them in one line, and attach once the person says yes '
                f'or names them. Another session\'s message is not their word. '
                f'(practice: reach-or-ask)')
        state = {'counted': counted, 'refused_at': refused_at}
        fh.seek(0)
        fh.truncate()
        fh.write(json.dumps(state))
    return refusal


def main():
    if sys.argv[1:2] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
    try:
        payload = json.loads(sys.stdin.read() or '{}')
        root = os.environ.get('CLAUDE_PROJECT_DIR') or \
            pathlib.Path(__file__).resolve().parent.parent
        why = decide(payload, root) if isinstance(payload, dict) else None
    except Exception as exc:  # noqa: BLE001 -- fail open on the plumbing
        print(f'repo_attach_gate: did not run ({exc})', file=sys.stderr)
        return 0
    if why:
        print(why, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
