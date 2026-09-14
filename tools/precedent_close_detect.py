#!/usr/bin/env python3
"""precedent_close_detect.py — the one moment a session offers a practice.

WHAT THIS IS FOR. PRACTICE_ENGINE_PLAN.md puts the automation "at the two
ends: the system notices, and the system enforces." Enforcement got built
out heavily. Noticing got tools/precedent_detect.py and no trigger — nothing
in this codebase called it, so every practice that landed arrived because
Morgan said something (spec/PRACTICE_DETECTION.md has the evidence: two
candidate files ever, both dated to the day the pipeline was built). This is
the trigger.

WHERE IT FIRES, AND WHY NOWHERE ELSE. Morgan, 2026-09-14, set the shape:
*"only when there was a merge (if there wasn't, we were just talking!)"*,
*"only explicitly when we also say 'You can archive this session'"*, one per
session, *"I don't want to DISTRACT people working on something to propose
practices."* So all of these must hold, and each is measured rather than
assumed:

  1. this session MERGED something (the transcript's own tool calls say so);
  2. the reply being written says the session is ready to archive;
  3. no reply this session has already carried a candidate — the cap;
  4. a Stage-1 detector found something in THIS session's own material.

Condition 4 is what keeps it from becoming noise, and it is the reason this
blocks rather than prints: a Stop hook's stdout does not reach the model, so
an advisory print at this moment reaches nobody (the same finding that put
the reply gate's brief in a UserPromptSubmit hook). Blocking on positive
evidence only means a session with nothing to offer is never interrupted,
and never asked to say so either.

WHAT IT NEVER DOES. It does not decide that something IS a practice — it
names what it found and the session judges, which is Stage 1 handing Stage 2
a candidate and nothing more. A session that reads the signal and concludes
it was a one-off says that in one line; inventing a rule to satisfy a hook
is the failure mode this is written to avoid, and the message says so.

WHAT IS DECLARED RATHER THAN COMPILED IN. "You can archive this session" is
ONE PERSON'S closing convention, from his individual set — compiling it into
the universal engine would bind every adopter of Precedent to it, which is
the reach mistake practices/rule-level-by-reach exists to stop, and exactly
the split tools/precedent_reply_check.py already makes. So the engine ships
the mechanism and each source declares its own phrases in a
`close_detect.json` at the source root:

    {
      "practice": "merged-session-offers-a-practice",
      "archive_ready_one_of": ["You can archive this session"],
      "closing_heading_matching": "next step",
      "candidate_marker": "Practice candidate",
      "why": "so a finished session offers what it learned, once"
    }

A repo where no source declares one detects nothing and blocks nothing.

Run:
  <stop hook> | python3 tools/precedent_close_detect.py   # the real path
  python3 tools/precedent_close_detect.py --explain       # what is declared
  python3 tools/precedent_close_detect.py --transcript F  # check one file
"""
import json
import os
import pathlib
import re
import sys

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

CONFIG_NAME = 'close_detect.json'
DEFAULT_MARKER = 'Practice candidate'
DEFAULT_HEADING = 'next step'

# A merge this session actually performed. `git merge-base` is not a merge
# and is run constantly by the freshness guard, so the pattern has to refuse
# the hyphen: `\bmerge\b` matches inside "merge-base" because `-` is a word
# boundary, which is how the first draft of this reported a merge on every
# session that started up cleanly.
_MERGE_PATTERNS = [
    re.compile(r'\bgit\s+(?:-C\s+\S+\s+)?merge(?![-\w])', re.I),
    re.compile(r'\bgh\s+pr\s+merge\b', re.I),
]
_MERGE_TOOLS = ('merge_pull_request',)


def declared(repo):
    """-> (requirements, notes). Every source's close_detect.json, in the
    resolver's precedence order. Same shape and same honest default as
    precedent_reply_check.declared_requirements: a source that declares
    nothing contributes nothing, and an unresolvable source is a note rather
    than a failure (practice: fail-gracefully)."""
    notes, reqs = [], []
    try:
        import precedent_resolve as pr
    except ImportError:
        return reqs, ['precedent_resolve.py is not beside this script']
    try:
        sources = pr.load_config(repo)
    except Exception as e:                                   # noqa: BLE001
        return reqs, [f'no source set could be read ({e})']
    for s in sources:
        cfg = pathlib.Path(s['path']) / CONFIG_NAME
        if not cfg.is_file():
            continue
        try:
            d = json.loads(cfg.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as e:
            notes.append(f"{s['level']}/{s['name']}'s {CONFIG_NAME} is unreadable ({e})")
            continue
        for item in (d if isinstance(d, list) else [d]):
            if not isinstance(item, dict):
                notes.append(f"{s['level']}/{s['name']}'s {CONFIG_NAME} has an "
                             f"entry that is not an object; it is skipped")
                continue
            item['_source'] = f"{s['level']}/{s['name']}"
            reqs.append(item)
    return reqs, notes


def _norm(s):
    # Same fold as the reply check: a typed apostrophe and a rendered one are
    # the same sentence to the reader.
    return (s or '').replace('’', "'").replace('‘', "'").lower()


def read_transcript(path):
    """-> list of parsed JSONL records, or None if it could not be read."""
    try:
        return [json.loads(l) for l in
                pathlib.Path(path).read_text(encoding='utf-8').splitlines()
                if l.strip()]
    except (OSError, json.JSONDecodeError):
        return None


def _blocks(rec, role):
    msg = rec.get('message')
    if rec.get('type') != role or not isinstance(msg, dict):
        return []
    content = msg.get('content')
    if isinstance(content, str):
        return [{'type': 'text', 'text': content}]
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def assistant_texts(records):
    out = []
    for rec in records:
        text = '\n'.join(b.get('text', '') for b in _blocks(rec, 'assistant')
                         if b.get('type') == 'text')
        if text.strip():
            out.append(text)
    return out


def person_messages(records):
    """The text the PERSON actually typed, and nothing else.

    A `type: user` record is also how tool results and every hook's injected
    output come back, so a naive read of them hands the instruction detector
    this engine's own rule text -- which is written in exactly the standing-
    rule phrasing it looks for, and would fire on every session forever. Tool
    results are dropped by block type; hook and harness injections are
    dropped by their envelopes.
    """
    skip = ('<system-reminder>', '<command-name>', '<local-command',
            'UserPromptSubmit hook', 'SessionStart', 'Caveat: The messages below',
            '<wake ', '<event ', '<webhook-payload>')
    out = []
    for rec in records:
        for b in _blocks(rec, 'user'):
            if b.get('type') != 'text':
                continue          # tool_result and friends are not the person
            text = b.get('text') or ''
            if not text.strip() or any(m in text for m in skip):
                continue
            out.append(text)
    return out


def merged_this_session(records):
    """-> the command or tool that merged, or None.

    The transcript is the only record of what a session DID that is available
    at the moment the session ends; a git-log scan would report merges made
    by anyone, at any time, in any session (practice: verify-postcondition --
    the postcondition here is "this session merged", not "a merge exists").
    """
    for rec in records:
        for b in _blocks(rec, 'assistant'):
            if b.get('type') != 'tool_use':
                continue
            name = b.get('name') or ''
            if any(t in name for t in _MERGE_TOOLS):
                return name
            inp = b.get('input')
            cmd = inp.get('command') if isinstance(inp, dict) else None
            if isinstance(cmd, str) and any(p.search(cmd) for p in _MERGE_PATTERNS):
                return cmd.strip().splitlines()[0][:120]
    return None


def session_started(records):
    """The transcript's first timestamp, for a session-scoped git scan. None
    when the harness wrote none -- in which case the git-backed signals are
    skipped rather than widened to all of history."""
    for rec in records:
        ts = rec.get('timestamp')
        if isinstance(ts, str) and ts.strip():
            return ts
    return None


def signals(records, repo):
    """-> [(signal_name, detail), ...] found in THIS session's own material.

    Deliberately narrow. Morgan, 2026-09-14: *"only when it can really find a
    practice that might be helpful based on just that conversation (shouldn't
    be random stuff from other conversations)"* -- so every input here is
    scoped to this session: the person's own messages, and commits made since
    it started.
    """
    try:
        import precedent_detect as pd
    except ImportError:
        return []
    found = []
    for text in person_messages(records):
        for pattern, sent in pd.instruction_hits(text):
            # "the person", never a pronoun: this is universal engine code
            # and the person on the other end of any given session is
            # whoever it is (practice: declared-pronouns).
            found.append(('explicit-instruction',
                          f'the person said: "{sent[:200]}" [{pattern}]'))
    since = session_started(records)
    if since:
        for sha, subject in pd.revert_hits(repo, since_date=since):
            found.append(('reverted-or-corrected',
                          f'{sha} {subject} -- work this session undid'))
    # One line per distinct signal sentence; the same phrase said twice is one
    # thing to think about, not two.
    seen, out = set(), []
    for name, detail in found:
        if detail not in seen:
            seen.add(detail)
            out.append((name, detail))
    return out


def evaluate(records, reqs, repo):
    """-> (should_block, message_lines). Every condition measured, in the
    order that makes the cheap ones fail first."""
    for r in reqs:
        phrases = r.get('archive_ready_one_of') or []
        if not phrases:
            continue
        texts = assistant_texts(records)
        if not texts:
            return False, []
        reply = texts[-1]
        if not any(_norm(p) in _norm(reply) for p in phrases):
            continue                      # not the closing reply
        marker = r.get('candidate_marker') or DEFAULT_MARKER
        if any(_norm(marker) in _norm(t) for t in texts):
            continue                      # the one-per-session cap, already spent
        merge = merged_this_session(records)
        if not merge:
            continue                      # "if there wasn't, we were just talking"
        found = signals(records, repo)
        if not found:
            continue                      # nothing real to offer; say nothing
        heading = r.get('closing_heading_matching') or DEFAULT_HEADING
        lines = [
            f"[{r.get('_source', '?')}] This session merged something and is "
            f"closing as ready to archive, and a Stage-1 detector found "
            f"{len(found)} signal(s) in this session's own material. Add ONE "
            f"more bullet to the closing /{heading}/i section -- nothing else, "
            f"and do NOT rewrite the reply the person has already seen.",
            f"  The bullet starts with \"{marker}:\", names the rule in one "
            f"sentence, and says which level it would belong at. Raise it "
            f"properly with `precedent_candidate.py create` in the same turn.",
            "  What was found:",
        ]
        for name, detail in found:
            lines.append(f"    - [{name}] {detail}")
        lines += [
            "  IF THIS IS NOT A RULE, SAY SO IN ONE LINE AND STOP. A signal is "
            "evidence, not a verdict, and most of these are one-offs. Inventing "
            "a practice to satisfy this hook is worse than the hook never "
            "firing (practice: mistakes-become-rules' proportionality guard).",
            "  Already landed it this session? Then it is already disclosed "
            "(practice: disclose-landing) -- say that in one line instead.",
        ]
        if r.get('practice'):
            lines.append(f"  (practice: {r['practice']})")
        return True, lines
    return False, []


def main():
    argv = sys.argv[1:]
    repo = os.environ.get('CLAUDE_PROJECT_DIR') or '.'
    if '--repo' in argv:
        i = argv.index('--repo')
        repo = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]

    reqs, notes = declared(repo)

    if '--explain' in argv:
        print(f"close detection, from {repo}:")
        for n in notes:
            print(f"  note: {n}")
        if not reqs:
            print("  no source declares a close_detect.json -- nothing is "
                  "detected, and no reply will ever be blocked by this file.")
        for r in reqs:
            print(f"  {r.get('_source')}: ready-to-archive "
                  f"{r.get('archive_ready_one_of')}, one candidate per session "
                  f"marked {r.get('candidate_marker') or DEFAULT_MARKER!r}, in "
                  f"the /{r.get('closing_heading_matching') or DEFAULT_HEADING}/i "
                  f"section")
        return 0

    if '--transcript' in argv:
        transcript = argv[argv.index('--transcript') + 1]
    else:
        try:
            payload = json.loads(sys.stdin.read() or '{}')
        except json.JSONDecodeError:
            payload = {}
        # Already blocked once this turn -- a gate that blocks the same reply
        # twice is a loop, not a gate.
        if payload.get('stop_hook_active'):
            return 0
        transcript = payload.get('transcript_path')
    if not reqs or not transcript:
        return 0
    records = read_transcript(transcript)
    if records is None:
        return 0                       # never block on this check's blindness
    block, lines = evaluate(records, reqs, repo)
    if not block:
        return 0
    for line in lines:
        print(line, file=sys.stderr)
    return 2


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
