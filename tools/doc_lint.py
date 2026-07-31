#!/usr/bin/env python3
"""doc_lint.py — markdown hygiene checks (BestPractice practice 11).

Two checks, both born from real bugs (an outward-facing document that rendered
with unintended strikethrough, and file references written as bare backticks
instead of links):

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

SCOPE: by default, only files CHANGED vs the default branch (the convention is
"fix the parts you touch"; this also avoids editing frozen documents, where a
`~`→`≈` change would be content drift). Pass explicit files, or --all to scan
the whole tree (reports the legacy backlog; does not fail).

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
    strikes, unlinked, unglossed = [], [], []
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
    return strikes, unlinked, unglossed, len(changed_lines)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    flags = {a for a in sys.argv[1:] if a.startswith('-')}
    fix = '--fix' in flags
    if '--all' in flags:
        files, gate = tracked_md(), False
    elif args:
        files, gate = args, True
    else:
        files, gate = changed_md(), True

    if not HAVE_GFM:
        print("doc_lint: cmark-gfm not installed — strikethrough check SKIPPED "
              "(pip install cmarkgfm). Running reference check only.")

    known = None if fix else load_known_acronyms()
    total_strikes = total_unlinked = total_unglossed = total_fixed = 0
    strike_lines, unlinked_lines, unglossed_lines = [], [], []
    for f in files:
        if not (ROOT / f).exists():
            continue
        s, u, g, nf = check_file(f, fix=fix, known=known)
        total_fixed += nf
        for i, txt in s:
            strike_lines.append(f"  {f}:{i}: {txt}")
        for i, ref in u:
            unlinked_lines.append(f"  {f}:{i}: `{ref}` is not a link")
        for i, tok in g:
            unglossed_lines.append(f"  {f}:{i}: {tok}")
        total_strikes += len(s); total_unlinked += len(u); total_unglossed += len(g)

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

    if not strike_lines and not unlinked_lines and not unglossed_lines:
        print(f"doc_lint OK: {len(files)} file(s) checked — no accidental strikethrough, "
              f"no unlinked references, no unglossed acronyms.")

    # gate: fail only on strikethrough, only in gated (changed/explicit) scope
    if gate and strike_lines:
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
