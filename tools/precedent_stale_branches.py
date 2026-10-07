"""precedent_stale_branches.py -- the remote branches you can delete, across
every repository open in this session: each one already in `main`, so
deleting it loses nothing.

    python3 tools/precedent_stale_branches.py                 # list them
    python3 tools/precedent_stale_branches.py --count         # one number
    python3 tools/precedent_stale_branches.py --fetch         # fetch --prune first
    python3 tools/precedent_stale_branches.py --html OUT.html # the page to publish

A branch is STALE when its tip is already in `origin/main`, or when it carries
no change `main` lacks (a Promote's fix branch or copy of staging whose merge commits
changed nothing). NEVER LISTED, whatever their state: `main`, `staging`,
`pre-staging`, staging's old name `precedent-beta-v01`, and the engine's own
branches (`precedent-check-receipts`, `precedent-promote-lock`) -- Morgan,
2026-10-05: "(And never pre-staging or staging)".

WHICH REPOSITORIES: every git checkout precedent_container_safe.py finds
(this repo, its siblings, the home directory's clones, declared sources),
with an origin on GitHub, where this session's person is a code owner
(precedent_audience.py). Branch management is a code owner's business; a
repository where you are not one is left out, and the listing says so.

Read-only: it deletes nothing, and never could -- a remote branch is the
person's to delete (practice: never-delete-a-remote-branch). Each row's link
is GitHub's branch list filtered to that one branch, where the trash icon
deletes it (practice: branch-delete-links). The ladder set's
`stale-branch-cleanup` practice puts the page in the closing Boildown.
"""
import html
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

NEVER = {'main', 'master', 'staging', 'pre-staging', 'precedent-beta-v01',
         'precedent-check-receipts', 'precedent-promote-lock', 'HEAD'}
_GH = re.compile(r'github\.com[:/]+([^/]+)/([^/\s]+?)(?:\.git)?/*$')


def _git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args],
                          capture_output=True, text=True)


def _slug(repo):
    r = _git(repo, 'remote', 'get-url', 'origin')
    m = _GH.search(r.stdout.strip()) if r.returncode == 0 else None
    return (m.group(1), m.group(2)) if m else None


def _repos():
    try:
        import precedent_container_safe as cs
        found = cs.checkouts()
    except Exception:                                        # noqa: BLE001
        found = [_ENGINE_DIR.parent]
    out, seen = [], set()
    for repo in found:
        slug = _slug(repo)
        if slug and slug not in seen:
            seen.add(slug)
            out.append((pathlib.Path(repo), slug))
    return out


def stale_in(repo, fetch=False):
    """-> [(branch, last_commit_date)] for `repo`, or None with no origin/main."""
    if fetch:
        _git(repo, 'fetch', '-q', '--prune', 'origin')
    if _git(repo, 'rev-parse', '--verify', '--quiet', 'origin/main').returncode:
        return None
    names = [l.strip()[len('origin/'):] for l in
             _git(repo, 'branch', '-r', '--format=%(refname:short)').stdout.splitlines()
             if l.strip().startswith('origin/')]
    merged = {l.strip()[len('origin/'):] for l in
              _git(repo, 'branch', '-r', '--merged', 'origin/main',
                   '--format=%(refname:short)').stdout.splitlines()}
    out = []
    for b in sorted(set(names)):
        if b in NEVER or b == 'origin':
            continue
        ref = f'origin/{b}'
        if b not in merged:
            # Not an ancestor, but maybe nothing main lacks: a copy whose
            # only commits are merges that changed no file.
            d = _git(repo, 'diff', '--quiet', f'origin/main...{ref}')
            if d.returncode != 0:
                continue
        date = _git(repo, 'log', '-1', '--format=%cs', ref).stdout.strip()
        out.append((b, date))
    return out


def collect(fetch=False):
    """-> ([(owner, name, [(branch, date)])], [notes])."""
    try:
        import precedent_audience as pa
    except ImportError:
        pa = None
    groups, notes = [], []
    for repo, (owner, name) in _repos():
        if pa is not None:
            ok, why = pa.is_code_owner(repo)
            if not ok:
                notes.append(f'{name}: left out -- {why}')
                continue
        rows = stale_in(repo, fetch=fetch)
        if rows is None:
            notes.append(f'{name}: no origin/main to compare against')
            continue
        if rows:
            groups.append((owner, name, rows))
    return groups, notes


def link(owner, name, branch):
    return (f'https://github.com/{owner}/{name}/branches/all?query='
            + urllib.parse.quote(branch, safe=''))


def render_html(groups):
    total = sum(len(r) for *_x, r in groups)
    secs = []
    for owner, name, rows in groups:
        lis = '\n'.join(
            f'<li><label class="row"><input type="checkbox" '
            f'id="{html.escape(name + "/" + b)}" data-k="{html.escape(name + "/" + b)}">'
            f'<a href="{link(owner, name, b)}" target="_blank" rel="noopener">'
            f'{html.escape(b)}</a><span class="date">{d}</span></label></li>'
            for b, d in rows)
        secs.append(f'<section class="repo"><h2>{html.escape(name)} '
                    f'<span class="count">{len(rows)}</span></h2>'
                    f'<p class="owner">github.com/{html.escape(owner)}/{html.escape(name)}</p>'
                    f'<ul>{lis}</ul></section>')
    return _PAGE.replace('{{TOTAL}}', str(total)).replace('{{SECTIONS}}', ''.join(secs))


_PAGE = '''<title>Branch Cleanup</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* Layout: one narrow reading column; a sticky progress line; one section per repository. */
:root { --bg:#f6f7f5; --surface:#ffffff; --fg:#1d2321; --muted:#5f6a66; --line:#dde2df; --accent:#2f6b57; --done:#9aa5a1;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif; --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#141816; --surface:#1b201e; --fg:#e4e9e6; --muted:#9aa6a1; --line:#2c3431; --accent:#7cc3a6; --done:#5d6864; color-scheme:dark; } }
:root[data-theme="dark"] { --bg:#141816; --surface:#1b201e; --fg:#e4e9e6; --muted:#9aa6a1; --line:#2c3431; --accent:#7cc3a6; --done:#5d6864; color-scheme:dark; }
body { background:var(--bg); color:var(--fg); font-family:var(--sans); font-size:15px; line-height:1.5; }
main { max-width:760px; margin:0 auto; padding-inline:16px; padding-block:28px 56px; display:grid; gap:28px; }
h1 { font-size:1.6rem; font-weight:600; margin:0; text-wrap:balance; }
.lede { color:var(--muted); margin:6px 0 0; max-width:62ch; }
.bar { position:sticky; top:env(safe-area-inset-top,0px); background:var(--bg); padding-block:10px; border-bottom:1px solid var(--line); display:flex; gap:12px; align-items:center; flex-wrap:wrap; z-index:1; }
.bar .progress { font-variant-numeric:tabular-nums; font-weight:500; }
.bar button { font:inherit; font-size:.85rem; background:none; border:1px solid var(--line); color:var(--muted); border-radius:4px; padding:3px 10px; cursor:pointer; }
.bar button:focus-visible, a:focus-visible, input:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.repo h2 { font-size:1.05rem; font-weight:600; margin:0; display:flex; gap:8px; align-items:baseline; }
.count, .owner { font-family:var(--mono); color:var(--muted); }
.count { font-size:.8rem; font-weight:400; }
.owner { font-size:.78rem; margin:2px 0 10px; }
ul { list-style:none; margin:0; padding:0; background:var(--surface); border:1px solid var(--line); border-radius:6px; }
li + li { border-top:1px solid var(--line); }
.row { display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:10px; align-items:center; padding:8px 12px; cursor:pointer; }
.row input { accent-color:var(--accent); width:16px; height:16px; margin:0; }
.row a { font-family:var(--mono); font-size:.84rem; color:var(--accent); text-decoration:none; overflow-wrap:anywhere; }
.row a:hover { text-decoration:underline; }
.date { font-family:var(--mono); font-size:.75rem; color:var(--muted); font-variant-numeric:tabular-nums; }
.row:has(input:checked) a { color:var(--done); text-decoration:line-through; }
</style>
<main>
<header>
<h1>Branch cleanup</h1>
<p class="lede">{{TOTAL}} branches, all already in <code>main</code>, so deleting any of them loses nothing. Each link opens GitHub's branch list filtered to that one branch; delete it with the trash icon there. Never listed: <code>main</code>, <code>staging</code>, <code>pre-staging</code> and the engine's own branches. Ticks are remembered in this browser only.</p>
</header>
<div class="bar"><span class="progress" id="progress">0 of {{TOTAL}} done</span><button type="button" id="clear">Clear ticks</button></div>
{{SECTIONS}}
</main>
<script>
(function(){
  var boxes=[].slice.call(document.querySelectorAll('input[data-k]'));
  var KEY='branch-cleanup-done', done={};
  try { done=JSON.parse(localStorage.getItem(KEY)||'{}')||{}; } catch(e) { done={}; }
  function save(){ try { localStorage.setItem(KEY, JSON.stringify(done)); } catch(e) {} }
  function render(){ var n=boxes.filter(function(b){return b.checked;}).length; document.getElementById('progress').textContent=n+' of '+boxes.length+' done'; }
  boxes.forEach(function(b){ b.checked=!!done[b.dataset.k]; b.addEventListener('change',function(){ if(b.checked) done[b.dataset.k]=1; else delete done[b.dataset.k]; save(); render(); }); });
  document.querySelectorAll('.row a').forEach(function(a){ a.addEventListener('click',function(){ var b=a.parentNode.querySelector('input'); if(!b.checked){ b.checked=true; done[b.dataset.k]=1; save(); render(); } }); });
  document.getElementById('clear').addEventListener('click',function(){ done={}; boxes.forEach(function(b){b.checked=false;}); save(); render(); });
  render();
})();
</script>
'''


def main(argv):
    groups, notes = collect(fetch='--fetch' in argv)
    total = sum(len(r) for *_x, r in groups)
    if '--count' in argv:
        print(total)
        return 0
    if '--html' in argv:
        out = pathlib.Path(argv[argv.index('--html') + 1])
        out.write_text(render_html(groups), encoding='utf-8')
        # Noted for the publish gate, which passes a page an engine
        # generator wrote, unedited, within the hour (artifact_publish_gate.py,
        # "ENGINE-REGISTERED GENERATORS"). Without it the page the
        # stale-branch-cleanup practice asks for was refused.
        try:
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
            import artifact_publish_gate
            noted = artifact_publish_gate.record_generated(
                out, 'precedent_stale_branches.py')
        except Exception:                                   # noqa: BLE001
            noted = False
        print(f'{total} stale branch(es) written to {out}'
              + ('' if noted else ' (not noted for the publish gate, which '
                 'will refuse it: artifact_publish_gate.py did not load)'))
        return 0
    if '--json' in argv:
        print(json.dumps({'total': total, 'notes': notes, 'repos': [
            {'owner': o, 'repo': n, 'branches': [
                {'branch': b, 'date': d, 'link': link(o, n, b)} for b, d in rows]}
            for o, n, rows in groups]}, indent=2))
        return 0
    for owner, name, rows in groups:
        print(f'{name} ({len(rows)}):')
        for b, d in rows:
            print(f'  {b}  {d}  {link(owner, name, b)}')
    for n in notes:
        print(f'note: {n}')
    print(f'{total} stale branch(es) across {len(groups)} repositor(ies).')
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
