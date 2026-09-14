#!/usr/bin/env python3
"""precedent_reply_check.py — the reply gate, made BLOCKING.

WHAT THIS IS FOR. Every other channel in this engine is advisory: the
resident block, the occasion index, the path triggers and
tools/precedent_gate.py all put a rule in front of a session and hope. For
rules about how a REPLY is written that hope is measurably thin, because the
one artifact they govern -- the conversation transcript -- is the one thing
no repo-scoped check has ever read. Morgan, 2026-09-13, on the closing
Next Steps list his own individual set has required since 2026-09-04: *"I
feel like it sometimes does that, sometimes doesn't, how can we force
that?"*

It is forceable, and the reason nobody had forced it was a false premise
written into the practice's own `## Install` section: that the transcript is
unreachable. It is not. Claude Code hands a Stop hook a JSON payload on
stdin carrying `transcript_path`, and that file is the session's own JSONL
log, final assistant message included, on disk, before the hook runs
(measured here that day). A Stop hook exiting 2 sends its stderr back to the
model and the turn continues -- so a reply that broke the rule is rewritten
before the person ever sees it. That is enforcement, not a reminder.

WHAT IT CHECKS, AND WHY NOT ONE WORD OF IT IS IN THIS FILE. The requirement
this was built for is an INDIVIDUAL practice -- one person's standing rule
about how replies to him close. Compiling his two sentences into the
universal engine would bind every adopter of Precedent to one person's reply
convention, which is exactly the reach mistake practices/rule-level-by-reach
exists to stop. So the engine ships the MECHANISM and every source declares
its own requirements, in a `reply_check.json` at the source root:

    {
      "practice": "next-steps-after-commit",
      "require_heading_matching": "next step",
      "require_one_of": ["You can close this session",
                         "Don't close this session"],
      "why": "so I never have to re-read a reply to find out what is on me"
    }

A repo where no source declares one checks nothing and says nothing. That is
the honest default: this file enforces rules somebody wrote down, and has no
opinion of its own about how a reply should end.

Run:
  <stop hook> | python3 tools/precedent_reply_check.py     # the real path
  python3 tools/precedent_reply_check.py --text FILE       # check a file
  python3 tools/precedent_reply_check.py --explain         # what is declared
"""
import json
import os
import pathlib
import re
import sys

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

CONFIG_NAME = 'reply_check.json'


def declared_requirements(repo):
    """-> (requirements, notes). Every source's reply_check.json, in
    precedence order as the resolver returns them. A source that does not
    declare one contributes nothing; an unresolvable source is a note, never
    a failure (practice: fail-gracefully -- a reply check that refuses to run
    must not also refuse the turn)."""
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
        d['_source'] = f"{s['level']}/{s['name']}"
        reqs.append(d)
    return reqs, notes


def last_assistant_text(transcript):
    """The text of the most recent assistant message in a Claude Code JSONL
    transcript -- every text block of it, joined.

    Tool-use turns carry no text block at all, which is why this returns ''
    rather than raising: a turn that said nothing has no closing line to
    check, and blocking one would be a gate firing at a moment its practice
    never named."""
    try:
        lines = [json.loads(l) for l in
                 pathlib.Path(transcript).read_text(encoding='utf-8').splitlines() if l.strip()]
    except (OSError, json.JSONDecodeError):
        return None
    for d in reversed(lines):
        if d.get('type') != 'assistant':
            continue
        msg = d.get('message')
        if not isinstance(msg, dict):
            continue
        content = msg.get('content')
        if not isinstance(content, list):
            continue
        text = '\n'.join(b.get('text', '') for b in content
                         if isinstance(b, dict) and b.get('type') == 'text')
        if text.strip():
            return text
    return ''


def _norm(s):
    # A typed apostrophe and a rendered one are the same sentence to the
    # reader and two different strings to `in`. Fold both, and case, before
    # matching -- a check that fails on "Don't" vs "Don’t" would block a
    # reply that followed the rule, which is the one failure a blocking gate
    # may never have.
    return s.replace('’', "'").replace('‘', "'").lower()


def violations(text, reqs):
    """-> list of human-readable failures, one per unmet requirement."""
    out = []
    headings = [re.sub(r'^#{1,6}\s+', '', l).strip()
                for l in text.splitlines() if re.match(r'^#{1,6}\s+\S', l)]
    for r in reqs:
        pat = r.get('require_heading_matching')
        if pat and not any(re.search(pat, h, re.I) for h in headings):
            out.append(
                f"[{r.get('_source', '?')}] this reply has no MARKDOWN HEADING "
                f"matching /{pat}/i. Bold text is not a heading -- the closing "
                f"list has to be a real `## ` heading, or it is exactly as "
                f"skimmable as the rest of the reply."
                + (f" (practice: {r['practice']})" if r.get('practice') else ''))
        one_of = r.get('require_one_of') or []
        if one_of and not any(_norm(o) in _norm(text) for o in one_of):
            out.append(
                f"[{r.get('_source', '?')}] this reply says none of: "
                + '; '.join(f'"{o}"' for o in one_of)
                + ". One of them has to be there, in those words -- an absent "
                  "line and a 'nothing is outstanding' line look identical on "
                  "the page and mean opposite things."
                + (f" (practice: {r['practice']})" if r.get('practice') else ''))
    return out


def main():
    argv = sys.argv[1:]
    repo = os.environ.get('CLAUDE_PROJECT_DIR') or '.'
    if '--repo' in argv:
        i = argv.index('--repo')
        repo = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]

    reqs, notes = declared_requirements(repo)

    if '--explain' in argv:
        print(f"reply check, from {repo}:")
        for n in notes:
            print(f"  note: {n}")
        if not reqs:
            print("  no source declares a reply_check.json -- nothing is checked, "
                  "and no reply will ever be blocked by this file.")
        for r in reqs:
            print(f"  {r.get('_source')}: heading /{r.get('require_heading_matching')}/i, "
                  f"one of {r.get('require_one_of')}")
        return 0

    if '--text' in argv:
        text = pathlib.Path(argv[argv.index('--text') + 1]).read_text(encoding='utf-8')
    else:
        try:
            payload = json.loads(sys.stdin.read() or '{}')
        except json.JSONDecodeError:
            payload = {}
        # Already blocked once this turn: Claude Code re-invokes the hook with
        # this set, and a gate that blocks the same reply twice is a loop, not
        # a gate.
        if payload.get('stop_hook_active'):
            return 0
        transcript = payload.get('transcript_path')
        if not transcript:
            return 0
        text = last_assistant_text(transcript)
        if not text:
            # No transcript we could parse, or a turn with no prose in it.
            # Never block on the check's own blindness.
            return 0

    # A turn with no prose in it has no closing line to check -- in either
    # path. The transcript branch already returns early for it; --text needs
    # the same, and a blank file is the shape a caller uses to ask "would
    # this block?" about a tool-only turn.
    if not reqs or not text.strip():
        return 0
    bad = violations(text, reqs)
    if not bad:
        return 0
    # The reply that was just refused has ALREADY been shown to the person --
    # a Stop hook cannot un-show it. So the only correct repair is to emit the
    # missing closing on its own; re-sending the whole answer makes them read
    # it twice, which is what happened on 2026-09-13 when this message said
    # only "rewrite the closing" and the session rewrote everything.
    # practice: durable-fix, label-describes-content.
    print('The reply gate blocked this turn. The person has ALREADY SEEN the '
          'reply above, so do NOT write it again: output ONLY the missing '
          'closing section(s) named below, as a short addition to what you '
          'already said. Nothing else -- no summary, no restatement, no '
          'apology.', file=sys.stderr)
    for b in bad:
        print(f'  - {b}', file=sys.stderr)
    print('  Full rules: `python3 tools/precedent_gate.py reply`.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
