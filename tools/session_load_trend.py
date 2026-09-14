#!/usr/bin/env python3
"""How much room every always-loaded surface has left, and how fast it is going.

code-cites-practice: session-load-budget

WHY THIS EXISTS. The ceiling check answers one question -- is this surface over
its number right now -- and that question only becomes askable at the moment it
is already too late. On 2026-09-13 and 2026-09-14 AGENTS.md crossed its 12,000
ceiling four times, and each crossing was found by a session that had come to
do something else entirely and now owed a reduction pass before it could push.
Three of those passes were paid in two days by three different people, none of
whom had added the thing that broke it.

Nothing anywhere reported the approach. `precedent_check.py --only
session-load-budget` is green at 11,999 and red at 12,001, and the distance
between those two states is about four hours of ordinary catalogue growth --
so "green" carried no information a session could plan against.

WHAT IT REPORTS, and the split is the point: for AGENTS.md the largest and
fastest-growing component is the GENERATED occasion index, which no reduction
pass can touch by hand. It grows when a practice is added, which is a thing
sessions do on purpose for good reasons and at a rate nobody has ever looked
at. A headroom figure that does not separate the part a person can cut from
the part they cannot is a figure that suggests the wrong remedy.

WHAT IT DOES NOT DO. It never edits a ceiling and never proposes a number.
Growth is measured over a window of real commits, so it is a description of
what has been happening, not a forecast anybody should defend -- a week when
six practices land and a week when none do are both normal, and the projection
below says "at the observed rate", never "on this date".
"""
import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))


def _today():
    """Today's calendar date in the PERSON's zone, and a note if it could not be.

    code-cites-practice: timestamps-carry-offset -- never a bare
    `datetime.date.today()`, which in a hosted container silently resolves to
    the container's UTC and is the wrong date for part of every day.

    Imported lazily rather than at module scope, because this script is
    vendored one file at a time: a partial vendor with no precedent_time.py
    beside it used to die on the import before argparse ever ran, so even
    `--help` exited non-zero (caught by verify_harness.py's every-tool---help
    check, 2026-09-14). A missing sibling degrades ONE figure; it must not
    take the whole tool down (practice: fail-gracefully).

    Returns (iso_date, note_or_None) -- the note is printed rather than
    swallowed, so a UTC fallback is never mistaken for the person's date.
    """
    try:
        import precedent_time
        return precedent_time.today(ROOT), None
    except Exception:                                        # noqa: BLE001
        utc = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        return utc, ("precedent_time.py is not vendored beside this script, so "
                     "dates here are UTC rather than the person's zone "
                     "(practice: timestamps-carry-offset). Re-vendor the "
                     "engine to fix it; the token figures are unaffected.")

# The surfaces the ceiling check itself measures, kept in that order so the two
# tools cannot disagree about what "always loaded" means.
SURFACES = ('AGENTS.md', 'CLAUDE.md', '.precedent/SESSION_PRACTICES.md')


def approx_tokens(text):
    """build_views.py's own estimator, so every figure here is comparable to
    the ones in the registry and in the check. Falls back to the same formula
    it uses if the import is unavailable (a source set without the engine)."""
    try:
        import build_views
        return build_views._approx_tokens(text)
    except Exception:
        return int(len(text.split()) * 1.3)


def _git(*args):
    """stdout and the return code, never stdout alone.

    environment-gotchas: a git helper that returns stdout and drops the exit
    code hands back a confident wrong answer -- `git show <sha>:<path>` exits
    128 with EMPTY stdout both for a commit this clone does not have and for a
    path that did not exist at that commit, which are different answers.
    """
    p = subprocess.run(['git', '-C', str(ROOT)] + list(args),
                       capture_output=True, text=True)
    return p.stdout, p.returncode


def registry():
    f = ROOT / 'tools' / 'session_load_budgets.json'
    try:
        return json.loads(f.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return None


def split_generated(text):
    """AGENTS.md's hand-written half and its generated half, separately.

    The resident block and the occasion index are written by build_views.py
    from the practice catalogue. A person editing AGENTS.md cannot shorten
    either one, so counting them inside a single 'reduce this file' figure
    points the next reduction pass at text it is not allowed to touch.
    """
    gen = 0
    if '## Resident block' in text and '## Occasion index' in text:
        res = text.split('## Resident block', 1)[1].split('## Occasion index', 1)[0]
        gen += approx_tokens(res)
    if '## Occasion index' in text:
        after = text.split('## Occasion index', 1)[1]
        parts = after.split('```')
        if len(parts) >= 3:
            gen += approx_tokens(parts[1])
    return approx_tokens(text) - gen, gen


def history(rel, days, cap):
    """(date, tokens, generated_tokens) per commit touching `rel`, oldest first.

    Bounded two ways because this runs `git show` once per commit: a date
    window and a hard commit cap. A shallow clone simply yields fewer points,
    and the caller says so rather than treating a short series as a flat one.
    """
    # timestamps-carry-offset: the window's start is a calendar date in the
    # person's zone, never the container's UTC 'today'.
    anchor = datetime.date.fromisoformat(_today()[0])
    since = (anchor - datetime.timedelta(days=days)).isoformat()
    out, rc = _git('log', f'--since={since}', '--format=%H|%ci', '--reverse',
                   '--', rel)
    if rc != 0:
        return []
    lines = [l for l in out.strip().splitlines() if l]
    if len(lines) > cap:
        lines = lines[-cap:]
    rows = []
    for line in lines:
        sha, date = line.split('|', 1)
        blob, rc = _git('show', f'{sha}:{rel}')
        if rc != 0:           # path absent at that commit, or commit not here
            continue
        hand, gen = split_generated(blob)
        rows.append((date[:10], hand + gen, gen))
    return rows


def catalogue_size():
    """Active practices now, which is what the occasion index grows with."""
    n = 0
    d = ROOT / 'practices'
    if not d.is_dir():
        return None
    for p in d.glob('*.md'):
        t = p.read_text(encoding='utf-8', errors='replace')
        if not t.startswith('---'):
            continue
        fm = t.split('---', 2)[1]
        m = re.search(r'^status:\s*(\S+)', fm, re.M)
        if m and m.group(1).strip() == 'active':
            n += 1
    return n


def _ledger(ref, reg, as_json):
    """Before/after per surface against `ref` -- what a reduction pass moved.

    code-cites-practice: reduction-pass -- the report has to say what each
    move cost, and a figure typed from memory is the half that drifts. This
    computes it from the two trees.

    Silent about WHY a surface changed: that is the reading the person writes.
    It reports the delta and nothing else, so it cannot be mistaken for an
    account of what happened.
    """
    surfaces = reg.get('surfaces') or {}
    out, rc = _git('rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}')
    sha = out.strip()
    # environment-gotchas: --verify --quiet exits 0 and echoes back ANY
    # well-formed 40-hex string, present in the clone or not, so ask the
    # object database rather than trusting the name resolved.
    if rc != 0 or not sha:
        print(f"session_load_trend: cannot resolve {ref!r} in this clone.")
        return 1
    _, rc2 = _git('cat-file', '-e', f'{sha}^{{commit}}')
    if rc2 != 0:
        print(f"session_load_trend: {ref!r} names a commit this clone does "
              f"not have (shallow?). Fetch deeper and retry.")
        return 1

    rows = []
    for rel in SURFACES:
        f = ROOT / rel
        after = approx_tokens(f.read_text(encoding='utf-8', errors='replace')) \
            if f.is_file() else 0
        blob, brc = _git('show', f'{sha}:{rel}')
        before = approx_tokens(blob) if brc == 0 else None
        ceiling = (surfaces.get(rel) or {}).get('ceiling')
        rows.append((rel, before, after, ceiling))

    if as_json:
        print(json.dumps({'since': ref, 'sha': sha, 'surfaces': [
            {'file': r, 'before': b, 'after': a, 'ceiling': c,
             'delta': (None if b is None else a - b)} for r, b, a, c in rows]},
            indent=2))
        return 0

    print(f"REDUCTION LEDGER -- always-loaded surfaces, {ref} ({sha[:8]}) -> working tree\n")
    tb = ta = 0
    skipped = []
    for rel, before, after, ceiling in rows:
        if before is None:
            # Not in the tree at `ref` -- an untracked surface like
            # .precedent/SESSION_PRACTICES.md, which is generated per session
            # and deliberately never committed. Counting its `after` against a
            # `before` it cannot have would book a reduction as a growth
            # (practice: name-both-sides-of-ledger).
            skipped.append((rel, after))
            continue
        tb += before
        ta += after
        d = after - before
        cap = f" of {ceiling:,}" if ceiling else ""
        print(f"  {rel}: {before:,} -> {after:,}{cap}   {d:+,}")
    print(f"\n  TOTAL {tb:,} -> {ta:,}   {ta - tb:+,}   (comparable surfaces only)")
    for rel, after in skipped:
        print(f"  NOT IN THE TOTAL -- {rel}: not tracked at {ref}, "
              f"so it has no before. It is {after:,} now.")
    print("\n  Figures only. What moved and where it went is the report's own")
    print("  to say, and so is what was considered and not done "
          "(practice: reduction-pass).")
    return 0


def headroom_notice(root=None, floor_pct=None):
    """One line per always-loaded surface that is close to its ceiling, or None.

    code-cites-practice: session-load-budget

    Called from the merge and push gates. Deliberately SILENT above the floor:
    a notice that prints on every push is one nobody reads by the third day,
    and the thing worth saying here is "you are nearly out of room", which is
    only true occasionally.

    The floor is declared in tools/session_load_budgets.json rather than
    written here (practice: registry-source-of-truth), so the one number that
    decides when this speaks sits beside the ceilings it is measured against.
    """
    reg = registry()
    if reg is None:
        return None
    if floor_pct is None:
        floor_pct = reg.get('headroom_floor_pct')
    if not isinstance(floor_pct, (int, float)):
        return None
    base = pathlib.Path(root) if root else ROOT
    surfaces = reg.get('surfaces') or {}
    tight = []
    for rel in SURFACES:
        f = base / rel
        if not f.is_file():
            continue
        entry = surfaces.get(rel) or {}
        ceiling = entry.get('ceiling')
        if not isinstance(ceiling, int) or ceiling <= 0:
            continue
        n = approx_tokens(f.read_text(encoding='utf-8', errors='replace'))
        pct = 100.0 * (ceiling - n) / ceiling
        if pct <= floor_pct:
            tight.append((rel, n, ceiling, ceiling - n, pct))
    if not tight:
        return None
    out = ["NOTE: an always-loaded surface is close to its declared ceiling."]
    for rel, n, ceiling, head, pct in tight:
        state = 'OVER by' if head < 0 else 'headroom'
        out.append(f"  {rel}: {n:,} of {ceiling:,} tokens, "
                   f"{state} {abs(head):,} ({pct:.1f}%).")
    out.append("  Run `python3 tools/session_load_trend.py` for the growth "
               "rate and how much of it is generated.")
    out.append("  session-load-budget: reduce by moving, and never raise the "
               "ceiling to clear the warning.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(
        description='Headroom and growth rate for every always-loaded surface.')
    ap.add_argument('--days', type=int, default=14,
                    help='history window in days (default 14)')
    ap.add_argument('--cap', type=int, default=80,
                    help='max commits to read per surface (default 80)')
    ap.add_argument('--since', metavar='REF',
                    help='before/after ledger against a git ref -- the figures '
                         'a "Reduction pass" report needs, measured rather '
                         'than typed (practice: reduction-pass)')
    ap.add_argument('--json', action='store_true', help='machine-readable')
    args = ap.parse_args()

    reg = registry()
    if reg is None:
        print('session_load_trend: no tools/session_load_budgets.json here.')
        return 0
    if args.since:
        return _ledger(args.since, reg, args.json)
    surfaces = reg.get('surfaces') or {}

    # timestamps-carry-offset
    measured, zone_note = _today()
    report = {'surfaces': {}, 'measured': measured}
    if zone_note:
        report['zone_note'] = zone_note
    total_now = total_ceiling = 0

    for rel in SURFACES:
        f = ROOT / rel
        if not f.is_file():
            continue
        text = f.read_text(encoding='utf-8', errors='replace')
        now = approx_tokens(text)
        hand, gen = split_generated(text)
        entry = surfaces.get(rel) or {}
        ceiling = entry.get('ceiling')
        total_now += now
        if isinstance(ceiling, int):
            total_ceiling += ceiling

        rows = history(rel, args.days, args.cap)
        rate = gen_rate = None
        span = 0
        if len(rows) >= 2:
            d0 = datetime.date.fromisoformat(rows[0][0])
            d1 = datetime.date.fromisoformat(rows[-1][0])
            span = max((d1 - d0).days, 1)
            rate = (rows[-1][1] - rows[0][1]) / span
            gen_rate = (rows[-1][2] - rows[0][2]) / span

        rec = dict(tokens=now, hand_written=hand, generated=gen,
                   ceiling=ceiling, points=len(rows), span_days=span,
                   tokens_per_day=rate, generated_per_day=gen_rate)
        if isinstance(ceiling, int):
            rec['headroom'] = ceiling - now
            rec['headroom_pct'] = round(100.0 * (ceiling - now) / ceiling, 1)
            # Projection uses GENERATED growth alone when it is positive: that
            # is the part a reduction pass cannot claw back, so it is the part
            # that sets a floor under how soon the ceiling is met again.
            drive = gen_rate if (gen_rate or 0) > 0 else rate
            rec['projection_basis'] = ('generated growth'
                                       if (gen_rate or 0) > 0 else 'total growth')
            if drive and drive > 0 and rec['headroom'] >= 0:
                rec['days_to_ceiling'] = round(rec['headroom'] / drive, 1)
        report['surfaces'][rel] = rec

    report['total_tokens'] = total_now
    report['total_ceiling'] = total_ceiling
    report['active_practices'] = catalogue_size()

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    if zone_note:
        print(f"NOTE: {zone_note}\n")
    print(f"SESSION LOAD -- what every session pays before it does any work")
    print(f"  measured {report['measured']}, "
          f"window {args.days}d, active practices: {report['active_practices']}")
    print()
    for rel, r in report['surfaces'].items():
        c = r['ceiling']
        head = f"{r['headroom']:,} ({r['headroom_pct']}%)" if c else 'no ceiling'
        print(f"  {rel}")
        print(f"    {r['tokens']:,} tokens"
              + (f" of {c:,}   headroom {head}" if c else "   (no ceiling declared)"))
        if r['generated']:
            print(f"    hand-written {r['hand_written']:,}  |  "
                  f"generated {r['generated']:,} "
                  f"({100.0*r['generated']/r['tokens']:.0f}% -- not trimmable by hand)")
        if r['points'] >= 2:
            print(f"    growth over {r['span_days']}d ({r['points']} commits): "
                  f"{r['tokens_per_day']:+.0f} tok/day"
                  + (f", of which generated {r['generated_per_day']:+.0f}"
                     if r['generated_per_day'] is not None else ''))
            if 'days_to_ceiling' in r:
                print(f"    at the observed {r['projection_basis']} the ceiling "
                      f"is met in ~{r['days_to_ceiling']} days")
                if r['projection_basis'] == 'generated growth' and (r['tokens_per_day'] or 0) <= 0:
                    print(f"      (total growth is {r['tokens_per_day']:+.0f}/day "
                          f"because a reduction pass falls inside the window; "
                          f"the generated share is what nobody can trim back)")
        elif r['points'] < 2:
            print(f"    growth: not measurable here "
                  f"({r['points']} commit(s) in window -- shallow clone?)")
        print()
    print(f"  TOTAL {total_now:,} tokens against declared ceilings "
          f"summing to {total_ceiling:,}")
    print()
    print("  A ceiling is a watermark, not an endorsement (session-load-budget).")
    print("  Headroom is not a target to spend; it is the distance to the next")
    print("  forced reduction pass, and the generated share says how much of")
    print("  that distance closes whether or not anybody writes a word.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
