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
      "require_no_contradiction": [
        {"if_says": "Nothing is blocked",
         "must_not_say_matching": "still (waiting|open|pending)"}
      ],
      "require_no_bare_pattern": [
        {"pattern": "\\bPR #\\d+\\b",
         "why": "a pull request number names a page with a destination"}
      ],
      "why": "<what goes wrong when the reply omits it>"
    }

`require_no_contradiction` is a narrower kind of check than the other two --
it never judges whether a verdict sentence is the RIGHT one (unreachable
from a repo-scoped script, per the-boildown's own Install section), only
whether the reply asserts it in the same breath as a plain-language phrase
that means the opposite. Added 2026-09-20 after exactly that: a reply said
"nothing is blocking" and then closed with "Don't archive this session".

`require_no_bare_pattern` checks a different practice family entirely --
rule-links and branch-links, both of which say a mentioned destination (a
PR, a session, a branch, a rule) gets a link the first time it is named, and
neither of which had a mechanical check before this. Each entry is a
`{pattern, why}` pair; every markdown link (`[text](url)`) in the reply is
stripped out FIRST, and each pattern is then tested against what remains --
a match there is a mention that never appeared inside a link at all. Because
the strip happens once, up front, a thing linked on its first mention and
named bare again later in the same reply still matches, which is a known
imprecision (rule-links only requires the FIRST mention to be linked) rather
than a bug -- see this repo's own reply_check.json, which declares this
predicate `advisory` for exactly that reason. Added 2026-09-20 after a bare
"PR #21" in a chat reply went unlinked and uncaught in a downstream
consumer.

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
import subprocess
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
        root = pathlib.Path(s['path'])
        cfg = root / CONFIG_NAME
        # A SOURCE THAT IS NOT THERE IS A NOTE; a source that is there and
        # declares nothing is silence. Until 2026-09-21 both took the same
        # `continue` and this function's own docstring claimed otherwise.
        #
        # The distinction is the whole point. Most sources genuinely have no
        # reply_check.json, and saying so every turn would be noise. But a
        # source whose CHECKOUT is missing declares its requirements
        # somewhere this session cannot read, and "no requirements" and
        # "requirements I could not reach" must never look the same --
        # the same rule this repo applies to its own check suite, where a
        # skip is not a pass. A set whose sibling BestPractice clone is
        # absent gets none of universal's blocking reply rules, and before
        # this it got no hint of that either.
        if not root.is_dir():
            notes.append(f"{s['level']}/{s['name']} is not on disk at "
                         f"{s['path']!r}, so any reply requirement it "
                         f"declares is NOT in force here -- unknown, not "
                         f"absent")
            continue
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


# Double-quoted spans only, never single -- a single quote or curly
# apostrophe is the same character English contractions use constantly
# ("Don't", "it's"), so treating it as a span delimiter would eat
# unpredictable stretches of ordinary prose. Double quotes carry no such
# collision, and this repo's own convention already uses them (never single
# quotes) to cite an exact phrase in running prose (this file's own
# docstring, reply_check.json's `why` fields, every *"..."* quote in the
# practice files). practice: the-boildown, cite-the-incident.
_DQUOTE_SPAN_RE = re.compile(r'"[^"]*"|“[^”]*”')


def _strip_quoted_spans(s):
    """Blank out every double-quoted span in `s`. A reply that CITES a
    phrase as a string -- describing a rule, quoting what a check refuses --
    is not ASSERTING that phrase, and require_no_contradiction's job is to
    catch the second, never the first. (2026-09-20: a reply explaining this
    very check quoted both trigger phrases and both contradiction patterns
    in the same paragraph, in single quotes -- which _norm() already folds
    to a bare apostrophe, so nothing distinguished them from the real
    thing, and the check refused the reply that had just shipped it. Fixed
    by stripping quoted citations before matching, and by this file's own
    convention -- double quotes, not single -- for citing these phrases
    from here on.)"""
    return _DQUOTE_SPAN_RE.sub(' ', s)


# A markdown link's text may itself look like the thing require_no_bare_pattern
# is hunting for ("[PR #21](https://...)"), so the whole `[text](url)` span
# is blanked out, not just the URL -- otherwise the pattern would still match
# inside the display text of a link that already satisfies rule-links (a
# shared-set practice this repo's own catalogue does not carry, so this is
# named without the anchored `practice:` form -- see
# todo-2026-09-07-universal-code-cites-team-slug for why, in the fail-gracefully
# citations that were in exactly this spot until they were promoted).
_MD_LINK_RE = re.compile(r'\[[^\]]*\]\([^)]*\)')


def _strip_markdown_links(s):
    """Blank out every markdown link in `s`. What is left is prose that was
    never wrapped in a link at all -- exactly what require_no_bare_pattern
    tests its patterns against, since a mention already linked is not a bare
    one, whatever text the link displays."""
    return _MD_LINK_RE.sub(' ', s)


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


# Every key a requirement entry may carry: the predicates this engine can
# evaluate, plus the metadata that describes one. Anything else is a
# requirement THIS engine does not understand -- see _unknown_predicates().
KNOWN_REQUIREMENT_KEYS = frozenset({
    # predicates
    'require_heading_matching',
    'require_one_of',
    'require_no_contradiction',
    'require_no_bare_pattern',
    'require_paired_with',
    'require_container_safe_if_says',
    'unless_reply_declares_loss',
    # conditions and metadata
    'require_when_context_grew_tokens',
    'advisory',
    'practice',
    'why',
    'checks_practice_at',
})


def _unknown_predicates(req):
    """-> sorted keys of `req` this engine has no branch for.

    WHY A REQUIREMENT NOBODY CAN EVALUATE MUST SAY SO. A practice source's
    reply_check.json is read LIVE from that source's own checkout, while the
    engine that evaluates it is VENDORED into the consuming repo -- two
    files that travel by completely different routes and go stale
    independently. So a source can declare a blocking requirement that the
    consumer's older engine has never heard of.

    Until 2026-09-21 that produced nothing at all: no violation, no warning,
    no trace. Measured against the requirement added that same day --
    current engine: 1 violation; an engine without the branch: 0 violations
    and silence. A set could sit for weeks believing a blocking rule was in
    force with nothing enforcing it, which is exactly the "reads as coverage
    and covers nothing" failure, in the one file whose whole job is refusing
    turns.

    Reported, never enforced. The reply is not what is wrong here -- the
    ENGINE is old -- and refusing somebody's turn over their vendored copy's
    age would punish the wrong thing at the wrong moment. The remedy is one
    command, and the message names it.

    Keys starting with `_` are skipped: declared_requirements() adds its own
    (`_source`), and a source is free to use the same convention for a
    comment, exactly as precedent.json does throughout.
    """
    return sorted(k for k in req
                  if not k.startswith('_') and k not in KNOWN_REQUIREMENT_KEYS)


def violations(text, reqs, timeline=None):
    """-> list of records, one per unmet requirement:

        {'kind': 'heading' | 'sentence' | 'contradiction' | 'bare_pattern'
                 | 'paired' | 'unknown_predicate',
         'message': <human-readable>, 'advisory': bool}

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
        _unknown = _unknown_predicates(r)
        if _unknown:
            out.append({'kind': 'unknown_predicate', 'advisory': True,
                        'message': (
                            f"[{r.get('_source', '?')}] declares "
                            + ', '.join(sorted(_unknown))
                            + ", which THIS engine cannot evaluate -- so that "
                              "requirement is not being enforced here, and "
                              "until now said nothing. The source is read "
                              "live; the engine is vendored, so the two go "
                              "stale independently. Refresh the vendored "
                              "engine: python3 tools/precedent_vendor_engine.py "
                              "refresh <bestpractice-clone>"
                            + (f" (practice: {r['practice']})"
                               if r.get('practice') else ''))})
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
        # require_no_contradiction does NOT try to judge whether a verdict
        # sentence is CORRECT -- the-boildown's own Install section already
        # tried that and gave up: "no regex distinguishes 'waiting on the
        # billing number you're pulling' from three bullets that happen to
        # precede the sentence." This is narrower and does not need to:
        # it only catches a reply asserting the fixed sentence AND, in the
        # same breath, a plain-language phrase that means the opposite --
        # "nothing blocking" beside "Don't archive this session", or a
        # still-open/waiting-on-you phrase beside "You can archive this
        # session". Both halves are never simultaneously true, whatever the
        # real state is, so this needs no judgment about which one is right
        # -- only that a reply is not allowed to assert both at once.
        # (2026-09-20: a reply said "no open work is blocking either way"
        # and closed with "Don't archive this session" -- exactly this
        # shape, caught by the person, not by any check. practice:
        # the-boildown, cite-the-incident.)
        #
        # Both patterns in reply_check.json's require_no_contradiction entry
        # exclude a trailing scope qualifier ("there", "on it/that/this",
        # "for it/that/this") via a negative lookahead -- same day, second
        # incident: "nothing left to do there", scoped to one closed PR
        # inside a Boildown bullet, is not asserting the opposite of a
        # correct "Don't archive this session" driven by a different, real
        # open item elsewhere in the same reply. Same family as the
        # double-quote citation exemption above: a phrase scoped away from
        # the whole session is not the assertion this check exists to catch.
        quoted_stripped = _strip_quoted_spans(text)
        for pair in (r.get('require_no_contradiction') or []):
            trigger, pat2 = pair.get('if_says'), pair.get('must_not_say_matching')
            if not trigger or not pat2:
                continue
            if (_norm(trigger) in _norm(quoted_stripped)
                    and re.search(pat2, quoted_stripped, re.I)):
                out.append({'kind': 'contradiction', 'advisory': advisory, 'message': (
                    f"[{r.get('_source', '?')}] this reply says \"{trigger}\" and "
                    f"ALSO matches /{pat2}/i elsewhere in the same reply -- the two "
                    "cannot both be true. Re-check the actual state (a fresh "
                    "push/fetch or the real condition, not what an earlier line in "
                    "this same reply already claimed) and fix whichever one is wrong."
                    + (f" (practice: {r['practice']})" if r.get('practice') else ''))})
        # require_no_bare_pattern closes the gap rule-links and branch-links
        # left mechanically unchecked: both say a mentioned destination gets
        # a link the first time it is named, and neither had any way to
        # catch a plain miss until this. (Named without the anchored
        # `practice:` form -- both live in a shared set this repo's own
        # catalogue does not carry; see the note beside _MD_LINK_RE above.)
        # Markdown links are stripped from the whole reply FIRST (a mention
        # already inside a link is not a bare one), then each declared
        # pattern is tested against what remains -- a match is a mention
        # that never appeared in a link anywhere in the reply.
        link_stripped = _strip_markdown_links(text)
        for entry in (r.get('require_no_bare_pattern') or []):
            pattern, pat_why = entry.get('pattern'), entry.get('why')
            if not pattern:
                continue
            m = re.search(pattern, link_stripped)
            if m:
                out.append({'kind': 'bare_pattern', 'advisory': advisory, 'message': (
                    f"[{r.get('_source', '?')}] this reply mentions "
                    f"\"{m.group(0)}\" without a markdown link to it"
                    + (f" -- {pat_why}" if pat_why else '') + "."
                    + (f" (practice: {r['practice']})" if r.get('practice') else ''))})

        # require_paired_with: when the reply contains X, it must also
        # contain Y. The mirror of require_no_contradiction -- that one
        # forbids a pairing, this one compels it.
        #
        # WHY IT EXISTS (Morgan, 2026-09-21, strength: decided, and the
        # capitals are his): "EVERY TIME YOU GIVE ME SOMETHING TO PASTE,
        # ALWAYS TELL ME IT GOES TO A SESSION ROOTED IN WHAT REPO AND WHAT
        # ATTACHED, OR WHAT EXISTING SESSION. YESTERDAY AND TODAY I ASKED
        # YOU 20 TIMES 'The text you gave me, what session is it for?'"
        #
        # fence-block-for-paste already made the FENCE mandatory, which is
        # why every one of those twenty blocks was correctly fenced and
        # none of them said where it went. A block of text with no
        # destination is not a handoff; it is homework, and the person has
        # to come back and ask before they can do anything with it.
        for pair in (r.get('require_paired_with') or []):
            trigger, needed = pair.get('if_matches'), pair.get('must_also_match')
            if not (trigger and needed):
                continue
            if re.search(trigger, text, re.I | re.M) and not re.search(
                    needed, text, re.I | re.M):
                out.append({'kind': 'paired', 'advisory': advisory, 'message': (
                    f"[{r.get('_source', '?')}] this reply matches "
                    f"/{trigger}/ but nothing in it matches /{needed}/"
                    + (f" -- {pair.get('why')}" if pair.get('why') else '')
                    + "."
                    + (f" (practice: {r['practice']})" if r.get('practice') else ''))})

        # require_container_safe_if_says: the only predicate here that looks
        # at the DISK rather than at the reply. When the reply says one of
        # these phrases, tools/precedent_container_safe.py must agree that
        # nothing in this container would be lost if it went away.
        #
        # WHY A TEXT CHECKER GREW A STATE CHECK (Morgan, 2026-09-22,
        # strength: decided): "if changes are done locally but not pushed to
        # main or precedent-beta-v01 then never never recommend 'You can
        # archive this session' (unless the work is intended to be lost!)".
        # Every other archive-line mechanism here reads the reply against
        # itself -- require_no_contradiction catches a reply that says both
        # halves at once and, by its own docstring, deliberately does not
        # judge whether the verdict is CORRECT. That was the right line to
        # draw while the verdict needed a judgment no script could make.
        # This one does not: "would anything be lost" is a fact about a
        # filesystem, and a script reads it better than a session
        # remembering which of six checkouts it has pushed. On 2026-09-22 a
        # session said the archive line with six unpushed commits sitting in
        # a source clone it had never looked at, and nothing caught it.
        #
        # Blocking, not advisory, and that is the whole point: archiving
        # releases the container, so this is the one closing claim whose
        # cost cannot be undone by saying it again next turn.
        for phrase in (r.get('require_container_safe_if_says') or []):
            # Quoted spans stripped, same as require_no_contradiction above
            # and for the same reason: a reply QUOTING the sentence -- this
            # practice's own text, a message being discussed -- is not
            # asserting it.
            if _norm(phrase) not in _norm(quoted_stripped):
                continue
            verdict = _container_verdict()
            if verdict is None:
                continue
            ok, report = verdict
            if not ok and _declares_loss(r, quoted_stripped):
                # THE EXCEPTION THE RULE ALWAYS HAD, FINALLY IMPLEMENTED.
                # Morgan's own words, quoted in this rule's `why` since
                # 2026-09-22: "never never recommend 'You can archive this
                # session' (unless the work is intended to be lost!)". The
                # parenthesis was never coded. The refusal text even told
                # the reader how to satisfy it -- "or say in the reply that
                # it is meant to be lost" -- and then ignored them doing so.
                #
                # On 2026-09-23 a session said exactly that, in those words,
                # in three consecutive replies about 34 watermark commits it
                # had established were superseded pointer advances in a
                # clone 74 commits behind its own origin and on an owner the
                # git proxy refuses pushes to. All three turns were refused,
                # so all three ended by telling the person NOT to archive a
                # session they could safely archive. A gate that forces a
                # false statement has stopped being a safety mechanism.
                #
                # It is deliberately not a magic phrase: `_declares_loss`
                # also requires the reply to NAME every checkout being given
                # up, so a session cannot wave away work it has not looked
                # at -- which is the exact 2026-09-22 failure this rule was
                # built for, and it stays caught.
                continue
            if not ok:
                out.append({'kind': 'container', 'advisory': False, 'message': (
                    f"[{r.get('_source', '?')}] this reply says "
                    f"\"{phrase}\" and this container is NOT safe to lose:"
                    f"\n{report}\n"
                    f"Push or merge it -- or say in the reply that it is "
                    f"meant to be lost -- before saying that sentence."
                    + (f" (practice: {r['practice']})" if r.get('practice') else ''))})
    return out


def _declares_loss(rule, text):
    """-> True when the reply has deliberately given up the unsafe work.

    Two conditions, and BOTH are needed. The reply says one of the rule's
    declared phrases, and it names every checkout the scanner called unsafe.
    The naming half is what keeps this from being a password: a session that
    has not looked at a clone cannot name it, and one that has can say so in
    the same breath as giving it up.

    Matching is on the checkout's directory name (`precedent-individual`),
    not its full path, because that is what a reply to a person actually
    writes. An unreadable or unrunnable scanner returns False -- the same
    fail-closed posture the caller takes everywhere else about this
    sentence, since archiving cannot be undone next turn."""
    phrases = (rule.get('unless_reply_declares_loss') or {}).get('phrases') or []
    if not phrases:
        return False
    if not any(_norm(ph) in _norm(text) for ph in phrases):
        return False
    names = _unsafe_checkout_names()
    if not names:
        # The scanner said unsafe but could not say WHICH. Nothing here can
        # verify the naming half, so the escape is not available.
        return False
    low = text.lower()
    return all(n.lower() in low for n in names)


def _unsafe_checkout_names():
    """-> [directory name] for each checkout the scanner calls unsafe, or []
    when it cannot be run or read. Run only on the unsafe path, which is
    rare, so the second subprocess costs nothing in the ordinary case."""
    tool = pathlib.Path(__file__).resolve().parent / 'precedent_container_safe.py'
    if not tool.is_file():
        return []
    try:
        p = subprocess.run([sys.executable, str(tool), '--json'],
                           capture_output=True, text=True, timeout=120)
        payload = json.loads(p.stdout or '{}')
    except (OSError, subprocess.SubprocessError, ValueError):
        return []
    names = []
    for entry in payload.get('unsafe') or []:
        repo = str(entry.get('repo') or '').rstrip('/')
        if repo:
            names.append(pathlib.PurePath(repo).name)
    return names


def _container_verdict():
    """-> (safe, report) from tools/precedent_container_safe.py, or None
    when this engine has no copy of it to run.

    None, rather than a violation, on a missing or unrunnable scanner. An
    engine vendored before the scanner existed is an OLD ENGINE, not a
    broken reply -- exactly the case _unknown_predicates() already reasons
    about above, and refusing somebody's turn over their vendored copy's age
    would punish the wrong thing at the wrong moment. `--brief` is not
    offered: the person needs to know WHICH checkout, or the refusal tells
    them nothing they can act on."""
    tool = pathlib.Path(__file__).resolve().parent / 'precedent_container_safe.py'
    if not tool.is_file():
        return None
    try:
        p = subprocess.run([sys.executable, str(tool)],
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.returncode == 0, (p.stdout or p.stderr or '').strip()


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
            if r.get('require_no_contradiction'):
                for pair in r['require_no_contradiction']:
                    bits.append(f"\"{pair.get('if_says')}\" must not also match "
                                f"/{pair.get('must_not_say_matching')}/i")
            if r.get('require_no_bare_pattern'):
                for entry in r['require_no_bare_pattern']:
                    bits.append(f"no bare (unlinked) match of /{entry.get('pattern')}/")
            if r.get('require_paired_with'):
                for pair in r['require_paired_with']:
                    bits.append(f"/{pair.get('if_matches')}/ requires "
                                f"/{pair.get('must_also_match')}/")
            if r.get('require_container_safe_if_says'):
                for ph in r['require_container_safe_if_says']:
                    bits.append(f'"{ph}" requires a container with nothing '
                                f'uncommitted and nothing off a remote '
                                f'(tools/precedent_container_safe.py)')
            if r.get('require_when_context_grew_tokens'):
                bits.append("ONLY once the context has grown "
                            f"{int(r['require_when_context_grew_tokens']):,} "
                            "tokens since that was last said")
            _unk = _unknown_predicates(r)
            if _unk:
                bits.append('!! ' + ', '.join(_unk)
                            + ' -- NOT EVALUATED by this engine (too old); '
                              'refresh the vendored engine')
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
    elif any(b['kind'] == 'contradiction' for b in bad):
        print('The reply gate blocked this turn: it asserts two things named '
              'below that cannot both be true. The person has ALREADY SEEN '
              'the reply above -- do NOT repeat it. Re-check the actual state '
              '(fetch/push status, what is really outstanding) rather than '
              'trusting either half of the contradiction, then output ONLY a '
              'short correction of whichever line was wrong.', file=sys.stderr)
    elif any(b['kind'] == 'container' for b in bad):
        # NOT the sentence-only message below. This refusal is not "you left
        # a line out" -- it is "the line you wrote is false, and acting on it
        # destroys the work named below". The repair is a push or a merge
        # first, in the checkouts named, and only then a corrected line.
        print('The reply gate blocked this turn: it told the person they can '
              'archive, and this container holds work that exists nowhere '
              'else -- named below, with the checkout it is in. The person '
              'has ALREADY SEEN the reply above -- do NOT repeat it. PUSH OR '
              'MERGE that work first, in each checkout named; then output '
              'ONLY a short correction of the archive line. If it is '
              'genuinely meant to be lost, say so in the reply, in those '
              'words.', file=sys.stderr)
    elif any(b['kind'] == 'bare_pattern' for b in bad):
        print('The reply gate blocked this turn: it names something with a '
              'destination -- a PR, a session, a branch, a rule -- without '
              'linking it, named below. The person has ALREADY SEEN the '
              'reply above -- do NOT repeat it. Output ONLY a short '
              'correction that adds the missing link(s) in place of the '
              'bare mention(s).', file=sys.stderr)
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
