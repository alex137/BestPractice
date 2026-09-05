#!/usr/bin/env python3
"""catalogue_stats.py — the figures about this catalogue that documents cite.

Every number here was, until phase 4, hand-typed into prose in several
documents at once. That is the failure `docs-track-models` describes, and it
had already happened: [spec/LOADER.md](../spec/LOADER.md)'s status table said
the resident block was "~621 tokens" for the whole of phase 3, while phase
3's own Rule/Detail split had halved it to ≈312. Every gate in the repository
was green, because no gate could see a number in a sentence.

So the numbers live here, the documents carry a generated block, and
tools/doc_sync.py fails on drift. The figures this script DECLARES IT OWNS
(owned_figures()) may not be restated in the prose around that block --
a restatement is a second copy with no gate on it.

  python3 tools/catalogue_stats.py                 # human-readable
  python3 tools/catalogue_stats.py --emit catalogue  # the generated block
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import build_views as bv


def _load():
    out = []
    for f in sorted((ROOT / 'practices').glob('*.md')):
        fm, sections = sp._read_practice_file(f)
        out.append((fm, sections, f))
    return out


def phase3_snapshot_stats():
    """The catalogue as phase 3 left it: BestPractice's original 52
    practices only (source_practice_number 1-52), excluding anything added
    since -- a practice minted fresh in Precedent, or a later BestPractice
    practice converted afterwards (see CHANGES_TO_TELL_ALEX.md). The two
    phase-3 ANCHORS below are a dated point-in-time record ("the catalogue
    as this session inherited it"), not a live invariant, and computing them
    over the growing practices/ directory would fail every anchor the first
    time anything was added after phase 3 -- which is exactly what happened
    the first time a practice was."""
    practices = [(fm, s, f) for fm, s, f in _load()
                 if (fm.get('source_practice_number') or '').isdigit()
                 and 1 <= int(fm['source_practice_number']) <= 52]
    return {
        'long_rules': sum(1 for _fm, s, _f in practices
                          if len(s.get('rule', '').split()) > 150),
        'with_detail': sum(1 for _fm, s, _f in practices if s.get('detail', '').strip()),
    }


def stats():
    practices = _load()
    resident = [p for p in practices if p[0].get('tier') == 'resident']
    resident_text = '\n\n'.join(
        f"**{fm['slug']}.** {sections.get('rule', '').strip()}"
        for fm, sections, _f in sorted(resident, key=lambda t: t[0]['slug']))
    order = ('rule', 'detail', 'why', 'story', 'install')
    words = {k: 0 for k in order}
    for _fm, sections, _f in practices:
        for k in order:
            words[k] += len(sections.get(k, '').split())
    total = sum(words.values()) or 1
    return {
        'practices': len(practices),
        'resident': len(resident),
        'resident_tokens': bv._approx_tokens(resident_text),
        'budget': bv.RESIDENT_BUDGET_TOKENS,
        'rule_share': round(100 * words['rule'] / total),
        'long_rules': sum(1 for _fm, s, _f in practices
                          if len(s.get('rule', '').split()) > 150),
        'with_detail': sum(1 for _fm, s, _f in practices if s.get('detail', '').strip()),
        'with_story': sum(1 for _fm, s, _f in practices if s.get('story', '').strip()),
        'enforced': sum(1 for fm, _s, _f in practices
                        if (fm.get('checked_by') or 'null').strip('"') != 'null'),
    }


# ---- the figures this script owns; nothing may restate them by hand -------
def owned_figures(_script=None):
    s = stats()
    return [
        ('resident block size', [f"≈{s['resident_tokens']} tokens",
                                 f"~{s['resident_tokens']} tokens"]),
        ('resident set', [f"{s['resident']} of {s['practices']} practices"]),
        ('enforced coverage', [f"{s['enforced']} of {s['practices']} practices carry"]),
        ('Rule share', [f"{s['rule_share']}% of the catalogue"]),
    ]


def self_check():
    """Invariants, not values -- a value comparison cannot catch a correct
    input transformed by a wrong law."""
    s = stats()
    out = []
    if not 0 < s['resident'] <= s['practices']:
        out.append(f"resident set ({s['resident']}) is not a non-empty subset "
                   f"of the catalogue ({s['practices']})")
    if s['resident_tokens'] > s['budget']:
        out.append(f"resident block {s['resident_tokens']} tokens exceeds the "
                   f"{s['budget']}-token hard cap, which build_views.py is "
                   f"supposed to make impossible")
    for k in ('long_rules', 'with_detail', 'with_story', 'enforced'):
        if not 0 <= s[k] <= s['practices']:
            out.append(f"{k} = {s[k]} is outside 0..{s['practices']}")
    if not 0 < s['rule_share'] < 100:
        out.append(f"Rule share {s['rule_share']}% is not a share")
    return out


ANCHORS = [
    # The plan states the resident target as a figure of record. This script
    # re-derives the cap from build_views.py, so the two can disagree.
    ('PRACTICE_ENGINE_PLAN.md, "The resident block ... Target ~2,000 tokens"',
     2000, 2000, lambda: (stats()['budget'], stats()['budget'])),
    # spec/PRACTICE_FORMAT.md's phase-3 column records the catalogue as this
    # session inherited it: originally 15 practices with a Detail, 8 Rules
    # over 150 words. Scoped to the original 52 (phase3_snapshot_stats), not
    # the live directory -- a dated snapshot, not an invariant that should
    # fail every time a later practice is added -- but a DELIBERATE rewrite
    # of an original-52 practice still moves it, same as the 8->7 Rules-over-
    # 150-words correction below: moved 15->16 on 2026-09-05 when
    # session-bootstrap gained a real Detail (see CHANGES_TO_TELL_ALEX.md).
    # See phase3_snapshot_stats's docstring.
    ('spec/PRACTICE_FORMAT.md, "The Rule/Detail Split" — practices with a Detail',
     16, 16, lambda: (phase3_snapshot_stats()['with_detail'], phase3_snapshot_stats()['with_detail'])),
    ('spec/PRACTICE_FORMAT.md, "The Rule/Detail Split" — Rules over 150 words',
     7, 7, lambda: (phase3_snapshot_stats()['long_rules'], phase3_snapshot_stats()['long_rules'])),
    # PRACTICE_ENGINE_PLAN.md's own phase-3 table restates the SAME figure as
    # the anchor above -- found stale (still "8", the pre-correction value)
    # by a 2026-09-01 deep-check audit, on the very day spec/PRACTICE_FORMAT.md
    # was corrected to 7 with an explicit note about the correction. Nothing
    # caught the plan's own copy because this whole anchor mechanism was never
    # wired into verify_harness.py -- see check_catalogue_anchors there.
    ('PRACTICE_ENGINE_PLAN.md, "The ## Detail split, and the three practices '
     'that refused it" — Rules over 150 words',
     7, 7, lambda: (phase3_snapshot_stats()['long_rules'], phase3_snapshot_stats()['long_rules'])),
]


def check_anchors():
    passes, failures = [], []
    for label, lo, hi, fn in ANCHORS:
        got_lo, got_hi = fn()
        if got_hi < lo or got_lo > hi:
            failures.append(f"{label}: recites {lo}..{hi}, this script derives "
                            f"{got_lo}..{got_hi}")
        else:
            passes.append(f"{label}: {got_lo}..{got_hi} overlaps {lo}..{hi}")
    return passes, failures


def block():
    s = stats()
    rows = [
        ('Practices in the catalogue', f"{s['practices']}"),
        ('Resident, loaded every session',
         f"{s['resident']} of {s['practices']} practices"),
        ('Resident block size',
         f"≈{s['resident_tokens']} tokens of a {s['budget']}-token hard cap"),
        ('`## Rule` share of the catalogue', f"{s['rule_share']}% of the catalogue"),
        ('Rules still over 150 words', f"{s['long_rules']}"),
        ('Carrying a `## Detail`', f"{s['with_detail']}"),
        ('Carrying a `## Story`', f"{s['with_story']}"),
        ('Enforced by a check',
         f"{s['enforced']} of {s['practices']} practices carry a `checked_by`"),
    ]
    out = ['| | |', '|---|---|']
    out += [f'| {k} | {v} |' for k, v in rows]
    return '\n'.join(out)


def enforcement_block():
    """The enforced-practice registry, rendered from the registry itself, so
    a document listing what is enforced cannot drift from what is.

    tools/precedent_check.py's CHECKS registry is shared infrastructure --
    it also carries checks for practices/ that live outside the universal
    catalogue (repo-local, under local/practices/, e.g.
    merge-target-is-beta-branch). This document is universal Precedent
    documentation, read by every consumer, so it lists and counts only
    checks whose slug names one of the universal practices/*.md files --
    a repo-local check appearing here would misrepresent a BestPractice-only
    rule as part of the catalogue every Precedent user gets."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_pc', ROOT / 'tools' / 'precedent_check.py')
    pc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pc)
    universal_slugs = {fm['slug'] for fm, _sections, _f in _load()}
    universal_checks = {slug: c for slug, c in pc.CHECKS.items()
                        if slug in universal_slugs}
    s = stats()
    out = ['| practice | scope | what the check asserts |', '|---|---|---|']
    for slug, c in sorted(universal_checks.items()):
        out.append(f"| `{slug}` | {c['scope']} | {c['what']} |")
    out.append('')
    out.append(f"{len(universal_checks)} of {s['practices']} practices are "
               f"enforced. Run `python3 tools/precedent_check.py --explain` "
               f"for what each check does **not** catch.")
    return '\n'.join(out)


BLOCKS = {'catalogue': lambda: block(), 'enforcement': enforcement_block}


def main():
    args = sys.argv[1:]
    if '--emit' in args:
        name = args[args.index('--emit') + 1]
        if name not in BLOCKS:
            sys.exit(f"catalogue_stats FAIL: no block named {name!r} "
                     f"(known blocks: {', '.join(sorted(BLOCKS))}).")
        print(BLOCKS[name]())
        return 0
    print(block())
    fails = self_check()
    passes, anchor_fails = check_anchors()
    for p in passes:
        print(f"  anchor ok  {p}")
    for f in fails + anchor_fails:
        print(f"  FAIL  {f}")
    return 1 if (fails or anchor_fails) else 0


if __name__ == '__main__':
    sys.exit(main())
