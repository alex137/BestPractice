#!/usr/bin/env python3
"""doc_lint.py — markdown hygiene checks (BestPractice practice 11).

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

  3. UNGLOSSED ACRONYM (warning; practice 17). If the repo has a GLOSSARY.md, this
     flags ALL-CAPS tokens in a changed doc that are NOT in it, not defined inline
     on the same line as `(TOKEN)`, and not a common word/unit — so you either
     expand the acronym on first use or add it to the glossary. Warning-only,
     deduped to one line per acronym; skipped entirely if there is no GLOSSARY.md
     (a repo without one opts out naturally).

  4. HTML ANCHOR WITH target= (warning). GitHub's sanitizer strips target=
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

Run:  python3 process/upstream/tools/doc_lint.py            # changed-vs-default-branch, gate
      python3 process/upstream/tools/doc_lint.py --all       # whole repo, report-only
      python3 process/upstream/tools/doc_lint.py --fix FILE   # rewrite ~ -> ≈ on struck lines
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
GLOSSARY_PATH = ROOT / 'GLOSSARY.md'
ACRONYM_SKIP_FILES = {'GLOSSARY.md'}
# common words / units / universally-known tech that are never worth glossing:
ACRONYM_STOP = {
    'THE','AND','FOR','NOT','BUT','ALL','ONE','TWO','OUR','YOU','WHO','WHY','HOW','NEW',
    'OLD','YES','OFF','ITS','ETC','NB','OK','AKA','VS','IE','EG','AM','PM','PER','TBD',
    'TODO','MAP','README','FIG','FIGS','NOTE','OPEN','DONE','DRAFT',
    'PDF','HTML','CSS','JSON','CSV','XML','SVG','PNG','JPG','API','URL','URI','CLI','GUI',
    'UI','UX','OS','CPU','GPU','RAM','SDK','HTTP','HTTPS','USB','LED','ID','IP',
    'USA','US','UK','EU','UN','USD','ROI','IRR','NPV','CAGR','CEO','CTO',
    'MJ','MW','MN','GW','KW','KWH','WH','NM','KM','MM','CM','HZ','KHZ','MHZ','GHZ','DB',
    'DBM','PSI','HP','KG','LB','KT','KN','GB','MB','TB','AC','DC','NE','NW','SSE','SSW',
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

def _decontent(line):
    """Strip code spans and link/URL targets so acronyms inside them aren't scanned."""
    line = re.sub(r'`[^`]*`', ' ', line)
    line = re.sub(r'\]\([^)]*\)', '] ', line)
    line = re.sub(r'https?://\S+', ' ', line)
    return line


# ---- unsourced-quantity check (OPT-IN; practice 33 extension) ----
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


def check_quantities(text):
    """[(line_no, quantity)] for quantities that are neither generated, cited,
    nor <!--rom-->-marked. Only meaningful for a document that opts in."""
    out = []
    outside = GEN_BLOCK_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    for i, line in enumerate(outside.splitlines(), 1):
        if "http://" in line or "https://" in line or "<!--rom-->" in line:
            continue
        for q in QTY_RE.findall(line):
            out.append((i, q.strip()))
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

def check_file(path, fix=False, known=None):
    strikes, unlinked, unglossed, targeted = [], [], [], []
    changed_lines = {}
    scan_acronyms = known is not None and path not in ACRONYM_SKIP_FILES
    seen_acr = set()
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
        # unglossed acronyms: ALL-CAPS token not known and not defined inline this line
        if scan_acronyms:
            clean = _decontent(line)
            for m in ACRONYM_RE.finditer(clean):
                tok = m.group(1)
                if tok not in known and tok not in seen_acr and f'({tok})' not in clean:
                    seen_acr.add(tok)
                    unglossed.append((i, tok))
    if fix and changed_lines:
        lines = (ROOT / path).read_text(encoding='utf-8', errors='ignore').splitlines()
        for i, new in changed_lines.items():
            lines[i-1] = new
        (ROOT / path).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return strikes, unlinked, unglossed, targeted, len(changed_lines)

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
    unsourced_lines = []
    for f in files:
        if not (ROOT / f).exists():
            continue
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

    if unsourced_lines:
        print(f"\nUNSOURCED QUANTITIES — {len(unsourced_lines)} in documents that "
              f"opted in with {GATE_MARKER} (FAIL; generate it, cite it, or mark "
              "the line <!--rom-->):")
        print('\n'.join(unsourced_lines[:40]))

    if (not strike_lines and not unlinked_lines and not unglossed_lines
            and not target_lines and not unsourced_lines):
        print(f"doc_lint OK: {len(files)} file(s) checked — no accidental strikethrough, "
              f"no unlinked references, no unglossed acronyms, no target= anchors.")

    # gate: strikethrough always fails in scope; unsourced quantities fail only
    # in documents that explicitly opted in, so the legacy corpus never blocks.
    if gate and (strike_lines or unsourced_lines):
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
