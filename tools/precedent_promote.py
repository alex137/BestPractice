#!/usr/bin/env python3
"""precedent_promote.py — Stage 3 of PRACTICE_ENGINE_PLAN.md's creation
pipeline: run a candidate (spec/CANDIDATE_FORMAT.md) against the four
promotion criteria. Refuses with a named reason on any failure; on a full
pass, drafts a practice file (spec/PRACTICE_FORMAT.md shape) plus a guessed
level and reason, ready for Stage 4's approval and Stage 5's landing.

This tool NEVER writes practices/*.md itself — that is Stage 5
(precedent_land.py), which additionally hard-enforces the carry-forward
rule from "What phase 5 should carry forward": a `checked_by` claim with no
registered, tested check is refused there, not merely warned about here.

THE FOUR CRITERIA (PRACTICE_ENGINE_PLAN.md, Stage 3):
  1. Recurrence or real cost.
  2. Reachability -- a checked_by, a narrow applies_to, or an occasion.
  3. Non-duplication -- no existing practice already covers this by slug or
     substance.
  4. Budget -- a resident request must fit the 2,000-token cap.

Usage:
  precedent_promote.py --file CANDIDATE.md --level individual|team|universal
      [--against PATH[,PATH...]]   # repo roots whose practices/ to check for
                                    # duplication; defaults to the candidate's
                                    # own repo (individual/team) plus this repo
                                    # (universal) -- see default_against()
"""
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp  # noqa: E402
import build_views as bv  # noqa: E402
import precedent_candidate as pc  # noqa: E402

WORD_RE = re.compile(r"[a-z0-9]+")


class PromoteRefused(Exception):
    """Carries the criterion number and the reason -- the plan's own done-
    when line is "a candidate failing any of the four criteria is refused
    with a reason," so the refusal message IS the deliverable here, not an
    afterthought."""


def _load_candidate(path):
    text = pathlib.Path(path).read_text(encoding='utf-8')
    fm, body = pc._parse_frontmatter(text)
    _observed, proposed_rule = pc.split_candidate_sections(body)
    return fm, proposed_rule


def check_recurrence_or_cost(fm, candidate_path):
    """Criterion 1. Real recurrence is a COUNT OF FILES sharing this slug in
    the same candidates/ directory, not the hand-typed field alone -- a
    session raising the same candidate twice should not have to remember to
    bump a number in the first file (spec/CANDIDATE_FORMAT.md)."""
    slug = fm.get('slug')
    cand_dir = pathlib.Path(candidate_path).parent
    file_count = 1
    if cand_dir.is_dir():
        # Match on the parsed slug field, not a filename glob -- `foo-*.md`
        # also matches `foo-bar-2026-09-02.md`, which would inflate `foo`'s
        # recurrence count with an unrelated candidate that merely shares a
        # name prefix.
        file_count = 0
        for f in cand_dir.glob('*.md'):
            try:
                other_fm, _ = pc._parse_frontmatter(f.read_text(encoding='utf-8'))
            except (pc.CandidateError, OSError):
                continue
            if other_fm.get('slug') == slug:
                file_count += 1
        file_count = max(file_count, 1)
    declared = int(fm.get('recurrence_count') or 1)
    actual = max(file_count, declared)
    cost = fm.get('cost_if_once')
    if actual >= 2:
        return f"recurrence: {actual} candidate file(s) name {slug!r}"
    if cost:
        return f"one-time cost stated: {cost!r}"
    raise PromoteRefused(
        1, 'recurrence or real cost',
        f"{slug!r} has recurrence_count {declared} (actual file count "
        f"{file_count}) and no cost_if_once -- it happened once, without a "
        f"stated reason it was expensive. Raise it again if it recurs, or "
        f"add --cost-if-once when creating it.")


def check_reachability(fm):
    """Criterion 2. A candidate that could only ever be `applies_to: ['**']`
    with no occasion and no proposed check cannot become an on-demand
    practice (PRACTICE_ENGINE_PLAN.md, Stage 3) -- it either earns a
    resident slot (separately justified by the budget criterion) or stays a
    candidate. Whether a stated checked_by is REAL (registered, tested) is
    Stage 5's job, not this one -- a candidate is allowed to propose a check
    that does not exist yet as part of what promotion approves."""
    applies_to = fm.get('proposed_applies_to') or ['**']
    narrow_glob = applies_to != ['**']
    has_occasion = bool(fm.get('proposed_occasion'))
    has_checked_by = bool(fm.get('proposed_checked_by'))
    is_resident = fm.get('tier_requested') == 'resident'
    if has_checked_by or narrow_glob or has_occasion or is_resident:
        via = ('checked_by' if has_checked_by else
               'narrow applies_to' if narrow_glob else
               'occasion' if has_occasion else 'resident tier')
        return f"reachable via {via}"
    raise PromoteRefused(
        2, 'reachability',
        f"proposed_applies_to is the unrestricted {applies_to!r}, no "
        f"proposed_occasion, no proposed_checked_by, and tier_requested is "
        f"not resident -- nothing would ever surface this practice. Name a "
        f"glob, an occasion, a check, or request resident tier.")


def _catalogue_slugs_and_rules(against_paths):
    """-> {slug: (rule_text, source_path)} across every practices/ directory
    named in against_paths. Exact-slug collision is a hard refusal; this
    does NOT attempt semantic duplicate detection beyond a crude shared-word
    ratio, on purpose -- judging whether two Rules mean the same thing is
    exactly the "reasoning-quality practice with no mechanical signature"
    class spec/ATTENTION_CEILING.md's enforcement pass already declined to
    fake a check for (e.g. check-source-architecture). A near-duplicate is
    reported so a human decides; it does not refuse."""
    out = {}
    for p in against_paths:
        d = pathlib.Path(p) / 'practices'
        if not d.is_dir():
            continue
        for f in sorted(d.glob('*.md')):
            try:
                fm, sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            slug = fm.get('slug', f.stem)
            if fm.get('status') == 'retired':
                continue
            out[slug] = (sections.get('rule', ''), str(f))
    return out


def _word_set(text):
    return set(WORD_RE.findall(text.lower()))


def check_non_duplication(fm, proposed_rule, against_paths):
    """Criterion 3."""
    slug = fm.get('slug')
    catalogue = _catalogue_slugs_and_rules(against_paths)
    if slug in catalogue:
        rule_text, source = catalogue[slug]
        overrides = fm.get('overrides')
        if overrides != slug:
            raise PromoteRefused(
                3, 'non-duplication',
                f"slug {slug!r} already exists at {source} -- this is either "
                f"the same practice restated (the promotion signal, per "
                f"Stage 1's mechanical signals) or a real naming collision. "
                f"Pick a different slug, or if this is a deliberate override "
                f"of that practice at a higher-precedence level, land it "
                f"with `overrides: {slug}` and a slug of its own.")
    proposed_words = _word_set(proposed_rule)
    warnings = []
    if proposed_words:
        for other_slug, (rule_text, source) in catalogue.items():
            other_words = _word_set(rule_text)
            if not other_words:
                continue
            overlap = len(proposed_words & other_words) / len(proposed_words | other_words)
            if overlap > 0.5:
                warnings.append(
                    f"{overlap:.0%} word overlap with existing practice "
                    f"{other_slug!r} ({source}) -- not refused, a human "
                    f"should judge whether this duplicates it")
    checked = (f"checked {len(catalogue)} practice(s) across "
               f"{len(against_paths)} source(s): {', '.join(str(p) for p in against_paths)}")
    return checked if not warnings else checked + ' -- ' + '; '.join(warnings)


def check_budget(fm, against_paths):
    """Criterion 4. Only binds a resident request -- an on-demand candidate
    is zero-cost to this budget by construction."""
    if fm.get('tier_requested') != 'resident':
        return "not requesting resident tier -- budget does not apply"
    current_tokens = 0
    for p in against_paths:
        d = pathlib.Path(p) / 'practices'
        if not d.is_dir():
            continue
        for f in sorted(d.glob('*.md')):
            try:
                pfm, sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            if bv._json_str(pfm.get('tier', 'on-demand')) == 'resident':
                current_tokens += bv._approx_tokens(sections.get('rule', ''))
    proposed_tokens = bv._approx_tokens(fm.get('_proposed_rule_text', ''))
    total = current_tokens + proposed_tokens
    if total > bv.RESIDENT_BUDGET_TOKENS:
        raise PromoteRefused(
            4, 'budget',
            f"current resident tier is already ~{current_tokens} tokens; "
            f"adding this ~{proposed_tokens}-token Rule brings it to ~{total}, "
            f"over the {bv.RESIDENT_BUDGET_TOKENS}-token cap. Request "
            f"on-demand instead, or name a resident practice this displaces.")
    return f"resident budget: ~{current_tokens} current + ~{proposed_tokens} proposed = ~{total} of {bv.RESIDENT_BUDGET_TOKENS}"


def promote(candidate_path, level, against_paths):
    fm, proposed_rule = _load_candidate(candidate_path)
    fm['_proposed_rule_text'] = proposed_rule
    if fm.get('status') != 'open':
        raise PromoteRefused(
            0, 'status',
            f"candidate status is {fm.get('status')!r}, not 'open' -- only an "
            f"open candidate can be promoted")

    results = []
    results.append(('recurrence or real cost', check_recurrence_or_cost(fm, candidate_path)))
    results.append(('reachability', check_reachability(fm)))
    results.append(('non-duplication', check_non_duplication(fm, proposed_rule, against_paths)))
    results.append(('budget', check_budget(fm, against_paths)))

    # Stage 4's own instruction: "the session always proposes a level with a
    # reason, defaulting to the narrowest." This mirrors that default rather
    # than trusting the candidate's raiser to have picked correctly.
    guessed_level = level
    level_reason = f"raised at --level {level}; promotion does not second-guess the level a session already chose"

    return {
        'fm': fm,
        'proposed_rule': proposed_rule,
        'criteria': results,
        'guessed_level': guessed_level,
        'level_reason': level_reason,
    }


def default_against(candidate_path, level):
    """Derive a sensible non-duplication scope when --against is not given,
    instead of silently defaulting to universal (this repo) alone regardless
    of the candidate's own level -- deep-check finding: promoting a team or
    individual candidate with no explicit --against never checked it against
    that repo's own catalogue, only ROOT's. A candidate file always lives at
    <repo>/candidates/<slug>-<date>.md (spec/CANDIDATE_FORMAT.md), so the
    candidate's own repo is its parent's parent; always include universal
    too, since every level sits above it in precedence and could duplicate
    it. Universal candidates have no such repo to infer (they are Issues,
    not files under a fixed repo layout), so they check universal alone,
    same as before."""
    paths = [str(ROOT)]
    if level != 'universal':
        own_repo = str(pathlib.Path(candidate_path).resolve().parent.parent)
        if own_repo not in paths:
            paths.insert(0, own_repo)
    return paths


def _parse_args(argv):
    args = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith('--') or i + 1 >= len(argv):
            sys.exit(f"precedent_promote FAIL: expected --flag value pairs, stuck at {tok!r}")
        args[tok] = argv[i + 1]
        i += 2
    return args


def main():
    args = _parse_args(sys.argv[1:])
    candidate_path = args.get('--file')
    level = args.get('--level')
    if not candidate_path or level not in pc.LEVELS:
        sys.exit("precedent_promote FAIL: --file CANDIDATE.md and "
                  f"--level ({sorted(pc.LEVELS)}) are both required")
    against = (args['--against'].split(',') if args.get('--against')
               else default_against(candidate_path, level))

    try:
        result = promote(candidate_path, level, against)
    except PromoteRefused as e:
        n, name, reason = e.args
        print(f"REFUSED (criterion {n}: {name}): {reason}")
        return 1

    print(f"PROMOTED: {result['fm']['slug']} -- all four criteria pass")
    for name, detail in result['criteria']:
        print(f"  {name}: {detail}")
    print(f"  proposed level: {result['guessed_level']} ({result['level_reason']})")
    print()
    print("Drafted practice Rule (Stage 4 approval, then Stage 5 lands this):")
    print(f"  {result['proposed_rule']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
