#!/usr/bin/env python3
"""build_views.py — phase-2 generated views (PRACTICE_ENGINE_PLAN.md,
Sequence row 2: "make AGENTS.md, MAP.md, GLOSSARY.md and the index
generated"). Regenerates:

  - the loader block inside AGENTS.md, between the
    <!-- BEGIN GENERATED: precedent-loader --> / <!-- END GENERATED -->
    markers: the resident block (## Rule of every tier: resident practice),
    the occasion index (on-demand practices grouped by occasion), and the
    standing instruction. This is "the one generated file containing
    exactly three things" from "How an Agent Knows Which Practices to
    Load" -- AGENTS.md carries it because AGENTS.md is what a session
    already loads at start, rather than inventing a second file sessions
    would need to be told to also read.
  - MAP.md, in full (a generated file, not hand-authored).
  - GLOSSARY.md, in full, built from every practice's `defines:` field.

Hand-editing any of these three fails the check: rerun this script and diff
against the committed tree; any difference is a check failure (wired into
tools/verify_harness.py).

The resident block has a hard token ceiling (see RESIDENT_BUDGET_TOKENS
below, and PRACTICE_ENGINE_PLAN.md's "The Resident Budget" -- "target ~2,000
tokens, hard-capped"). Token count is approximated as words * 1.3 (no
tokenizer dependency; see practice 19, computed numbers live in scripts --
this IS that script, not a number restated by hand elsewhere). Exceeding the
cap fails the build outright: adding a resident practice must cost demoting
or retiring another, mechanically, not by discipline.

Run:
  python3 tools/build_views.py             # write AGENTS.md/MAP.md/GLOSSARY.md
  python3 tools/build_views.py --check      # regenerate to memory, diff against
                                             # the committed files, exit 1 on any diff
"""
import collections, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRACTICES_DIR = ROOT / 'practices'
AGENTS_MD = ROOT / 'AGENTS.md'
MAP_MD = ROOT / 'MAP.md'
GLOSSARY_MD = ROOT / 'GLOSSARY.md'

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp

BEGIN_MARKER = '<!-- BEGIN GENERATED: precedent-loader -->'
END_MARKER = '<!-- END GENERATED -->'

RESIDENT_BUDGET_TOKENS = 2000
WORD_RE = re.compile(r"\S+")


def _approx_tokens(text):
    return int(len(WORD_RE.findall(text)) * 1.3)


def load_practices():
    out = []
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        fm, sections = sp._read_practice_file(f)
        out.append((fm, sections, f))
    return out


def _json_list(raw):
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []


def _json_str(raw):
    """`occasion:` is a JSON string LITERAL in frontmatter, quotes and all,
    so it has to be decoded, not de-quoted. This was `raw.strip('"')`, which
    leaves the backslashes in an escaped occasion: the one practice whose
    occasion contains quotes rendered in the resident block every session
    reads as `When naming what \\"run the checks\\" means in a repo:`."""
    raw = (raw or '').strip()
    if raw.startswith('"'):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return raw.strip('"')


# A handful of practices carry a non-canonical rule-opening label kept as
# literal content by split_practices.py (e.g. "**The practice.**" -- see its
# _label_to_section: only the exact canonical words rule/why/install get
# stripped at split time, so a real authored label like this one stays in
# the Rule text on purpose, since the plan's no-invented-content rule means
# split_practices.py cannot silently drop or reword it). Fine when the full
# Rule is loaded via precedent_show, but it adds no information in a
# one-line index entry -- stripped here for DISPLAY ONLY, in this generated
# summary line; the underlying practice file and everything precedent_show
# and precedent_paths return is untouched.
_GENERIC_RULE_LABEL_RE = re.compile(r'^\*\*(?:The practice)\.?\*\*\s*')
_SENTENCE_END_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9(\[])')


INDEX_CLAUSE_MAX = 80


def _index_clause(fm, sections):
    """The one-line routing entry a session actually decides on.

    This used to be derived: the first sentence of the Rule, truncated at 90
    characters. 86% of the 46 entries came out cut off mid-thought, and one
    ended on a dangling colon -- a routing table whose rows do not finish
    their sentence. The plan's own worked example is not a derived first
    sentence at all, it is a written clause:

        document-references-are-links — references are links; ≈ not ~
        trim-prose                    — trim after any substantial edit

    So the clause is authored, in `index_clause:`, and verify_harness.py
    requires one on every on-demand practice. This is metadata for a
    generated view, not practice text: the no-invented-content rule governs
    Rule/Why/Story/Install, which this never touches. Derivation stays as a
    fallback so a newly added practice renders before its clause is written,
    rather than silently rendering nothing."""
    written = _json_str(fm.get('index_clause', ''))
    if written:
        return written
    return _occasion_clause(sections.get('rule', ''))


def _occasion_clause(rule_text, max_len=90):
    """First sentence of a practice's Rule, collapsed to one line, for the
    occasion index. Joins the whole first paragraph (not just its first
    *wrapped* line -- markdown files wrap prose at ~80 columns, so a rule
    text's first physical line is very often mid-sentence) before looking
    for a sentence boundary."""
    first_para = rule_text.strip().split('\n\n', 1)[0]
    first_para = ' '.join(first_para.split())  # collapse internal line wraps
    first_para = _GENERIC_RULE_LABEL_RE.sub('', first_para)
    clause = _SENTENCE_END_RE.split(first_para, maxsplit=1)[0]
    if len(clause) > max_len:
        clause = clause[:max_len - 3].rstrip() + '...'
    return clause


def build_loader_block(practices):
    resident = [(fm, sections) for fm, sections, _f in practices if fm.get('tier') == 'resident']
    resident.sort(key=lambda t: t[0]['slug'])

    resident_text = '\n\n'.join(
        f"**{fm['slug']}.** {sections.get('rule', '').strip()}" for fm, sections in resident
    )
    token_count = _approx_tokens(resident_text)
    if token_count > RESIDENT_BUDGET_TOKENS:
        sys.exit(f"build_views FAIL: resident block is ~{token_count} tokens, "
                 f"over the {RESIDENT_BUDGET_TOKENS}-token hard cap -- demote or "
                 f"retire a resident practice before adding another.")

    on_demand = [(fm, sections) for fm, sections, _f in practices if fm.get('tier') == 'on-demand']
    by_occasion = collections.defaultdict(list)
    for fm, sections in on_demand:
        occasion = _json_str(fm.get('occasion', ''))
        if not occasion:
            continue
        by_occasion[occasion].append((fm['slug'], _index_clause(fm, sections)))

    index_lines = []
    for occasion in sorted(by_occasion):
        index_lines.append(f"When {occasion}:")
        for slug, clause in sorted(by_occasion[occasion]):
            index_lines.append(f"  {slug} — {clause}")
    index_text = '\n'.join(index_lines)

    lines = [BEGIN_MARKER, '']
    lines.append(f"<!-- Regenerate with: python3 tools/build_views.py -- do not hand-edit "
                 f"this block, tools/verify_harness.py's regeneration check fails on drift. -->")
    lines.append('')
    lines.append(f"### Resident block (~{token_count} of {RESIDENT_BUDGET_TOKENS} token budget, "
                 f"{len(resident)} of {len(practices)} practices)")
    lines.append('')
    lines.append(resident_text)
    lines.append('')
    lines.append("### Occasion index")
    lines.append('')
    lines.append("```")
    lines.append(index_text)
    lines.append("```")
    lines.append('')
    lines.append("### Standing instruction")
    lines.append('')
    lines.append("Before starting work of a kind named in the occasion index above, run "
                 "`python3 tools/precedent_show.py SLUG` for each listed slug to load its "
                 "Rule. When editing a file, `python3 tools/precedent_paths.py FILE` prints "
                 "any on-demand practice whose `applies_to` matches it, without needing the "
                 "index at all.")
    lines.append('')
    lines.append(END_MARKER)
    return '\n'.join(lines), token_count, len(resident)


def render_agents_md(practices):
    original = AGENTS_MD.read_text(encoding='utf-8')
    block, _tokens, _n = build_loader_block(practices)
    if BEGIN_MARKER not in original or END_MARKER not in original:
        sys.exit("build_views FAIL: AGENTS.md has no "
                 f"{BEGIN_MARKER} / {END_MARKER} markers to regenerate between.")
    pre = original[:original.index(BEGIN_MARKER)]
    post = original[original.index(END_MARKER) + len(END_MARKER):]
    return pre + block + post


def render_map_md(practices):
    by_tier = collections.Counter(fm.get('tier') for fm, _s, _f in practices)
    lines = [
        "<!-- GENERATED by tools/build_views.py -- do not hand-edit. Regenerate with "
        "`python3 tools/build_views.py`; tools/verify_harness.py fails the build if this "
        "file drifts from a fresh regeneration. -->",
        '',
        "# Repository map — where to find things",
        '',
        "Precedent's own repo map (PRACTICE_ENGINE_PLAN.md, Sequence row 2: "
        '"make AGENTS.md, MAP.md, GLOSSARY.md and the index generated"). '
        "For the plan and format spec, see AGENTS.md's quick index instead — this file "
        "indexes the practice catalogue and the engine's own code, not the whole repo's prose.",
        '',
        "## The practice catalogue",
        '',
        f"`practices/` holds {len(practices)} practice files "
        f"({by_tier.get('resident', 0)} resident, {by_tier.get('on-demand', 0)} on-demand). "
        "One file per practice; see [spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) for "
        "the format and [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md) for the design.",
        '',
        "| Practice | Tier | Occasion / scope |",
        "|---|---|---|",
    ]
    for fm, _sections, _f in sorted(practices, key=lambda t: t[0]['slug']):
        occasion = _json_str(fm.get('occasion', '""'))
        applies_to = _json_list(fm.get('applies_to', '[]'))
        scope = occasion if occasion else ', '.join(applies_to)
        lines.append(f"| [{fm['slug']}](practices/{fm['slug']}.md) | {fm.get('tier')} | {scope} |")
    lines += [
        '',
        "## The engine",
        '',
        "| Path | What it is |",
        "|---|---|",
        "| [tools/split_practices.py](tools/split_practices.py) | [PRACTICES.md](PRACTICES.md) ↔ [practices/](practices/) converter |",
        "| [tools/precedent_show.py](tools/precedent_show.py) | Load a practice's Rule/Why/Story/Install — the one code path that reads a practice file |",
        "| [tools/precedent_paths.py](tools/precedent_paths.py) | Path-triggered channel — matches a touched file against every practice's `applies_to` |",
        "| [tools/build_views.py](tools/build_views.py) | This file, [GLOSSARY.md](GLOSSARY.md), and AGENTS.md's loader block — generated views |",
        "| [tools/resplit_sections.py](tools/resplit_sections.py) | The phase-1.5 editorial Rule/Why/Story split, applied from [tools/section_split.json](tools/section_split.json) |",
        "| [tools/behavioral_replay.py](tools/behavioral_replay.py) | Measures the loader against this repo's own commit history |",
        "| [tools/verify_harness.py](tools/verify_harness.py) | The verification harness — run before trusting any change here |",
        '',
    ]
    return '\n'.join(lines) + '\n'


def render_glossary_md(practices):
    terms = []
    for fm, _sections, _f in practices:
        raw = fm.get('defines', '[]')
        for term in _json_list(raw):
            terms.append((term, fm['slug']))
    terms.sort(key=lambda t: t[0].lower())
    lines = [
        "<!-- GENERATED by tools/build_views.py -- do not hand-edit. Regenerate with "
        "`python3 tools/build_views.py`; tools/verify_harness.py fails the build if this "
        "file drifts from a fresh regeneration. -->",
        '',
        "# Canonical names",
        '',
        "Built from every practice's `defines:` frontmatter field -- the terms that "
        "practice owns (PRACTICE_ENGINE_PLAN.md, The Practice File). A term with no row "
        "here yet is simply a practice that hasn't had its `defines:` filled in; this is "
        "not the exhaustive vocabulary of the repo (that's the plan's own Vocabulary "
        "table), only what the practice catalogue itself has claimed so far.",
        '',
        "| Term | Defined in |",
        "|---|---|",
    ]
    if not terms:
        lines.append("| *(none yet)* | — |")
    else:
        for term, slug in terms:
            lines.append(f"| {term} | [{slug}](practices/{slug}.md) |")
    lines.append('')
    return '\n'.join(lines)


def main():
    check = '--check' in sys.argv
    practices = load_practices()

    new_agents = render_agents_md(practices)
    new_map = render_map_md(practices)
    new_glossary = render_glossary_md(practices)

    targets = [(AGENTS_MD, new_agents), (MAP_MD, new_map), (GLOSSARY_MD, new_glossary)]

    if check:
        drift = []
        for path, new_text in targets:
            old_text = path.read_text(encoding='utf-8') if path.exists() else None
            if old_text != new_text:
                drift.append(path.name)
        if drift:
            print(f"build_views --check FAIL: hand-edited or stale, drifted from "
                  f"regeneration: {', '.join(drift)}")
            return 1
        print("build_views --check OK: AGENTS.md, MAP.md, GLOSSARY.md all byte-identical "
              "to a fresh regeneration")
        return 0

    for path, new_text in targets:
        path.write_text(new_text, encoding='utf-8')
    _block, tokens, n_resident = build_loader_block(practices)
    print(f"build_views OK: wrote AGENTS.md (loader block regenerated, resident "
          f"{n_resident}/{len(practices)} practices, ~{tokens} tokens), MAP.md, GLOSSARY.md")
    return 0


if __name__ == '__main__':
    sys.exit(main())
