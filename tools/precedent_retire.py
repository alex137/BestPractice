#!/usr/bin/env python3
"""precedent_retire.py — Stage 6 of PRACTICE_ENGINE_PLAN.md's creation
pipeline: the periodic removal report. Proposes; never acts.

WHAT THIS REPORT IS AND IS NOT ASKING (2026-09-06). It finds practices that
are never cited and unreachable. That is evidence a COPY is idle here — it
is NOT evidence the rule is unwanted, because a rule already in force from a
higher source looks exactly the same from inside the source that stopped
carrying it. So a candidate here is the deduplication question first
(`status: deduplicated`, `in_force_at:` naming the surviving copy) and only
`status: retired` when nothing is in force anywhere. The tool keeps its
filename for the vendored-engine file set; the report it prints does not
claim more than it measured.

Per this phase's own amendment to Stage 6 (PRACTICE_ENGINE_PLAN.md,
"retirement is a candidate, never an action"), retiring anything this report
names still goes through the SAME per-level approval gate Stage 4 defines
for creation — this tool only ever prints, it never sets `status:` at all.

WHAT THIS CAN AND CANNOT SEE, stated the way routing_eval.py and
spec/ATTENTION_CEILING.md already state their own checks' limits, so this
report is not read as more authoritative than it is:

  never cited     MEASURABLE. Grepped across every practices/*.md and every
                  top-level doc in the source, excluding the practice's own
                  file.
  unreachable     MEASURABLE. Same three-way test verify_harness.py's
                  check_reachability already applies: no checked_by, no
                  narrower-than-`**` applies_to, no occasion, no gate.
  check never     NOT MEASURABLE. This codebase keeps no persistent log of
  trips           check runs over time — only the current run's pass/fail.
                  A practice with a real `checked_by` is reported as
                  "enforced, trip history not tracked" rather than silently
                  omitted or guessed at.

A practice is flagged a REMOVAL CANDIDATE only on the two measurable
signals together (never cited AND unreachable) — never on the unmeasurable
one, which would be reporting a number this tool does not actually have.

Usage:
  precedent_retire.py --against PATH[,PATH...]
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp  # noqa: E402
import build_views as bv  # noqa: E402

DOC_GLOBS = ['*.md', 'spec/*.md', 'decisions/*.md']


def _citation_count(slug, source_root, own_file):
    pat = re.compile(rf'\b{re.escape(slug)}\b')
    count = 0
    seen_files = set()
    for pattern in DOC_GLOBS:
        for f in pathlib.Path(source_root).glob(pattern):
            if f.resolve() == own_file.resolve() or f in seen_files:
                continue
            seen_files.add(f)
            try:
                text = f.read_text(encoding='utf-8')
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            count += len(pat.findall(text))
    practices_dir = pathlib.Path(source_root) / 'practices'
    if practices_dir.is_dir():
        for f in sorted(practices_dir.glob('*.md')):
            if f.resolve() == own_file.resolve():
                continue
            try:
                text = f.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            count += len(pat.findall(text))
    return count


def _is_unreachable(fm):
    """Frontmatter values come back as raw, unparsed strings from
    split_practices.py's reader (`applies_to` is literally the text
    '["**"]', not a Python list) -- this compares against the same known
    literal forms verify_harness.py's own check_reachability already
    established, rather than re-parsing JSON, to stay consistent with how
    every other tool in this codebase reads this frontmatter."""
    checked_by = fm.get('checked_by', 'null')
    applies_to = fm.get('applies_to', '[]')
    occasion = fm.get('occasion', '""')
    gates = fm.get('gates', '[]')
    has_checked_by = checked_by not in ('null', '')
    has_narrow_applies = applies_to not in ('[]', '["**"]', '')
    has_occasion = occasion not in ('""', "''", '', 'null')
    has_gates = gates not in ('[]', '')
    is_resident = fm.get('tier', 'on-demand').strip('"') == 'resident'
    return not (has_checked_by or has_narrow_applies or has_occasion or has_gates or is_resident), has_checked_by


def report(against_paths):
    candidates = []
    total = 0
    for source in against_paths:
        d = pathlib.Path(source) / 'practices'
        if not d.is_dir():
            continue
        for f in sorted(d.glob('*.md')):
            try:
                fm, _sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            # Any practice not in force -- a `deduplicated` one is
            # already gone from this source and must not be re-proposed
            # for removal.
            if not bv.is_in_force(fm):
                continue
            total += 1
            slug = fm.get('slug', f.stem)
            citations = _citation_count(slug, source, f)
            unreachable, has_checked_by = _is_unreachable(fm)
            enforced_note = ' [enforced, trip history not tracked]' if has_checked_by else ''
            if citations == 0 and unreachable:
                candidates.append((source, slug, citations))
                print(f"REMOVAL CANDIDATE: {slug!r} ({source}) — 0 citations "
                      f"elsewhere, unreachable by any channel{enforced_note}")
    print()
    print(f"{total} active practice(s) scanned across {len(against_paths)} source(s); "
          f"{len(candidates)} removal candidate(s).")
    if candidates:
        print(
            "\nASK THE DEDUPLICATION QUESTION FIRST. Never cited and "
            "unreachable says a COPY is idle here; it does not say the rule "
            "is unwanted. The same evidence fits a rule already in force "
            "from a higher source, which is the common case and the one "
            "that must not be read as a removal. So for each candidate: "
            "what is the surviving copy, and does it resolve in force? If "
            "there is one, this is `status: deduplicated` with "
            "`in_force_at:` naming it. Only when the answer is nothing, "
            "anywhere, is it `status: retired`.")
        print(
            "\nEither way it needs the SAME per-level approval as creating "
            "a practice (Stage 4, and Stage 6's own amendment): individual "
            "— the owner's own yes; team — an approver's review; universal — "
            "a PR to Precedent. This report proposes; it does not set "
            "`status:` on anything.")
    return candidates


def _parse_args(argv):
    # `--help` is the first thing anyone types, and until 2026-09-06 every
    # tool here answered it with "FAIL: expected --flag value pairs, stuck at
    # '--help'" -- a hard error, on the exact command documentation/ tells a
    # new reader to run. The module docstring is already the usage text; print
    # it and exit 0.
    if any(a in ('--help', '-h') for a in argv):
        print((sys.modules['__main__'].__doc__ or __doc__ or '').strip())
        raise SystemExit(0)
    args = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith('--') or i + 1 >= len(argv):
            sys.exit(f"precedent_retire FAIL: expected --flag value pairs, stuck at {tok!r}")
        args[tok] = argv[i + 1]
        i += 2
    return args


def main():
    args = _parse_args(sys.argv[1:])
    against = args['--against'].split(',') if args.get('--against') else [str(ROOT)]
    report(against)
    return 0


if __name__ == '__main__':
    sys.exit(main())
