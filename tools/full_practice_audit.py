#!/usr/bin/env python3
"""full_practice_audit.py -- the full practice audit (practice:
full-practice-audit).

Enumerates EVERY practice in force for this checkout -- universal, team, and
repo-local from tracked precedent.json, individual from the user-level
config, exactly as tools/precedent_resolve.py resolves them (same code path,
reused here rather than re-walked) -- and hands them to the invoking session
as a checklist to judge, one at a time, against the actual repo state.
On-demand only, invoked explicitly by a person; never wired into a commit,
push, or merge gate. The closest existing analog is "very deep check"
(PRACTICE_ENGINE_PLAN.md's naming-collision fix, 2026-09-01): a heavier,
whole-catalogue sweep kept deliberately outside the routine gates.

READ THIS BEFORE TRUSTING ITS OUTPUT. spec/ATTENTION_CEILING.md pre-registered
and ran almost exactly this shape -- a retrospective, judge-only pass over
practice candidates -- as "the review arm". Predicted 80-86% recall; measured
54%, WORSE than a session doing the work with no review pass at all (84%).
That result falsified a whole-catalogue review as the PRIMARY control; the
validated fix was converting more practices to mechanical `checked_by`
checks, which cost nothing regardless of catalogue size. This tool is
knowingly NOT that fix -- it is a backstop for what enforcement has not yet
reached, run deliberately and rarely, not a substitute for enforcement and
not proven reliable at this larger scope (the review arm judged a loader
PREFILTER, not the whole catalogue this tool enumerates). See
spec/UNBUILT_PLAN_ITEMS.md for the eval this still needs before its
findings should be trusted at face value.

WHY MECHANICALLY-ENFORCED PRACTICES ARE NOT PRINTED IN FULL. A practice with
a working `checked_by` "needs no human-style review: the check either fired
or it did not" (PRACTICE_ENGINE_PLAN.md, the routing audit's own reasoning,
practice: routing-audit) -- re-reading its Rule to re-judge it by hand adds
dilution for zero gain, since the check is the faster and more reliable way
to know its status. Every practice from every source still appears in the
output below; enforced and gate-reached ones appear as one line (how they're
covered), and only the judgment-only set -- the one this audit actually
exists for -- gets its full Rule text.

Run:
  python3 tools/full_practice_audit.py [--repo PATH] [--user-config PATH]
      -- the full checklist: a summary line per source, then every
         judgment-only practice's full Rule text, grouped by level.
  python3 tools/full_practice_audit.py --json [--repo PATH] [--user-config PATH]
      -- the same enumeration as structured data, for a session that wants
         to track verdicts itself rather than read the printed report.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_resolve as pr


def _status(fm):
    return (fm.get('status', 'active') or 'active').strip().strip('"')


def enumerate_practices(repo=None, user_config=None):
    """-> {'sources': [...], 'missing': [...], 'practices': [rows]}, one row
    per active, in-force practice: slug, level, source, title, coverage
    ('checked_by' / 'gates' / 'judgment-only'), and its Rule text."""
    sources = pr.load_config(repo or str(ROOT), user_config)
    if not sources:
        sys.exit("full practice audit FAIL: no practice sources are declared "
                 "-- see `python3 tools/precedent_resolve.py` for what this "
                 "repo and your user-level config need.")
    res = pr.resolve(sources)
    rows = []
    for slug, practice in sorted(res['practices'].items()):
        fm, sections = practice['fm'], practice['sections']
        if _status(fm) != 'active':
            continue
        checked_by = (fm.get('checked_by', 'null') or 'null').strip().strip('"')
        gates = json.loads(fm.get('gates', '[]') or '[]')
        if checked_by != 'null':
            coverage = f'checked_by: {checked_by}'
        elif gates:
            coverage = f'gates: {gates}'
        else:
            coverage = 'judgment-only'
        rows.append({
            'slug': slug, 'level': practice['level'], 'source': practice['source'],
            'title': fm.get('title', slug), 'coverage': coverage,
            'rule': sections.get('rule', '').strip(),
        })
    return {'sources': sources, 'missing': res['missing'], 'practices': rows}


def main():
    args = sys.argv[1:]
    repo, user_config = None, None
    for flag, dest in (('--repo', 'repo'), ('--user-config', 'user_config')):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(f"full practice audit FAIL: {flag} needs a value.")
            value = args[i + 1]
            args = args[:i] + args[i + 2:]
            if dest == 'repo':
                repo = value
            else:
                user_config = value
    as_json = '--json' in args

    data = enumerate_practices(repo, user_config)
    for m in data['missing']:
        print(f"full practice audit: the {m['level']} source {m['name']!r} "
             f"is not available ({m['reason']}) -- running WITHOUT it.",
             file=sys.stderr)

    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    total = len(data['practices'])
    judgment_only = [r for r in data['practices'] if r['coverage'] == 'judgment-only']
    print(f"full practice audit: {total} active practices across "
         f"{len(data['sources'])} source(s); {len(judgment_only)} are "
         f"judgment-only (no checked_by, no gates) -- the actual workload "
         f"below. Everything else is covered by a mechanical check or a "
         f"deterministic gate; confirm those separately with "
         f"`python3 tools/precedent_check.py` and "
         f"`python3 tools/precedent_gate.py --list` rather than re-judging "
         f"them here.\n")

    by_level = {}
    for r in data['practices']:
        by_level.setdefault(r['level'], []).append(r)
    for level in sorted(by_level):
        print(f"=== {level} ({len(by_level[level])} practices) ===")
        for r in by_level[level]:
            if r['coverage'] == 'judgment-only':
                print(f"\n--- {r['slug']} -- {r['title']} [{r['source']}] ---")
                print(r['rule'] or '(no Rule recorded)')
            else:
                print(f"{r['slug']}: {r['coverage']} ({r['source']})")
        print()

    print("For each judgment-only practice above: does it apply to the "
         "current repo state -- yes or no? If yes, is it satisfied -- yes "
         "or no, with the specific file and line? Judge one at a time; "
         "\"which of these might apply\" is the open framing that measured "
         "worse (spec/ATTENTION_CEILING.md).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
