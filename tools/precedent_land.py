#!/usr/bin/env python3
"""precedent_land.py — Stage 5 of PRACTICE_ENGINE_PLAN.md's creation
pipeline: write an approved candidate into the right repo's practices/ and
regenerate that repo's generated views.

Re-runs Stage 3's four criteria itself rather than trusting a prior
`precedent_promote.py` run — approval is a human act between promotion and
landing (Stage 4), and nothing should be able to skip straight to landing a
candidate that was never actually promoted.

THE ONE RULE STAGE 5 EXISTS TO ENFORCE ("What phase 5 should carry
forward," PRACTICE_ENGINE_PLAN.md): **a `checked_by` claim with no
registered, tested check is refused here, not merely warned about.**
"Registered" means different things per level, because the private repos
carry no `precedent_check.py` engine of their own
(spec/PRIVATE_ENFORCEMENT_BRIEF.md):

  universal          -> the slug must already be a key in
                         tools/precedent_check.py's CHECKS registry (which
                         the harness's check_precedent_check_fires already
                         guarantees carries a planted test case).
  individual / team  -> tools/checks/check_<name>.py must exist AND
                         tools/checks/tests/test_<name>.sh must exist AND
                         reference it by name — check_deep_check.py's own
                         invariant, replicated here rather than re-derived.

APPROVAL, per level (Stage 4, and this phase's own retirement-routing
amendment generalizes the same table to removal):
  individual -> --approved-by NAME is the owner's own "yes." Landed directly.
  team       -> --approved-by NAME must be a listed approver in that
                repo's approvers.json. Landed directly (the plan's own
                allowance: "for a small team ... the session commits it
                directly").
  universal  -> this tool DRAFTS practices/<slug>.md and STOPS. Stage 4's
                own answer for universal is "a PR to Precedent" — a human
                reviewing and merging a PR is the approval, and no tool
                should be able to grant that to itself. Commit the drafted
                file to a branch and open a PR.

Usage:
  precedent_land.py --file CANDIDATE.md --level individual|team
      --path REPO --approved-by NAME [--against PATH[,PATH...]]
  precedent_land.py --file CANDIDATE.md --level universal
      [--against PATH[,PATH...]]
"""
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_promote as pp  # noqa: E402
import precedent_candidate as pc  # noqa: E402


class LandRefused(Exception):
    pass


def _verify_checked_by_universal(checked_by, slug):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_pc_engine', ROOT / 'tools' / 'precedent_check.py')
    pc_engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pc_engine)
    if slug not in pc_engine.CHECKS:
        raise LandRefused(
            f"proposed_checked_by is {checked_by!r} but {slug!r} is not a "
            f"key in tools/precedent_check.py's CHECKS registry -- a claim "
            f"with no registered, tested check is refused here (the exact "
            f"gap phase 4 spent its first hours undoing). Register the "
            f"check and give it a planted case in "
            f"verify_harness.py's check_precedent_check_fires first.")


def _verify_checked_by_private(repo_path, checked_by):
    full = pathlib.Path(repo_path) / checked_by
    if not full.is_file():
        raise LandRefused(f"proposed_checked_by names {checked_by}, which "
                           f"does not exist under {repo_path}")
    m = re.match(r'tools/checks/check_(\w+)\.py$', checked_by)
    if not m:
        raise LandRefused(f"proposed_checked_by {checked_by!r} does not "
                           f"match the tools/checks/check_<name>.py convention "
                           f"this repo's checks use")
    name = m.group(1)
    test_path = pathlib.Path(repo_path) / 'tools' / 'checks' / 'tests' / f'test_{name}.sh'
    if not test_path.is_file():
        raise LandRefused(
            f"{checked_by} has no tools/checks/tests/test_{name}.sh -- "
            f"a check with no test proving it fires is exactly the claim-"
            f"without-a-case gap this rule exists to close.")
    if f'check_{name}.py' not in test_path.read_text(encoding='utf-8'):
        raise LandRefused(
            f"tools/checks/tests/test_{name}.sh exists but never invokes "
            f"check_{name}.py by name -- it is not actually testing this check.")


def _render_practice(fm, proposed_rule, observed, approved_by, level):
    today = datetime.date.today().isoformat()
    index_clause = fm.get('index_clause') or (
        proposed_rule[:76] + ('...' if len(proposed_rule) > 76 else ''))
    lines = ['---']
    lines.append(f"slug:        {fm['slug']}")
    lines.append(f"title:       {fm['title']}")
    lines.append(f"tier:        {fm.get('tier_requested', 'on-demand')}")
    lines.append("severity:    default")
    applies_to = fm.get('proposed_applies_to') or ['**']
    lines.append(f"applies_to:  [{', '.join(json.dumps(a) for a in applies_to)}]")
    occasion = fm.get('proposed_occasion')
    lines.append(f"occasion:    {json.dumps(occasion) if occasion else 'null'}")
    gates = fm.get('proposed_gates') or []
    lines.append(f"gates:       [{', '.join(json.dumps(g) for g in gates)}]")
    lines.append(f"index_clause: {json.dumps(index_clause)}")
    checked_by = fm.get('proposed_checked_by')
    lines.append(f"checked_by:  {checked_by if checked_by else 'null'}")
    lines.append("defines:     []")
    lines.append("status:      active")
    lines.append("supersedes:  []")
    overrides = fm.get('overrides')
    lines.append(f"overrides:   {json.dumps(overrides) if overrides else 'null'}")
    lines.append(f"added:       {today}")
    lines.append(f"approved_by: {json.dumps(f'{approved_by}, {today}')}")
    lines.append("source_practice_number: null")
    lines.append("---")
    lines.append("## Rule")
    lines.append(proposed_rule.strip())
    lines.append("")
    lines.append("## Why")
    lines.append(f"Raised via Precedent's creation pipeline (Stage 1 signal: "
                  f"{fm.get('signal')}), promoted at {level} level, approved "
                  f"by {approved_by} on {today}.")
    lines.append("")
    lines.append("## Story")
    lines.append(observed.strip())
    lines.append("")
    lines.append("## Install")
    if checked_by:
        lines.append(f"Enforced by `{checked_by}` (see spec/CANDIDATE_FORMAT.md "
                      f"for the candidate this was promoted from).")
    else:
        lines.append("No mechanical check yet -- reached via "
                      f"{'applies_to' if applies_to != ['**'] else 'occasion' if occasion else 'resident tier'} "
                      "only, per checkable-gets-checked's own standing rule, "
                      "a real check should still be attempted before this stays null indefinitely.")
    lines.append("")
    return '\n'.join(lines)


def land(candidate_path, level, repo_path, approved_by, against):
    result = pp.promote(candidate_path, level, against)  # raises PromoteRefused on failure
    fm = result['fm']
    checked_by = fm.get('proposed_checked_by')

    if level == 'universal':
        if checked_by:
            _verify_checked_by_universal(checked_by, fm['slug'])
        dest_dir = ROOT / 'practices'
        approved_by = approved_by or '(pending PR review)'
    else:
        if not repo_path:
            raise LandRefused('--path REPO is required for individual/team')
        if not approved_by:
            raise LandRefused('--approved-by NAME is required')
        if level == 'team':
            approvers_file = pathlib.Path(repo_path) / 'approvers.json'
            if not approvers_file.is_file():
                raise LandRefused(f'{approvers_file} does not exist -- cannot verify an approver')
            approvers = json.loads(approvers_file.read_text(encoding='utf-8')).get('approvers', [])
            names = {a.get('name') for a in approvers} | {a.get('github') for a in approvers}
            if approved_by not in names:
                raise LandRefused(
                    f"{approved_by!r} is not in {approvers_file}'s approver list "
                    f"({sorted(n for n in names if n)}) -- team-level landing "
                    f"needs a real approver, per Stage 4")
        if checked_by:
            _verify_checked_by_private(repo_path, checked_by)
        dest_dir = pathlib.Path(repo_path) / 'practices'

    _fm, _body = pc._parse_frontmatter(pathlib.Path(candidate_path).read_text(encoding='utf-8'))
    observed, _proposed_rule = pc.split_candidate_sections(_body)

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{fm['slug']}.md"
    if dest.exists():
        raise LandRefused(f'{dest} already exists -- refusing to overwrite')
    dest.write_text(_render_practice(fm, result['proposed_rule'], observed, approved_by, level), encoding='utf-8')
    if level in ('individual', 'team'):
        # Mark the source candidate promoted so it stops reading as still
        # open -- an already-landed candidate left at `status: open` would
        # keep surfacing from `precedent_candidate.py list --status open`
        # as if it still needed a decision, and nothing would stop a second
        # promote/land of the same file.
        pc.set_candidate_status(candidate_path, 'promoted', required_current='open')

    print(f"LANDED: {dest}")
    # A file path alone requires the reader to already know this repo's
    # layout to know what just happened -- say it in plain words too, so a
    # session relaying this to a human has no way to leave out WHICH of the
    # three it is or WHERE. Lives HERE, in land() itself, not in main() --
    # a 2026-09-03 deep-check audit found the disclosure printed only from
    # the CLI entry point, so a future programmatic caller of land() (an
    # orchestration script, a batch-land tool) would land a practice with
    # no disclosure at all. No such caller exists today, but the practice's
    # own Rule is "every time", not "every time through this one CLI".
    # practice: disclose-landing
    if level == 'individual':
        print(f"DISCLOSE TO THE HUMAN: this is now part of YOUR OWN "
              f"individual practice set ({repo_path}). It applies "
              f"only to you, is already in force, and nobody else approved "
              f"or needs to.")
    elif level == 'team':
        print(f"DISCLOSE TO THE HUMAN: this is now part of the TEAM "
              f"practice set at {repo_path}, approved by "
              f"{approved_by!r}. It is already in force for "
              f"everyone on that team.")
    else:  # universal
        print("DISCLOSE TO THE HUMAN: this is a DRAFT ONLY, not yet in "
              "force for anyone. Stage 4's universal approval is a PR to "
              "Precedent -- commit this file on a branch and open a PR; this "
              "tool does not merge it, and nothing is in force until that PR "
              "is reviewed and merged by a human other than whoever wrote "
              "it.")
    return dest, level


def _parse_args(argv):
    args = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith('--') or i + 1 >= len(argv):
            sys.exit(f"precedent_land FAIL: expected --flag value pairs, stuck at {tok!r}")
        args[tok] = argv[i + 1]
        i += 2
    return args


def main():
    args = _parse_args(sys.argv[1:])
    candidate_path = args.get('--file')
    level = args.get('--level')
    if not candidate_path or level not in pc.LEVELS:
        sys.exit(f"precedent_land FAIL: --file CANDIDATE.md and --level "
                  f"({sorted(pc.LEVELS)}) are both required")
    against = (args['--against'].split(',') if args.get('--against')
               else pp.default_against(candidate_path, level))

    try:
        dest, level = land(candidate_path, level, args.get('--path'),
                            args.get('--approved-by'), against)
    except (pp.PromoteRefused, LandRefused) as e:
        if isinstance(e, pp.PromoteRefused):
            n, name, reason = e.args
            print(f"REFUSED at promotion (criterion {n}: {name}): {reason}")
        else:
            print(f"REFUSED at landing: {e}")
        return 1

    # LANDED: / DISCLOSE TO THE HUMAN: already printed inside land() itself
    # (practice: disclose-landing) -- every caller gets it, not just this
    # CLI entry point.
    if level != 'universal':
        print(f"Regenerate this repo's generated views if it has any "
              f"(tools/build_views.py in Precedent; the private sets carry "
              f"no generated views today).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
