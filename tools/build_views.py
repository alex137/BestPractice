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
tokenizer dependency; see (practice: computed-numbers-in-scripts), computed
numbers live in scripts -- this IS that script, not a number restated by
hand elsewhere). Exceeding the
cap fails the build outright: adding a resident practice must cost demoting
or retiring another, mechanically, not by discipline.

Run:
  python3 tools/build_views.py             # write AGENTS.md/MAP.md/GLOSSARY.md
  python3 tools/build_views.py --check      # regenerate to memory, diff against
                                             # the committed files, exit 1 on any diff
  python3 tools/build_views.py --agents-only [--check]
      # write (or check) only AGENTS.md's loader block. MAP.md and
      # GLOSSARY.md's content is specific to how THIS repo is laid out
      # (render_map_md()'s TOOLS_DESCRIPTIONS table, its "this repo is
      # BestPractice itself" prose); a team or individual source repo
      # vendoring this same file for its own practices/ catalogue wants
      # the resident-block/occasion-index mechanism, not those two.
  python3 tools/build_views.py --repo DIR [--agents-only] [--check]
      # operate on DIR's practices/AGENTS.md/MAP.md/GLOSSARY.md instead of
      # this repo's own -- --repo defaults to this script's own parent
      # directory when omitted. The "## The engine" table inside MAP.md
      # still always lists the tools sitting beside THIS SCRIPT, regardless
      # of --repo: that table describes the engine's own code inventory,
      # not the target repo's content, the same "sibling files travel with
      # the script, not with --repo" rule sibling-module imports follow.
"""
import collections, json, pathlib, re, sys

# _ENGINE_DIR (where this file itself lives) is only ever used for the
# sibling-module import and the MAP.md "## The engine" listing below --
# both describe the engine's own code, which travels with wherever this
# script physically is, never with --repo. ROOT is which repo's CONTENT
# (practices/, AGENTS.md, MAP.md, GLOSSARY.md) to read and (re)generate; it
# defaults to the engine's own parent directory but is overridable with
# --repo in main() -- see precedent_show.py for the fuller rationale, and
# precedent_sync_views.py's own docstring for the trap this avoids
# (computing ROOT from `__file__` alone breaks the moment this script is
# relocated or vendored somewhere other than <repo>/tools/whatever.py).
_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = _ENGINE_DIR.parent  # unchanged default when --repo is omitted
PRACTICES_DIR = ROOT / 'practices'
AGENTS_MD = ROOT / 'AGENTS.md'
MAP_MD = ROOT / 'MAP.md'
GLOSSARY_MD = ROOT / 'GLOSSARY.md'

sys.path.insert(0, str(_ENGINE_DIR))
import split_practices as sp

BEGIN_MARKER = '<!-- BEGIN GENERATED: precedent-loader -->'
END_MARKER = '<!-- END GENERATED -->'

RESIDENT_BUDGET_TOKENS = 2000
WORD_RE = re.compile(r"\S+")


def _approx_tokens(text):
    return int(len(WORD_RE.findall(text)) * 1.3)


# A practice that is not active is still resolvable BY SLUG -- so a
# `supersedes:` reference points somewhere real -- but it is not in force, and
# nothing that presents the catalogue as current may show it. Defined here,
# in the lower-level module, and imported by precedent_resolve as
# bv.IN_FORCE_STATUS, so the loader and the resolver cannot disagree about
# what "in force" means. (precedent_resolve imports this module, never the
# other way round -- putting the constant there would be a cycle.)
IN_FORCE_STATUS = 'active'

# THE TWO WAYS A PRACTICE STOPS APPLYING HERE ARE NOT THE SAME THING, and
# collapsing them into one word is what let a live rule be dropped
# (2026-09-06; see spec/PRACTICE_FORMAT.md "Status" and this repo's
# practices/mistakes-become-rules.md).
#
#   deduplicated  The COPY here is redundant. The rule itself is fully in
#                 force, from somewhere else -- another source's practice,
#                 or the engine. `in_force_at:` says where, and the check
#                 resolves it. This is the common, cheap, verifiable path.
#   retired       Nobody wants this rule anywhere. `in_force_at: none`,
#                 plus a Story line saying why. Rare and deliberate.
#
# The distinction exists because "retire" invites the question "does
# something similar exist?", which is answerable by reading two files and
# feeling that they rhyme -- and that is exactly how a routine check was
# dropped on the authority of an unrelated occasional one. "Deduplicate"
# cannot be answered by resemblance: it forces the only question that
# matters, which is what the surviving copy is and whether it resolves in
# force.
DEDUPLICATED_STATUS = 'deduplicated'
RETIRED_STATUS = 'retired'

# Every status this engine recognizes. A practice carrying anything else is
# a typo or a newer engine's vocabulary, and is reported rather than
# silently treated as one of these (see verify_harness.py's
# check_status_contract) -- but it is still NOT IN FORCE, because
# `is_in_force` tests for `active` rather than testing against this list.
# Failing closed is the only safe direction: a status nobody here
# understands must never be loaded as if it were current.
KNOWN_STATUSES = (IN_FORCE_STATUS, DEDUPLICATED_STATUS, RETIRED_STATUS)


def practice_status(fm):
    """A practice's declared status, decoded, defaulting to in-force.

    `status:` is written unquoted in every practice file this repo has, but
    it is a frontmatter string like any other and a hand-authored one may
    arrive quoted -- so it goes through _json_str rather than being read
    raw. Two tools used to compare `fm.get('status') == 'retired'` directly
    and would have missed both a quoted value and, once this vocabulary
    landed, every `deduplicated` practice."""
    return _json_str(fm.get('status', IN_FORCE_STATUS)) or IN_FORCE_STATUS


def is_in_force(fm):
    """Whether this practice's rule applies here, now.

    The one predicate every loading channel must use. It is deliberately
    `== IN_FORCE_STATUS` and not `not in (DEDUPLICATED_STATUS,
    RETIRED_STATUS)`: an unrecognized status fails closed."""
    return practice_status(fm) == IN_FORCE_STATUS


# `in_force_at:` takes a slug, or one of these two literals.
IN_FORCE_AT_ENGINE = 'engine'    # absorbed into the mechanism; no practice to load
IN_FORCE_AT_NOWHERE = 'none'     # in force nowhere -- the retirement case


def status_contract_violation(fm, sections=None, slug_in_force=None):
    """-> a message naming what is wrong with this practice's `status:` /
    `in_force_at:` pair, or None when the pair is sound.

    WHY THE PAIR IS CHECKED AND NOT JUST THE STATUS. `status:` alone records
    that a rule stopped applying here but never whether anything replaced it,
    so "deduplicated safely" and "dropped and forgotten" were indistinguishable
    to every check in the system -- the forwarding address existed only as
    English prose in `## Story`, which no tool reads. That is the gap a live
    rule fell through on 2026-09-06.

    `slug_in_force` is a callable (slug) -> bool, INJECTED rather than
    imported. The real answer comes from precedent_resolve.resolve() against
    the actually-declared sources, and precedent_resolve imports this module,
    so reaching for it here would be a cycle. Passing None checks the SHAPE
    only -- that a forwarding address is present and well-formed -- and
    deliberately does not check that it resolves, which is the entire point
    of the field. A caller that can resolve must pass the callable; one that
    cannot must say so rather than reporting a shape check as the real one."""
    status = practice_status(fm)
    target = _json_str(fm.get('in_force_at', '')) or ''

    if status not in KNOWN_STATUSES:
        return (f"status: {status!r} is not a status this engine knows "
                f"({', '.join(KNOWN_STATUSES)}). It is treated as not in "
                f"force, which may not be what was meant.")

    if status == IN_FORCE_STATUS:
        if target:
            return (f"status: active carries in_force_at: {target!r}. A rule "
                    f"in force HERE has no forwarding address; one of the two "
                    f"is wrong.")
        return None

    if not target:
        return (f"status: {status} with no in_force_at:. Not optional on "
                f"anything that is not active -- it is what tells a "
                f"deduplication apart from a rule dropped and forgotten.")

    if status == DEDUPLICATED_STATUS:
        if target == IN_FORCE_AT_NOWHERE:
            return (f"status: deduplicated with in_force_at: none. "
                    f"Deduplicated means the rule IS in force, elsewhere; if "
                    f"it is in force nowhere, that is status: retired, and "
                    f"needs the evidence retirement needs.")
        if target == IN_FORCE_AT_ENGINE:
            return None
        if slug_in_force is None:
            return None          # shape is sound; resolution not checked here
        if not slug_in_force(target):
            return (f"status: deduplicated names in_force_at: {target!r}, but "
                    f"that slug does not resolve IN FORCE against the declared "
                    f"sources. A surviving copy that is itself dropped, "
                    f"shadowed or unreachable is not a surviving copy -- this "
                    f"is the deduplication that silently loses a rule.")
        return None

    # status == RETIRED_STATUS
    if target != IN_FORCE_AT_NOWHERE:
        return (f"status: retired with in_force_at: {target!r}. Retired means "
                f"the rule is wanted nowhere, so the only legal value is "
                f"'none'. If the rule survives at {target!r}, this is "
                f"status: deduplicated.")
    story = (sections or {}).get('story', '').strip()
    if not story:
        return ("status: retired with an empty ## Story. Retirement is the "
                "rare, deliberate case and is the one status no mechanism can "
                "verify for you, so it must say in prose why nobody wants "
                "this rule anywhere.")
    return None


def load_practices(practices_dir=None, in_force_only=True):
    """Every practice file in the directory, minus the ones not in force.

    WHY THE FILTER EXISTS (2026-09-06). This function read every *.md and
    returned it, and this module never looked at `status:` anywhere -- so a
    retired practice went on being emitted into the AGENTS.md loader block,
    MAP.md and GLOSSARY.md exactly like an active one. Retirement was
    cosmetic for the one channel that decides what a session actually loads.

    Invisible in BestPractice, whose own catalogue has no retired practice.
    Found 2026-09-06 in a private team set with three of them -- all three
    were listed in the AGENTS.md its own README calls "what a session
    actually loads", months after retirement, including one retired that
    same day. precedent_resolve.py had this right all along and prints
    `not in force: <slug> ... is status: retired`; the generated views did
    not, so the two channels disagreed and only the quieter one was read.

    A dropped practice is announced rather than silently skipped -- a
    retirement that vanishes without a word is the same silence in a
    smaller place."""
    practices_dir = practices_dir if practices_dir is not None else PRACTICES_DIR
    out, dropped = [], []
    for f in sorted(practices_dir.glob('*.md')):
        fm, sections = sp._read_practice_file(f)
        status = practice_status(fm)
        if in_force_only and not is_in_force(fm):
            dropped.append((fm.get('slug', f.stem), status))
            continue
        out.append((fm, sections, f))
    for slug, status in dropped:
        print(f"build_views: {slug} is status: {status}, so it is not in "
              f"force and is left out of the generated views.", file=sys.stderr)
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


def build_loader_block(practices, source_levels=None):
    """practices: (fm, sections, file) triples, exactly as load_practices()
    returns for this repo's own single-source catalogue. source_levels:
    optional {slug: level} for a caller resolving MULTIPLE sources (e.g.
    tools/precedent_materialize.py's output, walked by a consuming repo's
    own precedent_sync_views.py) -- purely cosmetic, breaking the header's
    practice count out by level, so the generated block discloses
    provenance at a glance rather than only in MANIFEST.json. Omitting it
    (the default) renders byte-identical to before this parameter existed,
    which is what keeps this repo's own single-source generation unchanged."""
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
    count_detail = f"{len(resident)} of {len(practices)} practices"
    if source_levels and resident:
        # Levels of the RESIDENT set specifically (not all `practices`) --
        # this sits right after "X of Y practices", so a reader's natural
        # reading is "the breakdown of X", not of the larger Y. Breaking
        # down Y instead once rendered "1 of 4 practices (1 individual, 1
        # repo-local, 1 team, 1 universal)" for a fixture with exactly ONE
        # resident practice -- readable as four resident practices, one per
        # level, which was never true.
        by_level = collections.Counter(source_levels.get(fm['slug'], '?')
                                        for fm, _s in resident)
        count_detail += ' (' + ', '.join(f"{by_level[l]} {l}" for l in
                                          sorted(by_level) if by_level[l]) + ')'
    lines.append(f"## Resident block (~{token_count} of {RESIDENT_BUDGET_TOKENS} token budget, "
                 f"{count_detail})")
    lines.append('')
    lines.append(resident_text)
    lines.append('')
    lines.append("## Occasion index")
    lines.append('')
    lines.append("```")
    lines.append(index_text)
    lines.append("```")
    lines.append('')
    lines.append("## Standing instruction")
    lines.append('')
    lines.append("Before starting work of a kind named in the occasion index above, run "
                 "`python3 tools/precedent_show.py SLUG` for each listed slug to load its "
                 "Rule. When editing a file, `python3 tools/precedent_paths.py FILE` prints "
                 "any on-demand practice whose `applies_to` matches it, without needing the "
                 "index at all. At a named moment — merging, reviewing, pushing, ending a "
                 "turn — run `python3 tools/precedent_gate.py merge|review|push|reply`: "
                 "some practices fire at a moment rather than in a file, and no path glob "
                 "reaches those.")
    lines.append('')
    lines.append(END_MARKER)
    return '\n'.join(lines), token_count, len(resident)


def source_levels_from_manifest(root):
    """{slug: level} read back out of a consuming repo's MANIFEST.json, or
    None where there is no such file.

    WHY THIS EXISTS. precedent_sync_views.py renders the loader block with
    `source_levels=` (it has the resolution in hand), and this tool's own
    main() rendered it WITHOUT -- so the two wrote different header lines
    for the same catalogue ("6 of 61 practices (6 universal)" vs "6 of 61
    practices"). In a consuming repo, where both are documented commands,
    that is a permanent unresolvable flip-flop: session start runs
    precedent_sync_views.py, then `build_views.py --check` -- which
    generated-artifact-provenance runs on every precedent_check.py --
    reports the block as hand-edited or stale, forever, whichever ran
    last. MANIFEST.json is precedent_materialize.py's own record of which
    source produced each practice, so reading it here makes the two
    renderers agree by construction rather than by both remembering to
    pass the same argument. Absent in a single-source repo (Precedent
    itself), where there are no levels to break down and the header is
    unchanged."""
    manifest = root / 'MANIFEST.json'
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None
    levels = {e['slug']: e['level'] for e in data.get('practices', [])
              if 'slug' in e and 'level' in e}
    return levels or None


def render_agents_md(practices, agents_md=None, source_levels=None):
    agents_md = agents_md if agents_md is not None else AGENTS_MD
    original = agents_md.read_text(encoding='utf-8')
    block, _tokens, _n = build_loader_block(practices, source_levels=source_levels)
    if BEGIN_MARKER not in original or END_MARKER not in original:
        sys.exit(f"build_views FAIL: {agents_md} has no "
                 f"{BEGIN_MARKER} / {END_MARKER} markers to regenerate between.")
    pre = original[:original.index(BEGIN_MARKER)]
    post = original[original.index(END_MARKER) + len(END_MARKER):]
    return pre + block + post



def _upstream_doc_pointer():
    """The " see X for the format and Y for the design" tail of MAP.md's
    catalogue line -- only when those documents actually exist here.

    This ran unconditionally and named two of BestPractice's OWN documents,
    which no vendoree has. Nothing noticed while only BestPractice generated
    a MAP.md; the moment an engine refresh brought this generator to three
    practice sets (2026-09-06), each one generated a map with two broken
    relative links, and each one's own light check reported them -- findings
    against a file the repo did not write, naming files it is not supposed
    to have. A generator shared across repositories cannot assume the
    generating repo's own prose."""
    tail = []
    if (ROOT / 'spec' / 'PRACTICE_FORMAT.md').is_file():
        tail.append("[spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) for the format")
    if (ROOT / 'PRACTICE_ENGINE_PLAN.md').is_file():
        tail.append("[PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md) for the design")
    return (" See " + " and ".join(tail) + ".") if tail else ""


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
        "One file per practice." + _upstream_doc_pointer(),
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
    ]
    for name in sorted(p.name for p in _ENGINE_DIR.glob('*.py')):
        try:
            desc = TOOLS_DESCRIPTIONS[name]
        except KeyError:
            sys.exit(f"build_views FAIL: tools/{name} exists but has no entry "
                     f"in TOOLS_DESCRIPTIONS (build_views.py) -- this table used "
                     f"to be a hand-written list that silently omitted whatever "
                     f"wasn't added to it (missing over half of tools/ by the "
                     f"time a 2026-09-01 deep-check audit found it, including "
                     f"precedent_check.py and precedent_gate.py). Add a "
                     f"one-line description for tools/{name} rather than "
                     f"leaving it out.")
        lines.append(f"| [tools/{name}](tools/{name}) | {desc} |")
    lines.append('')
    return '\n'.join(lines) + '\n'


# One entry per file in tools/*.py -- render_map_md() asserts every file that
# EXISTS has one, so a new script silently missing from MAP.md's "## The
# engine" table (the gap a 2026-09-01 deep-check audit found: 9 hardcoded
# rows against 20 real files, missing precedent_check.py and
# precedent_gate.py -- the implementations of two of the plan's four loading
# channels -- from the very table orientation-map, a RESIDENT practice, exists
# to keep current) fails the build instead of shipping quietly incomplete.
TOOLS_DESCRIPTIONS = {
    'behavioral_replay.py': "Measures the path-triggered loader against this repo's own commit history",
    'build_views.py': "This file, GLOSSARY.md, and AGENTS.md's loader block — generated views",
    'build_codeowners.py': "A team practice set's CODEOWNERS, generated from its own approvers.json",
    'catalogue_stats.py': "The figures about the catalogue that other documents cite, computed rather than hand-typed",
    'checkin.py': "Drives the periodic check-in (INSTALL.md §4) mechanically",
    'doc_html.py': "The one sortable-table HTML renderer for repo documents",
    'parse_check.py': "Does every JSON/YAML file in scope still parse — changed files for the deep check, the whole tree for the very deep check",
    'doc_lint.py': "Markdown hygiene checks — strikethrough, links, acronyms",
    'doc_sync.py': "Keeps script-generated blocks inside documents in sync with what the script emits",
    'full_practice_audit.py': "The full practice audit — on-demand, whole-catalogue sweep across every source",
    'leak_gate.py': "The push-time leak gate — structural rules always, private-term blocklist when configured",
    'model_audit.py': "Runs each computing script's own self-assertions and checks the figures it recites",
    'practice_audit.py': "Audits the practice-export layer for a repo that vendors one (this repo does not)",
    'practice_simulation.py': "Synthetic scenario generation for routing quality — invented cases, never a replayed benchmark",
    'precedent_check.py': "The ENFORCED loading channel — runs every practice's `checked_by` script",
    'precedent_gate.py': "The GATE-TRIGGERED loading channel — Rules for a named moment (merge, review, push, reply)",
    'precedent_bootstrap_source.py': "Instantiates a brand-new individual or team practice set from a skeleton, for an adopter who has neither yet",
    'precedent_source_bootstrap.py': "Retry-capable clone-or-pull for a privately-scoped individual source, used by its SessionStart hook and by precedent_resolve.py's own lazy self-heal",
    'precedent_candidate.py': "Stage 2 (phase 5) — raise, list and expire creation-pipeline candidates",
    'precedent_detect.py': "Stage 1 (phase 5) — the mechanical half of candidate detection",
    'precedent_land.py': "Stage 5 (phase 5) — writes an approved candidate into practices/, enforcing the registered-check invariant",
    'precedent_materialize.py': "Bridges precedent_resolve.py's multi-source resolution to the single-tree loader tools",
    'precedent_paths.py': "The PATH-TRIGGERED channel — matches a touched file against every practice's `applies_to`",
    'precedent_promote.py': "Stage 3 (phase 5) — runs a candidate against the four promotion criteria",
    'precedent_resolve.py': "Resolves the universal, team and individual sources into one set, by precedence",
    'precedent_migrate_status.py': "Classifies practices written under the old status vocabulary, where `retired` meant two different things; proposes, and refuses to guess a renamed successor",
    'precedent_retire.py': "Stage 6 (phase 5) — the periodic removal report; proposes, never acts",
    'precedent_show.py': "Loads a practice's Rule/Detail/Why/Story/Install — the one code path that reads a practice file",
    'precedent_simulate.py': "One command over the reach/mechanical-correctness and synthetic-batch tiers, plus the running trend log",
    'precedent_sync_views.py': "One command for a consuming repo: precedent_materialize.py + build_views.py --agents-only, glued together",
    'precedent_vendor_engine.py': "Vendors the minimal source-repo engine (this file, precedent_gate/paths/show.py, split_practices.py, a trimmed routing_scope.json) into an individual or team set, and keeps it refreshable",
    'resplit_sections.py': "The editorial Rule/Detail/Why/Story/Install split, applied from tools/section_split.json",
    'routing_audit.py': "The routing audit — mechanical coverage check plus a rotating deep-read slice",
    'routing_eval.py': "Measures whether trigger-based loading actually beats carrying the whole catalogue",
    'split_practices.py': "PRACTICES.md ↔ practices/ converter",
    'table_fmt.py': "One formatter per quantity kind — the engine",
    'title_case.py': "Headline (New York Times) capitalization for markdown headings — --check to gate, --write to fix",
    'verify_harness.py': "The verification harness — run before trusting any change here",
    'very_deep_check.py': "The very deep check — on-demand whole-repo coherence review, distinct from full-practice-audit",
}


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
    argv = sys.argv[1:]
    repo = None
    if '--repo' in argv:
        i = argv.index('--repo')
        if i + 1 >= len(argv):
            sys.exit("build_views FAIL: --repo needs a value.")
        repo = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    root = pathlib.Path(repo).resolve() if repo else ROOT
    practices_dir = root / 'practices'
    agents_md = root / 'AGENTS.md'
    map_md = root / 'MAP.md'
    glossary_md = root / 'GLOSSARY.md'
    # Graceful degradation, not a crash: the loader block is written INTO an
    # existing AGENTS.md, between markers the install step puts there. A
    # repo that has not instantiated it yet (INSTALL.md sec.0 step 4 /
    # sec.1 step 2) used to get a bare FileNotFoundError from deep inside
    # the renderer, which reads as the generator being broken rather than
    # as one install step not done.
    if not agents_md.is_file():
        sys.exit(f"build_views FAIL: {agents_md} does not exist. Instantiate "
                 f"it from templates/AGENTS.md.loader.template (or "
                 f"templates/AGENTS.md.template on the classic layout), "
                 f"keeping its BEGIN/END GENERATED markers, then re-run.")

    check = '--check' in argv
    # --agents-only: regenerate just AGENTS.md's loader block (resident
    # block, occasion index, standing instruction), skip MAP.md and
    # GLOSSARY.md. render_map_md()'s TOOLS_DESCRIPTIONS table and "this repo
    # is BestPractice itself" prose are specific to this repo; a team or
    # individual source repo vendoring this same engine for its OWN
    # catalogue (practice: layered-practice-packs -- every level needs the
    # same resident/occasion-index treatment universal already gets, not
    # just a hand-written README describing the practice list in prose)
    # wants only the loader-block mechanism, not BestPractice's own MAP/
    # GLOSSARY conventions.
    agents_only = '--agents-only' in argv
    practices = load_practices(practices_dir)

    levels = source_levels_from_manifest(root)
    new_agents = render_agents_md(practices, agents_md, source_levels=levels)
    targets = [(agents_md, new_agents)]
    if not agents_only:
        targets.append((map_md, render_map_md(practices)))
        targets.append((glossary_md, render_glossary_md(practices)))

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
        print(f"build_views --check OK: {', '.join(p.name for p, _t in targets)} "
              f"all byte-identical to a fresh regeneration")
        return 0

    for path, new_text in targets:
        path.write_text(new_text, encoding='utf-8')
    _block, tokens, n_resident = build_loader_block(
        practices, source_levels=source_levels_from_manifest(root))
    wrote = ', '.join(p.name for p, _t in targets)
    print(f"build_views OK: wrote {wrote} (loader block regenerated, resident "
          f"{n_resident}/{len(practices)} practices, ~{tokens} tokens)")
    return 0


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/HOW_TO_USE_THIS_TECHNICAL.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
