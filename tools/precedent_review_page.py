#!/usr/bin/env python3
"""precedent_review_page.py -- the very deep check's session-only review page.

Writes one self-contained HTML page with two lists, for the person who asked
for the check:

  1. Branches they can delete: every remote branch, in this checkout and in
     every practice source it resolves, whose work is already on `main`,
     `staging` or `pre-staging` (or whose commits cancel out), each with a
     link that opens GitHub's branch list filtered to it. Rows a session
     recommends deleting for another reason come from --recommend.
  2. Every active practice, by source: universal first, then this repo's
     own local practices, then the individual set, then each shared set.

WHY A SESSION PAGE AND NEVER A COMMITTED FILE (Morgan, 2026-09-28, strength:
decided). The practice list used to be written into spec/VERY_DEEP_CHECK.md
on every run. That file is public, so the individual and shared sets were
held back from it, and the person never got the list he asked for. The page
carries every source in full precisely because it is shown in the session
only (an Artifact in Claude Code on the web) and never committed, pushed or
linked from a repository. It is written under .precedent/, which every
Precedent repo ignores.

    python3 tools/precedent_review_page.py [--repo PATH] [--out PATH]
        [--recommend FILE.json] [--fetch]

--recommend takes a JSON list of {"repo": "owner/name", "branch": "...",
"why": "..."} rows: branches that still carry commits but should go anyway
(superseded, wrong, landed another way). --fetch refreshes every remote
branch ref first; without it the page reads the refs the clones already
hold, which a very deep check's own branch scan has just fetched.
"""
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
    return by_source, groups


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


def render(by_source, groups, recommend=(), day=None):
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
           '<a href="#practices">Active practices</a></nav>',
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
    out.append(f'</section></div><script>{SCRIPT}</script>')
    return '\n'.join(out) + '\n'


def write(repo_root, out=None, recommend=(), fetch=False, day=None):
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
    by_source, groups = collect(repo_root, fetch=fetch)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(by_source, groups, recommend, day), encoding='utf-8')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--repo', default=str(ROOT))
    ap.add_argument('--out')
    ap.add_argument('--recommend')
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--day')
    a = ap.parse_args(argv)
    rec = json.loads(pathlib.Path(a.recommend).read_text(encoding='utf-8')) \
        if a.recommend else []
    path = write(a.repo, a.out, rec, a.fetch, a.day)
    print(f'precedent_review_page: wrote {path} -- show it in the session '
          f'only (an Artifact in Claude Code on the web); never commit, push '
          f'or link it.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
