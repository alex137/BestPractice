#!/usr/bin/env python3
"""doc_lint.py — markdown hygiene checks (practice: doc-references-are-links).

Markdown hygiene checks, each born from a real bug (an outward-facing document
that rendered with unintended strikethrough; file references written as bare
backticks instead of links; a link converted to an HTML anchor for new-tab
behavior that GitHub silently neutered):

  1. ACCIDENTAL STRIKETHROUGH (error). GitHub renders `~text~` and `~~text~~` as
     <del> when the tildes flank properly. A lone `~` used for "approximately"
     (`~$5k`) is HARMLESS (it only ever *opens*, never closes) — the bug is when
     two tildes on a line pair into a strikethrough span. Detected EXACTLY with
     GitHub's own engine (cmark-gfm): a line is flagged only if it actually
     renders <del> AND does not use `~~` (double-tilde is treated as intentional
     strikethrough). Fix: use `≈` for "approximately", or --fix.

  2. UNLINKED FILE REFERENCE (warning). A backticked `*.md`/`*.py` filename that
     is not the text of a markdown link. Per the doc-reference convention, new
     text links its references. Warning-only (index docs legitimately carry many
     bare-backtick references); shown so you can link the ones you just touched.

  3. UNGLOSSED ACRONYM (warning) (practice: acronyms-glossary). If the repo has a GLOSSARY.md, this
     flags ALL-CAPS tokens in a changed doc that are NOT in it, not defined inline
     on the same line as `(TOKEN)`, and not a common word/unit — so you either
     expand the acronym on first use or add it to the glossary. Warning-only,
     deduped to one line per acronym; skipped entirely if there is no GLOSSARY.md
     (a repo without one opts out naturally).

  4. BROKEN RELATIVE LINK (error). A relative markdown link whose target does
     not exist, resolved from the linking FILE's own directory (not the repo
     root — the mistake that produced 96 of them here, in files one level
     down). A target carrying a `#fragment` is checked twice: the file must
     exist, and the fragment must match a heading in it -- GitHub's own slug
     rule, so `## Cost — the numbers` is `#cost--the-numbers`, two hyphens,
     because the dash is deleted and both of its spaces survive. Skips fenced
     blocks, code spans and URLs; skips templates/ and deck/, whose links
     deliberately name a tree that is not this repo's.

  5. HTML ANCHOR WITH target= (warning). GitHub's sanitizer strips target=
     (and most other attributes) from raw HTML anchors in rendered markdown,
     so an "open in new tab" link silently does nothing there (as of 2026-08;
     origin: a thread spent two commits adding target="_blank" and reverting
     it). Use a plain markdown link instead.

SCOPE: by default, only files CHANGED vs the default branch (the convention is
"fix the parts you touch"; this also avoids editing frozen documents, where a
`~`→`≈` change would be content drift). Pass explicit files, or --all to scan
the whole tree (reports the legacy backlog; does not fail).
Explicit paths are resolved against the REPO ROOT and must exist — a path that
resolves to nothing is a hard error, not a skip (origin: a fixture outside the
repo was "checked", scanned nothing, and reported OK).
Frozen-document artifacts (name prefixes in FROZEN_PREFIXES, per repo) are
excluded from the default and --all selections — they are immutable records,
so a lint hit on one is unfixable by design (origin: committing a frozen
record failed the gate on its own internal `~` tildes). Passing one
explicitly still scans it.

Requires cmark-gfm for exact detection:  pip install cmarkgfm
(If absent, the strikethrough check is SKIPPED with a notice rather than guessing.)

Run:  python3 tools/doc_lint.py             # changed-vs-default-branch, gate
      python3 tools/doc_lint.py --all        # whole repo, report-only
      python3 tools/doc_lint.py --fix FILE   # rewrite ~ -> ≈ on struck lines
(In a repo that vendors this the classic way, the path is
process/upstream/tools/doc_lint.py.)
"""
import re, sys, subprocess, pathlib

def _git(args, cwd=None):
    return subprocess.run(['git'] + args, cwd=cwd, capture_output=True, text=True).stdout.strip()

ROOT = pathlib.Path(_git(['rev-parse', '--show-toplevel'], cwd=pathlib.Path(__file__).resolve().parent)
                    or pathlib.Path(__file__).resolve().parents[2])

def default_branch():
    head = _git(['symbolic-ref', 'refs/remotes/origin/HEAD'], cwd=ROOT)
    if head:
        return head.rsplit('/', 1)[-1]
    for cand in ('main', 'master'):
        if _git(['rev-parse', '--verify', '--quiet', f'origin/{cand}'], cwd=ROOT):
            return cand
    return 'HEAD'

try:
    import cmarkgfm
    def renders_del(line):
        return '<del>' in cmarkgfm.github_flavored_markdown_to_html(line)
    HAVE_GFM = True
except Exception:
    HAVE_GFM = False

REF_RE = re.compile(r'`([^`]+\.(?:md|py))`')          # backticked filename in code span
TARGET_RE = re.compile(r'<a\s[^>]*\btarget\s*=', re.IGNORECASE)  # HTML anchor with target=

# Immutable frozen records: excluded from default/--all selections (unfixable
# by design). Dependent repos list their frozen-artifact name prefixes here.
FROZEN_PREFIXES = ()

def drop_frozen(files):
    if not FROZEN_PREFIXES:
        return files
    return [f for f in files if not pathlib.PurePath(f).name.startswith(FROZEN_PREFIXES)]

# ---- acronym check (check 3) ----
ACRONYM_RE = re.compile(r'\b([A-Z]{2}[A-Z0-9]{0,4})\b')   # 2-6 chars, ≥2 leading letters
# A dot plus a lowercase extension immediately after the token: the token is
# a filename stem (LEDGER.md, MAP.md, SETUP.md), never an acronym to gloss.
FILENAME_STEM_RE = re.compile(r'\.[a-z][a-z0-9]{0,4}\b')
HTML_COMMENT_RE = re.compile(r'<!--.*?-->', re.S)
GLOSSARY_PATH = ROOT / 'GLOSSARY.md'
ACRONYM_SKIP_FILES = {'GLOSSARY.md'}
# common words / units / universally-known tech that are never worth glossing:
ACRONYM_STOP = {
    'THE','AND','FOR','NOT','BUT','ALL','ONE','TWO','OUR','YOU','WHO','WHY','HOW','NEW',
    'OLD','YES','OFF','ITS','ETC','NB','OK','AKA','VS','IE','EG','AM','PM','PER','TBD',
    'TODO','MAP','README','FIG','FIGS','NOTE','OPEN','DONE','DRAFT','AGENTS',
    'PDF','HTML','CSS','JSON','CSV','XML','SVG','PNG','JPG','API','URL','URI','CLI','GUI',
    'UI','UX','OS','CPU','GPU','RAM','SDK','HTTP','HTTPS','USB','LED','ID','IP','AI',
    'USA','US','UK','EU','UN','USD','ROI','IRR','NPV','CAGR','CEO','CTO',
    'MJ','MW','MN','GW','KW','KWH','WH','NM','KM','MM','CM','HZ','KHZ','MHZ','GHZ','DB',
    'DBM','PSI','HP','KG','LB','KT','KN','GB','MB','TB','AC','DC','NE','NW','SSE','SSW',
    # NOTE on what does NOT belong here: ordinary English words this repo
    # happens to write in caps for emphasis (ONLY, BEGIN, BOTH, FAIL...).
    # A first pass at the 101-warning problem added about forty of them by
    # hand, which is a list that grows forever and is wrong the first time
    # somebody shouts a word nobody thought of. `looks_like_a_word()`
    # decides that from the repo's own corpus instead -- see its docstring.
    # This set is only for tokens the corpus CANNOT settle: units, and
    # acronyms so widely known that expanding them is noise rather than
    # clarity.
    #
    # Universally known in a software repository; expanding them on first
    # use in every document is noise, not clarity.
    'PR','PRS','CI','CD','VCS','UTC','YAML','TOML','DOM','JS','TS','LLM','LLMS',
    'HTML5','REST','SQL','SSH','TLS','SSL','ENV','REPO','REGEX','DIFF','SHA','UUID',
    'TL','DR','NA','IO','CWD','STDIN','STDOUT','STDERR',
}

def load_known_acronyms():
    """Acronyms already documented: GLOSSARY.md bold tokens + the stoplist. Returns None
    (check disabled) if the repo has no GLOSSARY.md."""
    if not GLOSSARY_PATH.exists():
        return None
    known = set(ACRONYM_STOP)
    for m in re.finditer(r'\*\*([^*]+)\*\*', GLOSSARY_PATH.read_text(encoding='utf-8', errors='ignore')):
        for tok in re.split(r'[/\s,]+', m.group(1)):
            tok = tok.strip(' .…-').upper()
            if tok:
                known.add(tok)
    return known

# ---- broken relative link check (check 4; practice: doc-references-are-links)
#
# A link is only a reference if it lands somewhere. 96 links in this repo did
# not (2026-09-06): the great majority were `practices/*.md` files written
# with root-relative targets -- `](tools/doc_lint.py)` from a file that lives
# in `practices/`, resolving to `practices/tools/doc_lint.py` and returning a
# 404 for every reader of the practice file itself. `doc-references-are-links`
# asked for links and nothing checked they resolved, so the convention broke
# quietly for as long as it existed. practice: convention-to-audit.
LINK_RE = re.compile(r'\[([^\]\n]*)\]\(([^)\s]+?)(?:\s+"[^"]*")?\)')
CODE_SPAN_RE = re.compile(r'`[^`]*`')
# Directories whose markdown deliberately links against a tree that is not
# this repo's own, so an unresolvable target there is correct, not broken:
#
#   templates/  -- a skeleton instantiated INTO another repo. Its links name
#                  files that will exist there (`tools/build_views.py` in a
#                  bootstrapped practice set, `approvers.json` in a team set),
#                  never files beside the template.
#   deck/*/slides/ -- deck/build_deck.py resolves a slide's asset paths from
#                  the DECK root, not the slide's own directory, so
#                  `assets/loop.svg` is right for the builder and wrong for a
#                  reader browsing the raw file. The builder is the audience.
LINK_CHECK_EXEMPT_DIRS = ('templates/', 'deck/')


# Anchors. A link's fragment is as breakable as its path and breaks more
# quietly: editing a heading silently invalidates every link into it, and the
# reader lands at the top of the right document instead of at a 404, so
# nobody reports it. Nine were dead here when this was written (2026-09-06),
# one of them pointing at an INSTALL.md section number that no longer exists
# and six at headings that had simply been reworded since. practice:
# convention-to-audit.
#
# GitHub's rule (github-slugger): lowercase, drop every character that is not
# alphanumeric, hyphen, underscore or space, then spaces to hyphens, then
# `-1`, `-2` for repeats. Note what that does to a dash set off by spaces --
# the dash goes, its two spaces stay, and the anchor gets a DOUBLE hyphen.
HEADING_RE = re.compile(r'#{1,6}\s+(.*)')
HTML_ANCHOR_ID_RE = re.compile(r'<a\s[^>]*(?:name|id)\s*=\s*"([^"]+)"', re.I)
SETEXT_RE = re.compile(r'^(?:=+|-{2,})\s*$')
_INLINE_MD = [(re.compile(r'`([^`]*)`'), r'\1'),
              (re.compile(r'\[([^\]]*)\]\([^)]*\)'), r'\1'),
              (re.compile(r'\*\*([^*]*)\*\*'), r'\1'),
              (re.compile(r'\*([^*]*)\*'), r'\1'),
              (re.compile(r'__([^_]*)__'), r'\1'),
              (re.compile(r'<[^>]+>'), '')]
_anchor_cache = {}


def heading_slug(text):
    """GitHub's anchor for one heading's raw markdown text."""
    for rx, rep in _INLINE_MD:
        text = rx.sub(rep, text)
    return re.sub(r'[^\w\- ]', '', text.strip().lower()).replace(' ', '-')


def document_anchors(path):
    """The set of anchors `path` offers, or None if that cannot be known.

    None rather than an empty set for a document using setext headings
    (`Title` over `=====`), which this does not parse: an unknown anchor set
    must not read as "the anchor is missing". Nothing in this repo uses
    them, so the guard costs nothing and stops the check inventing failures
    in a document written a way it does not understand."""
    key = str(path)
    if key in _anchor_cache:
        return _anchor_cache[key]
    out, seen, incode, prev = set(), {}, False, ''
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.lstrip().startswith(('```', '~~~')):
            incode, prev = not incode, ''
            continue
        if incode:
            continue
        if prev.strip() and SETEXT_RE.match(line):
            out = None
            break
        m = HEADING_RE.match(line)
        if m:
            a = heading_slug(m.group(1))
            n = seen.get(a, 0)
            seen[a] = n + 1
            out.add(a if n == 0 else f'{a}-{n}')
        out.update(x.lower() for x in HTML_ANCHOR_ID_RE.findall(line))
        prev = line
    _anchor_cache[key] = out
    return out


def check_broken_links(path):
    """[(lineno, target, why)] links in `path` that land nowhere.

    Skips fenced blocks and inline code spans (a link written inside
    backticks is a value being documented, not a reference), absolute URLs
    and mailto:. A bare `#anchor` is resolved against this file itself."""
    rel = str(path).replace('\\', '/')
    if rel.startswith(LINK_CHECK_EXEMPT_DIRS):
        return []
    p = ROOT / path
    out, incode = [], False
    for i, line in enumerate(p.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
        if line.lstrip().startswith(('```', '~~~')):
            incode = not incode
            continue
        if incode:
            continue
        clean = CODE_SPAN_RE.sub(lambda m: ' ' * len(m.group(0)), line)
        for _label, target in LINK_RE.findall(clean):
            if target.startswith(('http://', 'https://', 'mailto:')):
                continue
            bare, _, frag = target.partition('#')
            dest = p if not bare else (p.parent / bare)
            if bare and not dest.exists():
                out.append((i, target, 'no such file'))
                continue
            if not frag or dest.suffix.lower() != '.md':
                continue
            # An anchor into a tree that is not this repo's is as
            # unresolvable-on-purpose as a path into one.
            try:
                drel = str(dest.resolve().relative_to(ROOT.resolve()))
            except ValueError:
                continue
            if drel.replace('\\', '/').startswith(LINK_CHECK_EXEMPT_DIRS):
                continue
            have = document_anchors(dest)
            if have is not None and frag.lower() not in have:
                out.append((i, target, f'no heading makes #{frag} in {drel}'))
    return out


# The corpus rule. An initialism has no ordinary lowercase form -- nobody
# writes "ci" or "rpp" mid-sentence -- while a word being SHOUTED for
# emphasis is a word the same repository writes in lowercase constantly.
# That difference is measurable from the repository's own prose, and it is
# what actually separates the two classes; a hand-maintained list of
# English words is a proxy for it that grows forever and is wrong the first
# time somebody shouts a word nobody thought of.
#
# Measured on this repo, 2026-09-06: NOT appears 22 times in caps and 1,899
# in lowercase; ONLY 4 and 689; LOADER 38 and 181. Against that, RPP is 45
# and 0, CI 30 and 0, LLM 11 and 0, VCS 8 and 0. There is no overlap worth
# arguing about, which is why a plain ratio is enough and a dictionary is
# not needed.
LOWERCASE_WORD_RE = re.compile(r'\b([a-z]{2,8})\b')
# Above this share of lowercase uses, the token is a word being shouted.
# 0.4 rather than 0.5 because the caps count is inflated by headings and
# filename stems, which are the same token doing a different job.
WORD_FORM_RATIO = 0.4
_corpus_cache = None


def corpus_word_forms():
    """{TOKEN: lowercase_share} over this repo's own tracked markdown.

    Built once per process, lazily -- it costs ≈0.1s over ≈150 files here,
    and only the acronym check needs it. Fails to an empty map rather than
    raising: with no corpus the check simply falls back to the stoplist,
    which is the behaviour it had before this existed."""
    global _corpus_cache
    if _corpus_cache is not None:
        return _corpus_cache
    lower, caps = {}, {}
    try:
        listed = _git(['ls-files', '*.md'], cwd=ROOT).splitlines()
        paths = [ROOT / f for f in listed] or list(ROOT.rglob('*.md'))
    except Exception:
        paths = []
    for f in paths:
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        for w in LOWERCASE_WORD_RE.findall(text):
            lower[w] = lower.get(w, 0) + 1
        for w in ACRONYM_RE.findall(text):
            caps[w] = caps.get(w, 0) + 1
    _corpus_cache = {tok: lower.get(tok.lower(), 0)
                     / (lower.get(tok.lower(), 0) + n)
                     for tok, n in caps.items() if n}
    return _corpus_cache


def looks_like_a_word(tok):
    """True when this repository's own prose writes `tok` in lowercase far
    more often than in caps -- i.e. it is an English word being shouted,
    not an initialism. See corpus_word_forms() for the measurement."""
    return corpus_word_forms().get(tok, 0.0) >= WORD_FORM_RATIO


def scan_unglossed(text, known, path=None):
    """[(lineno, TOKEN)] — every ALL-CAPS token in `text` that is not a
    known acronym, not glossed inline as `LONG FORM (TOK)`, not a filename
    stem, and not the document's own name.

    THE ONE DETECTOR. tools/precedent_check.py's `acronyms-glossary` check
    used to carry its own copy of this loop, under a docstring promising
    "one detector, two callers" — and then drifted from it exactly as that
    docstring said it must not: two filters added here (filename stems,
    a document naming itself) fixed doc_lint's report and left the
    enforced check still failing on `LEDGER.md`. Both callers now go
    through this function, so a filter added here reaches the gate."""
    doc_name = pathlib.PurePath(path).stem.upper() if path else None
    # HTML comments are guidance to whoever edits the file, never content
    # the document asserts, and no reader ever sees them rendered -- so an
    # ALL-CAPS word used for emphasis inside one ("use this LOADER variant
    # for a fresh install", in templates/AGENTS.md.loader.template) is not
    # an acronym anybody can gloss. Blanked rather than removed so line
    # numbers still point at the right line.
    text = HTML_COMMENT_RE.sub(lambda m: '\n' * m.group(0).count('\n'), text or '')
    out, seen, incode = [], set(), False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith('```'):
            incode = not incode
            continue
        if incode:
            continue
        clean = _decontent(line)
        for m in ACRONYM_RE.finditer(clean):
            tok = m.group(1)
            if tok in known or tok in seen:
                continue
            if tok == doc_name:
                # A document naming itself in its own title (SETUP.md's
                # "# SETUP — guided install"). Not an acronym, and the one
                # person who cannot fix it is the person editing that file.
                continue
            if looks_like_a_word(tok):
                # An English word this repo shouts for emphasis, not an
                # initialism. Decided from the corpus, not a wordlist --
                # see looks_like_a_word().
                continue
            if FILENAME_STEM_RE.match(clean, m.end()):
                # An ALL-CAPS filename stem is a file reference, not an
                # acronym: LEDGER.md, MAP.md, TODO.md, AGENTS.md. This
                # repo's own report was 101 "unglossed acronyms", of which
                # the largest group was file names split at the dot.
                # Glossing "LEDGER" is not a thing anyone can do; the
                # reference is already covered by the unlinked-reference
                # check.
                continue
            # Glossed right here — covers THIS use, and every later bare
            # use in the same document. Recording `seen` only on the
            # violation branch (the bug this replaces) meant a correctly
            # glossed first use never protected a second, later mention.
            seen.add(tok)
            if f'({tok})' in clean:
                continue
            out.append((i, tok))
    return out


def _decontent(line):
    """Strip code spans, self-referential link labels, and link/URL targets so
    acronyms inside them aren't scanned. A self-referential link -- label
    identical to its own target, e.g. `[docs-team/BUSINESS-MODEL-CONCEPTS.md]
    (docs-team/BUSINESS-MODEL-CONCEPTS.md)`, the convention this repo's own
    doc-references-are-links practice produces -- is dropped whole; a
    hyphenated filename used this way (BUSINESS-MODEL-CONCEPTS.md) otherwise
    split into spurious ALL-CAPS fragments (MODEL) at every hyphen, since the
    old version stripped only the `](target)` half and left the repeated
    filename as scannable label text. A descriptive label that DIFFERS from
    its target (`[the ZQX report](file.md)`) still isn't self-referential, so
    its acronym is still caught."""
    line = re.sub(r'`[^`]*`', ' ', line)
    line = re.sub(r'\[([^\]]*)\]\(\1\)', ' ', line)
    line = re.sub(r'\]\([^)]*\)', '] ', line)
    line = re.sub(r'https?://\S+', ' ', line)
    return line


# ---- unsourced-quantity check (OPT-IN; docs-track-models extension) ----
# practice: docs-track-models
# Every quantity in a document should be generated by code, cited to an
# external source, or explicitly marked as an unsourced estimate. In any
# mature repo the bulk of the corpus predates that discipline -- MEASURE
# BEFORE GATING: in the origin repo, ~91% of quantity tokens were
# unexplained, so a repo-wide gate would fail forever and be switched off
# within a day. It is therefore OPT-IN per document: a document places
# <!--numbers:gated--> alone on a line and is then held to the rule. New
# outward-facing work opts in at birth; the legacy corpus is a report
# (--numbers-report), not a gate.
#
# Exemptions inside a gated document:
#   * inside a <!--gen:...--> block            (generated -- best)
#   * a line carrying an http(s) citation      (externally sourced)
#   * <!--rom--> on the line                   (declared unsourced estimate)
NUM_UNIT = (r"(?:m|km|mi|nmi|ft|kt|mph|kg|lb|MW|kW|kWh|MJ|kJ|h|hr|min|%|L|gal)")
QTY_RE = re.compile(r"(?<![\w.])(?:[≈~]\s?)?\d[\d,]*(?:\.\d+)?\s?(?:" + NUM_UNIT
                    + r")(?![\w/])|\$\s?\d[\d,]*(?:\.\d+)?[MBk]?")
GEN_BLOCK_RE = re.compile(r"<!--gen:.*?<!--/gen:[\w-]+-->", re.S)
GATE_MARKER = "<!--numbers:gated-->"


def opts_in(text):
    """True only if the gate marker is ALONE on its own line. Matching the
    bare string anywhere is wrong: a document that merely MENTIONS the marker
    -- a runbook, a task list, this file -- would opt itself in and then fail
    on every quantity it discusses. (That is exactly what happened on the
    first run, on the repo's task file, from the note announcing the check.)"""
    return any(l.strip() == GATE_MARKER for l in text.splitlines())


# A citing URL must actually cite the quantity, not merely share its line --
# a whole-line exemption let an unrelated URL anywhere on the line (a footer
# link, an unrelated reference) exempt a number nowhere near it. Require
# nothing but filler punctuation/whitespace (and an optional markdown link's
# own brackets) between the quantity and the URL that cites it, in EITHER
# direction: "500 mph (https://...)", "500 mph -- https://...", "[500
# mph](url)" all qualify; "500 mph, unrelated link: https://..." does not,
# because "unrelated link:" is content, not filler.
FILLER_RE = re.compile(r"^[\s,;:()\[\]—–-]*$")
URL_RE = re.compile(r"https?://\S+")


def _cited_by_nearby_url(line, qty_start, qty_end, urls):
    for u_start, u_end in urls:
        if u_end <= qty_start and FILLER_RE.match(line[u_end:qty_start]):
            return True
        if qty_end <= u_start and FILLER_RE.match(line[qty_end:u_start]):
            return True
    return False


def check_quantities(text):
    """[(line_no, quantity)] for quantities that are neither generated, cited,
    nor <!--rom-->-marked. Only meaningful for a document that opts in."""
    out = []
    outside = GEN_BLOCK_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    for i, line in enumerate(outside.splitlines(), 1):
        if "<!--rom-->" in line:
            continue
        urls = [m.span() for m in URL_RE.finditer(line)]
        for m in QTY_RE.finditer(line):
            if urls and _cited_by_nearby_url(line, m.start(), m.end(), urls):
                continue
            out.append((i, m.group(0).strip()))
    return out



def tracked_md():
    return _git(['ls-files', '*.md'], cwd=ROOT).split()

def changed_md():
    ref = f'origin/{default_branch()}'
    base = _git(['merge-base', 'HEAD', ref], cwd=ROOT) or ref
    committed = _git(['diff', '--name-only', '--diff-filter=d', base, '--', '*.md'], cwd=ROOT).split()
    worktree = _git(['diff', '--name-only', '--diff-filter=d', '--', '*.md'], cwd=ROOT).split()
    return sorted(set(committed) | set(worktree))

def iter_prose_lines(path):
    """Yield (lineno, text) for lines outside fenced code blocks."""
    incode = False
    for i, line in enumerate((ROOT / path).read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
        if line.lstrip().startswith('```'):
            incode = not incode
            continue
        if not incode:
            yield i, line

# NOT named HEADING_RE: line 189 already defines one, for anchor
# resolution, and redefining it here silently broke every anchor check
# in the harness the moment this was added (2026-09-06). A module-level
# name is a shared namespace; the second definition simply wins.
HEADING_LEVEL_RE = re.compile(r'^(#{1,6})\s+\S')


def scan_heading_skips(path):
    """[(lineno, from_level, to_level, text)] for every heading that jumps
    more than one level deeper than the heading before it.

    One detector, two callers -- this function and precedent_check.py's
    `heading-outline` gate -- the same discipline scan_unglossed() follows,
    for the same reason: the warning and the gate drifting apart is how a
    check stops meaning anything.

    WHAT THIS DELIBERATELY DOES NOT CHECK, measured rather than assumed.
    "The first heading is an H1" is not a rule here: 80 of this repo's 153
    tracked markdown files open at `##`, so it is not the convention and
    encoding it would be inventing one. "Siblings share a rank" is not
    mechanically decidable either -- a section legitimately nests deeper
    than the one before it. What IS decidable, and is the whole defect
    worth catching, is the skip: `##` followed by `####` has no `###` to
    belong to, so the outline it renders is wrong in any table of contents
    that reads it, and no reader can tell which level was meant."""
    out = []
    prev = None
    for i, line in iter_prose_lines(path):
        m = HEADING_LEVEL_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        if prev is not None and level > prev + 1:
            out.append((i, prev, level, line.strip()[:80]))
        prev = level
    return out


def iter_prose_paragraphs(path):
    """Yield (start_lineno, paragraph_text) for each blank-line-delimited
    span of prose lines outside fenced code blocks. GFM strikethrough (a
    tilde span) can open on one line and close on a LATER line within the
    same paragraph -- GitHub renders the whole span as one <del>, but
    testing renders_del() one line at a time never sees it, since neither
    half alone contains a matching pair of tildes. This is what lets
    check_file() additionally test a whole paragraph at once, which is what
    actually matches how the renderer sees the document."""
    incode = False
    para_lines, para_start = [], None
    for i, line in enumerate((ROOT / path).read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
        if line.lstrip().startswith('```'):
            incode = not incode
            if para_lines:
                yield para_start, '\n'.join(para_lines)
                para_lines, para_start = [], None
            continue
        if incode:
            continue
        if line.strip() == '':
            if para_lines:
                yield para_start, '\n'.join(para_lines)
                para_lines, para_start = [], None
            continue
        if para_start is None:
            para_start = i
        para_lines.append(line)
    if para_lines:
        yield para_start, '\n'.join(para_lines)

def check_file(path, fix=False, known=None):
    strikes, unlinked, unglossed, targeted = [], [], [], []
    changed_lines = {}
    if known is not None and path not in ACRONYM_SKIP_FILES:
        # One detector, shared with precedent_check.py's acronyms-glossary
        # gate — see scan_unglossed's docstring for the drift this closed.
        unglossed = scan_unglossed(
            (ROOT / path).read_text(encoding='utf-8', errors='ignore'),
            known, path)
    for i, line in iter_prose_lines(path):
        if HAVE_GFM and renders_del(line) and '~~' not in line:
            if fix:
                changed_lines[i] = line.replace('~', '≈')
            else:
                strikes.append((i, line.strip()[:100]))
        # unlinked refs: a `file.md` code span not immediately followed by ](
        for m in REF_RE.finditer(line):
            after = line[m.end():m.end()+2]
            if after != '](':
                unlinked.append((i, m.group(1)))
        # target= anchors: GitHub strips the attribute from rendered HTML (check 4);
        # code spans stripped first so documenting the rule doesn't trip it
        if TARGET_RE.search(re.sub(r'`[^`]*`', ' ', line)):
            targeted.append((i, line.strip()[:100]))
    if fix and changed_lines:
        lines = (ROOT / path).read_text(encoding='utf-8', errors='ignore').splitlines()
        for i, new in changed_lines.items():
            lines[i-1] = new
        (ROOT / path).write_text('\n'.join(lines) + '\n', encoding='utf-8')

    # A strikethrough span that only renders across a paragraph -- the loop
    # above tests one line at a time and never catches this, since neither
    # half of the span alone contains a matching tilde pair. Only meaningful
    # in report mode: --fix already handles the same-line case above, and a
    # cross-line span is not safe to auto-fix without knowing which physical
    # line owns the opening tilde and which owns the closing one.
    if HAVE_GFM and not fix:
        already = {ln for ln, _ in strikes}
        for start, para in iter_prose_paragraphs(path):
            if '~~' in para or start in already:
                continue
            if renders_del(para):
                strikes.append((start, para.splitlines()[0].strip()[:100]
                                + ' [strikethrough spans multiple lines]'))
    return strikes, unlinked, unglossed, targeted, len(changed_lines)


# ---- deliverable/record split (check 6; practice `deliverables-look-like-output`) ----
#
# A reader-facing document looks like its finished output; audit apparatus,
# decision provenance, verification bookkeeping, and history lore live in the
# paired record doc (*_diligence.md / *_record.md / *_decision.md), linked
# once. Origin: a flagship study in the first dependent repo accreted a
# claims-to-source table, a verification record, an unattributed "user
# decision", and menu-retirement lore -- the fourth recurrence of the same
# leak -- and the written rule alone had not held; the owner asked for the
# mechanical guard. Companion rule: an inclination to write a verify-later
# flag means GO VERIFY NOW; only an externally-blocked item may remain open,
# in the record's open tail.
RECORD_NAME_RE = re.compile(
    r"(_diligence|_record|_decision|_notes|_index|_ledger|README|TODO|MAP|"
    r"GLOSSARY|AGENTS|CLAUDE|PRACTICES|INSTALL|SETUP|METHOD|GIT|MOBILE)",
    re.I)
RECORD_DIR_RE = re.compile(r"(^|/)(process|archive|sent|templates|deck|practices|spec)(/|$)")
RESIDUE_PATTERNS = [
    (re.compile(r"\[verify\b", re.I),
     "verify-later flag -- verify now, or record the externally-blocked "
     "item in the record doc's open tail"),
    (re.compile(r"[\[(]\s*TBV\b", re.I), "verify-later flag -- same rule"),
    (re.compile(r"claims.to.source", re.I),
     "claims-to-source apparatus belongs in the record doc"),
    (re.compile(r"verification record", re.I),
     "verification bookkeeping belongs in the record doc"),
    (re.compile(r"\buser (decision|rule|direction)\b", re.I),
     "decision provenance belongs in the record doc, with the decider "
     "named"),
    (re.compile(r"retired from the (menu|table|study|set)", re.I),
     "history lore belongs in the record doc or version control"),
]


RECORD_MARKER = "<!--record-doc-->"


def is_record_doc(path):
    if (RECORD_NAME_RE.search(pathlib.Path(path).name)
            or RECORD_DIR_RE.search(str(path).replace("\\", "/"))):
        return True
    try:
        head = (ROOT / path).read_text(errors="ignore")[:2048]
    except OSError:
        return False
    return RECORD_MARKER in head


def check_residue(path):
    """[(lineno, message)] process-residue hits in a deliverable doc."""
    if is_record_doc(path):
        return []
    out = []
    # Was r"\]\([^)]*_(record|diligence)\.md\)" -- only two of the six
    # record-doc name suffixes is_record_doc() (and RECORD_NAME_RE) already
    # recognize. A line that is legitimately just a link to
    # thing_decision.md, thing_notes.md, thing_index.md or thing_ledger.md
    # was falsely flagged as residue and failed the gate, since none of
    # those four matched this narrower, separately-maintained pattern.
    link_re = re.compile(r"\]\([^)]*_(record|diligence|decision|notes|index"
                         r"|ledger)\.md\)", re.I)
    for i, line in iter_prose_lines(path):
        if link_re.search(line):
            continue        # the one allowed reference: a link to the record
        for pat, why in RESIDUE_PATTERNS:
            if pat.search(line):
                out.append((i, why))
    return out


# ---- findability check (check 5; practice `search-by-purpose`) ----
#
# An analysis nobody can find is an analysis that gets redone -- or, worse,
# silently contradicted by a later thread that never saw it. The generic
# failure: prior work is filed under the vocabulary of WHY it was done, while
# the searcher uses the vocabulary of HOW the thing works, so each search
# returns a clean, complete-looking result set with the other half absent.
#
# "Search both vocabularies" is advice a hurried reader skips. What is
# mechanically checkable is the weaker but durable property: a document
# carrying generated numbers should be reachable from at least one index a
# reader actually consults. That does not force the right search, but it
# guarantees the target of that search exists somewhere findable.
#
# Configure INDEX_FILES for the host repo's own index documents. Scoped like
# every other check here -- gate on what you touched, --all reports the
# backlog, so a legacy corpus never blocks.
# This repo's index documents. AGENTS.md carries the quick index a
# session actually consults; MAP.md is generated from the practices and
# indexes those, so a spec document is reachable only through AGENTS.md.
INDEX_FILES = ["MAP.md", "CLAUDE.md", "AGENTS.md"]

# Where the (document, block, model) registry lives. A document is "carrying
# generated numbers" if it appears in that registry.
GENERATED_REGISTRY = "tools/doc_sync.py"


def wired_docs():
    """Documents registered in the generated-block registry, or [] if absent."""
    for cand in (ROOT / GENERATED_REGISTRY,
                 pathlib.Path(__file__).resolve().parent / "doc_sync.py"):
        if not cand.exists():
            continue
        try:
            import importlib.util, io
            spec = importlib.util.spec_from_file_location("_dl_ds", cand)
            mod = importlib.util.module_from_spec(spec)
            real, sys.stdout = sys.stdout, io.StringIO()
            try:
                spec.loader.exec_module(mod)
            finally:
                sys.stdout = real
            return sorted({d for d, _n, _m in getattr(mod, "PAIRS", [])})
        except Exception:
            return []
    return []


def check_findability(docs):
    """Return [(doc, note)] for wired docs linked from no index."""
    blob = ""
    for name in INDEX_FILES:
        pth = ROOT / name
        if pth.exists():
            blob += pth.read_text(errors="ignore")
    out = []
    for d in docs:
        text = blob
        readme = (ROOT / d).parent / "README.md"
        if readme.exists():
            text += readme.read_text(errors="ignore")
        if pathlib.Path(d).name not in text:
            out.append((d, "carries generated numbers but is linked from none of "
                        + ", ".join(INDEX_FILES) + ", or its directory README"))
    return out


# A consuming repo mirrors this whole upstream tree at process/upstream/, and
# every file in it belongs to upstream: the consumer may not edit it (the
# mirror overwrites any change) and cannot fix what is wrong there. So a
# finding inside it is real information and must never be the thing that
# fails the consumer's own gate.
#
# 2026-09-06, exactly this: an engine refresh shipped the new skipped-heading
# check into two consumers whose vendored copy of upstream's own AGENTS.md
# still had the h1 -> h3 that upstream had already fixed five commits
# earlier. Both repos' doc_lint went red on a heading in a file they are
# forbidden to touch, with no action available except waiting for a catalogue
# mirror that is deliberately on hold. Reported loudly, counted separately,
# never fatal -- practice fail-gracefully: keep going, and tell the person.
VENDORED_PREFIXES = ('process/upstream/',)


def _is_vendored(rel):
    return str(rel).startswith(VENDORED_PREFIXES)


def _split_vendored(lines):
    """-> (ours, theirs). A finding line starts '  <path>:<line>: ...'."""
    ours, theirs = [], []
    for line in lines:
        (theirs if _is_vendored(line.strip().split(':', 1)[0]) else ours
         ).append(line)
    return ours, theirs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    flags = {a for a in sys.argv[1:] if a.startswith('-')}
    fix = '--fix' in flags
    if '--all' in flags:
        files, gate = drop_frozen(tracked_md()), False
    elif args:
        files, gate = args, True
        missing = [f for f in files if not (ROOT / f).exists()]
        if missing:
            for f in missing:
                print(f"doc_lint FAIL: file not found under repo root {ROOT}: {f}")
            print("(explicit paths are resolved against the repo root — a missing "
                  "file scanned as 'OK' is a silent no-op)")
            return 2
    else:
        files, gate = drop_frozen(changed_md()), True

    if not HAVE_GFM:
        print("doc_lint: cmark-gfm not installed — strikethrough check SKIPPED "
              "(pip install cmarkgfm). Running reference check only.")

    if '--numbers-report' in flags:
        rows, gated = [], 0
        for f in drop_frozen(tracked_md()):
            pth = ROOT / f
            if not pth.exists():
                continue
            t = pth.read_text(errors='ignore')
            if opts_in(t):
                gated += 1
            n = len(check_quantities(t))
            if n:
                rows.append((n, f, opts_in(t)))
        rows.sort(reverse=True)
        print(f"UNSOURCED-QUANTITY REPORT — {sum(r[0] for r in rows):,} unexplained "
              f"quantities across {len(rows)} file(s); {gated} opted in with "
              f"{GATE_MARKER}")
        for n, f, g in rows[:25]:
            print(f"  {n:5d}  {'[gated] ' if g else '        '}{f}")
        return 0

    known = None if fix else load_known_acronyms()
    total_strikes = total_unlinked = total_unglossed = total_targeted = total_fixed = 0
    strike_lines, unlinked_lines, unglossed_lines, target_lines = [], [], [], []
    unsourced_lines, residue_lines, broken_link_lines = [], [], []
    skip_lines = []
    for f in files:
        if not (ROOT / f).exists():
            continue
        for i, why in check_residue(f):
            residue_lines.append(f"  {f}:{i}: {why}")
        for i, target, why in check_broken_links(f):
            broken_link_lines.append(f"  {f}:{i}: -> {target}  ({why})")
        for i, frm, to, txt in scan_heading_skips(f):
            skip_lines.append(f"  {f}:{i}: h{frm} -> h{to} (no h{frm + 1} "
                              f"between them): {txt}")
        s, u, g, t, nf = check_file(f, fix=fix, known=known)
        total_fixed += nf
        for i, txt in s:
            strike_lines.append(f"  {f}:{i}: {txt}")
        for i, ref in u:
            unlinked_lines.append(f"  {f}:{i}: `{ref}` is not a link")
        for i, tok in g:
            unglossed_lines.append(f"  {f}:{i}: {tok}")
        for i, txt in t:
            target_lines.append(f"  {f}:{i}: {txt}")
        total_strikes += len(s); total_unlinked += len(u); total_unglossed += len(g)
        total_targeted += len(t)
        txt = (ROOT / f).read_text(errors='ignore')
        if opts_in(txt):
            for i, q in check_quantities(txt):
                unsourced_lines.append(f"  {f}:{i}: {q!r} is neither generated, "
                                       "cited, nor <!--rom--> -marked")

    if fix:
        print(f"doc_lint --fix: rewrote ~ -> ≈ on {total_fixed} accidental-strikethrough line(s).")
        return 0

    if strike_lines:
        print(f"ACCIDENTAL STRIKETHROUGH — {total_strikes} line(s) render <del> on GitHub "
              f"(use ≈ for 'approximately', or --fix):")
        print('\n'.join(strike_lines))
    if unlinked_lines:
        print(f"\nUNLINKED FILE REFERENCES — {total_unlinked} (warning; link the ones you touched):")
        print('\n'.join(unlinked_lines[:40]))
        if total_unlinked > 40:
            print(f"  … and {total_unlinked - 40} more")
    if unglossed_lines:
        print(f"\nUNGLOSSED ACRONYMS — {total_unglossed} (warning; expand on first use or add to "
              f"GLOSSARY.md):")
        print('\n'.join(unglossed_lines[:40]))
        if total_unglossed > 40:
            print(f"  … and {total_unglossed - 40} more")
    if target_lines:
        print(f"\nTARGET= ANCHORS — {total_targeted} (warning; GitHub strips target= from "
              f"rendered HTML, as of 2026-08 — use a plain markdown link):")
        print('\n'.join(target_lines[:40]))
        if total_targeted > 40:
            print(f"  … and {total_targeted - 40} more")

    if skip_lines:
        print(f"\nSKIPPED HEADING LEVELS — {len(skip_lines)} (FAIL; a heading "
              "more than one level below the one before it has no parent, so the "
              "outline it renders is wrong):")
        print('\n'.join(skip_lines[:40]))

    if unsourced_lines:
        print(f"\nUNSOURCED QUANTITIES — {len(unsourced_lines)} in documents that "
              f"opted in with {GATE_MARKER} (FAIL; generate it, cite it, or mark "
              "the line <!--rom-->):")
        print('\n'.join(unsourced_lines[:40]))

    if (not strike_lines and not unlinked_lines and not unglossed_lines
            and not target_lines and not unsourced_lines and not broken_link_lines
            and not skip_lines):
        print(f"doc_lint OK: {len(files)} file(s) checked — no accidental strikethrough, "
              f"no broken relative links, no unlinked references, no unglossed "
              f"acronyms, no target= anchors, no skipped heading levels.")

    # check 5: findability. Gate mode checks only documents in scope, so a new
    # analysis must be indexed; --all reports the legacy backlog.
    _wired = wired_docs()
    _scope = set(files)
    findability = [(d, n) for d, n in check_findability(_wired)
                   if (not gate) or d in _scope]
    if findability:
        print(f"\nUNFINDABLE ANALYSES — {len(findability)} document(s) carrying "
              f"generated numbers are not linked from "
              f"{', '.join(INDEX_FILES)} or a directory README "
              f"({'FAIL' if gate else 'backlog report'}; an analysis nobody can "
              f"find gets redone or silently contradicted):")
        for d, n in findability[:40]:
            print(f"  {d}: {n}")
        if len(findability) > 40:
            print(f"  … and {len(findability) - 40} more")

    if broken_link_lines:
        print(f"\nBROKEN RELATIVE LINKS — {len(broken_link_lines)} link(s) "
              f"land nowhere ({'FAIL' if gate else 'backlog report'}; a "
              "reference that 404s is not a reference — check the path is "
              "relative to THIS file's directory, not the repo root, and "
              "that a #fragment still matches a heading):")
        print('\n'.join(broken_link_lines[:40]))
        if len(broken_link_lines) > 40:
            print(f"  … and {len(broken_link_lines) - 40} more")

    if residue_lines:
        print(f"\nPROCESS RESIDUE IN DELIVERABLES — {len(residue_lines)} "
              f"line(s) ({'FAIL' if gate else 'backlog report'}; a "
              "reader-facing document looks like its output — apparatus, "
              "decision provenance, and open verification items live in the "
              "paired record doc):")
        print('\n'.join(residue_lines[:40]))
        if len(residue_lines) > 40:
            print(f"  … and {len(residue_lines) - 40} more")

    # gate: strikethrough always fails in scope; unsourced quantities fail only
    # in documents that explicitly opted in, so the legacy corpus never blocks;
    # process residue (check 6) fails on any deliverable in scope. Skipped
    # heading levels fail too: the whole tracked tree had exactly one when the
    # check was written (in generated output, since fixed), so there is no
    # legacy backlog to grandfather and nothing to soften this to a warning.
    #
    # Findings inside the vendored upstream tree are split out here rather
    # than filtered at the scan: the consumer still SEES them (they are
    # printed above, in full) and can report them upstream, but they cannot
    # fail a gate in the one repo that has no way to act on them. See
    # VENDORED_PREFIXES for the incident.
    fatal = []
    # EVERY fail-class group, listed exhaustively. The first version of this
    # loop omitted skip_lines, which silently disarmed the skipped-heading
    # check for the repo's own content too -- the finding still printed
    # "FAIL" and the run still exited 0. Caught by the negative control that
    # plants a real heading skip here; without that control it would have
    # shipped as a passing gate that checks nothing.
    for group in (strike_lines, unsourced_lines, residue_lines,
                  broken_link_lines, skip_lines):
        ours, theirs = _split_vendored(group)
        fatal.extend(ours)
        if theirs:
            print(f"\n  NOTE: {len(theirs)} further finding(s) of this kind "
                  f"are inside the vendored upstream tree "
                  f"({', '.join(VENDORED_PREFIXES)}). They are upstream's to "
                  f"fix and this repo may not edit them, so they do not fail "
                  f"this gate -- report them upstream if they look real:")
            print('\n'.join(theirs[:10]))
            if len(theirs) > 10:
                print(f"  … and {len(theirs) - 10} more")
    if gate and (fatal or findability):
        return 1
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
