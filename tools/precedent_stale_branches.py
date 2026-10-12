"""precedent_stale_branches.py -- the remote branches you can delete, across
every repository open in this session: each one already in `main`, so
deleting it loses nothing.

    python3 tools/precedent_stale_branches.py                 # list them
    python3 tools/precedent_stale_branches.py --count         # one number
    python3 tools/precedent_stale_branches.py --fetch         # fetch --prune first
    python3 tools/precedent_stale_branches.py --html OUT.html # the page to publish
    python3 tools/precedent_stale_branches.py --html OUT.html --merge SAVED.html
    python3 tools/precedent_stale_branches.py --html OUT.html --replace
    python3 tools/precedent_stale_branches.py --page-url      # the person's saved page

A branch is STALE when its tip is already in `origin/main`, or when it carries
no change `main` lacks (a Promote's fix branch or copy of staging whose merge commits
changed nothing). NEVER LISTED, whatever their state: `main`, `staging`,
`pre-staging`, staging's old name `precedent-beta-v01`, and the engine's own
branches (`precedent-check-receipts`, `precedent-promote-lock`) and any
branch starting `data-`, the ladder's name for a live record
(precedent_data_branches.py, 2026-10-11) -- Morgan,
2026-10-05: "(And never pre-staging or staging)". ONE EXCEPTION, 2026-10-09:
for a person who lands straight on staging, `pre-staging` is retired, and once
it holds nothing staging lacks it is listed like any finished branch
(precedent_branches.never_offered; Morgan: "telling he can delete
pre-staging"). Staging and main are never listed, for anyone.

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

ONE PAGE, UPDATED IN PLACE (2026-10-11). The person keeps one pinned
cleanup page rather than a new link from every session: its address is
`branch_cleanup_page` in their identity.json (precedent_identity), and
`--html` prints it, so the session republishes to that address. With none
saved, it says to publish a new page and save the address there. The page
says when it was built, in the person's own timezone, since between closes
it shows the last one's list; and its ticks belong to that build, so a
refreshed list starts unticked -- a branch still on it was not deleted.
Morgan, 2026-10-11: "Let's do this" (strength: decided).

THE SAVED PAGE IS MERGED, NEVER OVERWRITTEN (2026-10-12). This tool sees
only the clones on this machine, so a session with fewer repositories open
than the last one would wipe the rows that one listed. With a saved page,
`--html` writes nothing until it is handed that page as it stands --
`--merge FILE` (in Claude Code, the file the Artifact tool's read saves
with path index.html) -- or told
`--replace`, for a saved page that is gone or cannot be read. Merged, a
repository this run checked gets its fresh rows, or none if nothing in it
is deletable any more; one it did not check keeps the rows last listed,
under the date they were checked, since a branch there may have gone since.
The page carries its list as JSON for the next merge to read; a page built
before that is read from its sections. Reported by a consuming repository's
Update Vendors, 2026-10-12: "a session with fewer repos wipes the entries a
wider session listed. Merge them".
"""
import datetime
import html
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

# The file name the closing Boildown is told to write the page to, inside
# the session's scratch folder. Named once: the reply gate's instruction
# reads it, and so does precedent_container_safe.py, which skips this file
# when it looks for work left in a scratch folder -- the page is published
# as an artifact the moment it is built, so it is never work at risk.
PAGE_FILENAME = 'branch-cleanup.html'

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

NEVER = {'main', 'master', 'staging', 'pre-staging', 'precedent-beta-v01',
         'precedent-check-receipts', 'precedent-promote-lock', 'HEAD'}
DATA_PREFIX = 'data-'
_GH = re.compile(r'github\.com[:/]+([^/]+)/([^/\s]+?)(?:\.git)?/*$')


def _git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args],
                          capture_output=True, text=True)


def _slug(repo):
    r = _git(repo, 'remote', 'get-url', 'origin')
    m = _GH.search(r.stdout.strip()) if r.returncode == 0 else None
    return (m.group(1), m.group(2)) if m else None


def _same_place(repo):
    """-> a key equal for every path that reaches the same directory: its
    device and inode, which a case-insensitive filesystem and a symbolic
    link both share, else the resolved path."""
    try:
        st = pathlib.Path(repo).stat()
        return ('inode', st.st_dev, st.st_ino)
    except OSError:
        return ('path', str(pathlib.Path(repo).resolve()))


def _repos(found=None):
    """-> [(path, (owner, name))], one per repository. ONE REPOSITORY IS
    LISTED ONCE (2026-10-08): GitHub names are case-insensitive, so the key
    is the casefolded (owner, name) and the first spelling seen is the one
    shown; and a path whose real path was already seen -- one clone reached
    as both .../bestpractice and .../BestPractice, or through a link -- is
    skipped before its origin is even read. A consuming repository's session
    saw the same repository listed twice, once per spelling."""
    if found is None:
        try:
            import precedent_container_safe as cs
            found = cs.checkouts()
        except Exception:                                    # noqa: BLE001
            found = [_ENGINE_DIR.parent]
    out, seen, real_seen = [], set(), set()
    for repo in found:
        real = _same_place(repo)
        if real in real_seen:
            continue
        real_seen.add(real)
        slug = _slug(repo)
        if not slug:
            continue
        key = tuple(part.casefold() for part in slug)
        if key not in seen:
            seen.add(key)
            out.append((pathlib.Path(repo), slug))
    return out


def _retired_pre_staging(repo):
    """True when `repo`'s pre-staging is retired for this person and holds
    nothing staging lacks (precedent_branches.never_offered, the one rule).
    False whenever that cannot be read: it then stays never listed."""
    try:
        import precedent_branches as pb
        return pb.PRE_STAGING not in pb.never_offered(repo)
    except Exception:                                        # noqa: BLE001
        return False


_MERGED_PR = re.compile(r'^Merge pull request #(\d+) from [^/\s]+/(\S+)')
_REVERTED_PR = re.compile(r'^Revert (?:pull request #(\d+)|"Merge pull request #(\d+))')
_REVERTS_SHA = re.compile(r'This reverts commit ([0-9a-f]{7,40})')


def reverted_branches(repo, depth=500):
    """-> {branch} whose latest pull-request merge into origin/main was
    reverted there afterwards, by `Revert pull request #N` (what
    precedent_merge_check.py --landed writes), GitHub's `Revert "Merge pull
    request #N ..."`, or git's "This reverts commit <merge>".

    WHY (2026-10-12): the page offered `claude/archive-capture-check` for
    deletion. Its pull request was merged and reverted the same hour, so
    its tip is in main while its work is not -- and the revert tells its
    author to fix the work on that branch and merge again."""
    out = _git(repo, 'log', 'origin/main', '--first-parent', f'-{depth}',
               '--format=%H%x00%s%x00%b%x1e').stdout
    latest_merge, reverted_pr, reverted_sha = {}, {}, {}
    for i, rec in enumerate(r for r in out.split('\x1e') if r.strip()):
        sha, subject, body = (rec.strip('\n').split('\x00') + ['', ''])[:3]
        m = _MERGED_PR.match(subject)
        if m and m.group(2) not in latest_merge:
            latest_merge[m.group(2)] = (i, m.group(1), sha)
        r = _REVERTED_PR.match(subject)
        if r:
            reverted_pr.setdefault(r.group(1) or r.group(2), i)
        for s in _REVERTS_SHA.findall(body):
            reverted_sha.setdefault(s, i)
    gone = set()
    for branch, (i, pr, sha) in latest_merge.items():
        # Newest first: a revert at a smaller index came after the merge.
        if reverted_pr.get(pr, i) < i or any(
                sha.startswith(s) and j < i for s, j in reverted_sha.items()):
            gone.add(branch)
    return gone


def stale_in(repo, fetch=False):
    """-> [(branch, last_commit_date)] for `repo`, or None with no origin/main.
    A branch whose merge main reverted is never listed (reverted_branches)."""
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
    retired = 'pre-staging' in names and _retired_pre_staging(repo)
    reverted = reverted_branches(repo)
    for b in sorted(set(names)):
        if b in reverted:
            continue
        if b == 'pre-staging' and retired:
            # Measured against staging, where its work went, not main.
            date = _git(repo, 'log', '-1', '--format=%cs', f'origin/{b}').stdout.strip()
            out.append((b, date))
            continue
        if b in NEVER or b == 'origin' or b.startswith(DATA_PREFIX):
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


def collect(fetch=False, seen=None):
    """-> ([(owner, name, [(branch, date)])], [notes]). `seen`, a list, gets
    (owner, name) of every repository whose branches were read, the ones
    with nothing to delete included: what a merge replaces."""
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
        if seen is not None:
            seen.append((owner, name))
        if rows:
            groups.append((owner, name, rows))
    return groups, notes


def link(owner, name, branch):
    return (f'https://github.com/{owner}/{name}/branches/all?query='
            + urllib.parse.quote(branch, safe=''))


def _person():
    """-> the declared identity of whoever this session works for, or {}."""
    try:
        import precedent_identity as pid
        return pid.declared_identity(_ENGINE_DIR.parent)
    except Exception:                                        # noqa: BLE001
        return {}


def saved_page(person=None):
    """-> the address of the person's pinned cleanup page, or ''."""
    return ((_person() if person is None else person)
            .get('branch_cleanup_page') or '').strip()


def built_line(now=None, tz=''):
    """-> 'Refreshed 11 Oct 2026, 14:20 Buenos Aires time', in the person's
    zone when it is declared and readable, else UTC."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    zone, label = datetime.timezone.utc, 'UTC'
    if tz:
        try:
            from zoneinfo import ZoneInfo
            zone = ZoneInfo(tz)
            label = tz.rsplit('/', 1)[-1].replace('_', ' ') + ' time'
        except Exception:                                    # noqa: BLE001
            pass
    local = now.astimezone(zone)
    return f'Refreshed {local.day} {local:%b %Y, %H:%M} {label}'


def _key(owner, name):
    return (owner.casefold(), name.casefold())


_DATA = re.compile(r'<script type="application/json" id="branch-data">(.*?)</script>',
                   re.S)
_SECTION = re.compile(r'<section class="repo">.*?<p class="owner">github\.com/'
                      r'([^/<]+)/([^<]+)</p>.*?<ul>(.*?)</ul></section>', re.S)
_ROW = re.compile(r'<a href="[^"]*"[^>]*>([^<]*)</a><span class="date">([^<]*)</span>')
_STAMP = re.compile(r'branch-cleanup-done:(\d{8}T\d{6}Z)')


def read_page(text):
    """-> [{'owner', 'repo', 'checked', 'branches': [[branch, date]]}] from a
    page this tool built: its JSON block, or, on a page built before it
    carried one, its sections, all dated by the page's build stamp. [] for
    anything else."""
    m = _DATA.search(text)
    if m:
        try:
            repos = json.loads(m.group(1)).get('repos') or []
            return [r for r in repos if r.get('owner') and r.get('repo')]
        except (ValueError, AttributeError):
            return []
    stamp = _STAMP.search(text)
    checked = ''
    if stamp:
        checked = (datetime.datetime.strptime(stamp.group(1), '%Y%m%dT%H%M%SZ')
                   .replace(tzinfo=datetime.timezone.utc).isoformat())
    return [{'owner': html.unescape(o), 'repo': html.unescape(n), 'checked': checked,
             'branches': [[html.unescape(b), d] for b, d in _ROW.findall(body)]}
            for o, n, body in _SECTION.findall(text)]


def carried_over(previous, seen):
    """-> [(owner, name, rows, checked)]: the saved page's repositories this
    run did not check, with the rows it last listed for them. A repository
    this run checked is never carried: its fresh rows, or their absence,
    replace the old ones."""
    checked_now = {_key(o, n) for o, n in seen}
    out = []
    for r in previous:
        rows = [(b, d) for b, d in r.get('branches') or []]
        if rows and _key(r['owner'], r['repo']) not in checked_now:
            out.append((r['owner'], r['repo'], rows, r.get('checked') or ''))
    return out


def _section(owner, name, rows, note=''):
    lis = '\n'.join(
        f'<li><label class="row"><input type="checkbox" '
        f'id="{html.escape(name + "/" + b)}" data-k="{html.escape(name + "/" + b)}">'
        f'<a href="{link(owner, name, b)}" target="_blank" rel="noopener">'
        f'{html.escape(b)}</a><span class="date">{html.escape(d)}</span></label></li>'
        for b, d in rows)
    return (f'<section class="repo"><h2>{html.escape(name)} '
            f'<span class="count">{len(rows)}</span></h2>'
            f'<p class="owner">github.com/{html.escape(owner)}/{html.escape(name)}</p>'
            + (f'<p class="carried">{html.escape(note)}</p>' if note else '')
            + f'<ul>{lis}</ul></section>')


def render_html(groups, now=None, tz='', carried=()):
    """`carried`: [(owner, name, rows, checked)] kept from the saved page for
    repositories this run did not check (carried_over), shown after the
    fresh ones under the date they were last checked."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    total = sum(len(r) for *_x, r in groups) + sum(len(c[2]) for c in carried)
    secs = [_section(owner, name, rows) for owner, name, rows in groups]
    for owner, name, rows, checked in carried:
        try:
            when = ', ' + built_line(datetime.datetime.fromisoformat(checked),
                                     tz)[len('Refreshed '):]
        except (TypeError, ValueError):
            when = ''
        secs.append(_section(owner, name, rows,
                             f'Not open in the session that refreshed this page: '
                             f'as listed when last checked{when}. A branch here '
                             f'may already be gone.'))
    data = {'built': now.isoformat(), 'repos': [
        {'owner': o, 'repo': n, 'checked': now.isoformat(),
         'branches': [[b, d] for b, d in rows]} for o, n, rows in groups] + [
        {'owner': o, 'repo': n, 'checked': c, 'branches': [[b, d] for b, d in rows]}
        for o, n, rows, c in carried]}
    # The list the next merge reads (read_page); '<' escaped so no branch
    # name can close the script element.
    secs.append('<script type="application/json" id="branch-data">'
                + json.dumps(data).replace('<', '\\u003c') + '</script>')
    return (_PAGE.replace('{{TOTAL}}', str(total))
            .replace('{{BUILT}}', html.escape(built_line(now, tz)))
            .replace('{{BUILD}}', now.strftime('%Y%m%dT%H%M%SZ'))
            .replace('{{SECTIONS}}', ''.join(secs)))


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
.built { font-family:var(--mono); font-size:.8rem; color:var(--muted); margin:4px 0 0; font-variant-numeric:tabular-nums; }
.bar { position:sticky; top:env(safe-area-inset-top,0px); background:var(--bg); padding-block:10px; border-bottom:1px solid var(--line); display:flex; gap:12px; align-items:center; flex-wrap:wrap; z-index:1; }
.bar .progress { font-variant-numeric:tabular-nums; font-weight:500; }
.bar button { font:inherit; font-size:.85rem; background:none; border:1px solid var(--line); color:var(--muted); border-radius:4px; padding:3px 10px; cursor:pointer; }
.bar button:focus-visible, a:focus-visible, input:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.repo h2 { font-size:1.05rem; font-weight:600; margin:0; display:flex; gap:8px; align-items:baseline; }
.count, .owner { font-family:var(--mono); color:var(--muted); }
.count { font-size:.8rem; font-weight:400; }
.owner { font-size:.78rem; margin:2px 0 10px; }
.carried { font-size:.85rem; color:var(--muted); margin:-4px 0 10px; max-width:62ch; }
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
<p class="built">{{BUILT}}</p>
<p class="lede">{{TOTAL}} branches, all already in <code>main</code> (a retired <code>pre-staging</code>: already in <code>staging</code>), so deleting any of them loses nothing. Each link opens GitHub's branch list filtered to that one branch; delete it with the trash icon there. Never listed: <code>main</code>, <code>staging</code>, <code>pre-staging</code> while it is in use, and the engine's own branches. Ticks are remembered in this browser only, until the list is next refreshed.</p>
</header>
<div class="bar"><span class="progress" id="progress">0 of {{TOTAL}} done</span><button type="button" id="clear">Clear ticks</button></div>
{{SECTIONS}}
</main>
<script>
(function(){
  var boxes=[].slice.call(document.querySelectorAll('input[data-k]'));
  var KEY='branch-cleanup-done:{{BUILD}}', done={};
  try { for(var i=localStorage.length-1;i>=0;i--){ var k=localStorage.key(i); if(k&&k.indexOf('branch-cleanup-done')===0&&k!==KEY) localStorage.removeItem(k); } } catch(e) {}
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
    if '--page-url' in argv:
        url = saved_page()
        print(url or 'none saved: add "branch_cleanup_page" to your identity.json')
        return 0 if url else 1
    seen = []
    groups, notes = collect(fetch='--fetch' in argv, seen=seen)
    total = sum(len(r) for *_x, r in groups)
    if '--count' in argv:
        print(total)
        return 0
    if '--html' in argv:
        out = pathlib.Path(argv[argv.index('--html') + 1])
        person = _person()
        url = saved_page(person)
        carried = []
        if '--merge' in argv:
            prev = pathlib.Path(argv[argv.index('--merge') + 1])
            try:
                previous = read_page(prev.read_text(encoding='utf-8'))
            except OSError as e:
                print(f'Cannot read {prev}: {e}. Nothing written.')
                return 2
            if not previous and '--replace' not in argv:
                print(f'{prev} holds no branch list this tool can read, so '
                      f'merging it would keep nothing. Nothing written: pass '
                      f'the page the saved address holds, or --replace if '
                      f'replacing it is meant.')
                return 2
            carried = carried_over(previous, seen)
        elif url and '--replace' not in argv:
            print(f'Nothing written: the saved page ({url}) may list '
                  f'repositories this session cannot see, and publishing over '
                  f'it would drop them. Save the page as it stands to a file '
                  f'(in Claude Code: the Artifact tool\'s read of that url '
                  f'with path index.html), then run this again adding '
                  f'--merge <that file>. Only if it is gone or unreadable, '
                  f'add --replace instead.')
            return 2
        out.write_text(render_html(groups, tz=person.get('timezone') or '',
                                   carried=carried), encoding='utf-8')
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
        kept = sum(len(c[2]) for c in carried)
        print(f'{total} stale branch(es) written to {out}'
              + (f', and {kept} kept from the saved page for '
                 f'{len(carried)} repositor(ies) this session did not check'
                 if carried else '')
              + ('' if noted else ' (not noted for the publish gate, which '
                 'will refuse it: artifact_publish_gate.py did not load)'))
        print(f'Publish it to the saved page, in place: {url}' if url else
              'No saved page yet: publish it as a new page, then save its '
              'address as "branch_cleanup_page" in the identity.json of your '
              'individual practice source, so the next close updates it.')
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
