#!/usr/bin/env python3
"""The very deep check's session-only page: branches to delete, with a link each, and every active practice by source

precedent_review_page.py -- the very deep check's session-only review page.

Writes one self-contained HTML page with two lists, for the person who asked
for the check:

  1. Branches they can delete: every remote branch, in this checkout and in
     every practice source it resolves, whose work is already on `main`,
     `staging` or `pre-staging` (or whose commits cancel out), each with a
     link that opens GitHub's branch list filtered to it. Rows a session
     recommends deleting for another reason come from --recommend.
  2. Every active practice, by source: universal first, then this repo's
     own local practices, then the individual set, then each shared set.
  3. Practices that may overlap: pairs whose wording reads alike, across
     every source and within each one, each marked "same slug", "different
     sources" or "same source", with the session's verdict beside it --
     merge them (and where), or keep both and why.

WHY PART 3 (Morgan, 2026-09-29, strength: decided): two sources can each
carry the same rule without either one's own check noticing, because the
two copies never sit in the same file to compare -- and inside one source,
two rules can say nearly the same thing in different words. Wording alone
also matches rules that do different jobs (two rules about links), so the
script only proposes pairs; the session judges each one and passes its
verdicts through --verdicts, and a pair judged different stays on the page
with its reason so nobody has to judge it twice.

WHY A SESSION PAGE AND NEVER A COMMITTED FILE (Morgan, 2026-09-28, strength:
decided). The practice list used to be written into spec/VERY_DEEP_CHECK.md
on every run. That file is public, so the individual and shared sets were
held back from it, and the person never got the list he asked for. The page
carries every source in full precisely because it is shown in the session
only (an Artifact in Claude Code on the web) and never committed, pushed or
linked from a repository. It is written under .precedent/, which every
Precedent repo ignores.

    python3 tools/precedent_review_page.py [--repo PATH] [--out PATH]
        [--recommend FILE.json] [--verdicts FILE.json] [--fetch]
    python3 tools/precedent_review_page.py --similar   # the pairs, as JSON

--recommend takes a JSON list of {"repo": "owner/name", "branch": "...",
"why": "..."} rows: branches that still carry commits but should go anyway
(superseded, wrong, landed another way). --fetch refreshes every remote
branch ref first; without it the page reads the refs the clones already
hold, which a very deep check's own branch scan has just fetched.
--verdicts takes a JSON list of {"a": "SOURCE:SLUG", "b": "SOURCE:SLUG",
"verdict": "..."} rows for the pairs --similar printed.
"""
import collections
import math
import argparse
import html
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))

DEFAULT_OUT = pathlib.Path('.precedent') / 'very-deep-check-review.html'
# Never offered for deletion: the tiers, staging's old name, and the two
# branches Promote and the push-check receipts live on
# (practice: branch-delete-links, "Never a tier branch").
KEEP = {'HEAD', 'main', 'staging', 'pre-staging', 'precedent-beta-v01',
        'precedent-promote-lock', 'precedent-check-receipts'}
BASES = ('main', 'staging', 'pre-staging')
LEVEL_ORDER = {'universal': 0, 'repo-local': 1, 'individual': 2, 'shared': 3}
LEVEL_LABEL = {'universal': 'Universal', 'repo-local': 'This repo only',
               'individual': 'Individual', 'shared': 'Shared'}


def _git(repo, *args):
    r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                       text=True)
    return r.returncode, r.stdout.strip()


def github_slug(repo):
    """-> 'owner/name' from the clone's origin URL, or None."""
    rc, url = _git(repo, 'remote', 'get-url', 'origin')
    if rc != 0 or not url:
        return None
    url = re.sub(r'\.git$', '', url.rstrip('/'))
    parts = re.split(r'[/:]', url)
    return '/'.join(parts[-2:]) if len(parts) >= 2 else None


def landed_branches(repo, fetch=False):
    """-> [(branch, last commit date)] for every remote branch whose commits
    are all already on one of BASES (by patch, so a squash or cherry-pick
    counts), or whose net diff against the first base is empty."""
    if fetch:
        _git(repo, 'fetch', '--quiet', 'origin',
             '+refs/heads/*:refs/remotes/origin/*')
    bases = [f'origin/{b}' for b in BASES
             if _git(repo, 'rev-parse', '--verify', '-q', f'origin/{b}')[0] == 0]
    if not bases:
        return []
    rc, refs = _git(repo, 'for-each-ref', '--format=%(refname:short)',
                    'refs/remotes/origin')
    out = []
    for ref in refs.splitlines() if rc == 0 else []:
        name = ref[len('origin/'):]
        if not ref.startswith('origin/') or name in KEEP:
            continue
        unlanded = None
        for b in bases:
            _rc, cherry = _git(repo, 'cherry', b, ref)
            mine = {l[2:] for l in cherry.splitlines() if l.startswith('+')}
            unlanded = mine if unlanded is None else unlanded & mine
        landed = not unlanded
        if not landed:
            landed = subprocess.run(
                ['git', '-C', str(repo), 'diff', '--quiet',
                 f'{bases[0]}...{ref}'], capture_output=True).returncode == 0
        if landed:
            out.append((name, _git(repo, 'log', '-1', '--format=%cs', ref)[1]))
    return sorted(out)


def delete_link(slug, branch):
    return (f'https://github.com/{slug}/branches/all?query='
            f'{urllib.parse.quote(branch, safe="")}')


def collect(repo_root, fetch=False):
    """-> (sources, branch_groups) for the page, in the order it shows them."""
    import very_deep_check as vdc
    data = vdc.enumerate_scope(repo_root)
    sources = sorted(data['sources'],
                     key=lambda s: (LEVEL_ORDER.get(s['level'], 9), s['name']))
    rows = vdc._practice_catalogue_rows(sources)
    by_source = []
    for s in sources:
        repo = pathlib.Path(s['path'])
        top = _git(repo, 'rev-parse', '--show-toplevel')[1] or str(repo)
        slug = github_slug(top)
        prefix = pathlib.Path(s['path']).resolve().relative_to(
            pathlib.Path(top).resolve()).as_posix()
        prefix = '' if prefix == '.' else prefix + '/'
        practices = [(p, c) for _lvl, name, p, c in rows if name == s['name']]
        by_source.append({'name': s['name'], 'level': s['level'], 'slug': slug,
                          'prefix': prefix, 'practices': practices})
    seen, groups = set(), []
    for s in sources:
        top = _git(pathlib.Path(s['path']), 'rev-parse', '--show-toplevel')[1]
        if not top or top in seen:
            continue
        seen.add(top)
        groups.append({'slug': github_slug(top) or pathlib.Path(top).name,
                       'branches': landed_branches(top, fetch=fetch)})
    return by_source, groups, similar_pairs(sources)


# ---- part 3: practices that may overlap ------------------------------------
SIMILAR_THRESHOLD = 0.33   # tuned 2026-09-29 on the five real catalogues:
SIMILAR_LIMIT = 30         # every pair above it was worth a look; few below
_STOP = set("""the a an and or of to in on for is it its be by as at this that
with from not no any every each one two when what which who are was were has
have had do does did can may must should will would never only also than then
so if but into out about their there them they you your our we us me my his
her all more most other such same own just very too how why where while been
being these those itself here""".split())


def _words(text):
    out = []
    for w in re.findall(r"[a-z][a-z\-]{2,}", text.lower()):
        if w in _STOP:
            continue
        out.append(re.sub(r"(ing|ed|es|s)$", "", w) if len(w) > 5 else w)
    return out


def _practice_texts(sources):
    """-> [(source name, level, slug, text)] for every in-force practice:
    its slug, title, occasion, one-line summary and Rule -- the parts that
    say what a practice asks for, not its history."""
    import build_views as bv
    out = []
    for s in sources:
        pdir = pathlib.Path(s['path']) / 'practices'
        if not pdir.is_dir():
            continue
        for fm, sections, f in bv.load_practices(pdir, announce=False):
            slug = bv._json_str(fm.get('slug', '')) or f.stem
            rule = sections.get('Rule', '') if isinstance(sections, dict) else ''
            text = ' '.join([slug.replace('-', ' '),
                             bv._json_str(fm.get('title', '')),
                             bv._json_str(fm.get('occasion', '')),
                             bv._index_clause(fm, sections) or '', rule])
            out.append((s['name'], s['level'], slug, text))
    return out


def similar_pairs(sources, threshold=SIMILAR_THRESHOLD, limit=SIMILAR_LIMIT):
    """-> [{score, kind, a: {source, level, slug}, b: {...}}], most alike
    first. TF-IDF cosine over each practice's words: a word every practice
    uses weighs nothing, one only two practices share weighs a lot. A slug
    that appears in two sources is always listed, whatever its score: that
    is the same rule twice by construction."""
    docs = _practice_texts(sources)
    bags = [collections.Counter(_words(t)) for *_x, t in docs]
    df = collections.Counter(w for b in bags for w in b)
    n = len(docs) or 1
    vecs = []
    for b in bags:
        v = {w: (1 + math.log(c)) * math.log(n / df[w]) for w, c in b.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({w: x / norm for w, x in v.items()})
    pairs = []
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            a, b = vecs[i], vecs[j]
            if len(a) > len(b):
                a, b = b, a
            score = sum(x * b.get(w, 0.0) for w, x in a.items())
            same_slug = docs[i][2] == docs[j][2]
            if score < threshold and not same_slug:
                continue
            kind = ('same slug' if same_slug else 'same source'
                    if docs[i][0] == docs[j][0] else 'different sources')
            pairs.append({'score': round(score, 2), 'kind': kind,
                          'a': dict(zip(('source', 'level', 'slug'), docs[i][:3])),
                          'b': dict(zip(('source', 'level', 'slug'), docs[j][:3]))})
    pairs.sort(key=lambda p: (p['kind'] != 'same slug', -p['score']))
    return pairs[:limit]


def _pair_key(p):
    return frozenset((f"{p['a']['source']}:{p['a']['slug']}",
                      f"{p['b']['source']}:{p['b']['slug']}"))


CSS = """
:root{--bg:#F5F7F8;--surface:#FFFFFF;--ink:#1A2230;--muted:#5A6474;
--line:#DCE2E6;--accent:#0E6B66;--accent-soft:#E3F1EF;--danger:#A8322D;
--danger-soft:#FBEAE8;}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
--bg:#12171C;--surface:#1A2128;--ink:#E4E9EE;--muted:#98A3AF;--line:#2C3640;
--accent:#5CC3BA;--accent-soft:#17312F;--danger:#F08A82;--danger-soft:#3A1D1B;
color-scheme:dark;}}
:root[data-theme="dark"]{--bg:#12171C;--surface:#1A2128;--ink:#E4E9EE;
--muted:#98A3AF;--line:#2C3640;--accent:#5CC3BA;--accent-soft:#17312F;
--danger:#F08A82;--danger-soft:#3A1D1B;color-scheme:dark;}
body{background:var(--bg);color:var(--ink);font:15px/1.55 "IBM Plex Sans",
system-ui,-apple-system,"Segoe UI",sans-serif;}
.wrap{max-width:980px;margin:0 auto;padding-inline:16px;padding-block:28px 64px;}
h1{font-size:1.7rem;line-height:1.2;margin:0 0 6px;text-wrap:balance;}
h2{font-size:1.25rem;margin:0 0 4px;text-wrap:balance;}
h3{font-size:1rem;margin:0;display:flex;gap:10px;align-items:baseline;
flex-wrap:wrap;}
p{margin:0;max-width:68ch;}
.lede{color:var(--muted);}
.mono,code{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
font-size:.88em;}
nav.jump{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 28px;}
nav.jump a{color:var(--accent);background:var(--accent-soft);padding:4px 12px;
border-radius:999px;text-decoration:none;font-weight:500;}
nav.jump a:focus-visible,a:focus-visible,input:focus-visible{outline:2px solid
var(--accent);outline-offset:2px;}
section.part{display:grid;gap:18px;margin-bottom:44px;}
.group{background:var(--surface);border:1px solid var(--line);border-radius:8px;
overflow:hidden;}
.group header{padding:12px 16px;border-bottom:1px solid var(--line);display:grid;
gap:2px;}
.tag{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;
color:var(--muted);font-weight:600;}
.count{color:var(--muted);font-size:.85rem;font-weight:400;}
ul.rows{list-style:none;margin:0;padding:0;}
ul.rows li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 16px;
align-items:baseline;padding:9px 16px;border-top:1px solid var(--line);}
ul.rows li:first-child{border-top:0;}
ul.rows li .name{overflow-wrap:anywhere;}
ul.rows li .note{grid-column:1/-1;color:var(--muted);font-size:.9rem;}
.date{color:var(--muted);font-variant-numeric:tabular-nums;font-size:.85rem;}
a.del{color:var(--danger);background:var(--danger-soft);text-decoration:none;
padding:2px 10px;border-radius:6px;font-size:.85rem;white-space:nowrap;}
a.del:hover{text-decoration:underline;}
ul.practices li{grid-template-columns:minmax(0,15rem) minmax(0,1fr);}
ul.practices a{color:var(--accent);text-decoration:none;overflow-wrap:anywhere;}
ul.practices a:hover{text-decoration:underline;}
.empty{padding:12px 16px;color:var(--muted);}
.filter{display:flex;gap:10px;align-items:center;flex-wrap:wrap;}
.filter input{font:inherit;padding:7px 10px;border:1px solid var(--line);
border-radius:6px;background:var(--surface);color:var(--ink);width:min(100%,22rem);}
.callout{background:var(--accent-soft);border-radius:8px;padding:12px 16px;}
.score{color:var(--muted);font-variant-numeric:tabular-nums;font-size:.85rem;
white-space:nowrap;}
.verdict{grid-column:1/-1;font-size:.9rem;}
.verdict.open{color:var(--muted);font-style:italic;}
@media (max-width:560px){ul.practices li{grid-template-columns:minmax(0,1fr);}}
"""

SCRIPT = """
(function(){
  var box=document.getElementById('practice-filter');
  if(!box)return;
  box.addEventListener('input',function(){
    var q=box.value.trim().toLowerCase();
    document.querySelectorAll('ul.practices li').forEach(function(li){
      li.hidden=q&&li.textContent.toLowerCase().indexOf(q)<0;
    });
    document.querySelectorAll('#practices .group').forEach(function(g){
      var any=g.querySelector('ul.practices li:not([hidden])');
      g.hidden=q&&!any;
    });
  });
})();
"""


def render(by_source, groups, recommend=(), day=None, pairs=(), verdicts=()):
    e = html.escape
    # A recommended branch that has since landed is listed once, as landed.
    landed = {(g['slug'], b) for g in groups for b, _d in g['branches']}
    recommend = [r for r in recommend if (r['repo'], r['branch']) not in landed]
    n_landed = sum(len(g['branches']) for g in groups)
    n_prac = sum(len(s['practices']) for s in by_source)
    out = ['<title>Branch and Practice Review</title>',
           '<link rel="preconnect" href="https://fonts.googleapis.com">',
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
           'family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;'
           '500;600;700&display=swap">',
           f'<style>{CSS}</style>', '<div class="wrap">',
           '<h1>Branch and Practice Review</h1>',
           f'<p class="lede">From the very deep check{" of " + e(day) if day else ""}. '
           f'{n_landed + len(recommend)} branches you can delete, and '
           f'{n_prac} active practices across {len(by_source)} sources. '
           'This page is for this session only; it is never committed.</p>',
           '<nav class="jump"><a href="#branches">Branches to delete</a>'
           '<a href="#practices">Active practices</a>'
           '<a href="#overlap">May overlap</a></nav>',
           '<section class="part" id="branches"><div><h2>Branches you can '
           'delete</h2><p class="lede">Each link opens GitHub\'s branch list '
           'filtered to that one branch; delete it with the trash icon on its '
           'row. Afterwards the page says "no branches matched". That means it '
           'worked.</p></div>']
    if recommend:
        out.append('<div class="group"><header><span class="tag">Recommended'
                   '</span><h3>Still carrying commits, but safe to delete'
                   f'<span class="count">{len(recommend)}</span></h3></header>'
                   '<ul class="rows">')
        for r in recommend:
            out.append(f'<li><span class="name mono">{e(r["repo"])} · '
                       f'{e(r["branch"])}</span><a class="del" href="'
                       f'{e(delete_link(r["repo"], r["branch"]))}">Open to '
                       f'delete</a><span class="note">{e(r["why"])}</span></li>')
        out.append('</ul></div>')
    for g in groups:
        out.append('<div class="group"><header><span class="tag">Fully landed'
                   f'</span><h3><span class="mono">{e(g["slug"])}</span>'
                   f'<span class="count">{len(g["branches"])}</span></h3>'
                   '</header>')
        if not g['branches']:
            out.append('<p class="empty">Nothing to delete here.</p></div>')
            continue
        out.append('<ul class="rows">')
        for b, date in g['branches']:
            out.append(f'<li><span class="name mono">{e(b)} <span class="date">'
                       f'{e(date)}</span></span><a class="del" href="'
                       f'{e(delete_link(g["slug"], b))}">Open to delete</a></li>')
        out.append('</ul></div>')
    out.append('</section><section class="part" id="practices"><div><h2>'
               'Active practices</h2><p class="lede">Every practice in force, '
               'by source: universal first, then this repo\'s own, then your '
               'individual set, then each shared set. Each sentence is the '
               'practice\'s own one-line summary.</p></div><div class="filter">'
               '<label for="practice-filter">Filter</label><input '
               'id="practice-filter" type="search" placeholder="a slug or a '
               'word"></div>')
    for s in by_source:
        out.append('<div class="group"><header><span class="tag">'
                   f'{e(LEVEL_LABEL.get(s["level"], s["level"]))}</span><h3>'
                   f'<span class="mono">{e(s["name"])}</span><span class="count">'
                   f'{len(s["practices"])}</span></h3></header>')
        if not s['practices']:
            out.append('<p class="empty">No active practices.</p></div>')
            continue
        out.append('<ul class="rows practices">')
        for slug, clause in s['practices']:
            name = f'<span class="mono">{e(slug)}</span>'
            if s['slug']:
                url = (f'https://github.com/{s["slug"]}/blob/main/'
                       f'{s["prefix"]}practices/{urllib.parse.quote(slug)}.md')
                name = f'<a class="mono" href="{e(url)}">{e(slug)}</a>'
            out.append(f'<li>{name}<span>{e(clause)}</span></li>')
        out.append('</ul></div>')
    out.append('</section>')
    out.extend(_render_pairs(by_source, pairs, verdicts))
    out.append(f'</div><script>{SCRIPT}</script>')
    return '\n'.join(out) + '\n'


def _practice_link(by_source, side):
    e = html.escape
    src = next((s for s in by_source if s['name'] == side['source']), None)
    label = f"{side['slug']} ({side['source']})"
    if src and src['slug']:
        url = (f"https://github.com/{src['slug']}/blob/main/{src['prefix']}"
               f"practices/{urllib.parse.quote(side['slug'])}.md")
        return f'<a class="mono" href="{e(url)}">{e(label)}</a>'
    return f'<span class="mono">{e(label)}</span>'


def _render_pairs(by_source, pairs, verdicts):
    e = html.escape
    judged = {frozenset((v['a'], v['b'])): v['verdict'] for v in verdicts}
    out = ['<section class="part" id="overlap"><div><h2>Practices that may '
           'overlap</h2><p class="lede">Pairs whose wording reads alike, in '
           'different sources and within one. A script finds them; the verdict '
           'beside each is the session\'s: merge them, and where, or keep both '
           'and why. Wording alone also matches rules that do different jobs, '
           'so a pair here is a question, not a finding.</p></div>']
    groups = (('same slug', 'The same practice in two sources'),
              ('different sources', 'Alike, in different sources'),
              ('same source', 'Alike, within one source'))
    for kind, title in groups:
        rows = [p for p in pairs if p['kind'] == kind]
        if not rows:
            continue
        out.append(f'<div class="group"><header><span class="tag">{e(kind)}'
                   f'</span><h3>{e(title)}<span class="count">{len(rows)}'
                   '</span></h3></header><ul class="rows">')
        for p in rows:
            v = judged.get(_pair_key(p))
            verdict = (f'<span class="verdict">{e(v)}</span>' if v else
                       '<span class="verdict open">Not judged yet.</span>')
            out.append(f'<li><span class="name">{_practice_link(by_source, p["a"])}'
                       f' and {_practice_link(by_source, p["b"])}</span>'
                       f'<span class="score">{p["score"]:.2f} alike</span>'
                       f'{verdict}</li>')
        out.append('</ul></div>')
    if not pairs:
        out.append('<p class="empty">No two practices read alike enough to '
                   'list.</p>')
    out.append('</section>')
    return out


def write(repo_root, out=None, recommend=(), fetch=False, day=None,
          verdicts=()):
    """Write the page; -> its path. Refuses a path git would track."""
    repo_root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(out) if out else repo_root / DEFAULT_OUT
    if not out.is_absolute():
        out = repo_root / out
    rc, _ = _git(repo_root, 'check-ignore', '-q', str(out))
    inside = str(out.resolve()).startswith(str(repo_root) + '/')
    if inside and rc != 0:
        raise SystemExit(f'precedent_review_page: refusing {out} -- git would '
                         f'track it, and this page carries private practice '
                         f'text. Write it under .precedent/ or outside the repo.')
    by_source, groups, pairs = collect(repo_root, fetch=fetch)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(by_source, groups, recommend, day, pairs, verdicts),
                   encoding='utf-8')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--repo', default=str(ROOT))
    ap.add_argument('--out')
    ap.add_argument('--recommend')
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--day')
    ap.add_argument('--verdicts')
    ap.add_argument('--similar', action='store_true',
                    help='print the practice pairs that may overlap, as JSON, '
                         'for the session to judge; writes nothing')
    a = ap.parse_args(argv)
    if a.similar:
        import very_deep_check as vdc
        data = vdc.enumerate_scope(pathlib.Path(a.repo).resolve())
        print(json.dumps(similar_pairs(data['sources']), indent=1))
        return 0
    rec = json.loads(pathlib.Path(a.recommend).read_text(encoding='utf-8')) \
        if a.recommend else []
    ver = json.loads(pathlib.Path(a.verdicts).read_text(encoding='utf-8')) \
        if a.verdicts else []
    path = write(a.repo, a.out, rec, a.fetch, a.day, ver)
    print(f'precedent_review_page: wrote {path} -- show it in the session '
          f'only (an Artifact in Claude Code on the web); never commit, push '
          f'or link it.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
