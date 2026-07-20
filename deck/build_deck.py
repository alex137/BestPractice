#!/usr/bin/env python3
"""build_deck.py — generic self-contained HTML slide-deck engine.

The practice (see deck/README.md): presentations ship as ONE self-contained
HTML file — theme, figures, even embedded animations inlined — never as
Word/PDF/PowerPoint sources. Slide content lives in per-slide markdown files
listed by a deck manifest, so concurrent threads can draft different slides
(or competing versions of the same slide) without conflict, and the manifest
picks the preferred set. The engine is content-free and public; decks are
content and live wherever their repo keeps them.

Deck directory layout (the manifest is the only required name):

    deck.json           manifest (see below)
    slides/*.md         one slide per file; first `# Heading` is the slide
                        title; everything after a line `<!-- notes -->` is
                        speaker notes. `.html` slides are used verbatim.
    assets/*            figures referenced by slides (svg inlined as markup,
                        png/jpg/gif/webp inlined as data URIs)
    theme.css           optional CSS-variable overrides of the built-in theme
    glossary.json       optional {"TERM": "definition"} hover-tooltips

deck.json:

    {
      "title": "...", "subtitle": "...",
      "output": "My_Deck",                    -> My_Deck.html / My_Deck_send.html
      "footer": "per-slide footer/legend text",
      "theme": "theme.css",
      "glossary": "glossary.json",
      "slides": ["slides/01_cover.md",
                 {"file": "slides/07_detail.md", "review_only": true}],
      "appendix": [{"group": "Backup", "slides": ["slides/a1.md"]}]
    }

Two builds from one source (the review/send split — speaker notes carry
internal-only guidance and must not travel with a sent deck):

    python3 build_deck.py <deck-dir>          review build: notes visible
                                              below each slide, review_only
                                              slides included
    python3 build_deck.py <deck-dir> --send   external build: notes and
                                              review_only slides REMOVED
                                              from the HTML, not hidden

Viewer: arrows/space/PgUp/PgDn navigate, Home/End jump, P toggles present
mode (full-slide, notes hidden), and @media print gives one slide per page
so a PDF is always one browser print away — generated FROM the HTML, never
a source format.

Self-containment is asserted, not hoped for: after writing, the engine scans
the output for external asset references (img/script/link/iframe src) and
exits non-zero if any remain. Requires cmarkgfm or markdown
(pip install cmarkgfm) for .md slides; .html slides need neither.
"""
import base64, html, json, mimetypes, pathlib, re, sys

# ---------------------------------------------------------------- markdown
try:
    import cmarkgfm
    def md_to_html(text):
        return cmarkgfm.github_flavored_markdown_to_html(text)
except Exception:                                       # pragma: no cover
    try:
        import markdown as _md
        def md_to_html(text):
            return _md.markdown(text, extensions=['tables'])
    except Exception:
        def md_to_html(text):
            sys.exit("build_deck FAIL: no markdown renderer — "
                     "pip install cmarkgfm (or use .html slides)")

NOTES_MARK = re.compile(r'<!--\s*notes\s*-->', re.I)
IMG_RE = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"[^>]*>', re.I)
IFRAME_RE = re.compile(r'<iframe\b[^>]*\bdata-inline="([^"]+)"[^>]*>\s*</iframe>', re.I)
EXTERNAL_RE = re.compile(
    r'<(?:img|script|link|iframe)\b[^>]*\b(?:src|href)="(https?://[^"]+)"', re.I)
H1_RE = re.compile(r'<h1[^>]*>(.*?)</h1>', re.S)


def _slide_entries(manifest):
    """Normalize manifest slide lists to (file, review_only, group)."""
    out = []
    for e in manifest.get('slides', []):
        e = {'file': e} if isinstance(e, str) else e
        out.append((e['file'], bool(e.get('review_only')), None))
    for grp in manifest.get('appendix', []):
        for e in grp.get('slides', []):
            e = {'file': e} if isinstance(e, str) else e
            out.append((e['file'], bool(e.get('review_only')), grp.get('group')))
    return out


def _inline_img(m, deck_dir):
    src = m.group(1)
    if src.startswith(('http://', 'https://', 'data:')):
        return m.group(0)          # external refs are caught by the final scan
    p = deck_dir / src
    if not p.exists():
        sys.exit(f"build_deck FAIL: figure not found: {src}")
    if p.suffix.lower() == '.svg':
        # Inline the svg markup UNWRAPPED: an extra wrapper element breaks
        # deck themes that size figures with direct child selectors.
        svg = re.sub(r'<\?xml[^>]*\?>\s*', '', p.read_text(encoding='utf-8'))
        return svg
    mime = mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
    b64 = base64.b64encode(p.read_bytes()).decode('ascii')
    return m.group(0).replace(src, f'data:{mime};base64,{b64}')


def _inline_iframe(m, deck_dir):
    p = deck_dir / m.group(1)
    if not p.exists():
        sys.exit(f"build_deck FAIL: iframe doc not found: {m.group(1)}")
    esc = p.read_text(encoding='utf-8').replace('&', '&amp;').replace('"', '&quot;')
    return f'<iframe class="anim" srcdoc="{esc}"></iframe>'


def _apply_glossary(body_html, glossary):
    """Wrap glossary terms in hover-tooltip spans — text nodes only."""
    if not glossary:
        return body_html
    pat = re.compile(r'\b(' + '|'.join(re.escape(t) for t in
                     sorted(glossary, key=len, reverse=True)) + r')\b')
    parts = re.split(r'(<[^>]+>)', body_html)
    for i, part in enumerate(parts):
        if part.startswith('<'):
            continue
        parts[i] = pat.sub(lambda m: f'<span class="gl" title="{html.escape(glossary[m.group(1)])}">'
                                     f'{m.group(1)}</span>', part)
    return ''.join(parts)


def _render_slide(path, deck_dir, glossary):
    raw = path.read_text(encoding='utf-8')
    parts = NOTES_MARK.split(raw, maxsplit=1)
    body_src, notes_src = parts[0], (parts[1] if len(parts) > 1 else '')
    if path.suffix.lower() == '.html':
        body, notes = body_src, (md_to_html(notes_src) if notes_src.strip() else '')
    else:
        body = md_to_html(body_src)
        notes = md_to_html(notes_src) if notes_src.strip() else ''
    # Glossary first, while figures are still <img>/<iframe> tags: tooltip
    # spans must never be injected into inlined SVG/srcdoc content (invalid
    # there — the browser hoists them out and the figure loses its labels).
    body = _apply_glossary(body, glossary)
    body = IFRAME_RE.sub(lambda m: _inline_iframe(m, deck_dir), body)
    body = IMG_RE.sub(lambda m: _inline_img(m, deck_dir), body)
    m = H1_RE.search(body)
    title = re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else path.stem
    return body, notes, title


THEME = """
:root { --bg:#ffffff; --ink:#1a1a2e; --accent:#2f6f4f; --muted:#667;
        --slide-w:960px; --slide-h:540px; }
* { box-sizing:border-box; margin:0; }
body { background:#e9ebee; color:var(--ink);
       font:16px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif; }
.slide { width:var(--slide-w); min-height:var(--slide-h); margin:24px auto 8px;
         background:var(--bg); padding:40px 56px 56px; position:relative;
         box-shadow:0 2px 10px rgba(0,0,0,.18); display:flow-root; }
.slide h1 { font-size:34px; color:var(--accent); margin-bottom:18px; }
.slide h2 { font-size:22px; margin:14px 0 8px; }
.slide ul, .slide ol { margin:8px 0 8px 26px; }
.slide li { margin:4px 0; }
.slide p { margin:8px 0; }
.slide table { border-collapse:collapse; margin:10px 0; }
.slide th, .slide td { border:1px solid #ccd; padding:4px 10px; text-align:left; }
.slide code { background:#f0f2f5; padding:1px 5px; border-radius:3px;
              font-size:.92em; }
.slide pre { background:#f0f2f5; padding:10px 14px; border-radius:6px;
             overflow-x:auto; margin:8px 0; }
.slide pre code { background:none; padding:0; }
.slide svg { max-width:100%; height:auto; display:block; margin:10px auto; }
img { max-width:100%; }
iframe.anim { width:100%; height:380px; border:1px solid #ccd; }
.gl { border-bottom:1px dotted var(--accent); cursor:help; }
.foot { position:absolute; bottom:14px; left:56px; right:56px;
        display:flex; justify-content:space-between;
        font-size:11px; color:var(--muted); }
.notes { width:var(--slide-w); margin:0 auto 26px; padding:10px 56px;
         font-size:14px; color:#334; background:#f6f7f3;
         border-left:4px solid var(--accent); }
.notes:before { content:"speaker notes"; display:block; font-size:10px;
                text-transform:uppercase; letter-spacing:.1em; color:var(--muted); }
.grouphead { width:var(--slide-w); margin:30px auto 0; font-size:12px;
             text-transform:uppercase; letter-spacing:.12em; color:var(--muted); }
body.present { background:#000; }
body.present .notes, body.present .grouphead { display:none; }
body.present .slide { display:none; margin:0 auto; }
body.present .slide.on { display:flow-root; transform-origin:top center; }
@media print { body { background:#fff; }
  .notes, .grouphead { display:none; }
  .slide { box-shadow:none; page-break-after:always; margin:0 auto; } }
"""

JS = """
(function(){
  var slides=[].slice.call(document.querySelectorAll('.slide')), cur=0;
  function show(i){ cur=(i+slides.length)%slides.length;
    slides.forEach(function(s,j){ s.classList.toggle('on', j===cur); });
    if(document.body.classList.contains('present')) fit();
    else slides[cur].scrollIntoView({behavior:'smooth'}); }
  function fit(){ var s=slides[cur],
    k=Math.min(innerWidth/s.offsetWidth, innerHeight/s.offsetHeight);
    s.style.transform='scale('+k+')'; }
  addEventListener('keydown', function(e){
    if(e.key==='p'||e.key==='P'){ document.body.classList.toggle('present');
      slides[cur].style.transform=''; show(cur); }
    else if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown') show(cur+1);
    else if(e.key==='ArrowLeft'||e.key==='PageUp') show(cur-1);
    else if(e.key==='Home') show(0);
    else if(e.key==='End') show(slides.length-1); });
  addEventListener('resize', function(){
    if(document.body.classList.contains('present')) fit(); });
  show(0);
})();
"""


def build(deck_dir, send=False):
    deck_dir = pathlib.Path(deck_dir).resolve()
    mpath = deck_dir / 'deck.json'
    if not mpath.exists():
        sys.exit(f"build_deck FAIL: no deck.json in {deck_dir}")
    manifest = json.loads(mpath.read_text(encoding='utf-8'))
    glossary = {}
    if manifest.get('glossary'):
        glossary = json.loads((deck_dir / manifest['glossary']).read_text(encoding='utf-8'))
    theme_extra = ''
    if manifest.get('theme') and (deck_dir / manifest['theme']).exists():
        theme_extra = (deck_dir / manifest['theme']).read_text(encoding='utf-8')

    entries = _slide_entries(manifest)
    if send:
        entries = [e for e in entries if not e[1]]
    if not entries:
        sys.exit("build_deck FAIL: no slides selected")

    total = len(entries)
    footer = manifest.get('footer', '')
    out_parts, last_group = [], None
    for n, (file, _ro, group) in enumerate(entries, 1):
        body, notes, _title = _render_slide(deck_dir / file, deck_dir, glossary)
        if group != last_group and group:
            out_parts.append(f'<div class="grouphead">{html.escape(group)}</div>')
        last_group = group
        out_parts.append(
            f'<section class="slide" id="s{n}">{body}'
            f'<div class="foot"><span>{html.escape(footer)}</span>'
            f'<span>{n} / {total}</span></div></section>')
        if notes and not send:
            out_parts.append(f'<aside class="notes">{notes}</aside>')

    title = manifest.get('title', 'Deck')
    subtitle = manifest.get('subtitle', '')
    doc = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
           f'<meta name="viewport" content="width=device-width, initial-scale=1">'
           f'<title>{html.escape(title)}'
           + (f' — {html.escape(subtitle)}' if subtitle else '') + '</title>'
           f'<style>{THEME}{theme_extra}</style></head><body>'
           + ''.join(out_parts) + f'<script>{JS}</script></body></html>')

    base = manifest.get('output', 'Deck')
    out = deck_dir / (f'{base}_send.html' if send else f'{base}.html')
    out.write_text(doc, encoding='utf-8')

    externals = EXTERNAL_RE.findall(doc)
    if externals:
        for u in externals[:10]:
            print(f"  external asset: {u}")
        sys.exit(f"build_deck FAIL: {len(externals)} external asset reference(s) — "
                 f"a shipped deck must be fully self-contained")
    if send and ('class="notes"' in doc):
        sys.exit("build_deck FAIL: send build still contains notes markup")
    kb = out.stat().st_size // 1024
    print(f"build_deck OK: {out.name} — {total} slide(s), {kb} KB, "
          f"self-contained{' (send: notes & review-only stripped)' if send else ''}")
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not args:
        sys.exit(__doc__)
    build(args[0], send='--send' in sys.argv)
