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
    python3 tools/precedent_stale_branches.py --waiting       # staging that main lacks

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
pre-staging"). Staging and main are never listed, for anyone. A SECOND
EXCEPTION, 2026-10-13: an engine branch's old name is listed once its `data-`
copy is on origin and holds the old branch's whole history. The engine then
reads only the `data-` one, and the old name is checked for nothing but a
fresh claim by a window on an older engine, which would push the branch back
anyway -- so deleting it loses nothing (precedent_data_branches.py).
Reported from an Update Vendors that moved three repositories onto
`data-promote-lock`: each kept `precedent-promote-lock`, and nothing said
whether it was dead or how to remove it.

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
with path index.html, read immediately before the build: never a copy
from earlier in the session, which another session may have republished
over since -- the tool warns when the file looks like one) -- or told
`--replace`, for a saved page that is gone or cannot be read. Merged, a
repository this run checked gets its fresh rows, or none if nothing in it
is deletable any more; one it did not check keeps the rows last listed,
under the date they were checked, since a branch there may have gone since.
The page carries its list as JSON for the next merge to read; a page built
before that is read from its sections. Reported by a consuming repository's
Update Vendors, 2026-10-12: "a session with fewer repos wipes the entries a
wider session listed. Merge them".

THE PAGE SAVES ITS OWN TICKS (2026-10-13). A carried row is one no session
since could check, so a branch the person deleted stayed on the page until a
session that could open that repository came by -- and their ticks lived in
one browser's storage, keyed to the build, so the next refresh minutes later
showed the same list again, unticked. Morgan: "the branch cleanup doc
usually has links that I have already cleaned up within the last hour".
Now a tick (or a click on a row's link, which ticks it) is written into the
page's own JSON, as `done`, and the page saves itself as a new version
through the artifact capability -- published with capabilities
{"artifact": {}}. The next `--merge` reads `done` and leaves a ticked branch
off every CARRIED repository; a repository this run checked is listed fresh
as before, so a stray tick never hides a branch that is still there. Each
build starts `done` empty: what it recorded has been applied. Where the
page cannot save itself (a viewer who cannot edit, a view with no
capability), ticks fall back to this browser's storage, as before. Morgan
chose the page over precedent-individual, 2026-10-13 ("Ahhhh great. Go
ahead.", strength: decided): the page cannot write to a repository, and a
tick only has to last until a session that can check that repository
comes by. A tick made between a session's read of the page and its
republish is lost, and that branch shows once more.

THE PAGE CARRIES ITS FORMAT (2026-10-13). The JSON block records
`format`, the PAGE_FORMAT of the engine that built the page. Handed to
`--merge`, a saved page whose format is newer than this tool's own was
built by a newer engine, whose fields this one may not read, so merging it
could drop what the page holds: the tool refuses, writes nothing, and says
the engine here is older than the page and Update Vendors fixes it. A page
with no `format` predates the field and counts as format 0, accepted.
Reported by a consuming repository, 2026-10-13, after a vendored engine
older than the page's merged it.

WAITING TO GO LIVE (2026-10-16). The page also lists, above the branches,
each repository whose staging tier carries a change main lacks: how many
commits, the date of the oldest, and a link to GitHub's comparison of the
two. Same repositories, same code-owner filter, and merged across sessions
the same way: a repository this run checked gets its fresh row, or none
when it is level, and one it did not check keeps its last row under the
date it was checked. A repository with no staging tier, where main is
staging, has no row. This is what the retired chief-of-staff practice's
Promotion Reviews did on request; Morgan, 2026-10-16, retiring it: "Let's
implement your three suggestion" (strength: decided), the suggestion being
to put the staging check on this page so it comes without being asked and
covers, across sessions, every repository the person works in. A page
carrying a waiting list is format 2, so an engine from before this refuses
to merge it rather than drop the list.
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

# The version of the page's JSON block (`format` in branch-data). Raise it
# whenever the block gains a field an older engine would drop or misread:
# an older engine handed a newer page refuses to merge it (page_format).
PAGE_FORMAT = 2

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


def _moved_data_branches(repo, names):
    """-> {old name} of each engine data branch whose `data-` copy is on
    origin and contains the old branch's tip: nothing reads the old one, and
    deleting it loses nothing. Empty when the names cannot be read."""
    try:
        import precedent_data_branches as pdb
        pairs = {pdb.legacy_name(w): pdb.new_name(w) for w in pdb.LEGACY}
    except Exception:                                        # noqa: BLE001
        return set()
    return {old for old, new in pairs.items()
            if old in names and new in names
            and _git(repo, 'merge-base', '--is-ancestor',
                     f'origin/{old}', f'origin/{new}').returncode == 0}


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
    moved = _moved_data_branches(repo, names)
    for b in sorted(set(names)):
        if b in reverted:
            continue
        if b in moved:
            date = _git(repo, 'log', '-1', '--format=%cs', f'origin/{b}').stdout.strip()
            out.append((b, date))
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


def waiting_in(repo):
    """-> (staging, commits, oldest_date) when `repo`'s staging tier carries
    a change origin/main lacks; None when the two are level, when main is
    staging here, or when either is missing. Reads the remote-tracking refs
    as they stand: fetch first for a current answer."""
    try:
        import precedent_branches as pb
        staging = pb.staging_branch(repo)
    except Exception:                                        # noqa: BLE001
        staging = 'staging'
    if not staging or staging == 'main':
        return None
    lo, hi = 'origin/main', f'origin/{staging}'
    for ref in (lo, hi):
        if _git(repo, 'rev-parse', '--verify', '--quiet', ref).returncode:
            return None
    # Nothing to move when staging changes no file main lacks: a staging
    # that only merged main back in after a Produce is level, not waiting.
    if _git(repo, 'diff', '--quiet', f'{lo}...{hi}').returncode == 0:
        return None
    dates = _git(repo, 'log', '--no-merges', '--format=%cs',
                 f'{lo}..{hi}').stdout.split()
    if not dates:
        dates = _git(repo, 'log', '--format=%cs', f'{lo}..{hi}').stdout.split()
    if not dates:
        return None
    return staging, len(dates), min(dates)


def collect_waiting(fetch=False, seen=None):
    """-> [(owner, name, staging, commits, oldest)] for every repository
    open here, where the person is a code owner, whose staging waits to go
    into main. `seen`, a list, gets (owner, name) of every repository read,
    the level ones included: what a merge replaces."""
    try:
        import precedent_audience as pa
    except ImportError:
        pa = None
    out = []
    for repo, (owner, name) in _repos():
        if pa is not None and not pa.is_code_owner(repo)[0]:
            continue
        if fetch:
            _git(repo, 'fetch', '-q', '--prune', 'origin')
        if _git(repo, 'rev-parse', '--verify', '--quiet', 'origin/main').returncode:
            continue
        if seen is not None:
            seen.append((owner, name))
        row = waiting_in(repo)
        if row:
            out.append((owner, name, *row))
    return out


def compare_link(owner, name, staging):
    return (f'https://github.com/{owner}/{name}/compare/main...'
            + urllib.parse.quote(staging, safe=''))


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


def done_key(name, branch):
    """-> the key a row's tick is saved under: the page's own `data-k`."""
    return f'{name}/{branch}'


def read_done(text):
    """-> {done_key: when ticked} the page saved for itself, {} when it
    carries none (a page built before 2026-10-13, or one never ticked)."""
    m = _DATA.search(text)
    if not m:
        return {}
    try:
        done = json.loads(m.group(1)).get('done') or {}
    except (ValueError, AttributeError):
        return {}
    return {str(k): str(v) for k, v in done.items()} if isinstance(done, dict) else {}


def page_format(text):
    """-> the `format` a saved page's JSON block records: 0 for a page
    without one (built before the field existed, or with no JSON block at
    all), None when the block cannot be read or the value is not a whole
    number."""
    m = _DATA.search(text)
    if not m:
        return 0
    try:
        fmt = json.loads(m.group(1)).get('format', 0)
    except (ValueError, AttributeError):
        return None
    return fmt if isinstance(fmt, int) and not isinstance(fmt, bool) else None


def page_built(text):
    """-> the aware datetime a page's JSON block says it was built, or None
    (no block, or no readable `built`)."""
    m = _DATA.search(text)
    if not m:
        return None
    try:
        when = datetime.datetime.fromisoformat(json.loads(m.group(1))['built'])
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    return when if when.tzinfo else when.replace(tzinfo=datetime.timezone.utc)


# How old a file handed to --merge may be before it is called out as not a
# fresh read. A judgment, not a measurement: a read made just before the
# build is seconds old, and a copy from earlier in the session is usually
# far older than this.
FRESH_READ_MINUTES = 10


def stale_merge_warnings(prev, out, prev_text, now=None):
    """-> the reasons the file handed to --merge looks like something other
    than a read of the saved page made just before this build (2026-10-15:
    a session merged its own earlier copy after another session had
    republished the page, which would have dropped that session's rows and
    the ticks saved since). Warnings, never a refusal: the artifact
    service's conflict check is the backstop, and only the person's page
    knows what is current."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    said = []
    try:
        same = prev.resolve() == out.resolve()
    except OSError:
        same = False
    if same:
        said.append(f'{prev} is the file this tool writes, so it is this '
                    f'session\'s own last build, not the saved page')
    elif out.is_file():
        try:
            ours = page_built(out.read_text(encoding='utf-8'))
        except OSError:
            ours = None
        theirs = page_built(prev_text)
        if ours and theirs and theirs < ours:
            said.append(f'{prev} was built before the page this session '
                        f'last wrote to {out}, so it is an older copy')
    try:
        age = now.timestamp() - prev.stat().st_mtime
    except OSError:
        age = 0
    if age > FRESH_READ_MINUTES * 60:
        said.append(f'{prev} was saved {int(age // 60)} minutes ago')
    return said


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


def carried_over(previous, seen, done=None):
    """-> [(owner, name, rows, checked)]: the saved page's repositories this
    run did not check, with the rows it last listed for them, less any the
    person ticked on the page (`done`, read_done). A repository this run
    checked is never carried: its fresh rows, or their absence, replace the
    old ones."""
    checked_now = {_key(o, n) for o, n in seen}
    done = done or {}
    out = []
    for r in previous:
        rows = [(b, d) for b, d in r.get('branches') or []
                if done_key(r['repo'], b) not in done]
        if rows and _key(r['owner'], r['repo']) not in checked_now:
            out.append((r['owner'], r['repo'], rows, r.get('checked') or ''))
    return out


def read_waiting(text):
    """-> [{'owner', 'repo', 'checked', 'staging', 'commits', 'oldest'}]
    from a page's JSON block; [] for a page from before the list existed."""
    m = _DATA.search(text)
    if not m:
        return []
    try:
        rows = json.loads(m.group(1)).get('waiting') or []
    except (ValueError, AttributeError):
        return []
    return [r for r in rows if isinstance(r, dict) and r.get('owner') and r.get('repo')]


def carried_waiting(previous, seen):
    """-> [(owner, name, staging, commits, oldest, checked)]: the saved
    page's waiting rows for repositories this run did not check."""
    checked_now = {_key(o, n) for o, n in seen}
    return [(r['owner'], r['repo'], r.get('staging') or 'staging',
             int(r.get('commits') or 0), r.get('oldest') or '', r.get('checked') or '')
            for r in previous if _key(r['owner'], r['repo']) not in checked_now]


def is_page(text):
    """True when `text` is a page this tool built: its JSON block reads, or,
    before the block, it carries the build stamp."""
    m = _DATA.search(text)
    if m:
        try:
            return isinstance(json.loads(m.group(1)), dict)
        except ValueError:
            return False
    return bool(_STAMP.search(text) and _SECTION.search(text))


def _waiting_section(waiting, carried, tz):
    if not waiting and not carried:
        return ''
    lis = []
    for owner, name, staging, n, oldest, *rest in [(*w, '') for w in waiting] + list(carried):
        checked = rest[0] if rest else ''
        note = ''
        if checked:
            try:
                note = (' <span class="carried">As of the last check, '
                        + html.escape(built_line(datetime.datetime.fromisoformat(checked),
                                                 tz)[len('Refreshed '):])
                        + '; it may have moved since.</span>')
            except (TypeError, ValueError):
                note = ' <span class="carried">As of an earlier check.</span>'
        lis.append(
            f'<li><div class="wait"><a href="{compare_link(owner, name, staging)}" '
            f'target="_blank" rel="noopener">{html.escape(name)}</a>'
            f'<span>{n} commit{"" if n == 1 else "s"} on <code>{html.escape(staging)}</code> '
            f'that <code>main</code> lacks, oldest from {html.escape(oldest)}.{note}</span>'
            f'</div></li>')
    return ('<section class="waiting"><h2>Waiting to go live '
            f'<span class="count">{len(lis)}</span></h2>'
            '<p class="carried">Say Produce in a session rooted in that repository '
            'to move it into main. Each link opens GitHub\'s comparison of the two.</p>'
            f'<ul>{"".join(lis)}</ul></section>')


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


def render_html(groups, now=None, tz='', carried=(), waiting=(), carried_wait=()):
    """`carried`: [(owner, name, rows, checked)] kept from the saved page for
    repositories this run did not check (carried_over), shown after the
    fresh ones under the date they were last checked. `waiting`:
    [(owner, name, staging, commits, oldest)] from collect_waiting, and
    `carried_wait` the saved page's rows this run did not check
    (carried_waiting), listed first, above the branches."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    total = sum(len(r) for *_x, r in groups) + sum(len(c[2]) for c in carried)
    secs = [_waiting_section(waiting, carried_wait, tz)]
    secs += [_section(owner, name, rows) for owner, name, rows in groups]
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
    data = {'format': PAGE_FORMAT, 'built': now.isoformat(), 'done': {}, 'repos': [
        {'owner': o, 'repo': n, 'checked': now.isoformat(),
         'branches': [[b, d] for b, d in rows]} for o, n, rows in groups] + [
        {'owner': o, 'repo': n, 'checked': c, 'branches': [[b, d] for b, d in rows]}
        for o, n, rows, c in carried], 'waiting': [
        {'owner': o, 'repo': n, 'checked': now.isoformat(), 'staging': st,
         'commits': k, 'oldest': d} for o, n, st, k, d in waiting] + [
        {'owner': o, 'repo': n, 'checked': c, 'staging': st, 'commits': k, 'oldest': d}
        for o, n, st, k, d, c in carried_wait]}
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
.repo h2, .waiting h2 { font-size:1.05rem; font-weight:600; margin:0; display:flex; gap:8px; align-items:baseline; }
.count, .owner { font-family:var(--mono); color:var(--muted); }
.count { font-size:.8rem; font-weight:400; }
.owner { font-size:.78rem; margin:2px 0 10px; }
.carried { font-size:.85rem; color:var(--muted); margin:-4px 0 10px; max-width:62ch; }
.waiting .carried { margin:2px 0 10px; }
.wait { display:grid; gap:2px; padding:8px 12px; }
.wait a { font-weight:600; color:var(--accent); text-decoration:none; }
.wait a:hover { text-decoration:underline; }
.wait span { color:var(--muted); font-size:.88rem; }
.wait .carried { display:block; margin:2px 0 0; font-size:.8rem; }
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
<p class="lede">{{TOTAL}} branches, all already in <code>main</code> (a retired <code>pre-staging</code>: already in <code>staging</code>), so deleting any of them loses nothing. Each link opens GitHub's branch list filtered to that one branch; delete it with the trash icon there. Never listed: <code>main</code>, <code>staging</code>, <code>pre-staging</code> while it is in use, and the engine's own branches. Ticking a branch, or opening its link, saves the tick into this page, so the next refresh leaves it off a repository it cannot check.</p>
</header>
<div class="bar"><span class="progress" id="progress">0 of {{TOTAL}} done</span><button type="button" id="clear">Clear ticks</button></div>
{{SECTIONS}}
</main>
<script>
(function(){
  // Captured before anything below changes the page: the document this
  // page republishes is this, with its saved ticks rewritten.
  var BODY=document.body.innerHTML;
  var HEAD='<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style></head><body>';
  var DATA_RE=/(<script type="application\\/json" id="branch-data">)[\\s\\S]*?(<\\/script>)/;
  var data={}; try { data=JSON.parse(document.getElementById('branch-data').textContent)||{}; } catch(e) { data={}; }
  var boxes=[].slice.call(document.querySelectorAll('input[data-k]'));
  var KEY='branch-cleanup-done:{{BUILD}}', done={}, saved=data.done||{}, page=null, timer=null, dirty=false;
  try { for(var i=localStorage.length-1;i>=0;i--){ var k=localStorage.key(i); if(k&&k.indexOf('branch-cleanup-done')===0&&k!==KEY) localStorage.removeItem(k); } } catch(e) {}
  try { done=JSON.parse(localStorage.getItem(KEY)||'{}')||{}; } catch(e) { done={}; }
  Object.keys(saved).forEach(function(k){ done[k]=saved[k]; });
  function document_with(d){
    var copy=JSON.parse(JSON.stringify(data)); copy.done=d;
    var json=JSON.stringify(copy).replace(/</g,'\\\\u003c');
    return HEAD+BODY.replace(DATA_RE,function(_m,a,b){ return a+json+b; })+'</body></html>';
  }
  function publish(){
    if(timer){ clearTimeout(timer); timer=null; }
    if(!page||!dirty) return;
    dirty=false;
    page.publish(document_with(done)).catch(function(){});
  }
  function save(){
    try { localStorage.setItem(KEY, JSON.stringify(done)); } catch(e) {}
    dirty=true;
    if(timer) clearTimeout(timer);
    timer=setTimeout(publish, 5000);
  }
  function mark(b, on){ if(on) done[b.dataset.k]=new Date().toISOString(); else delete done[b.dataset.k]; save(); render(); }
  function render(){ var n=boxes.filter(function(b){return b.checked;}).length; document.getElementById('progress').textContent=n+' of '+boxes.length+' done'; }
  boxes.forEach(function(b){ b.checked=!!done[b.dataset.k]; b.addEventListener('change',function(){ mark(b, b.checked); }); });
  document.querySelectorAll('.row a').forEach(function(a){ a.addEventListener('click',function(){ var b=a.parentNode.querySelector('input'); if(!b.checked){ b.checked=true; mark(b, true); } }); });
  document.getElementById('clear').addEventListener('click',function(){ done={}; boxes.forEach(function(b){b.checked=false;}); save(); render(); });
  // Opening a branch's link leaves this page for GitHub: save then.
  document.addEventListener('visibilitychange',function(){ if(document.visibilityState==='hidden') publish(); });
  render();
  try { if(window.claude&&window.claude.use) window.claude.use('artifact').then(function(a){ page=a; if(dirty) save(); }).catch(function(){}); } catch(e) {}
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
    # After collect, whose --fetch already brought every ref up to date.
    wait_seen = []
    waiting = collect_waiting(seen=wait_seen)
    if '--waiting' in argv:
        for owner, name, staging, n, oldest in waiting:
            print(f'{name}: {n} commit(s) on {staging} that main lacks, oldest '
                  f'from {oldest}  {compare_link(owner, name, staging)}')
        print(f'{len(waiting)} repositor(ies) waiting to go live.')
        return 0
    if '--html' in argv:
        out = pathlib.Path(argv[argv.index('--html') + 1])
        person = _person()
        url = saved_page(person)
        carried, ticked, carried_wait = [], 0, []
        if '--merge' in argv:
            prev = pathlib.Path(argv[argv.index('--merge') + 1])
            try:
                prev_text = prev.read_text(encoding='utf-8')
                previous, done = read_page(prev_text), read_done(prev_text)
            except OSError as e:
                print(f'Cannot read {prev}: {e}. Nothing written.')
                return 2
            fmt = page_format(prev_text)
            if fmt is not None and fmt > PAGE_FORMAT:
                print(f'{prev} was built by a newer engine (page format '
                      f'{fmt}; this engine writes format {PAGE_FORMAT}). The '
                      f'engine here is older than the page, and merging could '
                      f'drop what the page holds. Nothing written. Update '
                      f'Vendors in this repository brings the engine up to '
                      f'date; then run this again.')
                return 2
            if not is_page(prev_text) and '--replace' not in argv:
                print(f'{prev} holds no branch list this tool can read, so '
                      f'merging it would keep nothing. Nothing written: pass '
                      f'the page the saved address holds, or --replace if '
                      f'replacing it is meant.')
                return 2
            for why in stale_merge_warnings(prev, out, prev_text):
                print(f'WARNING: {why}. Merge a read of the saved page made '
                      f'immediately before this build (the Artifact tool\'s '
                      f'read of its url with path index.html), or rows and '
                      f'ticks saved since are lost.')
            carried = carried_over(previous, seen, done)
            carried_wait = carried_waiting(read_waiting(prev_text), wait_seen)
            ticked = (sum(len(r.get('branches') or []) for r in previous
                          if (r['owner'], r['repo']) in
                          {(o, n) for o, n, *_x in carried_over(previous, seen)})
                      - sum(len(c[2]) for c in carried))
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
                                   carried=carried, waiting=waiting,
                                   carried_wait=carried_wait), encoding='utf-8')
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
              + (f'; {ticked} left off because the person ticked them on the '
                 f'page' if ticked else '')
              + (f'; {len(waiting) + len(carried_wait)} repositor(ies) waiting '
                 f'to go live' + (f' ({len(carried_wait)} kept from the saved '
                                  f'page)' if carried_wait else '')
                 if waiting or carried_wait else '')
              + ('' if noted else ' (not noted for the publish gate, which '
                 'will refuse it: artifact_publish_gate.py did not load)'))
        print(f'Publish it to the saved page, in place: {url}, with '
              f'capabilities {{"artifact": {{}}}} so the page can save its own '
              f'ticks' if url else
              'No saved page yet: publish it as a new page with capabilities '
              '{"artifact": {}}, so it can save its own ticks, then save its '
              'address as "branch_cleanup_page" in the identity.json of your '
              'individual practice source, so the next close updates it.')
        return 0
    if '--json' in argv:
        print(json.dumps({'total': total, 'notes': notes, 'waiting': [
            {'owner': o, 'repo': n, 'staging': st, 'commits': k, 'oldest': d,
             'link': compare_link(o, n, st)} for o, n, st, k, d in waiting],
            'repos': [
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
    for owner, name, staging, n, oldest in waiting:
        print(f'waiting to go live: {name}, {n} commit(s) on {staging} that '
              f'main lacks, oldest from {oldest}')
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
