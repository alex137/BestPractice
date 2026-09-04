#!/usr/bin/env python3
"""behavioral_replay.py — phase-2's own done-when condition, the one the
plan calls out by name (Sequence row 2: "and the premise is measured, not
assumed"; Risks: "Phase 2 is not done when the plumbing works; it is done
when the loading model has been measured against real work — replay past
commits where a practice demonstrably applied and assert the loader would
have surfaced it, then compare the miss rate against the old always-loaded
arrangement.").

What this CAN measure mechanically, from git history alone, without a human
re-reading every commit: for every commit that touched at least one file,
which on-demand practices' `applies_to` glob matches a changed file (this is
"a practice demonstrably applied," to the precision path-globbing can state
it), and whether tools/precedent_paths.py -- the actual path-triggered
loading channel, not a reimplementation of it -- surfaces that practice for
those files. Comparing that against the old arrangement (every practice
always resident, so it "surfaces" everything, unconditionally, at the cost
of loading everything every time) gives the real, measured trade this repo's
own history exhibits.

What this CANNOT measure mechanically, and says so rather than pretending
otherwise: whether an `occasion`-only practice (no narrow applies_to, no
checked_by) would actually have been read by a model that saw only the
occasion-index clause for it. That is a judgment call about what a session
did with prose it was shown, not a fact recoverable from a diff, and the
plan names this as the design's real weak point (the deep check exists
precisely because of it). This script reports how many on-demand practices
are occasion-only and therefore outside what it can verify, rather than
silently treating "not measurable" as "passing."

MECHANICAL CORRECTNESS, ADDED LATER (spec/SIMULATION_BRIEF.md phase 1). The
measurement above is REACH ONLY: would a practice have been surfaced. It
never asks whether the work that followed was actually correct. `--with-
checks` adds a second, still-mechanical measurement for the ~26 practices
whose checked_by is PROVEN to fire both ways by
tools/verify_harness.py's check_precedent_check_fires (never the full 26 --
only the ones that function actually exercises; a checked_by claim nobody
has watched fire is worth less than no claim, per spec/ENFORCEMENT.md's own
phase-4 finding): check out each replayed commit into a scratch worktree
and run THAT COMMIT'S OWN tools/precedent_check.py against the diff it
made. This is retrospective enforcement compliance, not routing -- it says
whether the check would have fired at the time, nothing about whether a
session was ever shown the practice or complied with it on purpose. It is
also slower (a worktree checkout and two subprocesses per commit), so it is
bounded separately by --max-correctness-commits and left off by default.

Run:
  python3 tools/behavioral_replay.py [--max-commits N]
  python3 tools/behavioral_replay.py --with-checks [--max-correctness-commits N]
"""
import fnmatch, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import precedent_paths as pp


# --------------------------------------------------- the reference matcher
# The cross-check below is only worth running if it is a DIFFERENT
# implementation. The first version of this file "independently re-derived"
# each commit's matches with `fnmatch.fnmatch(f, g)` -- the exact call
# precedent_paths.py was making at the time. It therefore agreed with the
# loader on every commit and reported "0 misses" while the loader was
# silently failing to match any top-level file against "**/*.md".
#
# So this is deliberately a different algorithm: a recursive walk over path
# SEGMENTS, where `**` consumes zero or more whole segments and every other
# segment is matched with fnmatch (safe there -- a single segment contains
# no "/"). It shares no code with precedent_paths.py's glob-to-regex
# translation, so the two can only agree by both being right about the
# semantics rather than by sharing a mistake.
def _ref_match_segments(path_segs, glob_segs):
    if not glob_segs:
        return not path_segs
    head = glob_segs[0]
    if head == '**':
        if len(glob_segs) == 1:
            return len(path_segs) >= 1      # "dir/**" = everything INSIDE dir
        return any(_ref_match_segments(path_segs[i:], glob_segs[1:])
                   for i in range(len(path_segs) + 1))
    if not path_segs:
        return False
    return (fnmatch.fnmatchcase(path_segs[0], head)
            and _ref_match_segments(path_segs[1:], glob_segs[1:]))


def ref_match(path, glob):
    # Same root-relative normalization the channel does, re-derived here
    # rather than imported, for the same reason as above.
    root = ROOT.as_posix().rstrip('/') + '/'
    p = str(path).replace('\\', '/')
    if p.startswith(root):
        p = p[len(root):]
    while p.startswith('./'):
        p = p[2:]
    return _ref_match_segments(p.lstrip('/').split('/'), glob.split('/'))


def load_all_practices():
    out = []
    for f in sorted((ROOT / 'practices').glob('*.md')):
        fm, sections = sp._read_practice_file(f)
        out.append(fm)
    return out


def git_commits(max_commits):
    log = subprocess.run(
        ['git', '-C', str(ROOT), 'log', '--no-merges', '--pretty=format:%H',
         f'-n{max_commits}'],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return log


def changed_files(commit_hash):
    out = subprocess.run(
        ['git', '-C', str(ROOT), 'diff-tree', '--no-commit-id', '--name-only',
         '-r', commit_hash],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return [f for f in out if f]


def is_shallow_clone():
    out = subprocess.run(
        ['git', '-C', str(ROOT), 'rev-parse', '--is-shallow-repository'],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return out == 'true'


# --------------------------------------------------- mechanical correctness
# (phase 1 of spec/SIMULATION_BRIEF.md -- see the module docstring above)

def _proven_checked_slugs():
    """Slugs verify_harness.py's check_precedent_check_fires() actually
    proves fire both ways -- read from its own case(...) calls rather than
    hand-copied here, so this list cannot silently drift from what the
    harness actually proves as new checks are added or retired. Returns []
    if the function cannot be found (a vendored/older tree, say), so a
    caller failing to find any proven slugs reads as "nothing to check",
    never as a crash."""
    vh_path = ROOT / 'tools' / 'verify_harness.py'
    if not vh_path.exists():
        return []
    text = vh_path.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'\ndef check_precedent_check_fires\(.*?(?=\ndef [a-zA-Z_]+\()',
                  text, re.S)
    if not m:
        return []
    return sorted(set(re.findall(r"\bcase\('([a-z][a-z0-9-]*)'", m.group(0))))


def _git_out(*args, cwd=None):
    r = subprocess.run(['git', *args], cwd=str(cwd or ROOT),
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


_VIOLATION_RE = re.compile(r'^VIOLATION\s+(\S+)', re.M)
_ERROR_RE = re.compile(r'^ERROR\s+(\S+)', re.M)
_SKIPPED_RE = re.compile(r'^SKIPPED\s+(\S+)', re.M)
# scope is padded to 8 chars with trailing spaces before the closing "]" --
# \S+ stops at the first space regardless, so the padding is harmless here.
_LIST_ROW_RE = re.compile(r'^\s{2}(\S+)\s+\[(\S+)\s*\]', re.M)


def checked_replay(commits, max_commits, proven):
    """For up to `max_commits` of the given (already non-merge,
    file-touching) commits, most recent first: check the commit out into a
    scratch worktree and run THAT COMMIT'S OWN tools/precedent_check.py
    (not this tree's copy -- older commits may predate a check entirely,
    which is a real "not yet built" fact, not a gap to paper over) against
    the diff that single commit made, via --range parent..commit. Only
    `proven` slugs are trusted, and only in 'tree' or 'change' scope --
    'turn-end' checks (verify-postcondition, no-rewrite-for-warnings) are
    about live session state, never exercised by --range at all, and would
    read as a false 100% pass rate if counted here.

    PASS is inferred: the slug appears in that commit's own --list output
    (the check existed and applies in general) and in none of that
    commit's VIOLATION/ERROR/SKIPPED lines. This is the same "a skip is
    not a pass" convention precedent_check.py itself uses; a check that
    raises NotApplicable for that commit contributes no data point either
    way, in either direction.

    Returns (commits_considered, {slug: {'PASS': n, 'VIOLATION': n,
    'ERROR': n}}), or a string explaining why it could not run at all."""
    sample = commits[:max_commits]
    if not sample:
        return 0, {}
    tally = {}
    considered = 0
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-checked-replay-'))
    try:
        rc, _out, err = _git_out('worktree', 'add', '--detach', '-q', str(tmp), 'HEAD')
        if rc != 0:
            return f'could not create a scratch worktree: {err.strip()}'
        for sha in sample:
            rc, parent, _e = _git_out('rev-parse', f'{sha}^')
            if rc != 0:
                continue        # no parent (the initial commit) -- nothing to diff
            parent = parent.strip()
            rc, _o, _e = _git_out('checkout', '--detach', '-q', sha, cwd=tmp)
            if rc != 0:
                continue
            script = tmp / 'tools' / 'precedent_check.py'
            if not script.exists():
                continue        # the enforced channel did not exist yet at this commit
            list_r = subprocess.run([sys.executable, str(script), '--list'],
                                    cwd=str(tmp), capture_output=True, text=True)
            available = dict(_LIST_ROW_RE.findall(list_r.stdout))
            run_r = subprocess.run([sys.executable, str(script), '--range',
                                    f'{parent}..{sha}'],
                                   cwd=str(tmp), capture_output=True, text=True)
            out = run_r.stdout + run_r.stderr
            violated = set(_VIOLATION_RE.findall(out))
            errored = set(_ERROR_RE.findall(out))
            skipped = set(_SKIPPED_RE.findall(out))
            considered += 1
            for slug in proven:
                if available.get(slug) not in ('tree', 'change'):
                    continue    # not registered yet at this commit, or turn-end scope
                t = tally.setdefault(slug, {'PASS': 0, 'VIOLATION': 0, 'ERROR': 0})
                if slug in violated:
                    t['VIOLATION'] += 1
                elif slug in errored:
                    t['ERROR'] += 1
                elif slug in skipped:
                    continue    # NotApplicable at this commit -- not a data point
                else:
                    t['PASS'] += 1
        return considered, tally
    finally:
        _git_out('worktree', 'remove', '--force', str(tmp))


def report_checked_replay(commits, max_correctness_commits):
    print("\n== Mechanical correctness (checked_by, historical replay) ==")
    proven = _proven_checked_slugs()
    if not proven:
        print("  Could not find any proven checked_by slugs in verify_harness.py's "
              "check_precedent_check_fires -- skipping.")
        return
    result = checked_replay(commits, max_correctness_commits, set(proven))
    if isinstance(result, str):
        print(f"  {result}")
        return
    considered, tally = result
    if not tally:
        print(f"  {considered} commit(s) sampled, checked out one at a time into a "
              f"scratch worktree -- none of the {len(proven)} proven checked_by "
              f"practices both existed at the time and applied to any of them.")
        return
    total_pass = sum(t['PASS'] for t in tally.values())
    total_violation = sum(t['VIOLATION'] for t in tally.values())
    total_error = sum(t['ERROR'] for t in tally.values())
    total = total_pass + total_violation + total_error
    print(f"  {considered} commit(s) checked out into a scratch worktree, each run "
          f"through THAT COMMIT'S OWN tools/precedent_check.py against the diff it "
          f"made, for the {len(proven)} practices verify_harness.py proves fire both "
          f"ways.")
    if total:
        print(f"  {total} (commit, proven-check) data point(s): {total_pass} clean, "
              f"{total_violation} violated, {total_error} errored "
              f"({100 * total_violation / total:.0f}% violation rate).")
    else:
        print("  0 data points -- every proven check either did not exist yet or "
              "raised NotApplicable on every commit sampled.")
    for slug in sorted(tally):
        t = tally[slug]
        n = t['PASS'] + t['VIOLATION'] + t['ERROR']
        if n == 0:
            continue
        note = f", {t['ERROR']} errored" if t['ERROR'] else ""
        print(f"    {slug:32} {t['PASS']}/{n} clean{note}")
    print("  Read this narrowly. It is retrospective enforcement compliance for the "
          f"{len(proven)} practices with a checked_by proven to fire both ways -- it "
          "says nothing about the other practices in the catalogue, and nothing about "
          "whether a session was ever shown or complied with these on purpose. Some "
          "change-scope checks also return a vacuous clean result (no findings) when "
          "no file of the relevant type was touched at all, rather than raising "
          "NotApplicable for it -- so 'clean' here is an upper bound on compliance, "
          "not confirmation the check meaningfully exercised anything on every commit "
          "counted.")


# Below this many replayable (non-merge, file-touching) commits, a miss-rate
# or cost-reduction percentage is noise, not a measurement -- report the
# gap plainly and degrade rather than either crashing (a fresh `git clone
# --depth 1`, this repo's own documented default per AGENTS.md's environment
# notes, has exactly ONE commit and zero parents to diff against) or
# printing a confident-looking number computed from too little data.
MIN_COMMITS_FOR_MEANINGFUL_REPLAY = 20


def main():
    args = sys.argv[1:]
    max_commits = 142
    if '--max-commits' in args:
        i = args.index('--max-commits') + 1
        if i >= len(args):
            sys.exit("behavioral_replay FAIL: --max-commits needs a number after it.")
        try:
            max_commits = int(args[i])
        except ValueError:
            sys.exit(f"behavioral_replay FAIL: --max-commits wants an integer, got "
                     f"{args[i]!r}.")
        if max_commits < 1:
            sys.exit("behavioral_replay FAIL: --max-commits must be at least 1.")

    with_checks = '--with-checks' in args
    max_correctness_commits = 25
    if '--max-correctness-commits' in args:
        i = args.index('--max-correctness-commits') + 1
        if i >= len(args):
            sys.exit("behavioral_replay FAIL: --max-correctness-commits needs a "
                     "number after it.")
        try:
            max_correctness_commits = int(args[i])
        except ValueError:
            sys.exit(f"behavioral_replay FAIL: --max-correctness-commits wants an "
                     f"integer, got {args[i]!r}.")
        if max_correctness_commits < 1:
            sys.exit("behavioral_replay FAIL: --max-correctness-commits must be at "
                     "least 1.")

    practices = load_all_practices()
    n_total = len(practices)
    resident = [p for p in practices if p.get('tier') == 'resident']
    on_demand = [p for p in practices if p.get('tier') == 'on-demand']
    on_demand_narrow = pp.load_on_demand_practices()  # (slug, globs, rule) with real applies_to
    narrow_slugs = {slug for slug, _g, _r in on_demand_narrow}
    occasion_only = [p for p in on_demand if p['slug'] not in narrow_slugs]

    commits = git_commits(max_commits)
    if not commits:
        print("REPLAY_STATUS: DEGRADED (no commits at all -- unexpected, but not a loader defect)")
        return 0

    n_commits = 0
    n_commits_with_hit = 0
    total_path_matches = 0
    total_old_loaded = 0
    total_new_loaded = 0
    verify_ok = True
    miss_examples = []

    for h in commits:
        files = changed_files(h)
        if not files:
            continue
        n_commits += 1

        # "demonstrably applied": which on-demand practices' applies_to
        # matches a file this commit actually touched.
        applicable = pp.matches_for_paths(files, on_demand_narrow)
        applicable_slugs = {slug for slug, _path in applicable}
        if applicable_slugs:
            n_commits_with_hit += 1
            total_path_matches += len(applicable_slugs)

        # Independently re-derive with the segment-walk matcher above -- a
        # different algorithm, not a second call to the same one -- so this
        # is a real cross-check rather than a tautology.
        reference = set()
        for slug, globs, _rule in on_demand_narrow:
            if any(ref_match(f, g) for f in files for g in globs):
                reference.add(slug)
        if reference != applicable_slugs:
            verify_ok = False
            miss_examples.append((h[:10], reference - applicable_slugs, applicable_slugs - reference))

        # Cost comparison for this commit: old arrangement loads all 52
        # every time; new arrangement loads the resident set plus whatever
        # the path channel actually surfaced for these specific files.
        total_old_loaded += n_total
        total_new_loaded += len(resident) + len(applicable_slugs)

    if n_commits < MIN_COMMITS_FOR_MEANINGFUL_REPLAY:
        shallow = is_shallow_clone()
        print(f"Replayed only {n_commits} file-touching non-merge commit(s) "
              f"(of {len(commits)} available in this clone) -- below "
              f"{MIN_COMMITS_FOR_MEANINGFUL_REPLAY}, not enough for a meaningful miss-rate "
              f"or cost figure, so none is printed rather than reporting a number computed "
              f"from too little data.")
        if shallow:
            print(f"  This is a shallow clone (git rev-parse --is-shallow-repository: true). "
                  f"Deepen it first: `git fetch --depth=500 origin <branch>` (bounded, per this "
                  f"repo's own environment notes), then re-run.")
        if with_checks:
            report_checked_replay(commits, max_correctness_commits)
        print("REPLAY_STATUS: DEGRADED (insufficient commit history for a meaningful replay -- "
              "not a loader defect; deepen the clone and re-run)")
        return 0

    print(f"Replayed {n_commits} non-merge commits (of {len(commits)} requested) from this "
          f"repo's own history.\n")

    print("== Mechanical channel (applies_to path matching) ==")
    print(f"  On-demand practices reachable this way: {len(narrow_slugs)} of {len(on_demand)}")
    print(f"  Commits where at least one such practice's applies_to matched a "
          f"changed file: {n_commits_with_hit} of {n_commits} "
          f"({100 * n_commits_with_hit / n_commits:.0f}%)")
    print(f"  Total (practice, commit) matches: {total_path_matches}")
    print(f"  precedent_paths.py cross-checked against an independent segment-walk matcher: "
          f"{'MATCH on every commit (0 misses)' if verify_ok else 'MISMATCH -- see below'}")
    if not verify_ok:
        for h, missed, extra in miss_examples[:10]:
            print(f"    {h}: missed={missed} extra={extra}")

    print("\n== Cost: old (always-resident) vs. new (resident + path-triggered) ==")
    old_avg = total_old_loaded / n_commits
    new_avg = total_new_loaded / n_commits
    print(f"  Old: {old_avg:.0f} practices in context per commit (constant: all {n_total}, always)")
    print(f"  New: {new_avg:.1f} practices in context per commit on average "
          f"({len(resident)} resident + practices the path channel actually surfaced)")
    print(f"  Reduction: {100 * (1 - new_avg / old_avg):.0f}%")

    print("\n== What this does NOT measure (stated plainly, not glossed over) ==")
    print(f"  {len(occasion_only)} of {len(on_demand)} on-demand practices have no "
          f"checked_by and no applies_to narrower than \"**\" -- they are reachable only "
          f"via the occasion index's prose, which this script cannot mechanically verify "
          f"a session would have read and acted on for any given commit. That gap is the "
          f"plan's own named weak point (\"a practice with a wrong or missing trigger is "
          f"worse than one buried in a wall of text, because nobody notices its absence\") "
          f"and is what the periodic deep check exists to catch going forward, not what "
          f"this one-off replay can settle.")

    print("\n== Miss rate, stated directly ==")
    print(f"  Old arrangement: 0% miss rate by construction (everything always loaded).")
    if verify_ok:
        print(f"  New arrangement, mechanical channel: 0 disagreements across {n_commits} "
              f"replayed commits ({total_path_matches} applicable-practice instances) between "
              f"precedent_paths.py and a separately-written segment-walk matcher.")
        print(f"  Read that precisely. It says the channel's two implementations agree on this "
              f"history; it does NOT say the globs are the right globs, and it is not a "
              f"'0% miss rate' in any sense the plan would recognise. An earlier version of "
              f"this cross-check re-derived matches with the same fnmatch call the loader "
              f"used, agreed with it on every commit, and reported 0 misses while the loader "
              f"was silently matching NO top-level file against \"**/*.md\" at all. What "
              f"pins the semantics is tools/verify_harness.py's stated-case table, not this "
              f"agreement. And the occasion-index channel remains untested here, as above.")
    else:
        print(f"  New arrangement, mechanical channel: MISMATCH on {len(miss_examples)} of "
              f"{n_commits} replayed commits -- precedent_paths.py's output disagreed with an "
              f"independent fnmatch re-derivation over the same files (see examples above). "
              f"This is a real bug in the loader's path-matching, not a measurement caveat.")

    if with_checks:
        report_checked_replay(commits, max_correctness_commits)

    print(f"\nREPLAY_STATUS: {'OK' if verify_ok else 'MISMATCH'}")
    return 0 if verify_ok else 1


if __name__ == '__main__':
    sys.exit(main())
