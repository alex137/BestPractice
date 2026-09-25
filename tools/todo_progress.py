#!/usr/bin/env python3
"""Which open items a change may have moved, and which look closable.

code-cites-practice: item-closes-on-its-condition

WHY THIS EXISTS. Nothing ever told a session that the work it just did
finished somebody's open item. On 2026-09-13 a session answering an unrelated
question hit a cross-owner `add_repo` refusal that bore directly on an item
asking whether that refusal was a first-call artifact -- and only noticed
because it happened to be reading TODO.md for something else. The closing was
never the hard part; the NOTICING was, and no session reads 83 items asking
what it might have finished.

WHAT IT DOES NOT DO, said here because the obvious use is the wrong one: it
never closes anything, and it never claims an item IS done. It matches what a
change touched against what an item names, which is a resemblance. Whether the
item's own stated condition is met is a reading, and the practice puts that
reading on a person or on the session that did the work.

Two modes, one implementation, so the merge moment and the deep read cannot
disagree about what counts as a candidate:

  --changed BASE..HEAD   what this change may have moved. Quiet when nothing
                         matches, because a gate that speaks at every merge
                         stops being read.
  (no --changed)         the whole file: items naming paths that are gone,
                         and items the person asked to be reminded of.
"""
import argparse, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# An item opens with `N. <a id="slug"></a>` and runs to the next such line.
ITEM_RE = re.compile(r'(?m)^(\d+)\. <a id="([A-Za-z0-9_-]+)"></a>')
# Paths an item names: markdown links to repo files, and backticked paths.
# The destination excludes whitespace: an item body is many lines, and `[^)]`
# would pair a stray "(" with a ")" lines later and report the text between
# as a path.
LINK_RE = re.compile(r'\]\((?!https?://|mailto:|#)([^)#\s]+)[^)\s]*\)')
TICKED_PATH_RE = re.compile(r'`((?:[\w.-]+/)+[\w.-]+\.\w+)`')
REMIND_RE = re.compile(r'(?m)^\s*\*\*Remind:\*\*\s*(.+)$')
# A closed item is marked in one of two shapes here: a bolded DONE/Closed
# lead, or a struck-through title. Missing the second read four closed items
# as live on the first run.
DONE_RE = re.compile(r'\*\*(?:DONE|Done|Closed|Half-closed)\b|</a>\*\*~~')


def items(text):
    """-> [(number, slug, body)] for every item in a TODO file."""
    marks = list(ITEM_RE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((m.group(1), m.group(2), text[m.start():end]))
    return out


def named_paths(body):
    """-> repo-relative paths an item names, by link or by backtick.

    Both forms, deliberately: an item citing `tools/foo.py` in a code span is
    naming the same file as one linking it, and matching only links would miss
    exactly the items that predate the links convention.
    """
    out = set()
    for rx in (LINK_RE, TICKED_PATH_RE):
        for p in rx.findall(body):
            p = p.strip()
            if p and not p.startswith(('http', '#')):
                out.add(p)
    return out


def _git(*args):
    r = subprocess.run(['git', '-C', str(ROOT), *args],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''


def changed_files(rev_range):
    return {l for l in _git('diff', '--name-only', rev_range).split('\n') if l}


# A path most items name cannot tell them apart. AGENTS.md is cited by more
# than a third of the open items here and is touched by nearly every change,
# so matching on it returned 13 of 83 items for one ordinary day's work --
# which is a list nobody reads twice. Measured, not guessed: the first run of
# this tool produced exactly that.
COMMON_PATH_SHARE = 0.15


def common_paths(text, share=COMMON_PATH_SHARE):
    """-> paths so widely cited they carry no signal about any one item."""
    live = [b for _n, _s, b in items(text) if not DONE_RE.search(b)]
    if not live:
        return set()
    counts = {}
    for body in live:
        for p in named_paths(body):
            counts[p] = counts.get(p, 0) + 1
    # max(3, ...), not max(2, ...). A path cited by two items is not "common"
    # in any repo, and the 2 floor meant a small adopter -- ten open items,
    # say -- suppressed almost every path it had. Found by a fixture too small
    # to have a specific path left after suppression, which is exactly the
    # shape of the repo this would have hurt.
    floor = max(3, int(len(live) * share))
    return {p for p, c in counts.items() if c >= floor} | {'TODO.md'}


# How many candidates are worth printing at one merge. Not a limit on what
# matches -- a limit on what is SHOWN, with the remainder counted out loud.
# Measured on this repository: a narrow change produced 5 candidates and a
# broad one (two new practices, three tools, every generated view) produced
# 13, spread across eight files with none dominating. Thirteen is not wrong,
# and it is still more than anybody reads at a merge. The ones kept are the
# most SPECIFIC -- an item matched on a file few items cite is saying more
# about itself than one matched on a file half the queue mentions in passing.
REPORT_LIMIT = 6


def candidates(text, changed, ignore=None):
    """-> [(number, slug, hits)] items whose named paths this change touched.

    An item is a candidate only when a path it NAMES was actually modified,
    and only for paths that are not cited across the whole file (see
    common_paths). Both exclusions exist for the same reason: a candidate list
    that includes everything says nothing.

    Ordered most-specific first: by how many live items cite the rarest path
    the item matched on. `tools/verify_harness.py` is named by five open items
    and touched by most changes to this repo, so an item matching only on it
    is the weakest kind of hit -- and sorting is honest where suppressing
    would not be, because the hit is real.
    """
    ignore = common_paths(text) if ignore is None else ignore
    live = [b for _n, _s, b in items(text) if not DONE_RE.search(b)]
    cites = {}
    for body in live:
        for pth in named_paths(body):
            cites[pth] = cites.get(pth, 0) + 1
    out = []
    for num, slug, body in items(text):
        if DONE_RE.search(body):
            continue
        hits = sorted((named_paths(body) & changed) - ignore)
        if hits:
            out.append((num, slug, hits))
    out.sort(key=lambda c: min(cites.get(h, 1) for h in c[2]))
    return out


def stale_paths(text):
    """-> [(number, slug, missing)] items naming a path that is not there."""
    out = []
    for num, slug, body in items(text):
        if DONE_RE.search(body):
            continue
        gone = sorted(p for p in named_paths(body)
                      if not p.endswith('/') and not (ROOT / p).exists())
        if gone:
            out.append((num, slug, gone))
    return out


def reminders(text):
    """-> [(number, slug, note)] items the person asked to be reminded of."""
    out = []
    for num, slug, body in items(text):
        if DONE_RE.search(body):
            continue
        m = REMIND_RE.search(body)
        if m:
            out.append((num, slug, m.group(1).strip()))
    return out


def title_of(body):
    m = re.search(r'</a>\*\*(.+?)\*\*', body, re.S)
    return ' '.join(m.group(1).split())[:74] if m else ''


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--changed', metavar='BASE..HEAD',
                    help='report items this change may have moved')
    ap.add_argument('--todo', default='TODO.md')
    ap.add_argument('--all', action='store_true',
                    help='show every candidate, not just the most specific')
    args = ap.parse_args(argv)

    f = ROOT / args.todo
    if not f.is_file():
        print(f'todo_progress: no {args.todo} here -- nothing to check')
        return 0
    text = f.read_text(encoding='utf-8', errors='replace')
    by_slug = {s: b for _n, s, b in items(text)}

    if args.changed:
        ch = changed_files(args.changed)
        if not ch:
            print(f'todo_progress: {args.changed} changed no files')
            return 0
        cands = candidates(text, ch)
        if not cands:
            # Silence is the point. A gate that says something at every merge
            # is a gate nobody reads by the third week.
            return 0
        shown = cands[:REPORT_LIMIT]
        print(f'todo_progress: {len(cands)} open item(s) name a file this '
              f'change touched. A resemblance, not a verdict --')
        print('  record what you established in the item; close it only if '
              'its own stated\n  condition is now met.')
        if len(cands) > len(shown):
            print(f'  Showing the {len(shown)} most specific; '
                  f'{len(cands) - len(shown)} more matched only on files much '
                  f'of the\n  queue mentions. `--all` for those.')
        print()
        for num, slug, hits in (cands if args.all else shown):
            print(f'  TODO {num} ({slug}) — {title_of(by_slug[slug])}')
            for h in hits[:4]:
                print(f'      touched: {h}')
            if len(hits) > 4:
                print(f'      (+{len(hits) - 4} more)')
        return 0

    rem = reminders(text)
    if rem:
        print(f'REMINDERS — {len(rem)} item(s) he asked to be reminded of:')
        for num, slug, note in rem:
            print(f'  TODO {num} ({slug}) — {title_of(by_slug[slug])}')
            print(f'      {note}')
        print()
    stale = stale_paths(text)
    if stale:
        print(f'STALE PATHS — {len(stale)} open item(s) name a file that is '
              f'not in the tree.\n  Either the work landed under another name, '
              f'or the item has rotted:')
        for num, slug, gone in stale:
            print(f'  TODO {num} ({slug}) — {title_of(by_slug[slug])}')
            for g in gone[:3]:
                print(f'      missing: {g}')
            if len(gone) > 3:
                print(f'      (+{len(gone) - 3} more)')
        print()
    if not rem and not stale:
        print('todo_progress: no reminder-marked item, and every open item\'s '
              'named files\n  are present.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
