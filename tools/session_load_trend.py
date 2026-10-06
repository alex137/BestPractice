#!/usr/bin/env python3
"""How much room every always-loaded surface has left and how fast it is going -- headroom, the hand-written/generated split, and the growth rate; its headroom_notice() is what the merge and push gates print

How much room every always-loaded surface has left, and how fast it is going.

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

def _which_repo():
    """The helper that names the measured repo, or None if not vendored here.

    This script reads the repo it lives in, never the current directory --
    on 2026-09-29 a session ran BestPractice's copy from inside
    precedent-individual, got BestPractice's figures under a header that named
    no repo, and reported a ceiling breach that did not exist
    (gotchas/gotcha-2026-09-29-engine-tools-measure-their-own-repo-not-the-cwd.md).
    Imported lazily for the same reason as precedent_time above: a partial
    vendor must lose the label, not the tool (practice: fail-gracefully).
    """
    try:
        import precedent_which_repo
        return precedent_which_repo
    except Exception:                                        # noqa: BLE001
        return None


def _repo():
    """-> {'name', 'path', 'origin'} for the measured repo."""
    w = _which_repo()
    if w is not None:
        try:
            return w.describe(ROOT)
        except Exception:                                    # noqa: BLE001
            pass
    return {'name': ROOT.name, 'path': str(ROOT), 'origin': None}


def _repo_label(repo):
    return f"{repo['name']} ({repo['origin']})" if repo['origin'] else repo['name']

# The surfaces the ceiling check itself measures, kept in that order so the two
# tools cannot disagree about what "always loaded" means.
SURFACES = ('AGENTS.md', 'CLAUDE.md', '.precedent/SESSION_PRACTICES.md')
# build_views.py's heading for the generated resident block, e.g.
# "## Resident block (~539 of 550 token budget, 4 of 17 practices)".
RESIDENT_HEADING = re.compile(
    r'^## Resident block \(~([\d,]+) of ([\d,]+) token budget', re.M)


def as_measured(rel, text):
    """`text` as a cap measures it: the session-start file without the
    over-target warning its generator writes, since that warning exists
    only because the file is over and must not count toward the ceiling
    (precedent_session_practices.without_target_warning)."""
    if rel != '.precedent/SESSION_PRACTICES.md':
        return text
    try:
        import precedent_session_practices
        return precedent_session_practices.without_target_warning(text)
    except Exception:                                         # noqa: BLE001
        return text


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
        after = approx_tokens(as_measured(rel, f.read_text(encoding='utf-8', errors='replace'))) \
            if f.is_file() else 0
        blob, brc = _git('show', f'{sha}:{rel}')
        before = approx_tokens(blob) if brc == 0 else None
        ceiling = (surfaces.get(rel) or {}).get('ceiling')
        rows.append((rel, before, after, ceiling))

    repo = _repo()
    if as_json:
        print(json.dumps({'repo': repo, 'since': ref, 'sha': sha, 'surfaces': [
            {'file': r, 'before': b, 'after': a, 'ceiling': c,
             'delta': (None if b is None else a - b)} for r, b, a, c in rows]},
            indent=2))
        return 0

    print(f"REDUCTION LEDGER -- {_repo_label(repo)}")
    print(f"  always-loaded surfaces, {ref} ({sha[:8]}) -> working tree\n")
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


def _registry_at(root):
    f = pathlib.Path(root) / 'tools' / 'session_load_budgets.json'
    try:
        return json.loads(f.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return None


def over_target(root=None):
    """-> [(surface, tokens, target, ceiling)] for every always-loaded file
    over the `target` its registry entry declares.

    code-cites-practice: session-load-budget

    A TARGET IS NOT A CEILING. The hard ceiling is the hard number, enforced
    where the file's text is written. The target is where the file is meant to live, and
    being over it is reported in every session until someone brings it
    down: the session-start file carries a warning at its top, and the
    reply gate requires one line in The Boildown. Morgan, 2026-09-29:
    "The target should be 4000 or less but at the 4000 level, you get
    warnings, with every session to bring it down" (strength: decided).
    """
    base = pathlib.Path(root) if root else ROOT
    reg = _registry_at(base)
    if not reg:
        return []
    out = []
    for rel in SURFACES:
        entry = (reg.get('surfaces') or {}).get(rel) or {}
        target = entry.get('target')
        f = base / rel
        if not isinstance(target, int) or not f.is_file():
            continue
        n = approx_tokens(as_measured(rel, f.read_text(encoding='utf-8', errors='replace')))
        if n > target:
            out.append((rel, n, target, entry.get('hard_ceiling', entry.get('ceiling'))))
    return out


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
        n = approx_tokens(as_measured(rel, f.read_text(encoding='utf-8', errors='replace')))
        pct = 100.0 * (ceiling - n) / ceiling
        if pct <= floor_pct:
            tight.append((rel, n, ceiling, ceiling - n, pct))
    # The resident block has its own allocation (`resident_block_tokens`),
    # far smaller than the file's ceiling, and build_views.py refuses to
    # build past it -- so a set can sit at 98% of it with the FILE nowhere
    # near its own ceiling, and learn only when a practice edit fails to
    # build. Very deep check, 2026-09-28: an individual set's block was at
    # ~539 of 550 and nothing said so. build_views writes both numbers into
    # the block's own heading, which is what is read here.
    agents = base / 'AGENTS.md'
    if agents.is_file():
        m = RESIDENT_HEADING.search(
            agents.read_text(encoding='utf-8', errors='replace'))
        if m:
            n, budget = (int(g.replace(',', '')) for g in m.groups())
            if budget > 0:
                pct = 100.0 * (budget - n) / budget
                if pct <= floor_pct:
                    tight.append(('AGENTS.md resident block', n, budget,
                                  budget - n, pct))
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


_RESIDENT_ENTRY = re.compile(r'^\*\*([a-z0-9][a-z0-9-]*)\.\*\*', re.M)
_INDEX_SLUG = re.compile(r'^\s+([a-z0-9][a-z0-9-]*) \u2014 ', re.M)


def _slug_sources(root):
    """-> {slug: source name} from the sources `root`'s precedent.json
    declares, highest precedence last so it wins; {} when they cannot be
    read."""
    try:
        import precedent_resolve as pr
        sources = pr.load_config(str(root))
    except Exception:                                         # noqa: BLE001
        return {}
    out = {}
    for s in sources:
        d = pathlib.Path(root) / str(s.get('path') or '') / 'practices'
        for f in (d.glob('*.md') if d.is_dir() else ()):
            out[f.stem] = s.get('name') or s.get('level') or '?'
    return out


def breakdown(root, rel):
    """-> [(tokens, kind, label, source)], largest first: each resident
    entry, each occasion-index group, and the rest of the file, as the cap
    measures it.

    code-cites-practice: session-load-budget

    The over-target line gave one number. A session in a consumer read
    "precedent-individual: .precedent/SESSION_PRACTICES.md is 4,004 tokens,
    over its 4,000-token target", proposed trimming a practice whose line was
    not in that file at all, and found the real one only later (2026-10-06).
    A Reduction pass starts from what is actually there, and from which
    source each piece comes, since that is where it is cut."""
    f = pathlib.Path(root) / rel
    text = as_measured(rel, f.read_text(encoding='utf-8', errors='replace'))
    owner = _slug_sources(root)
    rows, used = [], 0
    if '## Resident block' in text:
        res = text.split('## Resident block', 1)[1].split('## Occasion index', 1)[0]
        starts = [m.start() for m in _RESIDENT_ENTRY.finditer(res)] + [len(res)]
        for a, b in zip(starts, starts[1:]):
            chunk = res[a:b]
            slug = _RESIDENT_ENTRY.match(chunk).group(1)
            n = approx_tokens(chunk)
            used += n
            rows.append((n, 'resident', slug, owner.get(slug, '?')))
    if '## Occasion index' in text:
        parts = text.split('## Occasion index', 1)[1].split('```')
        if len(parts) >= 3:
            group = []
            for line in parts[1].split('\n') + ['']:
                if (not line or not line.startswith(' ')) and group:
                    body = '\n'.join(group)
                    slugs = _INDEX_SLUG.findall(body)
                    if slugs:
                        n = approx_tokens(body)
                        used += n
                        rows.append((n, 'index', ', '.join(slugs),
                                     ', '.join(sorted({owner.get(s, '?')
                                                       for s in slugs}))))
                    group = []
                if line.strip():
                    group.append(line)
    rest = approx_tokens(text) - used
    if rest > 0:
        rows.append((rest, 'other', 'headings, prose and notes outside the '
                     'entries', '-'))
    return sorted(rows, key=lambda r: -r[0])


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
    ap.add_argument('--breakdown', metavar='FILE',
                    help='one always-loaded file, entry by entry, largest '
                         'first, with the source each entry comes from -- '
                         'where a Reduction pass starts')
    ap.add_argument('--root', metavar='DIR',
                    help='the repository to measure (default: the one this '
                         'script lives in)')
    args = ap.parse_args()

    # --root measures another repository (2026-09-30): ROOT otherwise comes
    # from __file__, so this could only ever read the repo it was copied
    # into. With --root the reader named it, so there is nothing to warn of.
    global ROOT
    if args.root:
        ROOT = pathlib.Path(args.root).resolve()
    # Before anything else, including the no-registry exit: a run from inside
    # another repo is the one case where every figure below is right and
    # none of them is the answer (precedent_which_repo.py).
    w = None if args.root else _which_repo()
    if w is not None:
        w.warn_if_elsewhere(ROOT, 'session_load_trend.py')

    if args.breakdown:
        if not (ROOT / args.breakdown).is_file():
            print(f'session_load_trend: no {args.breakdown} in {ROOT}.')
            return 1
        rows = breakdown(ROOT, args.breakdown)
        if args.json:
            print(json.dumps([dict(zip(('tokens', 'kind', 'entry', 'source'), r))
                              for r in rows], indent=2))
            return 0
        total = sum(r[0] for r in rows)
        print(f'{ROOT / args.breakdown}: ~{total:,} tokens, as the cap measures it')
        for n, kind, label, src in rows:
            print(f'  {n:>5,}  {kind:<8}  {label}  [{src}]')
        return 0

    reg = registry()
    if reg is None:
        print(f'session_load_trend: no tools/session_load_budgets.json in '
              f'{_repo_label(_repo())} at {ROOT}.')
        return 0
    if args.since:
        return _ledger(args.since, reg, args.json)
    surfaces = reg.get('surfaces') or {}

    # timestamps-carry-offset
    measured, zone_note = _today()
    report = {'repo': _repo(), 'surfaces': {}, 'measured': measured}
    if zone_note:
        report['zone_note'] = zone_note
    total_now = total_ceiling = 0

    for rel in SURFACES:
        f = ROOT / rel
        if not f.is_file():
            continue
        text = as_measured(rel, f.read_text(encoding='utf-8', errors='replace'))
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
    print(f"SESSION LOAD -- {_repo_label(report['repo'])}")
    print(f"  what every session pays before it does any work, at {ROOT}")
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
