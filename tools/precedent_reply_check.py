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

WHAT IT CHECKS, AND WHY NOT ONE WORD OF IT IS IN THIS FILE. Nothing here
says how a reply should end. The engine ships the MECHANISM, and every
source declares its own requirements, in a `reply_check.json` at the source
root. The shape, with an invented requirement so the example is not
mistaken for a live declaration:

    {
      "practice": "<the slug this enforces>",
      "require_heading_matching": "what I need from you",
      "require_one_of": ["Nothing is blocked", "Blocked on:"],
      "why": "<what goes wrong when the reply omits it>"
    }

A source may declare one requirement (an object) or several (a list). Add
`"advisory": true` to a requirement and an unmet one is still detected and
named (by `violations()`, to whoever reads `--explain` or calls this
programmatically) but never enters the blocking set `main()` acts on --
so it can never refuse a turn. That is the one way this file's mechanism
stops being "enforcement, not a reminder" for a specific requirement,
deliberately: a source declares `advisory` when it wants the SHAPE of a
recommendation -- reviewed, stated one way or the other -- without the
gate that gave next-steps-after-commit its teeth. (the-boildown's own
compact-check and archive-line requirements are the first to use it,
2026-09-17.)

THAT SPLIT IS STILL THE POINT, AND ONE REQUIREMENT HAS SINCE CROSSED IT.
`next-steps-after-commit` -- the closing `## Next Steps` heading and one of
two session-disposition sentences -- was an INDIVIDUAL practice when this
file was written, and this docstring used it as the worked example of
something the engine must not compile into itself: binding every adopter of
Precedent to one person's reply convention is exactly the reach mistake
practices/rule-level-by-reach exists to stop. Morgan moved it to universal
on 2026-09-14 (*"I think we should move the next steps at the end to be
universal"*), so it is now declared in THIS repository's own
reply_check.json and does bind every adopter -- deliberately, and said out
loud in the pull request that moved it rather than left to be discovered.

That changes which source declares one requirement. It changes nothing
about the mechanism: this file still has no requirement of its own, reads
every source's declaration the same way, and a repo where no source
declares one checks nothing and says nothing. A source that wants different
wording than the universal declaration has no override key yet; that is
real follow-up work, not a property of the split.

WHAT A REQUIREMENT MAY BE CONDITIONED ON. `require_when_context_grew_tokens`
makes a requirement fire only once the conversation has grown by that many
tokens since the sentence was last said -- which is how the universal
compaction offer is enforced without becoming a line on every reply. The
size is read from the transcript's own `usage` records, and it decides
WHETHER THE OFFER IS OWED, never anything about compacting: the person still
answers it. That is deliberate, and it is the clause
practices/session-spend-follows-the-task.md already carried -- how full the
context is picks which boundary you speak at, never whether the choice is
yours to take.

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
        # A source may declare ONE requirement (an object, the original shape)
        # or SEVERAL (a list). The list arrived when the universal source
        # needed a second requirement that fires on a different condition from
        # its first; an object is still read exactly as it was.
        items = d if isinstance(d, list) else [d]
        for item in items:
            if not isinstance(item, dict):
                notes.append(f"{s['level']}/{s['name']}'s {CONFIG_NAME} has an "
                             f"entry that is not an object; it is skipped")
                continue
            item['_source'] = f"{s['level']}/{s['name']}"
            reqs.append(item)
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


def assistant_timeline(transcript):
    """-> [(context_tokens, text), ...] for every assistant message in the
    transcript, oldest first, or None if the transcript could not be read.

    `context_tokens` is how big the conversation was when that message was
    produced: the whole input the model was handed, which is
    `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`.
    Most of a long session is cache READS, so a size taken from
    `input_tokens` alone reads as ~2 tokens on a 150,000-token thread --
    measured here 2026-09-14, and the reason this sums all three.

    Transcript bytes were the obvious proxy and are a bad one: the JSONL
    repeats every system reminder on every line, so it grows with turn COUNT
    as much as with context. The usage record is the actual quantity, already
    on disk, written by the harness (practice: no-invented-specifics -- this
    is read, not estimated).
    """
    try:
        lines = [json.loads(l) for l in
                 pathlib.Path(transcript).read_text(encoding='utf-8').splitlines()
                 if l.strip()]
    except (OSError, json.JSONDecodeError):
        return None
    out = []
    for d in lines:
        if d.get('type') != 'assistant':
            continue
        msg = d.get('message')
        if not isinstance(msg, dict):
            continue
        u = msg.get('usage') or {}
        ctx = sum(int(u.get(k) or 0) for k in
                  ('input_tokens', 'cache_creation_input_tokens',
                   'cache_read_input_tokens'))
        content = msg.get('content')
        text = ''
        if isinstance(content, list):
            text = '\n'.join(b.get('text', '') for b in content
                             if isinstance(b, dict) and b.get('type') == 'text')
        out.append((ctx, text))
    return out


def offer_is_due(timeline, every, phrases):
    """Has the conversation grown by `every` tokens since one of `phrases`
    was last said? -> (bool, current_context_tokens, tokens_since).

    This is the whole of the size-aware channel, and what it deliberately
    does NOT do is decide anything about compacting. It decides only WHETHER
    THE OFFER IS OWED, which is the clause
    practices/session-spend-follows-the-task.md already carries: how full the
    context is picks which boundary you speak at, never whether the choice is
    yours. The person still answers it.

    Stateless on purpose -- the transcript is the state. The alternative was a
    counter file somewhere, which goes stale the moment a session is resumed
    in a fresh container (practice: durable-fix).
    """
    # The BASELINE is where the session started, not zero. A session in this
    # repository opens at ≈97,000 tokens before anybody types anything --
    # measured 2026-09-14 -- so counting from zero would owe an offer within
    # two or three turns of every session, in a repo whose always-loaded files
    # happen to be large. Counting from the floor makes `every` mean what it
    # says: how much CONVERSATION has accumulated.
    # ctx_now is the LATEST context, never the high-water mark. A compaction
    # is exactly the event that makes those two differ -- the context drops and
    # the historical maximum does not -- so a `max()` here would go on demanding
    # the offer from a session that had just taken it, which is the one session
    # that owes nothing. Caught by reading this function's own diff before
    # committing it, not by a test.
    ctx_now = next((c for c, _ in reversed(timeline) if c), 0)
    ctx_at_last_offer = next((c for c, _ in timeline if c), 0)
    for ctx, text in timeline:
        if any(_norm(ph) in _norm(text) for ph in phrases):
            ctx_at_last_offer = max(ctx_at_last_offer, ctx)
    since = ctx_now - ctx_at_last_offer
    return since >= every, ctx_now, since


def _norm(s):
    # A typed apostrophe and a rendered one are the same sentence to the
    # reader and two different strings to `in`. Fold both, and case, before
    # matching -- a check that fails on "Don't" vs "Don’t" would block a
    # reply that followed the rule, which is the one failure a blocking gate
    # may never have.
    return s.replace('’', "'").replace('‘', "'").lower()


# practices/the-boildown.md (practice: the-boildown) names one fixed template
# for a turn where nothing happened that is visible, or non-trivial, to the
# person -- "Unchanged since the last update: <what it's still waiting on>."
# -- and says that turn does not owe a fresh Boildown reworded from scratch.
# Widened 2026-09-20 (Morgan,
# direct instruction) from "a scheduled wakeup, a reminder firing, or a
# background-task notification" to any turn that shape fits, including one
# the stop hook itself forces -- a practice-candidate detector rechecking its
# own prior false positive is the incident that prompted the widening, and it
# produced two closing headings in a row with nothing between them but "still
# not a rule." The practice's own prose changed that day; this is the other
# half, so the gate matches what the practice now actually says.
#
# Matched at the START of the stripped reply, case-insensitively, allowing
# the phrase to open under light emphasis markup (`**Unchanged...**`) since a
# session bolding its own lead phrase is expected, not a different sentence.
# This is a literal, narrow match on the fixed template -- not a heuristic
# about length, tone, or how "trivial" a reply feels -- because a fuzzy
# trigger is a fuzzy exemption from a rule declared as blocking, and reads
# every reply as a candidate for skipping its own gate.
_TRIVIAL_CHECKIN_RE = re.compile(r'^[\s*_]*unchanged since the last update:', re.I)


def is_trivial_checkin(text):
    """True when `text` opens with the fixed one-line check-in template
    practices/the-boildown.md names for a turn with nothing visible or
    non-trivial to report. Such a turn is exempt from every requirement
    below, the same way an empty reply already is -- it is not a shorter
    Boildown, it is the documented substitute for one."""
    return bool(_TRIVIAL_CHECKIN_RE.match(text.strip()))


def violations(text, reqs, timeline=None):
    """-> list of records, one per unmet requirement:

        {'kind': 'heading' | 'sentence', 'message': <human-readable>,
         'advisory': bool}

    `advisory` mirrors the requirement's own `"advisory": true` declaration
    (default false). main() still detects and names an unmet advisory
    requirement -- a session should still hear about it -- but never lets
    one refuse the turn: `advisory` marks a recommendation the person can
    take or leave, not a shape the reply must have. (Morgan, 2026-09-17,
    on the-boildown's own compact/archive lines specifically: give the
    honest answer after actually reviewing which situation applies, "and
    note these aren't binding, it's just recommendations.")

    The KIND is the reason this returns records rather than the plain strings
    it used to. A reply that is missing the HEADING has to write the whole
    closing section; a reply that already carries the heading and is missing
    only a SENTENCE must add one line and nothing else. Told the same thing in
    both cases -- "output only the missing closing section(s)" -- sessions
    wrote the section again, and the person read two near-identical `## Next
    Steps` blocks. main() composes a different instruction per kind; nothing
    else reads this field. (practice: cite-the-incident -- the incident is in
    main().)

    `timeline` is assistant_timeline()'s output, needed only by a requirement
    that declares `require_when_context_grew_tokens`. Absent (the --text path,
    or an unreadable transcript), such a requirement is SKIPPED rather than
    enforced: a size condition nobody could evaluate must not block a reply
    (practice: fail-gracefully).
    """
    out = []
    headings = [re.sub(r'^#{1,6}\s+', '', l).strip()
                for l in text.splitlines() if re.match(r'^#{1,6}\s+\S', l)]
    for r in reqs:
        every = r.get('require_when_context_grew_tokens')
        if every:
            phrases = r.get('require_one_of') or []
            if timeline is None or not phrases:
                continue
            due, ctx_now, since = offer_is_due(timeline, int(every), phrases)
            if not due:
                continue
            r = dict(r, _context_note=(
                f"this conversation is at ≈{ctx_now:,} tokens of context and "
                f"has grown ≈{since:,} since the last time this was said"))
        pat = r.get('require_heading_matching')
        # None when this requirement declares no heading at all, so the
        # sentence message below can tell "you already wrote the heading"
        # apart from "there is no heading in play here".
        heading_present = None
        if pat:
            heading_present = any(re.search(pat, h, re.I) for h in headings)
        advisory = bool(r.get('advisory'))
        if pat and not heading_present:
            out.append({'kind': 'heading', 'advisory': advisory, 'message': (
                f"[{r.get('_source', '?')}] this reply has no MARKDOWN HEADING "
                f"matching /{pat}/i. Bold text is not a heading -- the closing "
                f"list has to be a real `## ` heading, or it is exactly as "
                f"skimmable as the rest of the reply."
                + (f" (practice: {r['practice']})" if r.get('practice') else ''))})
        one_of = r.get('require_one_of') or []
        if one_of and not any(_norm(o) in _norm(text) for o in one_of):
            out.append({'kind': 'sentence', 'advisory': advisory, 'message': (
                f"[{r.get('_source', '?')}] this reply says none of: "
                + '; '.join(f'"{o}"' for o in one_of)
                + ("." if advisory else
                   ". One of them has to be there, in those words -- an absent "
                   "line and a 'nothing is outstanding' line look identical on "
                   "the page and mean opposite things.")
                + (" Your reply ALREADY CARRIES the heading this belongs "
                   "under, so add the sentence as one more line there -- do "
                   "NOT write that section a second time."
                   if heading_present and not advisory else '')
                + (f" ({r['_context_note']})" if r.get('_context_note') else '')
                + (f" (practice: {r['practice']})" if r.get('practice') else ''))})
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
            bits = []
            if r.get('require_heading_matching'):
                bits.append(f"heading /{r['require_heading_matching']}/i")
            if r.get('require_one_of'):
                bits.append(f"one of {r['require_one_of']}")
            if r.get('require_when_context_grew_tokens'):
                bits.append("ONLY once the context has grown "
                            f"{int(r['require_when_context_grew_tokens']):,} "
                            "tokens since that was last said")
            if r.get('advisory'):
                bits.append("ADVISORY -- named when unmet, never blocks")
            print(f"  {r.get('_source')}: " + ', '.join(bits))
        return 0

    timeline = None
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
        timeline = assistant_timeline(transcript)
        text = last_assistant_text(transcript)
        if not text:
            # No transcript we could parse, or a turn with no prose in it.
            # Never block on the check's own blindness.
            return 0

    # A turn with no prose in it has no closing line to check -- in either
    # path. The transcript branch already returns early for it; --text needs
    # the same, and a blank file is the shape a caller uses to ask "would
    # this block?" about a tool-only turn.
    #
    # A turn that opens with the fixed trivial-check-in template is the
    # documented substitute for a Boildown, not a shorter one -- exempt the
    # same way (practice: the-boildown).
    if not reqs or not text.strip() or is_trivial_checkin(text):
        return 0
    bad = [b for b in violations(text, reqs, timeline) if not b.get('advisory')]
    if not bad:
        return 0
    # The reply that was just refused has ALREADY been shown to the person --
    # a Stop hook cannot un-show it. So the only correct repair is to emit the
    # missing closing on its own; re-sending the whole answer makes them read
    # it twice, which is what happened on 2026-09-13 when this message said
    # only "rewrite the closing" and the session rewrote everything.
    # practice: durable-fix, label-describes-content.
    #
    # THE SECOND INCIDENT, 2026-09-14, is why there are two messages. The
    # individual set revised its required sentence that morning from "close
    # this session" to "archive this session". Every reply already carrying a
    # `## Next Steps` heading and the OLD sentence was refused for the
    # sentence alone -- and the message above, which says "the missing closing
    # SECTION(S)", got what it asked for: the session wrote a whole second
    # `## Next Steps` block. Morgan: *"In various recent sessions of the last
    # few minutes, you repeated the 'next steps' section two times."* A
    # sentence-only failure now says sentence-only, in the imperative, and
    # names the repeat as the thing not to do.
    if any(b['kind'] == 'heading' for b in bad):
        print('The reply gate blocked this turn. The person has ALREADY SEEN '
              'the reply above, so do NOT write it again: output ONLY the '
              'missing closing section(s) named below, as a short addition to '
              'what you already said. Nothing else -- no summary, no '
              'restatement, no apology.', file=sys.stderr)
    else:
        print('The reply gate blocked this turn. The person has ALREADY SEEN '
              'the reply above, and it ALREADY CARRIES every closing heading '
              'it needs -- what is missing is a SENTENCE. Output that one line '
              'and nothing else. Do NOT repeat the closing section you just '
              'wrote: a second copy of it is the exact failure this message '
              'exists to prevent. No new heading, no summary, no restatement, '
              'no apology.', file=sys.stderr)
    for b in bad:
        print(f"  - {b['message']}", file=sys.stderr)
    print('  Full rules: `python3 tools/precedent_gate.py reply`.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
