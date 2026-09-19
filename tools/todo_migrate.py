#!/usr/bin/env python3
"""todo_migrate.py — one-time converter from the old TODO.md / gotchas-index
format into the per-item file format spec/OPEN_ITEM_AND_GOTCHA_PLAN.md
specifies (Part 1: open items under todo/, Part 2: gotchas under gotchas/).

Part 4.1 step 4 built this alongside tools/build_todo_index.py; step 5 is
the real run against every remaining item and gotcha, and per the plan's
own "Decisions" section (step 3) that real run is announced by name
("starting step 5 now") and follows a reviewed dry run against a handful
of real items -- this tool defaults to that dry run and only writes files
when told to.

What it does NOT try to do: split an old item's freeform prose into the
target format's ## What / ## How It Closes / ## Notes sections by
understanding the prose. `## What` gets the item's full original text
verbatim (title plus body) -- that is what "written once, rarely touched
again" already describes, and it is what the old format already was.
`## How It Closes` gets one line synthesized from a "Blocked on:" /
"Blocked-on:" clause when the item states one, and a placeholder asking a
session to fill it in otherwise. Per the plan's own Part 4.1: `domain` and
`severity` are left `null` on every migrated item -- guessed at for a
few dozen files in bulk is the wrong trade, and a session sets them when
it next touches the item, same as `decision_strength`.

A checked box (`- [x] ...`) always migrates to `status: done`. A checkbox
alone cannot distinguish "done" from "abandoned/overtaken/moot" -- this
tool does not try to infer that from the checkbox bit alone. Hand-review
any checked item whose own text reads as an abandonment ("moot",
"overtaken", "superseded" near the checkbox is a reasonable heuristic to
scan for) and correct its `status` to `dropped` before committing the
migration's output.

`noted` (the day an item was first written down) is computed the same way
spec/OPEN_ITEM_AND_GOTCHA_PLAN.md's own Appendix measured it: the first
commit in this repository's history whose diff introduces that item's own
`id="<slug>"` anchor string in the source file, via
`git log -S'id="<slug>"'`. Anchors were retrofitted onto every item on
2026-09-06 (TODO.md's own header note), so for an item that existed before
that sweep this is a FLOOR, not the true creation date -- the migration
writes the caveat spec/OPEN_ITEM_AND_GOTCHA_PLAN.md's "Every Item Has a
Date" section asks for into ## Notes when the found commit is at or before
that sweep.

Run:
  python3 tools/todo_migrate.py --source todo.md
      # dry run: parse TODO.md, print what WOULD be written for every item,
      # write nothing.
  python3 tools/todo_migrate.py --source todo.md --slug SLUG [SLUG ...]
      # dry run against only the named item(s) -- the "handful of real
      # items" the plan's Decisions section asks for before the real run.
  python3 tools/todo_migrate.py --source todo.md --limit N
      # dry run against the first N items in file order.
  python3 tools/todo_migrate.py --source todo.md --apply
      # write todo/todo-<date>-<slug>.md for every item (or every named
      # / limited subset), and print the old-slug -> new-filename mapping
      # table the plan's step 5 requires.
  python3 tools/todo_migrate.py --source gotchas.md --status live --apply
  python3 tools/todo_migrate.py --source gotchas-archive.md --status retired --apply
      # same shape, for record/GOTCHAS.md and record/GOTCHAS_ARCHIVE.md,
      # writing gotchas/gotcha-<date>-<slug>.md instead.
  python3 tools/todo_migrate.py --source todo.md --repo DIR [...]
      # operate on DIR's TODO.md / todo/ instead of this repo's own.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # practice: timestamps-carry-offset -- the one module

# The bullet marker a top-level item starts with: an unordered `- ` bullet,
# or a NUMBERED `51. ` one. Both are real pre-migration shapes -- this
# repository's own TODO.md used numbered markers for 119 of its 148
# top-level items right up to the commit that migrated it (`9a08363b`,
# 2026-09-16), and dash markers for the other 29. Found 2026-09-19, after
# that migration turned out to have dropped 50 items with no trace: this
# regex, at the time, matched `-\s+` only, so a numbered item could never
# start a `starts` entry on its own. It is not proven to be what actually
# happened in that one giant hand-and-tool commit (some numbered items DID
# get real todo/ files, so whatever ran was not purely "run this regex over
# the file" -- see todo/todo-2026-09-19-migration-dropped-54-items.md for
# the fuller account), but it is a real gap this tool would hit again on
# any TODO.md still using numbered markers, precedent-individual's among
# them per its own not_binding exemption. Fixed here regardless of whether
# it explains the original loss, because the next repo to run this tool
# should not have to find out the same way.
BULLET_MARKER_RE = r'(?:-|\d+\.)\s+'
TODO_ANCHOR_RE = re.compile(r'^' + BULLET_MARKER_RE + r'(?:\[ \]\s+)?<a id="([^"]+)"></a>')
TODO_BARE_RE = re.compile(r'^' + BULLET_MARKER_RE + r'\*\*')
# A checkbox bullet with no anchor -- `- [ ] **Title.**` / `- [x] **Title.**` --
# is a DIFFERENT shape from both of the above: TODO_ANCHOR_RE requires an
# `<a id=>` tag after an optional checkbox, and TODO_BARE_RE requires `**`
# immediately after `- `, with no checkbox in between. Neither matches this
# shape at all, so a file using it (the shape templates/TODO.md.template
# itself taught every consumer before the todo/ migration -- see e.g. its own
# `- [ ] **Precedent check-in:**` example) parses as ZERO items: no anchor,
# no bare-bold start is ever found, so parse_todo_items's own `starts` list
# stays empty except for the sentinel, and the whole file becomes either no
# items at all, or -- worse -- a single fabricated "item" if some unrelated
# prose bullet elsewhere happens to match TODO_BARE_RE (a bold label with no
# checkbox, e.g. "- **Claiming (multi-member repos):**" in this same
# template's own intro prose), silently swallowing everything after it up to
# the next such bullet. Found 2026-09-18 running this tool against a real
# consumer's TODO.md for the first time since #445 vendored it out.
TODO_CHECKBOX_RE = re.compile(r'^' + BULLET_MARKER_RE + r'\[([ xX])\]\s+\*\*')
GOTCHA_HEADING_RE = re.compile(
    r'^##\s+\d+\.\s+(?:<a id="(g\d+)"></a>)?(.*)$')
# A plain `##` heading in a TODO file -- not the gotcha format's numbered
# one above. This is the classic template's REAL kind signal
# (templates/TODO.md.template pre-migration: "## Analyses (agent-doable)",
# "## Verify before external use", "## Decisions (user's call)"), which
# parse_todo_items previously threw away entirely -- it only looked for
# bullet starts, never recorded which heading preceded one. A section
# whose text doesn't name a kind (e.g. "## Recurring") yields no match,
# same as no heading at all.
TODO_SECTION_HEADING_RE = re.compile(r'^##\s+(.*)$')
SECTION_KIND_RE = re.compile(
    r'\b(analys(?:is|es)|verif(?:y|ication)|physical|manual|decisions?)\b',
    re.IGNORECASE)
SECTION_KIND_MAP = {
    'analysis': 'analysis', 'analyses': 'analysis',
    'verify': 'verify', 'verification': 'verify',
    'physical': 'manual', 'manual': 'manual',
    'decision': 'decision', 'decisions': 'decision',
}
# An item's own explicit kind marker, e.g. "...done. (**decision**)" --
# reported from a real consumer's TODO.md, not attested anywhere in this
# repo's own history (checked both the template's real classic version and
# this repo's own pre-migration TODO.md). Kept as a fallback below the
# section heading for exactly that reason: it may be real in some
# consumer's own drifted template copy, and costs nothing when absent.
KIND_MARKER_RE = re.compile(
    r'\(\*\*(analysis|verify|verification|physical|manual|decision)\*\*',
    re.IGNORECASE)
KIND_MARKER_MAP = {'verification': 'verify', 'physical': 'manual'}

class TodoShapeError(ValueError):
    """Raised when a source file matches none of parse_todo_items's known
    start shapes -- see _heading_per_item_shaped()."""


TITLE_RE = re.compile(r'\*\*(.+?)\*\*', re.DOTALL)
BLOCKED_ON_RE = re.compile(
    r'\*\*Blocked[- ]on(?:\s*/\s*out of scope)?:?\*\*\s*(.+?)'
    r'(?:\n\n|\*\*Disposition:|\Z)',
    re.DOTALL)
DISPOSITION_RE = re.compile(r'\*\*Disposition:\*\*\s*(\w+)')
REMIND_RE = re.compile(r'\*\*Remind:\*\*')
WAITING_ON_NAME_RE = re.compile(r'\b(Morgan|Alex)\b')

DECISION_CUES = ('decide whether', 'decide the', 'decide how')
VERIFY_CUES = ('verify ', 'confirm ', 'measure whether', 'check whether',
               're-verify')
MANUAL_CUES = ('no session can', 'cannot be done from a session',
               'needs morgan to', 'needs him to', 'a person', 'by hand')


def _slugify(text):
    text = re.sub(r'[`*_\[\]()]', '', text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", '-', text)
    return text.strip('-')[:60] or 'item'


def _run(*cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def anchor_noted_date(repo, source_relpath, anchor_id, wrap_id=True):
    """First commit (oldest) whose diff introduces `id="<anchor_id>"` (or,
    with `wrap_id=False`, the literal string `anchor_id` itself -- for a
    source with no `<a id=>` to search for, such as GOTCHAS_ARCHIVE.md, a
    distinctive snippet of the entry's own title is still real text that
    is literally in the file) in `source_relpath`. Returns (date,
    is_floor) -- is_floor is True when the found commit is at or before
    2026-09-06, the day every TODO.md item's anchor was retrofitted
    (TODO.md's own header note), which means the date is a lower bound on
    the item's true age, not the true age itself. Falls back to this
    repository's own earliest commit (a floor either way) if the string
    cannot be found at all -- e.g. text that has since been reworded."""
    needle = f'id="{anchor_id}"' if wrap_id else anchor_id
    rc, out, _ = _run('git', 'log', f'-S{needle}', '--format=%ad',
                       '--date=short', '--follow', '--', source_relpath,
                       cwd=repo)
    dates = [d for d in out.splitlines() if d.strip()]
    if rc == 0 and dates:
        oldest = dates[-1]
        return oldest, oldest <= '2026-09-06'
    rc, out, _ = _run('git', 'log', '--format=%ad', '--date=short', cwd=repo)
    dates = [d for d in out.splitlines() if d.strip()]
    floor = dates[-1] if dates else '1970-01-01'
    return floor, True


class Item:
    def __init__(self, anchor, title, body, has_anchor, checked=None,
                 section_kind=None):
        self.anchor = anchor
        self.title = title
        self.body = body
        self.has_anchor = has_anchor
        # None: this item's start line carries no checkbox at all (the
        # anchor-tagged or bare-bold shapes) -- checkbox-open/closed is not
        # this format's own way of saying status, so build_plan's caller
        # decides some other way (today: always 'open', a pre-existing gap
        # this migration doesn't try to fix). True/False: `- [x] `/`- [ ] `
        # was matched, and IS this format's own status signal -- honor it.
        self.checked = checked
        # The kind-named `##` section this item was filed under in the
        # source file (None outside any such section, or under one whose
        # heading names no kind, e.g. "## Recurring"). See guess_kind().
        self.section_kind = section_kind

    @property
    def slug(self):
        return self.anchor or _slugify(self.title)


def _heading_per_item_shaped(lines):
    """True if this file uses one `## <slug>` heading per item, each with
    its own **Disposition:** line nearby, rather than a flat bullet list --
    a real pre-migration shape (found 2026-09-18 against a real consumer's
    TODO.md, which used exactly this) that none of TODO_ANCHOR_RE /
    TODO_CHECKBOX_RE / TODO_BARE_RE recognizes. Left undetected, an
    indented `- **Blocked on:**` / `- **Disposition:**` sub-bullet under
    each heading matches TODO_BARE_RE as if it were its own top-level item,
    fabricating two items per real one and swallowing whichever headings
    fall between a fabricated item and the next bullet into that item's
    body verbatim. Detected by the same signature that trips the bug: at
    least two `##` headings, each followed shortly by a **Disposition:**
    line before the next heading."""
    heading_idxs = [i for i, l in enumerate(lines)
                    if TODO_SECTION_HEADING_RE.match(l)]
    if len(heading_idxs) < 2:
        return False
    bounds = heading_idxs + [len(lines)]
    with_disposition = sum(
        1 for j, i in enumerate(heading_idxs)
        if any(DISPOSITION_RE.search(l) for l in lines[i:bounds[j + 1]]))
    return with_disposition >= 2 and with_disposition == len(heading_idxs)


def parse_todo_items(text):
    """Split TODO.md's flat bullet list into Items. A bullet starts a new
    item at column 0 (`- ...`); everything indented under it, down to the
    next column-0 bullet, is that item's body. The file's own intro prose
    (before the first bullet) is not an item and is skipped.

    Three start shapes, tried in this order so the more specific ones win:
    an anchor-tagged bullet (`- [ ] <a id="x"></a>...` or bare), a checkbox
    bullet with no anchor (`- [ ] **Title.**` / `- [x] **Title.**` --
    templates/TODO.md.template's own pre-migration shape), or a bare bold
    bullet with neither (`- **Title.**`). TODO_CHECKBOX_RE has to be tried
    BEFORE TODO_BARE_RE: `- [ ] **` also starts with `- ` followed
    eventually by `**`, but TODO_BARE_RE's own `^-\\s+\\*\\*` does not match
    it (the checkbox sits in between), so the two never actually collide --
    the ordering just keeps that invariant explicit rather than relying on
    it by accident.

    A file shaped some other way entirely -- checked against
    _heading_per_item_shaped() before any of the three shapes are trusted
    -- raises TodoShapeError rather than silently returning whatever the
    bare-bold pattern happens to match (practice: fail-gracefully; a
    fabricated item set looks exactly like a real one to every caller
    downstream of this function).

    Also tracks the nearest preceding `##` heading for each bullet, so an
    item filed under a kind-named section (the classic template's own
    "## Analyses (agent-doable)" / "## Verify before external use" /
    "## Decisions (user's call)") carries that as `section_kind` --
    previously thrown away here entirely, before guess_kind() ever ran."""
    lines = text.split('\n')
    if _heading_per_item_shaped(lines):
        raise TodoShapeError(
            "this file doesn't match any known TODO.md shape -- it looks "
            "like one `## <slug>` heading per item with its own "
            "**Disposition:** line, which none of TODO_ANCHOR_RE / "
            "TODO_CHECKBOX_RE / TODO_BARE_RE recognizes. Parsing it anyway "
            "would fabricate items from indented sub-bullets and swallow "
            "headings' text into them -- write the todo/ items for this "
            "file by hand instead of trusting --apply.")
    starts = []
    section_kind_at = {}
    current_section_kind = None
    for i, line in enumerate(lines):
        hm = TODO_SECTION_HEADING_RE.match(line)
        if hm:
            km = SECTION_KIND_RE.search(hm.group(1))
            current_section_kind = (
                SECTION_KIND_MAP[km.group(1).lower()] if km else None)
            continue
        if TODO_ANCHOR_RE.match(line) or TODO_CHECKBOX_RE.match(line) or TODO_BARE_RE.match(line):
            starts.append(i)
            section_kind_at[i] = current_section_kind
    starts.append(len(lines))
    items = []
    for idx in range(len(starts) - 1):
        block = lines[starts[idx]:starts[idx + 1]]
        # drop trailing blank lines so body doesn't carry the separator
        while block and not block[-1].strip():
            block.pop()
        raw = '\n'.join(block)
        m = TODO_ANCHOR_RE.match(block[0])
        anchor = m.group(1) if m else None
        cm = None if anchor else TODO_CHECKBOX_RE.match(block[0])
        checked = (cm.group(1).lower() == 'x') if cm else None
        tm = TITLE_RE.search(raw)
        title = tm.group(1).strip() if tm else raw.strip().splitlines()[0][:80]
        items.append(Item(anchor, title, raw, has_anchor=bool(anchor),
                           checked=checked,
                           section_kind=section_kind_at[starts[idx]]))
    _assert_no_dropped_items(lines, items)
    return items


# Independent of the three specific start shapes above, on purpose: this
# counts every `<a id="...">` anywhere in the file, by a completely
# different method (a bare regex over the whole text, not the line-by-line
# marker scan `starts` above uses), and refuses to proceed if that number
# disagrees with how many items got parsed. Built 2026-09-19, after the
# 2026-09-16 migration (`9a08363b`) turned out to have silently dropped 50
# of 148 real items with nothing anywhere catching it -- neither this
# module nor anything downstream of it asserted the one property that
# would have caught it immediately: item count in equals item count out.
# `_heading_per_item_shaped`'s TodoShapeError guards a DIFFERENT failure
# (the whole file being an unrecognized shape); this guards the one this
# function could pass while still being wrong -- recognizing some items
# correctly and silently missing others, which looks identical to success
# at every point downstream (practice: control-asserts-which-failure).
ANY_ANCHOR_RE = re.compile(r'<a id="([^"]+)"></a>')


def _assert_no_dropped_items(lines, items):
    text = '\n'.join(lines)
    all_anchors = set(ANY_ANCHOR_RE.findall(text))
    parsed_anchors = {it.anchor for it in items if it.anchor}
    missing = all_anchors - parsed_anchors
    if missing:
        raise TodoShapeError(
            f'{len(missing)} anchor(s) exist in this file but were not '
            f'recognized as the start of any item -- parse_todo_items '
            f'found {len(items)} item(s) total. Each is either a nested '
            f'anchor inside another item\'s body (harmless -- add it to a '
            f'reviewed exemption if so) or a top-level item whose start '
            f'line matches none of TODO_ANCHOR_RE / TODO_BARE_RE / '
            f'TODO_CHECKBOX_RE (the real failure this guards). Missing: '
            + ', '.join(f'`{a}`' for a in sorted(missing)[:20])
            + (f', and {len(missing) - 20} more' if len(missing) > 20 else ''))


def parse_gotcha_items(text):
    """Split a GOTCHAS.md- or GOTCHAS_ARCHIVE.md-shaped file into Items,
    one per `## N. <a id="gN">...` or bare `## N. ...` heading (the
    archive carries no `<a id=>` at all -- its entries were never given
    one), body running to the next such heading."""
    lines = text.split('\n')
    starts = []
    for i, line in enumerate(lines):
        if GOTCHA_HEADING_RE.match(line):
            starts.append(i)
    # Independent recount, the same reason and shape as
    # _assert_no_dropped_items below: any `## N.` heading at all, matched by
    # a bare regex over the whole file rather than trusted because
    # GOTCHA_HEADING_RE happened to accept it here. Checked directly
    # 2026-09-19 against this repo's own real pre-migration files (44 in
    # record/GOTCHAS.md, 33 in record/GOTCHAS_ARCHIVE.md) and found clean --
    # unlike TODO.md's multi-shape bullet list, a single consistent heading
    # format is much harder to under-parse. Guarded anyway: "checked once
    # and found clean" is not the same claim as "cannot go wrong", and a
    # team's own GOTCHAS.md is not guaranteed to be as regular as this one.
    raw_heading_count = len(re.findall(r'^##\s+\d+\.\s+', text, re.M))
    if raw_heading_count != len(starts):
        raise TodoShapeError(
            f'{raw_heading_count} lines look like a numbered `## N.` gotcha '
            f'heading, but only {len(starts)} matched GOTCHA_HEADING_RE '
            f'exactly -- something about the other '
            f'{raw_heading_count - len(starts)} does not fit the expected '
            f'shape (a stray space, a missing period, text before the '
            f'number). Fix the file or the regex before trusting this '
            f'parse; do not proceed with a silent undercount.')
    starts.append(len(lines))
    items = []
    for idx in range(len(starts) - 1):
        block = lines[starts[idx]:starts[idx + 1]]
        while block and not block[-1].strip():
            block.pop()
        raw = '\n'.join(block)
        m = GOTCHA_HEADING_RE.match(block[0])
        anchor, title = m.group(1), m.group(2).strip()
        items.append(Item(anchor, title, raw, has_anchor=bool(anchor)))
    return items


def guess_kind(item):
    low = item.body.lower()
    title_low = item.title.lower()
    if any(title_low.startswith(c) for c in DECISION_CUES):
        return 'decision'
    if any(c in title_low for c in VERIFY_CUES):
        return 'verify'
    if any(c in low for c in MANUAL_CUES):
        return 'manual'
    return 'analysis'


def determine_kind(item):
    """The section heading an item was filed under (the classic template's
    real, verified kind signal) wins first; an explicit inline marker like
    `(**decision**)` is next (reported from one real consumer, not attested
    in this repo's own history, so it's a fallback rather than trusted
    first); guess_kind()'s phrase heuristics are last resort."""
    if item.section_kind:
        return item.section_kind
    mm = KIND_MARKER_RE.search(item.body)
    if mm:
        raw = mm.group(1).lower()
        return KIND_MARKER_MAP.get(raw, raw)
    return guess_kind(item)


def guess_blocked_on(item):
    # Items are an append-only log (## Notes' own convention, carried over
    # from the old format): a later "Blocked on:" restates or supersedes
    # an earlier one in the same item, so the LAST match is the current
    # state -- not the first, which is often the original, since-resolved
    # blocker.
    matches = list(BLOCKED_ON_RE.finditer(item.body))
    if not matches:
        return None
    text = re.sub(r'\s+', ' ', matches[-1].group(1)).strip()
    return text[:300]


def guess_disposition(item):
    if REMIND_RE.search(item.body):
        return 'ask'
    matches = list(DISPOSITION_RE.finditer(item.body))
    for m in reversed(matches):  # last stated disposition wins
        word = m.group(1).lower()
        if word in ('wait', 'ask', 'parked'):
            return word
    return 'wait'


def guess_remind_on(item, disposition, noted):
    """The plan's step 5 rule for the old `**Remind:**` convention: those
    items become `disposition: ask` with `remind_on` set to the item's own
    `noted` date -- eligible immediately, which is what `**Remind:**`
    already meant before this format gave reminders a date. Every other
    item keeps `remind_on: null`, which the spec says explicitly is legal
    and means "not a Reminder" -- an ordinary item is not turned into one
    just because it happens to carry `disposition: ask` for some other
    reason."""
    if REMIND_RE.search(item.body):
        return noted
    return None


def guess_waiting_on(blocked_on_text):
    if not blocked_on_text:
        return None
    m = WAITING_ON_NAME_RE.search(blocked_on_text)
    return m.group(1) if m else None


def _yaml_str(value):
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def render_todo_frontmatter(slug, kind, status, disposition, remind_on,
                             blocked_on, batch, decision, decision_strength,
                             waiting_on, noted, closed):
    def scalar(v):
        return 'null' if v is None else _yaml_str(v)
    return '\n'.join([
        '---',
        f'slug:              {slug}',
        f'kind:              {kind}',
        'domain:            null',
        'severity:          null',
        f'status:            {status}',
        f'disposition:       {disposition}',
        f'remind_on:         {scalar(remind_on)}',
        f'blocked_on:        {scalar(blocked_on)}',
        f'batch:             {scalar(batch)}',
        f'decision:          {scalar(decision)}',
        f'decision_strength: {"null" if decision_strength is None else decision_strength}',
        f'waiting_on:        {scalar(waiting_on)}',
        f'noted:             {noted}',
        f'closed:            {scalar(closed)}',
        '---',
        '',
    ])


def render_gotcha_frontmatter(slug, status, noted, severity, retired,
                               retires_when):
    def scalar(v):
        return 'null' if v is None else _yaml_str(v)
    return '\n'.join([
        '---',
        f'slug:            {slug}',
        f'status:          {status}',
        f'noted:           {noted}',
        f'severity:        {"null" if severity is None else severity}',
        f'retired:         {scalar(retired)}',
        f'retires_when:    {scalar(retires_when)}',
        '---',
        '',
    ])


def render_todo_body(item, blocked_on, is_floor):
    lines = ['## What', '', item.body.strip(), '', '## How It Closes', '']
    if blocked_on:
        lines.append(f'Not open until: {blocked_on}')
    else:
        lines.append('(not yet stated by the migration -- a session filling '
                      'this in should read ## What and say what has to be '
                      'true for `status` to become `done`.)')
    lines += ['', '## Notes', '']
    if is_floor:
        lines.append(
            f'{TODAY}: noted date is a floor, not exact -- this item '
            'predates anchor tracking (every anchor was retrofitted '
            '2026-09-06) and its true creation date is unknown. Migrated '
            'from TODO.md by tools/todo_migrate.py.')
    else:
        lines.append(f'{TODAY}: migrated from TODO.md by tools/todo_migrate.py.')
    lines.append('')
    return '\n'.join(lines)


def render_gotcha_body(item):
    paras = re.split(r'\n\s*\n', item.body.strip())
    # paras[0] is the `## N. <a id="gN">` heading line, whose own title
    # text is sometimes truncated with "..." (GOTCHAS.md's own heading
    # style). The real symptom statement is the first bold run inside the
    # next paragraph -- every entry opens with one, restating the heading
    # in full, unbolded surrounding prose stripped off.
    story_paras = paras[1:] if len(paras) > 1 else []
    # GOTCHAS_ARCHIVE.md opens some entries with a one-line "Verdict:
    # `compressed`." paragraph before the real symptom sentence -- skip it
    # rather than mistake it for the symptom.
    while story_paras and story_paras[0].strip().lstrip('*').startswith('Verdict:'):
        story_paras = story_paras[1:]
    symptom = item.title
    if story_paras:
        tm = TITLE_RE.search(story_paras[0])
        if tm:
            symptom = re.sub(r'\s+', ' ', tm.group(1)).strip()
    fix = None
    story = []
    for p in story_paras:
        if re.match(r'^\*\*Fix', p) or p.lower().lstrip('* ').startswith('fix'):
            fix = p
        else:
            story.append(p)
    lines = ['## Symptom', '', symptom, '', '## Story', '']
    lines.append('\n\n'.join(story) if story else '(migration found no '
                 'separate story paragraph -- see the symptom above.)')
    lines += ['', '## Fix', '']
    lines.append(fix or '(migration could not isolate a distinct Fix '
                 'paragraph -- read ## Story.)')
    lines.append('')
    return '\n'.join(lines)


TODAY = None  # set in main() from precedent_time.today(repo)


def build_plan(items, repo, source_relpath, kind_of_source):
    """Return a list of (item, new_relpath, frontmatter_text, body_text,
    noted, is_floor) for every item, without writing anything."""
    plan = []
    seen_slugs = set()
    for item in items:
        # The FILENAME slug wants to be a readable name (bold-key-phrases,
        # shallow-clone-reads-as-diverged); the GIT-HISTORY lookup wants
        # the literal string actually in the file. For a todo item those
        # are the same thing -- its anchor already is a readable slug. A
        # gotcha's anchor is a bare position id ("g1"), never a slug, so
        # its filename is built from its title instead while the lookup
        # still searches for the real `id="g1"` string.
        slug = (_slugify(item.title) if kind_of_source != 'todo'
                else item.slug)
        base_slug = slug
        n = 2
        while slug in seen_slugs:
            slug = f'{base_slug}-{n}'
            n += 1
        seen_slugs.add(slug)
        if item.anchor:
            noted, is_floor = anchor_noted_date(repo, source_relpath, item.anchor)
        else:
            # No `<a id=>` to search for (GOTCHAS_ARCHIVE.md, or a
            # bare-bulleted TODO.md item): search for a snippet of the
            # entry's own title text instead -- real text that is
            # literally in the file, unlike a slug built from it.
            snippet = re.sub(r'\s+', ' ', item.title).strip()[:60]
            noted, is_floor = anchor_noted_date(
                repo, source_relpath, snippet, wrap_id=False)
        if kind_of_source == 'todo':
            blocked_on = guess_blocked_on(item)
            kind = determine_kind(item)
            disposition = guess_disposition(item)
            remind_on = guess_remind_on(item, disposition, noted)
            waiting_on = guess_waiting_on(blocked_on)
            new_slug = f'todo-{noted}-{slug}'
            # item.checked is None for the anchor/bare-bold shapes (this
            # format carries no done/not-done signal of its own -- always
            # 'open', the pre-existing behavior). A checkbox bullet DOES
            # carry one: `[x]` closes the item as of today (the real close
            # date isn't recoverable from a checked box alone -- there is
            # no signal in the source for WHEN it was checked, only that it
            # is), `[ ]` stays open. `done` is the honest default for a
            # checked item -- a checkbox alone can't distinguish done from
            # dropped/abandoned, and `closed` is not a status
            # build_todo_index.py recognizes at all (its vocabulary is
            # open/done/dropped, per spec/OPEN_ITEM_AND_GOTCHA_PLAN.md);
            # writing `closed` here silently dropped every checked item
            # from both generated indexes. Hand-correct an item whose own
            # text reads as abandoned rather than finished to `dropped`.
            status = 'done' if item.checked else 'open'
            closed = TODAY if item.checked else None
            fm = render_todo_frontmatter(
                new_slug, kind, status, disposition, remind_on, blocked_on,
                None, None, None, waiting_on, noted, closed)
            body = render_todo_body(item, blocked_on, is_floor)
            new_relpath = f'todo/{new_slug}.md'
        else:
            new_slug = f'gotcha-{noted}-{slug}'
            fm = render_gotcha_frontmatter(
                new_slug, kind_of_source, noted, None,
                noted if kind_of_source == 'retired' else None, None)
            body = render_gotcha_body(item)
            new_relpath = f'gotchas/{new_slug}.md'
        plan.append((item, new_relpath, fm, body, noted, is_floor))
    return plan


def main(argv):
    global TODAY
    repo = ROOT
    source = None
    only_slugs = None
    limit = None
    apply_ = False
    status_flag = None
    rest = list(argv)
    while rest:
        a = rest.pop(0)
        if a == '--repo':
            repo = pathlib.Path(rest.pop(0)).resolve()
        elif a == '--source':
            source = rest.pop(0)
        elif a == '--slug':
            only_slugs = []
            while rest and not rest[0].startswith('--'):
                only_slugs.append(rest.pop(0))
        elif a == '--limit':
            limit = int(rest.pop(0))
        elif a == '--apply':
            apply_ = True
        elif a == '--status':
            status_flag = rest.pop(0)
        elif a in ('--help', '-h'):
            print((__doc__ or '').strip())
            return 0
        else:
            sys.exit(f'todo_migrate FAIL: unknown argument {a!r}.')

    if source is None:
        sys.exit('todo_migrate FAIL: --source is required '
                  '(todo.md | gotchas.md | gotchas-archive.md).')

    source_map = {
        'todo.md': ('TODO.md', 'todo'),
        'gotchas.md': ('record/GOTCHAS.md', 'live'),
        'gotchas-archive.md': ('record/GOTCHAS_ARCHIVE.md', 'retired'),
    }
    if source not in source_map:
        sys.exit(f'todo_migrate FAIL: --source must be one of '
                  f'{", ".join(source_map)}, got {source!r}.')
    source_relpath, kind_of_source = source_map[source]
    if source in ('gotchas.md', 'gotchas-archive.md') and status_flag is not None:
        kind_of_source = status_flag  # explicit --status overrides the default

    source_path = repo / source_relpath
    if not source_path.exists():
        sys.exit(f'todo_migrate FAIL: {source_path} does not exist.')
    text = source_path.read_text(encoding='utf-8')

    TODAY = precedent_time.today(repo)

    try:
        items = (parse_todo_items(text) if source == 'todo.md'
                 else parse_gotcha_items(text))
    except TodoShapeError as e:
        sys.exit(f'todo_migrate FAIL: {e}')
    if only_slugs:
        wanted = set(only_slugs)
        items = [it for it in items if it.slug in wanted]
        missing = wanted - {it.slug for it in items}
        if missing:
            sys.exit('todo_migrate FAIL: slug(s) not found: '
                      f'{", ".join(sorted(missing))}.')
    elif limit is not None:
        items = items[:limit]

    if not items:
        print('todo_migrate: nothing matched -- 0 items.')
        return 0

    plan = build_plan(items, repo, source_relpath,
                       'todo' if source == 'todo.md' else kind_of_source)

    print(f'todo_migrate: {len(plan)} item(s) from {source_relpath}'
          f'{" (DRY RUN — nothing written)" if not apply_ else " (APPLYING)"}')
    print()
    print('| old anchor/slug | new file |')
    print('|---|---|')
    for item, new_relpath, _fm, _body, noted, is_floor in plan:
        floor_note = ' (floor date)' if is_floor else ''
        print(f'| `{item.slug}` | `{new_relpath}`{floor_note} |')
    print()

    for item, new_relpath, fm, body, noted, is_floor in plan:
        print('=' * 78)
        print(f'--- {new_relpath} ---')
        print(fm + body)

    if not apply_:
        print()
        print('todo_migrate: dry run only. Re-run with --apply to write '
              'these files.')
        return 0

    written = []
    for item, new_relpath, fm, body, noted, is_floor in plan:
        dest = repo / new_relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            sys.exit(f'todo_migrate FAIL: {dest} already exists; refusing '
                      'to overwrite (this tool is one-time-per-item -- '
                      'delete it first if you mean to redo it).')
        dest.write_text(fm + body, encoding='utf-8')
        written.append(new_relpath)

    print()
    print(f'todo_migrate: wrote {len(written)} file(s):')
    for w in written:
        print(f'  {w}')
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
