#!/usr/bin/env python3
"""routing_audit.py -- the routing audit (practice: routing-audit).

PRACTICE_ENGINE_PLAN.md's "The Routing Audit Checks Coverage, Not Content"
names a periodic, two-part mechanism for the standing risk the loader's own
design accepts: a practice with a wrong or missing trigger goes unrouted and
nobody notices, because nothing is loaded to notice its absence. Approved for
phase 5 in the 2026-09-01 preflight review (v28) and never built until now --
see spec/UNBUILT_PLAN_ITEMS.md for why, and what is still open about it.

Two parts, deliberately narrower than "did we follow every practice":

  1. A COVERAGE CHECK, fully mechanical, cheap, every run: which on-demand
     practices, scoped by a narrower-than-"**" `applies_to` glob, match a
     given set of files -- filtered to the ones with no `checked_by` and no
     `gates`, since anything with a working check or a deterministic gate
     "needs no human-style review: the check either fired or it did not"
     (the plan's own words). This is the set that depends on a session
     noticing it unaided -- the routing-failure candidates.
  2. A ROTATING DEEP READ: a bounded slice of that same judgment-only set,
     picked by whichever have gone longest without one, handed to the
     invoking session to actually read and judge against real work. Full
     coverage accumulates across many runs; no single run holds the whole
     catalogue in context. spec/ATTENTION_CEILING.md's review-arm result is
     why this is a *slice*, not a sweep: a one-pass, whole-set judge scored
     54% recall, WORSE than doing nothing -- see practices/full-practice-audit.md
     for the sibling mechanism that accepts that risk deliberately, on
     request only, as a backstop rather than a routine control.

WHAT THIS DOES NOT DO, disclosed rather than assumed. The plan's own design
for part 1 compares "practices that matched" against "practices the session
actually loaded" -- this repo keeps no record of what a past session actually
loaded, so this tool computes only the first half (which practices SHOULD
have fired) and cannot verify the second (whether they DID). A match with no
checked_by/gates is reported as a routing-failure CANDIDATE, not a proven
miss. See spec/UNBUILT_PLAN_ITEMS.md.

This is a detective control, not a preventive one -- it finds candidate
misses after the fact. What it should produce is fixes to routing (a
narrower glob, a better occasion, or, best, a promotion to `checked_by`),
not just a list of misses cleared and forgotten.

Run:
  python3 tools/routing_audit.py coverage FILE [FILE...]
      -- judgment-only on-demand practices whose applies_to matches FILE(s).
  python3 tools/routing_audit.py coverage --changed
      -- same, against files changed vs the default branch (committed and
         worktree), the same scope tools/doc_lint.py uses for markdown.
  python3 tools/routing_audit.py slice [--size N]
      -- the N judgment-only practices least recently reviewed (default 5):
         slug, source file, and full Rule text, to read and judge now.
  python3 tools/routing_audit.py mark-reviewed SLUG [SLUG...]
      -- record that this run's slice was actually read and judged;
         updates tools/routing_audit_state.json.
  python3 tools/routing_audit.py --list
      -- every judgment-only on-demand practice and when it was last
         reviewed ("never" if absent from the state file).
"""
import datetime, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRACTICES_DIR = ROOT / 'practices'
STATE_PATH = ROOT / 'tools' / 'routing_audit_state.json'

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import precedent_paths as pp


def _git(args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def _status(fm):
    return (fm.get('status', 'active') or 'active').strip().strip('"')


def judgment_only_practices():
    """-> [(slug, narrow_globs, rule_text, file)] for every active,
    on-demand practice with no checked_by and no gates -- the set a
    session has to notice unaided, since nothing mechanical reaches it."""
    out = []
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError as e:
            sys.exit(f"routing audit FAIL: {e}")
        if fm.get('tier') != 'on-demand' or _status(fm) != 'active':
            continue
        checked_by = (fm.get('checked_by', 'null') or 'null').strip().strip('"')
        gates = json.loads(fm.get('gates', '[]') or '[]')
        if checked_by != 'null' or gates:
            continue
        globs = pp._globs(fm.get('applies_to', '[]'))
        out.append((fm['slug'], globs, sections.get('rule', ''), str(f)))
    return out


def _default_branch():
    head = _git(['symbolic-ref', 'refs/remotes/origin/HEAD'])
    if head:
        return head.rsplit('/', 1)[-1]
    for cand in ('main', 'master'):
        if _git(['rev-parse', '--verify', '--quiet', f'origin/{cand}']):
            return cand
    return 'HEAD'


def changed_files():
    """Every file changed vs the default branch, committed or in the
    worktree -- the same scope tools/doc_lint.py uses for markdown,
    generalized to every file rather than just *.md."""
    ref = f'origin/{_default_branch()}'
    base = _git(['merge-base', 'HEAD', ref]) or ref
    committed = _git(['diff', '--name-only', '--diff-filter=d', base]).split()
    worktree = _git(['diff', '--name-only', '--diff-filter=d']).split()
    return sorted(set(committed) | set(worktree))


def coverage(files):
    """-> [(slug, file)] for every judgment-only practice whose
    applies_to matches one of `files`."""
    practices = [(slug, globs, rule) for slug, globs, rule, _f
                 in judgment_only_practices()]
    hits = []
    for slug, globs, _rule in practices:
        narrow = [g for g in globs if g != '**']
        if not narrow:
            continue
        for path in files:
            if any(pp.path_matches(path, g) for g in narrow):
                hits.append((slug, path))
                break
    return hits


def _load_state():
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding='utf-8'))


def _save_state(state):
    STATE_PATH.write_text(
        json.dumps(state, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def slice_least_recent(size):
    state = _load_state()
    practices = judgment_only_practices()

    def key(item):
        slug = item[0]
        return state.get(slug, {}).get('last_reviewed', '')  # '' sorts first

    return sorted(practices, key=key)[:size]


def mark_reviewed(slugs):
    known = {slug for slug, *_ in judgment_only_practices()}
    unknown = [s for s in slugs if s not in known]
    if unknown:
        sys.exit(f"routing audit FAIL: not a judgment-only on-demand "
                 f"practice: {', '.join(unknown)}. Run --list to see the "
                 f"current set.")
    state = _load_state()
    today = datetime.date.today().isoformat()
    commit = _git(['rev-parse', 'HEAD']) or '(no commit)'
    for slug in slugs:
        state[slug] = {'last_reviewed': today, 'commit': commit}
    _save_state(state)
    print(f"routing audit: marked {', '.join(slugs)} reviewed as of {today}.")


def main():
    args = sys.argv[1:]
    if not args or args[0] == '--list':
        state = _load_state()
        for slug, _globs, _rule, _f in judgment_only_practices():
            when = state.get(slug, {}).get('last_reviewed', 'never')
            print(f"{slug}: last reviewed {when}")
        return 0

    cmd, rest = args[0], args[1:]

    if cmd == 'coverage':
        if rest == ['--changed']:
            files = changed_files()
        elif rest:
            files = rest
        else:
            sys.exit("routing audit FAIL: coverage needs FILE... or --changed.")
        hits = coverage(files)
        if not hits:
            print("routing audit: no judgment-only practice matches these files.")
            return 0
        for slug, path in hits:
            print(f"routing-failure candidate: {slug} matches {path} "
                 f"(checked_by: null, gates: [] -- nothing forces this to "
                 f"be seen except a session noticing it)")
        return 0

    if cmd == 'slice':
        size = 5
        if rest[:1] == ['--size']:
            if len(rest) < 2:
                sys.exit("routing audit FAIL: --size needs a value.")
            size = int(rest[1])
        for slug, _globs, rule, f in slice_least_recent(size):
            print(f"--- {slug} ({f}) ---")
            print(rule.strip() or '(no Rule recorded)')
            print()
        print(f"Read each Rule above against the actual work, then run:\n"
             f"  python3 tools/routing_audit.py mark-reviewed SLUG [SLUG...]")
        return 0

    if cmd == 'mark-reviewed':
        if not rest:
            sys.exit("routing audit FAIL: mark-reviewed needs at least one SLUG.")
        mark_reviewed(rest)
        return 0

    sys.exit(f"routing audit FAIL: unknown command {cmd!r} -- one of "
             f"coverage, slice, mark-reviewed, --list.")


if __name__ == '__main__':
    sys.exit(main())
