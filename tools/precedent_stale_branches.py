"""precedent_stale_branches.py -- the remote branches you can delete, across
every repository open in this session: each one already in `main`, so
deleting it loses nothing.

    python3 tools/precedent_stale_branches.py                 # list them
    python3 tools/precedent_stale_branches.py --count         # one number
    python3 tools/precedent_stale_branches.py --fetch         # fetch --prune first
    python3 tools/precedent_stale_branches.py --fetch --db-docs DIR --versions "ID=N ..."
    python3 tools/precedent_stale_branches.py --db-docs DIR --db-seed OLD.html
    python3 tools/precedent_stale_branches.py --db-page OUT.html     # the page itself
    python3 tools/precedent_stale_branches.py --page-url      # the person's saved page
    python3 tools/precedent_stale_branches.py --waiting       # staging that main lacks
    python3 tools/precedent_stale_branches.py --delete-merged [--keep NAME]
            [--skip-heads FILE]   # ONLY inside precedent-branch-cleanup.yml

A branch is STALE when its tip is already in `origin/main`, or when it carries
no change `main` lacks (a Promote's fix branch or copy of staging whose merge commits
changed nothing). NEVER LISTED, whatever their state: `main`, `staging`,
staging's old name `precedent-beta-v01`, and the engine's own
branches (`precedent-check-receipts`, `precedent-promote-lock`) and any
branch starting `data-`, the ladder's name for a live record
(precedent_data_branches.py, 2026-10-11). Staging and main are never
listed, for anyone (Morgan, 2026-10-05). ONE
EXCEPTION, 2026-10-13: an engine branch's old name is listed once its `data-`
copy is on origin and holds the old branch's whole history. The engine then
reads only the `data-` one, and the old name is checked for nothing but a
fresh claim by a window on an older engine, which would push the branch back
anyway -- so deleting it loses nothing (precedent_data_branches.py).
Not the receipts' old name, `precedent-check-receipts`, while an older
engine still writes to it (precedent_data_branches.KEPT_OLD_NAMES; seen
2026-10-28; Morgan, 2026-10-31, strength: assented).
Reported from an Update Vendors that moved three repositories onto
`data-promote-lock`: each kept `precedent-promote-lock`, and nothing said
whether it was dead or how to remove it.

WHICH REPOSITORIES: every git checkout precedent_container_safe.py finds
(this repo, its siblings, the home directory's clones, declared sources),
with an origin on GitHub, where this session's person is a code owner
(precedent_audience.py). Branch management is a code owner's business; a
repository where you are not one is left out, and the listing says so.

Read-only from a session: it deletes nothing there, and never could -- a
remote branch is the person's to delete (practice:
never-delete-a-remote-branch). The one route that deletes, `--delete-merged`
(2026-10-16), refuses to run anywhere but the precedent-branch-cleanup
workflow a person starts on GitHub, which a session never starts. Each row's link
is GitHub's branch list filtered to that one branch, where the trash icon
deletes it (practice: branch-delete-links). The ladder set's
`stale-branch-cleanup` practice links the page in the closing Boildown and
refreshes it when the person says "Branch cleanup".

ONE PAGE, UPDATED IN PLACE (2026-10-11). The person keeps one pinned
cleanup page rather than a new link from every session: its address is
`branch_cleanup_page` in their identity.json (precedent_identity), and the
tool prints it. With none saved, it says to publish a new page and save the
address there. The page says when its newest row was checked, in the
person's own timezone, and each repository says when it was; and its ticks
belong to that check, so a refreshed list starts unticked -- a branch still
on it was not deleted. Morgan, 2026-10-11: "Let's do this" (strength:
decided).

THE PAGE IS THE LIST, NOTHING ELSE (Morgan, 2026-10-20, strength: decided:
"you give me paragraphs about it's checkmarks etc - ... just give it to me
and say nothing else"). No intro, no note on how a button works or why a
repository has none, no advice on what to say next: the build time, the
counts, the buttons, the branches and their dates. An error a button meets
still says what failed.

THE ROWS LIVE IN THE PAGE'S DATABASE (2026-10-27). One document a
repository, in the page's own `repos` collection (the Artifact `db`
capability, PAGE_CAPABILITIES): its branches, its waiting row, its
delete-all record, the time it was checked, and the section the page shows,
rendered here. A refresh writes only the documents of the repositories this
session can see, in one ArtifactData batch; every other repository's
document is untouched, so nothing has to be merged and no session can wipe
another's rows. The page itself is a shell that reads the documents live:
it is published once, and again only when its code changes, never for a
refresh. The refresh is:

  1. ArtifactData list, collection `repos`, out_dir DIR (the files only,
     nothing read into the conversation);
  2. `--fetch --db-docs DIR --versions "ID=N ..."`, with each document's
     version as the listing printed it (its files hold the body only),
     which writes one file a repository under DIR/out and prints the
     batch's `writes`, each pinned to that version;
  3. ArtifactData batch with those writes.

WHY. Until then the page carried every row inside its own HTML and was
republished whole, which the Artifact tool allows over another session's
version only after the session has Read every line of it. On 2026-10-27
the page was 1,097 lines and the read about 98,000 tokens, paid at nearly
every close (the ladder set's stale-branch-cleanup; BestPractice
todo/todo-2026-10-20-branch-page-data-in-a-file.md). Morgan, 2026-10-27:
"Both, A first. ... Act, Book." (strength: decided), A being the refresh
only on "Branch cleanup" and B this.

TICKS AND CLICKS ARE THE PAGE'S OWN WRITES (2026-10-13, moved 2026-10-27).
A tick (or a click on a row's link, which ticks it) is written to
`ticks/<repository>` with the check it belongs to, and a delete-all click
to `clicks/<repository>`. A refresh never touches either: a new check of
that repository starts unticked because its `checked` changed, and the
page folds the click into when the button comes back. Before 2026-10-27
the page saved them into its own HTML, which is what made every refresh a
merge. Morgan chose the page over precedent-individual for them,
2026-10-13 ("Ahhhh great. Go ahead.", strength: decided).

`--db-seed OLD.html` moves a page from before 2026-10-27 into the
database: its rows for repositories this run did not check, less any the
person ticked, its waiting rows and its delete-all records, beside this
run's own. The readers of that old page (read_page, read_done,
read_cleanup, read_waiting) stay for it.

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
covers, across sessions, every repository the person works in. 
THE DELETE-ALL BUTTON (2026-10-16, spec/BRANCH_CLEANUP_BUTTON_PLAN.md).
Each repository's section opens with a link to its
`.github/workflows/precedent-branch-cleanup.yml` page on GitHub, where the
person clicks Run workflow: that workflow deletes every branch this tool
would list, through `--delete-merged`, which refuses to run anywhere but
inside it. A session never starts it (practice:
never-delete-a-remote-branch). The rows stay exactly as they were. Morgan:
"it should ALSO keep the list as it is now, because I want to both see all
the branches ... and also because I may not use the new button because I
am careful on github minutes" (strength: decided).

WHEN THE BUTTON SHOWS. Always in a public repository. In a private one only
once `github_branch_cleanup_every_hours` (precedent_branches.
branch_cleanup_cadence; 336 for Morgan) has passed since THAT repository's
last cleanup run -- one tracker per repository, apart from the main test's.
The tracker is GitHub's own run history, read for each repository this run
can ask; a click on the page also writes its date into the page (`clicked`)
and hides that button at once, and the page's script shows it again when
the hours are up. For a repository this run checked, GitHub's history
replaces the page's click record; for one it did not, or could not ask,
the newer of the two is kept. Any doubt -- visibility unknown, no number
set -- shows the button: showing it costs nothing, only a click does. A
repository whose `main` lacks the workflow gets a line saying so, never a
dead link.

ONE CLICK FOR EVERY PUBLIC REPOSITORY (2026-10-16,
spec/BRANCH_CLEANUP_ALL_REPOS_PLAN.md). Above the sections, one button
starts the cleanup workflow in every repository on the page that is
known to be public and carries it: the page calls GitHub's
actions_run_trigger through the VIEWER's own GitHub connector (the `mcp`
capability, PAGE_CAPABILITIES), so it holds no credential, and only that
click calls it. A private repository, or one whose visibility is unknown,
is never included: those cost minutes. And any cleanup click, this one
or a repository's own, checks off every row of the repositories it
covers. Morgan: "whenever any of these cleanup buttons are clicked ... it
should check the box and cross it off if it doesn't already" (strength:
decided).

OPEN ALL IN TABS (2026-10-17), ONE CLICK PER TAB (2026-10-19). A
repository with more than one branch listed carries, under its delete-all
line, a link that opens that repository's next branch not yet checked off
in a new tab, checks it off, and moves on to the one after. Morgan, 2026-10-17:
"at the start of the section for each repo, have a link to open all those
links (in that repo) in new tabs". It was first a button that called
window.open once per branch, and on 2026-10-19 Morgan reported that it
"didn't work". Two limits stop it: a browser opens one tab per click, and
inside an artifact window.open returns nothing for almost every viewer,
so the button opened no tabs and said pop-ups were blocked. A real link
is the one thing the page's frame always opens, so the link is a real
<a href> whose address the script moves to the next branch after each
click: one click per tab, with no hunting down the list.
"""
import datetime
import html
import json
import os
import pathlib
import re
import subprocess
import sys
# finished typography on every HTML page (finish_html.py; practice: curly-quotes)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from precedent_repo_id import same_repo  # noqa: E402 -- practice: upstream-fix
try:
    from finish_html import finish as finish_html
except ImportError:     # a copy of this file without the engine beside it
    def finish_html(page):
        return page
import urllib.parse

# The file name the closing Boildown is told to write the page to, inside
# the session's scratch folder. Named once: the reply gate's instruction
# reads it, and so does precedent_container_safe.py, which skips this file
# when it looks for work left in a scratch folder -- the page is published
# as an artifact the moment it is built, so it is never work at risk.
PAGE_FILENAME = 'branch-cleanup.html'

# The folder, inside the session's scratch folder, that the refresh lists
# the page's database into and writes its batch from (module docstring,
# "THE ROWS LIVE IN THE PAGE'S DATABASE"). precedent_container_safe.py
# skips it: everything in it is a copy of what the database holds.
DB_DIRNAME = 'branch-db'

# The page's collections: `repos` this tool writes, `ticks` and `clicks`
# the page writes for itself.
DB_REPOS, DB_TICKS, DB_CLICKS = 'repos', 'ticks', 'clicks'

# The version a repository's document records (`format`), and, for a page
# from before the database, of its JSON block. Raise it whenever a document
# gains a field an older engine would drop or misread. 4: the database.
PAGE_FORMAT = 4

# The most writes one ArtifactData batch takes.
DB_BATCH_MAX = 50

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# The engine's own data branches' old names, from the one module that names
# them (precedent_data_branches.LEGACY); the two it had on 2026-10-17 when
# that module cannot load. A branch here is listed only once its `data-`
# copy holds its whole history (_moved_data_branches), and then marked so.
try:
    import precedent_data_branches as _pdb
    ENGINE_BRANCHES = frozenset(_pdb.legacy_name(w) for w in _pdb.LEGACY)
except Exception:                                            # noqa: BLE001
    ENGINE_BRANCHES = frozenset({'precedent-check-receipts', 'precedent-promote-lock'})
# Never listed, whatever their state. Applied where branches are gathered,
# where a saved page is carried over, and again where the page is drawn
# (_listable), so no path can offer one (2026-10-17: two sessions saw a
# lock and a receipt branch on the page and took them for engine branches
# offered by mistake; they were moved old names, unmarked).
ALWAYS_KEPT = frozenset({'main', 'master', 'staging', 'precedent-beta-v01', 'HEAD'})
NEVER = ALWAYS_KEPT | ENGINE_BRANCHES
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
    link both share, else the resolved path. precedent_source_home.tree_key
    since 2026-10-19, the one copy every lister shares; this is the fallback
    for an engine without it."""
    try:
        import precedent_source_home as psh
        return psh.tree_key(repo)
    except ImportError:
        pass
    try:
        st = pathlib.Path(repo).stat()
        return ('inode', st.st_dev, st.st_ino)
    except OSError:
        return ('path', str(pathlib.Path(repo).resolve()))


def _github_spelling(slug):
    """-> (owner, name) as GitHub spells them, when the slug is written all
    in lowercase and GitHub answers; else `slug` unchanged. The attach tool
    clones from a lowercase URL (alex137/bestpractice), so the cleanup page
    headed the repository in lowercase (2026-10-17). Only an all-lowercase
    spelling is asked about: any capital means someone typed it on purpose."""
    owner, name = slug
    if any(ch.isupper() for ch in f'{owner}/{name}'):
        return slug
    gh = _github()
    if gh is None:
        return slug
    try:
        data, err = gh.call(f'repos/{owner}/{name}')
    except Exception:                                        # noqa: BLE001
        return slug
    full = data.get('full_name') if not err and isinstance(data, dict) else None
    if (isinstance(full, str) and full.count('/') == 1
            and same_repo(full, f'{owner}/{name}')):
        return tuple(full.split('/'))
    return slug


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
        slug = _github_spelling(slug)
        key = tuple(part.casefold() for part in slug)
        if key not in seen:
            seen.add(key)
            out.append((pathlib.Path(repo), slug))
    return out


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
    deleting it loses nothing. Never an old name an older engine still
    writes (precedent_data_branches.KEPT_OLD_NAMES). Empty when the names
    cannot be read."""
    try:
        import precedent_data_branches as pdb
        pairs = {pdb.legacy_name(w): pdb.new_name(w) for w in pdb.LEGACY
                 if pdb.old_name_deletable(w)}
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
    reverted = reverted_branches(repo)
    moved = _moved_data_branches(repo, names)
    for b in sorted(set(names)):
        if b in reverted:
            continue
        if b in moved:
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


# THE DELETE-ALL BUTTON (module docstring, "THE DELETE-ALL BUTTON").
CLEANUP_WORKFLOW = 'precedent-branch-cleanup.yml'
CLEANUP_PATH = '.github/workflows/' + CLEANUP_WORKFLOW

# The all-public button starts each public repository's cleanup workflow
# through the VIEWER's own GitHub connector: the page holds no credential,
# and only a person's click calls it. The page is published with these
# capabilities -- its own saves, and that one GitHub tool, nothing else.
GITHUB_CONNECTOR = 'github'
# The rows a session writes are editors' only: a document's `section` is
# HTML the page shows as it stands, so nobody below an editor may write
# one. Ticks and clicks stay open to anyone who can use the page.
PAGE_CAPABILITIES = {'db': {'rules': [{'path': DB_REPOS, 'write': 'admin'}]},
                     'mcp': {'servers': [
                         {'server': GITHUB_CONNECTOR, 'tools': ['actions_run_trigger']}]}}
# THE PAGE'S RUNTIME VERSION STAYS WHERE IT IS (2026-10-17, decided by the
# session under Morgan's "use your judgment on what to fix"). A republish
# reported "contract 0.2.76 (newest 0.2.84)" and nothing said whether to
# move. Publish the shell with `contract` omitted; move it with
# `contract: "latest"` only when the page needs something a newer runtime
# adds, or a runtime bug shows on it, and say so to the person in that
# reply. The "newest" note is information, not a task.
PAGE_RUNTIME_LINE = ('Leave its runtime version as it is (omit `contract`) '
                     'unless the page needs something a newer runtime adds. '
                     'The "newest" note is not a task.')
# A run in one of these states has been started and may still delete: it
# counts as a run, so a second click is not invited while it works.
_RUN_STARTED = {'queued', 'in_progress', 'waiting', 'requested', 'pending'}


def workflow_link(owner, name):
    return f'https://github.com/{owner}/{name}/actions/workflows/{CLEANUP_WORKFLOW}'


def cleanup_installed(repo):
    """True when `repo`'s origin/main carries the cleanup workflow: GitHub
    offers Run workflow only for a file on the default branch."""
    return _git(repo, 'cat-file', '-e', f'origin/main:{CLEANUP_PATH}').returncode == 0


def _declared_visibility(repo):
    try:
        v = json.loads((pathlib.Path(repo) / 'precedent.json')
                       .read_text(encoding='utf-8')).get('visibility')
    except (OSError, ValueError, AttributeError):
        return None
    return {'private': True, 'public': False}.get(v)


def _is_source(repo):
    """True for a practice set: a private one carries no GitHub workflow at
    all, so it never gets the button; a public one carries the cleanup
    workflow alone, and gets it (practice: source-sets-run-no-ci)."""
    for f in (pathlib.Path(repo) / 'tools' / 'ENGINE_MANIFEST.json',
              pathlib.Path(repo) / 'precedent.json'):
        try:
            if json.loads(f.read_text(encoding='utf-8')).get('kind') == 'source':
                return True
        except (OSError, ValueError, AttributeError):
            continue
    return False


def _github():
    try:
        import github_budget
        return github_budget
    except Exception:                                        # noqa: BLE001
        return None


def last_cleanup_run(slug, gh):
    """-> the ISO time of `slug`'s newest cleanup run that succeeded or is
    still going, '' when it has none, None when GitHub could not be asked.
    A failed run deleted nothing that counts, so it does not count."""
    if gh is None:
        return None
    data, err = gh.call(f'repos/{slug}/actions/workflows/{CLEANUP_WORKFLOW}'
                        f'/runs?per_page=20', cache=False)
    if err or not isinstance(data, dict):
        return '' if err and '404' in str(err) else None
    for run in data.get('workflow_runs') or []:
        if run.get('conclusion') == 'success' or run.get('status') in _RUN_STARTED:
            return run.get('created_at') or ''
    return ''


def cleanup_state(repo, owner, name, gh=None, hours=None, now=None):
    """-> the page's record of one repository's button: installed, private
    (True, False, or None when unknown), hours, last (ISO, '' for never,
    None when GitHub could not be asked) and checked."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if hours is None:
        try:
            import precedent_branches as pb
            hours = pb.branch_cleanup_cadence(repo)[0]
        except Exception:                                    # noqa: BLE001
            hours = 0.0
    private = None
    if gh is not None:
        data, err = gh.call(f'repos/{owner}/{name}')
        if not err and isinstance(data, dict) and isinstance(data.get('private'), bool):
            private = data['private']
    if private is None:
        private = _declared_visibility(repo)
    installed = cleanup_installed(repo)
    last = last_cleanup_run(f'{owner}/{name}', gh) if installed and private else ''
    return {'owner': owner, 'repo': name, 'installed': installed, 'private': private,
            'source': _is_source(repo),
            'hours': float(hours or 0), 'last': last, 'checked': now.isoformat()}


def _when(iso):
    if not iso:
        return None
    try:
        t = datetime.datetime.fromisoformat(str(iso).replace('Z', '+00:00'))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)


def cleanup_due(state, now=None):
    """-> (shown, back_on): whether the repository's button shows now, and,
    when it does not, the aware datetime it comes back. Not installed: never
    shown, no date. Anything in doubt: shown."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if not state or not state.get('installed'):
        return False, None
    hours = state.get('hours') or 0
    last = _when(state.get('last'))
    if state.get('private') is not True or not hours or last is None:
        return True, None
    back = last + datetime.timedelta(hours=hours)
    return (True, None) if now >= back else (False, back)


def merge_cleanup(fresh, previous, clicked):
    """-> {(owner, name) key: state} for the page: a fresh state for each
    repository this run looked at, the saved one for every other, and the
    page's own click dates folded in. For a repository this run asked about,
    GitHub's history wins over a click -- a click that never reached Run
    workflow started nothing; when GitHub could not be asked (last None)
    the newer of the saved last run and the click is kept. A saved record
    is kept for every repository without a fresh one, checked or not: one
    with nothing to delete today still ran when it ran."""
    out = {}
    fresh_keys = {_key(st['owner'], st['repo']) for st in fresh}
    prev = {_key(r['owner'], r['repo']): r for r in previous
            if isinstance(r, dict) and r.get('owner') and r.get('repo')}

    def newest(*isos):
        ts = [(t, i) for i in isos if (t := _when(i)) is not None]
        return max(ts)[1] if ts else ''

    for k, r in prev.items():
        if k not in fresh_keys:
            out[k] = dict(r, last=newest(r.get('last'), clicked.get(f'{r["owner"]}/{r["repo"]}')))
    for st in fresh:
        k = _key(st['owner'], st['repo'])
        st = dict(st)
        if st.get('last') is None:
            old = prev.get(k) or {}
            st['last'] = newest(old.get('last'), clicked.get(f'{st["owner"]}/{st["repo"]}'))
        out[k] = st
    return out


def read_cleanup(text):
    """-> (records, clicked) a saved page carries: its `cleanup` list and
    the click dates its script saved; ([], {}) for a page from before."""
    m = _DATA.search(text)
    if not m:
        return [], {}
    try:
        data = json.loads(m.group(1))
    except ValueError:
        return [], {}
    recs = data.get('cleanup') if isinstance(data, dict) else None
    clicked = data.get('clicked') if isinstance(data, dict) else None
    return ([r for r in recs if isinstance(r, dict)] if isinstance(recs, list) else [],
            {str(k): str(v) for k, v in clicked.items()} if isinstance(clicked, dict) else {})


def _day(when, tz=''):
    zone = datetime.timezone.utc
    if tz:
        try:
            from zoneinfo import ZoneInfo
            zone = ZoneInfo(tz)
        except Exception:                                    # noqa: BLE001
            pass
    local = when.astimezone(zone)
    return f'{local.day} {local:%b}'


def _cleanup_line(owner, name, n, state, now=None, tz=''):
    """-> the section's opening line: the delete-all link, the date it comes
    back, or why there is none. '' when there is no record at all."""
    if not state:
        return ''
    if not state.get('installed') and state.get('source'):
        return ''
    if not state.get('installed'):
        return ''
    shown, back = cleanup_due(state, now)
    attrs = (f' data-repo="{html.escape(owner + "/" + name)}"'
             f' data-private="{"1" if state.get("private") is True else "0"}"'
             f' data-public="{"1" if state.get("private") is False else "0"}"'
             f' data-hours="{state.get("hours") or 0:g}"'
             f' data-last="{html.escape(state.get("last") or "")}"')
    back_text = f'Delete-all button back on {_day(back, tz)}.' if back else ''
    return (f'<p class="cleanup"{attrs}>'
            f'<a class="del-all" href="{workflow_link(owner, name)}" target="_blank" '
            f'rel="noopener"{"" if shown else " hidden"}>Delete every merged branch '
            f'({n} listed)</a>'
            f'<span class="back"{"" if back else " hidden"}>{html.escape(back_text)}</span>'
            f'</p>')


def delete_merged(repo, keep=(), skip_heads=(), env=None, push=None, say=print):
    """Delete every branch stale_in lists for `repo`, less the never-deleted
    ones, `keep` and `skip_heads`. -> exit status. Runs ONLY inside the
    precedent-branch-cleanup workflow, started by hand (practice:
    never-delete-a-remote-branch): anywhere else it refuses and deletes
    nothing."""
    env = os.environ if env is None else env
    if env.get('GITHUB_ACTIONS') != 'true' or env.get('GITHUB_EVENT_NAME') != 'workflow_dispatch':
        say('--delete-merged runs only inside the precedent-branch-cleanup workflow, '
            'started by a person from GitHub. Nothing deleted (practice: '
            'never-delete-a-remote-branch).')
        return 2
    rows = stale_in(repo)
    if rows is None:
        say('No origin/main to compare against. Nothing deleted.')
        return 1
    push = push or (lambda b: _git(repo, 'push', '-q', 'origin', '--delete', b))
    keep, heads = set(keep), set(skip_heads)
    deleted, skipped, failed = [], [], []
    for b, _d in rows:
        if b in NEVER or b.startswith(DATA_PREFIX) or b in keep:
            skipped.append((b, 'never deleted by the button'))
        elif b in heads:
            skipped.append((b, 'an open pull request comes from it'))
        else:
            r = push(b)
            (deleted.append(b) if r.returncode == 0
             else failed.append((b, (r.stderr or r.stdout or '').strip()[:200])))
    lines = [f'Deleted {len(deleted)} branch(es) already in main.']
    lines += [f'- deleted `{b}`' for b in deleted]
    lines += [f'- skipped `{b}`: {why}' for b, why in skipped]
    lines += [f'- FAILED `{b}`: {why}' for b, why in failed]
    for line in lines:
        say(line)
    summary = env.get('GITHUB_STEP_SUMMARY')
    if summary:
        try:
            with open(summary, 'a', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')
        except OSError:
            pass
    return 1 if failed else 0


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
    old ones. A branch in NEVER is dropped too, whoever listed it: on
    2026-10-17 a saved page carried one repository's precedent-promote-lock
    and precedent-check-receipts as deletable, and every refresh kept them."""
    checked_now = {_key(o, n) for o, n in seen}
    done = done or {}
    out = []
    for r in previous:
        rows = [(b, d) for b, d in r.get('branches') or []
                if done_key(r['repo'], b) not in done and b not in NEVER]
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


def _checked_text(checked, tz=''):
    """-> 'Checked 27 Oct 2026, 11:20 Buenos Aires time.' for an ISO time,
    'Checked earlier.' when it cannot be read."""
    try:
        when = datetime.datetime.fromisoformat(str(checked))
    except (TypeError, ValueError):
        return 'Checked earlier.'
    return 'Checked ' + built_line(when, tz)[len('Refreshed '):] + '.'


def _waiting_li(owner, name, staging, n, oldest, checked='', tz=''):
    """-> one repository's row under Waiting to go live: a link to GitHub's
    comparison of main and its staging, the count and the oldest's date."""
    note = (' <span class="carried">' + html.escape(_checked_text(checked, tz))
            + '</span>') if checked else ''
    return (f'<li><div class="wait"><a href="{compare_link(owner, name, staging)}" '
            f'target="_blank" rel="noopener">{html.escape(name)}</a>'
            f'<span>{n} commit{"" if n == 1 else "s"}, oldest {html.escape(oldest)}.{note}</span>'
            f'</div></li>')


def _listable(rows, fresh=True):
    """-> `rows` less any branch the page must never offer: main, staging
    and the rest of ALWAYS_KEPT, a live `data-` branch, and -- on a row not
    from this run's own check -- an engine branch's old name, which only a
    fresh check can show is safe (its `data-` copy holds its whole history)."""
    return [(b, d) for b, d in rows
            if b not in ALWAYS_KEPT and not b.startswith(DATA_PREFIX)
            and (fresh or b not in ENGINE_BRANCHES)]


def _moved_note(b):
    if b not in ENGINE_BRANCHES:
        return ''
    return (' <span class="carried">Old name of '
            f'<code>{html.escape(DATA_PREFIX + b.split("-", 1)[1])}</code>.</span>')


def _section(owner, name, rows, note='', cleanup=''):
    lis = '\n'.join(
        f'<li><label class="row"><input type="checkbox" '
        f'id="{html.escape(name + "/" + b)}" data-k="{html.escape(name + "/" + b)}">'
        f'<a href="{link(owner, name, b)}" target="_blank" rel="noopener">'
        f'{html.escape(b)}</a><span class="date">{html.escape(d)}</span>'
        f'{_moved_note(b)}</label></li>'
        for b, d in rows)
    return (f'<section class="repo"><h2>{html.escape(name)} '
            f'<span class="count">{len(rows)}</span></h2>'
            f'<p class="owner">github.com/{html.escape(owner)}/{html.escape(name)}</p>'
            + (f'<p class="carried">{html.escape(note)}</p>' if note else '')
            + cleanup
            + (_open_next(owner, name, rows) if len(rows) > 1 else '')
            + f'<ul>{lis}</ul></section>')


# OPEN ALL IN TABS (module docstring): a real link, never window.open.
def _open_next(owner, name, rows):
    first = link(owner, name, rows[0][0]) if rows else '#'
    return ('<p class="open-all"><a class="open-next" href="' + first + '" '
            'target="_blank" rel="noopener">Open next</a>'
            '<span class="open-status" role="status"></span></p>')


# THE ROWS LIVE IN THE PAGE'S DATABASE (module docstring).
_DOC_ID_BAD = re.compile(r'[^A-Za-z0-9_\-.~:@+]')


def doc_id(owner, name):
    """-> a repository's document id in the page's database: owner--repo,
    case folded, any character a document id refuses made '_'."""
    return _DOC_ID_BAD.sub('_', f'{owner}--{name}'.casefold())[:200]


def repo_doc(owner, name, rows, checked, tz='', waiting=None, cleanup=None,
             fresh=True, now=None):
    """-> one repository's document: its listable branches, its waiting row
    (staging, commits, oldest) or None, its delete-all record, when it was
    checked, and the HTML the page shows for it, rendered here so the page
    and this tool cannot disagree about a row. `fresh` False for rows
    carried from a saved page (_listable)."""
    rows = _listable(rows, fresh)
    state = cleanup or None
    text = _checked_text(checked, tz)
    line = _cleanup_line(owner, name, len(rows), state, now, tz) if rows else ''
    return {
        'format': PAGE_FORMAT, 'owner': owner, 'repo': name, 'checked': checked,
        'checked_text': text,
        'branches': [[b, d] for b, d in rows],
        'waiting': ({'staging': waiting[0], 'commits': int(waiting[1]),
                     'oldest': waiting[2]} if waiting else None),
        'cleanup': state,
        'public': bool(rows and state and state.get('installed')
                       and state.get('private') is False),
        # The "Checked" line is the page's to add: only where a repository
        # was checked before the newest, which the header already dates.
        'section': finish_html(_section(owner, name, rows, cleanup=line)) if rows else '',
        'waiting_li': finish_html(_waiting_li(owner, name, *waiting[:3])) if waiting else '',
    }


def read_listing(folder):
    """-> {doc id: (version or None, document)} from an ArtifactData listing
    of the page's `repos` collection saved with out_dir=`folder` (the files
    land in <folder>/repos/). Takes either shape a saved document may have:
    the document itself, or {id, version, data}. {} when nothing is there,
    which is right for a page whose database is still empty."""
    base = pathlib.Path(folder)
    sub = base / DB_REPOS
    out = {}
    for f in sorted((sub if sub.is_dir() else base).glob('*.json')):
        try:
            j = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if not isinstance(j, dict):
            continue
        body = j['data'] if isinstance(j.get('data'), dict) else j
        ver = j.get('version')
        if not isinstance(ver, int) or isinstance(ver, bool):
            ver = None
        out[str(j.get('id') or j.get('doc_id') or f.stem)] = (ver, body)
    return out


_VERSION_PAIR = re.compile(r'"?([A-Za-z0-9_\-.~:@+]+)"?\s*(?:=|\s+\d+\s+bytes\s+version\s+)(\d+)')


def parse_versions(text):
    """-> {doc id: version} from `--versions`: `id=N` pairs, or the lines
    of the ArtifactData listing itself pasted in (`"id"  772 bytes
    version 3  "path"`). The listing saves each document's body, not its
    version (seen 2026-10-27), and a write over an existing document must
    carry the version it was read at."""
    return {i: int(v) for i, v in _VERSION_PAIR.findall(text or '')}


def build_docs(groups, waiting, seen, wait_seen, fresh_states, listing,
               now=None, tz='', seed_text=None):
    """-> {doc id: document} to write: one for each repository this run
    checked, and, given `seed_text` (a page from before the database), one
    for each repository that page lists and this run did not check, less
    the rows the person ticked there. A repository this run checked and
    found with nothing to offer is written only when the database already
    holds it, so its old rows go. Every other document is left alone."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    checked = now.isoformat()
    rows_by = {_key(o, n): rows for o, n, rows in groups}
    wait_by = {_key(o, n): (st, k, d) for o, n, st, k, d in waiting}
    prev_cleanup = [b['cleanup'] for _v, b in listing.values()
                    if isinstance(b, dict) and isinstance(b.get('cleanup'), dict)]
    carried, carried_w, clicked = {}, {}, {}
    if seed_text:
        recs, clicked = read_cleanup(seed_text)
        prev_cleanup += recs
        carried = {_key(o, n): (o, n, rows, c) for o, n, rows, c in
                   carried_over(read_page(seed_text), seen, read_done(seed_text))}
        carried_w = {_key(w[0], w[1]): w for w in
                     carried_waiting(read_waiting(seed_text), wait_seen)}
    cleanup = merge_cleanup(fresh_states, prev_cleanup, clicked)
    names = {_key(o, n): (o, n) for o, n in [*seen, *wait_seen,
                                              *[(o, n) for o, n, _r in groups]]}
    docs = {}
    for k, (o, n) in names.items():
        docs[doc_id(o, n)] = repo_doc(o, n, rows_by.get(k, []), checked, tz,
                                      wait_by.get(k), cleanup.get(k), now=now)
    for k in [*carried, *[k for k in carried_w if k not in carried]]:
        if k in names:
            continue
        o, n = (carried.get(k) or carried_w[k])[:2]
        rows, when = carried[k][2:4] if k in carried else ([], '')
        w = carried_w.get(k)
        docs[doc_id(o, n)] = repo_doc(o, n, rows, when or (w[5] if w else ''), tz,
                                      w[2:5] if w else None, cleanup.get(k),
                                      fresh=False, now=now)
    return {i: d for i, d in docs.items() if d['branches'] or d['waiting'] or i in listing}


def db_writes(docs, listing, outdir):
    """Write each document to <outdir>/<doc id>.json and -> the ArtifactData
    batch `writes` that set them, each pinned to the version the listing
    saw. A document the listing did not see is a create; if it exists after
    all, the write is refused rather than overwriting it unread."""
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    writes = []
    for did, doc in sorted(docs.items()):
        f = out / f'{did}.json'
        f.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
        w = {'op': 'set', 'collection': DB_REPOS, 'doc_id': did,
             'file_path': str(f.resolve())}
        ver = (listing.get(did) or (None, None))[0]
        if ver is not None:
            w['if_version'] = ver
        writes.append(w)
    return writes


def render_page():
    """-> the page: a shell that reads its rows from its own database."""
    return _PAGE.replace('{{GH}}', GITHUB_CONNECTOR).replace('{{WORKFLOW}}', CLEANUP_WORKFLOW)


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
.cleanup { display:grid; gap:2px; margin:0 0 10px; font-size:.88rem; color:var(--muted); max-width:62ch; }
.cleanup a { font-weight:600; color:var(--accent); text-decoration:none; justify-self:start; }
.cleanup a:hover { text-decoration:underline; }
.cleanup [hidden] { display:none; }
.cleanup-all { display:grid; gap:4px; margin:0; font-size:.88rem; color:var(--muted); max-width:62ch; }
.cleanup-all button { font:inherit; font-weight:600; justify-self:start; background:var(--accent); color:var(--surface); border:0; border-radius:4px; padding:6px 12px; cursor:pointer; }
.cleanup-all button:disabled { opacity:.6; cursor:default; }
.cleanup-all button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.cleanup-all .status { color:var(--fg); }
.open-all { margin:0 0 10px; font-size:.88rem; color:var(--muted); max-width:62ch; }
.open-all a.open-next { font-weight:600; color:var(--accent); text-decoration:none; }
.open-all a.open-next:hover { text-decoration:underline; }
.open-all a.open-next:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
</style>
<main>
<header>
<h1>Branch cleanup</h1>
<p class="built" id="built"></p>
</header>
<div class="bar"><span class="progress" id="progress"></span><button type="button" id="clear">Clear checkmarks</button><span class="carried" id="note" role="status"></span></div>
<div id="list"></div>
</main>
<script>
(function(){
  // The rows are the page's own database: one document a repository in
  // `repos`, written by the sessions that check it; this page writes only
  // `ticks` and `clicks` (precedent_stale_branches.py, "THE ROWS LIVE IN
  // THE PAGE'S DATABASE"). A repository's `section` is HTML only editors
  // can write (the page's db rules), shown as it stands.
  var list=document.getElementById('list'), noteEl=document.getElementById('note');
  var db=null, loaded=false, repos=[], ticks={}, clicks={}, local={}, timers={};
  var boxes=[], lines=[], nexts=[], status='', busy=false;
  function now(){ return new Date().toISOString(); }
  function esc(s){ return String(s).replace(/[&<>"]/g,function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function note(t){ noteEl.textContent=t; }
  function byId(id){ for(var i=0;i<repos.length;i++) if(repos[i].id===id) return repos[i]; return null; }
  function docOf(el){ var c=el.closest('[data-doc]'); return c?c.getAttribute('data-doc'):''; }
  // A repository's ticks count only for the check they were made on: a
  // refreshed list starts unticked, since a branch still on it was not
  // deleted.
  function doneOf(id){
    if(local[id]) return local[id];
    var r=byId(id), t=ticks[id];
    return (r&&t&&t.built===r.checked&&t.done&&typeof t.done==='object')?JSON.parse(JSON.stringify(t.done)):{};
  }
  function save(id){
    if(!db) return;
    if(timers[id]) clearTimeout(timers[id]);
    timers[id]=setTimeout(function(){
      timers[id]=null;
      var r=byId(id); if(!r) return;
      db.doc('ticks/'+id).set({built:r.checked, done:local[id]||{}})
        .then(function(){ if(!timers[id]) delete local[id]; })
        .catch(function(e){ note('A checkmark was not saved ('+((e&&e.code)||'failed')+').'); });
    },1500);
  }
  function mark(b, on){
    var id=docOf(b); if(!id) return;
    var d=local[id]=doneOf(id);
    if(on) d[b.dataset.k]=now(); else delete d[b.dataset.k];
    save(id); progress();
  }
  function progress(){
    var n=boxes.filter(function(b){ return b.checked; }).length;
    document.getElementById('progress').textContent=n+' of '+boxes.length+' done';
    nexts.forEach(function(a){ if(a._row) aim(a); });
  }
  // A private repository's button comes back once its hours have passed
  // since the newer of its last run and a click here; a public one, or one
  // with no number, always shows (spec/BRANCH_CLEANUP_BUTTON_PLAN.md).
  function cleanup(p){
    var a=p.querySelector('.del-all'); if(!a) return;
    var back=p.querySelector('.back'), c=clicks[docOf(p)];
    var hours=parseFloat(p.dataset.hours)||0, last=0;
    [p.dataset.last, c&&c.at].forEach(function(t){ var v=t?Date.parse(t):NaN; if(!isNaN(v)&&v>last) last=v; });
    var due=last+hours*3600000, shown=p.dataset.private!=='1'||!hours||!last||Date.now()>=due;
    a.hidden=!shown; back.hidden=shown;
    if(!shown) back.textContent='Delete-all button back on '+new Date(due).toLocaleDateString(undefined,{day:'numeric',month:'short'})+'.';
  }
  // Any cleanup click checks off every row of the repositories it covers
  // (Morgan, 2026-10-16): the run deletes them, so they are done here.
  function started(p){
    var id=docOf(p), at=now();
    clicks[id]={at:at};
    if(db) db.doc('clicks/'+id).set({at:at}).catch(function(){});
    var sec=p.closest('section.repo');
    if(sec){
      var d=local[id]=doneOf(id);
      sec.querySelectorAll('input[data-k]').forEach(function(b){ if(!b.checked){ b.checked=true; d[b.dataset.k]=now(); } });
      save(id);
    }
    cleanup(p); progress();
  }
  // Open the next branch not yet checked off, one tab per click. It is a
  // real link because a page in an artifact frame cannot open tabs from a
  // script (window.open returns null for almost every viewer), and a
  // browser gives one click one tab anyway.
  function aim(a){
    var sec=a.closest('section.repo'), st=sec.querySelector('.open-status');
    var rows=[].slice.call(sec.querySelectorAll('.row'));
    var left=rows.filter(function(r){ return !r.querySelector('input').checked; });
    var row=(left.length?left:rows)[0];
    a.href=row.querySelector('a').href;
    a._row=row;
    st.textContent=left.length?' '+left.length+' of '+rows.length+' left'
      :' All '+rows.length+' checked off';
  }
  var WHY={needs_reauth:'reconnect GitHub in claude.ai Settings, Connectors',
    server_not_connected:'add the GitHub connector in claude.ai Settings, Connectors',
    selection_required:'choose which GitHub connector this page uses',
    not_in_manifest:'this page is not allowed to use GitHub; allow it in this page’s Permissions menu',
    approval_required:'GitHub access for this page was not approved',
    blocked_by_policy:'your organization blocks this'};
  // One click for every public repository: the page asks GitHub, through
  // the viewer's own GitHub connector, to run each one's cleanup workflow.
  // Only this click calls it; nothing on load or on a timer does.
  function runPublic(){
    var pub=lines.filter(function(p){ return p.dataset.public==='1'; });
    if(!pub.length) return;
    busy=true; pub.forEach(started);
    status='Starting '+pub.length+' cleanup run(s)...'; show();
    var use=(window.claude&&window.claude.use)?window.claude.use('mcp'):Promise.resolve(null);
    Promise.resolve(use).catch(function(){ return null; }).then(function(mcp){
      if(!mcp){ status='Cannot reach GitHub from here; use each repository\\'s button below.'; busy=false; show(); return; }
      var ok=[], bad=[];
      return pub.reduce(function(chain,p){
        return chain.then(function(){
          var r=p.dataset.repo.split('/');
          return mcp.callTool('{{GH}}','actions_run_trigger',{method:'run_workflow',owner:r[0],repo:r[1],workflow_id:'{{WORKFLOW}}',ref:'main'})
            .then(function(){ ok.push(r[1]); }, function(e){ bad.push(r[1]+' ('+((e&&WHY[e.code])||(e&&e.code)||'failed')+')'); });
        });
      }, Promise.resolve()).then(function(){
        status='Started '+ok.length+' of '+pub.length+'.'+(bad.length?' Not started: '+bad.join('; ')+'.':'');
        busy=false; show();
      });
    });
  }
  function show(){
    var all=document.getElementById('del-public'), st=document.getElementById('del-public-status');
    if(all) all.disabled=busy;
    if(st) st.textContent=status;
  }
  function render(){
    if(!loaded) return;
    var shown=repos.filter(function(r){ return r.section||r.waiting_li; });
    shown.sort(function(a,b){ return a.checked<b.checked?1:a.checked>b.checked?-1:String(a.repo).localeCompare(String(b.repo)); });
    var newest=shown[0];
    document.getElementById('built').textContent=newest?String(newest.checked_text||'').replace(/^Checked /,'Refreshed ').replace(/\\.$/,''):'';
    var waits=shown.filter(function(r){ return r.waiting_li; });
    var pub=shown.filter(function(r){ return r.public&&r.section; });
    var h='';
    if(pub.length){
      var n=pub.reduce(function(s,r){ return s+(r.branches||[]).length; },0);
      h+='<p class="cleanup-all"><button type="button" id="del-public">Delete every merged branch in all '+pub.length
        +' public repositor'+(pub.length===1?'y':'ies')+' ('+n+' listed)</button><span class="status" id="del-public-status" role="status"></span></p>';
    }
    if(waits.length) h+='<section class="waiting"><h2>Waiting to go live <span class="count">'+waits.length+'</span></h2><ul>'
      +waits.map(function(r){ var w=when(r); return w?r.waiting_li.replace('</span></div></li>',' <span class="carried">'+w+'</span></span></div></li>'):r.waiting_li; }).join('')+'</ul></section>';
    // A repository checked before the newest says when, under its name.
    function when(r){ return newest&&r.checked!==newest.checked&&r.checked_text?esc(r.checked_text):''; }
    shown.forEach(function(r){ if(r.section){ var w=when(r); h+='<div data-doc="'+esc(r.id)+'">'+(w?r.section.replace('</p>','</p><p class="carried">'+w+'</p>'):r.section)+'</div>'; } });
    list.innerHTML=h||'<p class="carried">Nothing to delete.</p>';
    boxes=[].slice.call(list.querySelectorAll('input[data-k]'));
    boxes.forEach(function(b){
      b.checked=!!doneOf(docOf(b))[b.dataset.k];
      b.addEventListener('change',function(){ mark(b, b.checked); });
    });
    list.querySelectorAll('.row a').forEach(function(a){ a.addEventListener('click',function(){ var b=a.parentNode.querySelector('input'); if(!b.checked){ b.checked=true; mark(b, true); } }); });
    lines=[].slice.call(list.querySelectorAll('.cleanup[data-repo]'));
    lines.forEach(function(p){
      cleanup(p);
      var a=p.querySelector('.del-all');
      if(a) a.addEventListener('click',function(){ started(p); });
    });
    var all=document.getElementById('del-public');
    if(all) all.addEventListener('click',runPublic);
    nexts=[].slice.call(list.querySelectorAll('section.repo a.open-next'));
    nexts.forEach(function(a){
      aim(a);
      a.addEventListener('click',function(){
        var b=a._row&&a._row.querySelector('input');
        // The tab opens from the address the link has now; move it after.
        setTimeout(function(){ if(b&&!b.checked){ b.checked=true; mark(b, true); } aim(a); },0);
      });
    });
    show(); progress();
  }
  document.getElementById('clear').addEventListener('click',function(){
    repos.forEach(function(r){ if(r.section){ local[r.id]={}; save(r.id); } });
    render();
  });
  function fail(e){ note('The list could not load ('+((e&&e.code)||'error')+').'); }
  var use=(window.claude&&window.claude.use)?window.claude.use('db'):Promise.resolve(null);
  Promise.resolve(use).catch(function(){ return null; }).then(function(d){
    if(!d){ list.innerHTML='<p class="carried">The list loads from this page’s data, which needs claude.ai, signed in.</p>'; return; }
    db=d;
    db.collection('repos').onSnapshot(function(snap){
      repos=snap.docs.filter(function(x){ return x.exists; }).map(function(x){ var v=Object.assign({},x.data()); v.id=x.id; return v; });
      loaded=true; render();
    }, fail);
    db.collection('ticks').onSnapshot(function(snap){ ticks={}; snap.docs.forEach(function(x){ if(x.exists) ticks[x.id]=x.data(); }); render(); }, fail);
    db.collection('clicks').onSnapshot(function(snap){ clicks={}; snap.docs.forEach(function(x){ if(x.exists) clicks[x.id]=x.data(); }); render(); }, fail);
  });
})();
</script>
'''


def _arg_values(argv, flag):
    return [argv[i + 1] for i, a in enumerate(argv[:-1]) if a == flag]


def main(argv):
    if '--delete-merged' in argv:
        heads = []
        for f in _arg_values(argv, '--skip-heads'):
            try:
                heads += [l.strip() for l in pathlib.Path(f).read_text(
                    encoding='utf-8').splitlines() if l.strip()]
            except OSError as e:
                print(f'Cannot read {f}: {e}. Nothing deleted.')
                return 1
        return delete_merged(pathlib.Path.cwd(), keep=_arg_values(argv, '--keep'),
                             skip_heads=heads)
    if '--page-url' in argv:
        url = saved_page()
        print(url or 'none saved: add "branch_cleanup_page" to your identity.json')
        return 0 if url else 1
    if '--html' in argv or '--merge' in argv:
        print('The branch cleanup page keeps its rows in its own database since '
              '2026-10-27, so there is no page to build and merge. To refresh it: '
              'ArtifactData list of collection "repos" with out_dir <scratchpad>/'
              f'{DB_DIRNAME}, then --db-docs <scratchpad>/{DB_DIRNAME}, then the '
              'batch it prints. Nothing written.')
        return 2
    if '--db-page' in argv:
        out = pathlib.Path(argv[argv.index('--db-page') + 1])
        out.write_text(finish_html(render_page()), encoding='utf-8')
        # Noted for the publish gate, which passes a page an engine
        # generator wrote, unedited, within the hour (artifact_publish_gate.py,
        # "ENGINE-REGISTERED GENERATORS").
        try:
            import artifact_publish_gate
            noted = artifact_publish_gate.record_generated(
                out, 'precedent_stale_branches.py')
        except Exception:                                   # noqa: BLE001
            noted = False
        url = saved_page()
        caps = json.dumps(PAGE_CAPABILITIES)
        print(f'The page is written to {out}'
              + ('' if noted else ' (not noted for the publish gate, which '
                 'will refuse it: artifact_publish_gate.py did not load)') + '. '
              + (f'Publish it to the saved page, in place: {url}, with '
                 f'capabilities {caps}. A page another session published last '
                 f'is refused until this session has read it through, once. '
                 + PAGE_RUNTIME_LINE if url else
                 f'No saved page yet: publish it as a new page with capabilities '
                 f'{caps}, then save its address as "branch_cleanup_page" in the '
                 f'identity.json of your individual practice source.')
              + ' Then fill it: --db-docs.')
        return 0
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
    if '--db-docs' in argv:
        folder = pathlib.Path(argv[argv.index('--db-docs') + 1])
        seed_text = None
        if '--db-seed' in argv:
            old = pathlib.Path(argv[argv.index('--db-seed') + 1])
            try:
                seed_text = old.read_text(encoding='utf-8')
            except OSError as e:
                print(f'Cannot read {old}: {e}. Nothing written.')
                return 2
            if not is_page(seed_text):
                print(f'{old} holds no branch list this tool can read. Nothing '
                      f'written.')
                return 2
        listing = read_listing(folder)
        versions = parse_versions(' '.join(_arg_values(argv, '--versions')))
        listing = {i: (versions.get(i, v), d) for i, (v, d) in listing.items()}
        newer = sorted(i for i, (_v, d) in listing.items()
                       if isinstance(d.get('format'), int) and d['format'] > PAGE_FORMAT)
        if newer:
            print(f'The page\'s database was written by a newer engine (format '
                  f'above {PAGE_FORMAT}: {", ".join(newer)}). Nothing written: '
                  f'Update Vendors in this repository, then run this again.')
            return 2
        person = _person()
        gh = _github()
        try:
            paths = {_key(*slug): repo for repo, slug in _repos()}
        except Exception:                                    # noqa: BLE001
            paths = {}
        fresh = [cleanup_state(paths[_key(o, n)], o, n, gh=gh)
                 for o, n, _rows in groups if _key(o, n) in paths]
        docs = build_docs(groups, waiting, seen, wait_seen, fresh, listing,
                          tz=person.get('timezone') or '', seed_text=seed_text)
        unpinned = sorted(i for i in docs if i in listing and listing[i][0] is None)
        if unpinned:
            print(f'The page already holds {", ".join(unpinned)}, and a write over '
                  f'a document must carry the version it was listed at. Nothing '
                  f'written: run this again with --versions "<id>=<version> ..." '
                  f'(or the listing\'s own lines) for every document the listing '
                  f'named.')
            return 2
        writes = db_writes(docs, listing, folder / 'out')
        url = saved_page(person)
        print(f'{len(writes)} repositor(ies) to write, of {len(listing)} the page '
              f'holds; every other repository on it is left as it is. Send the '
              f'writes below with ArtifactData batch to {url or "the page"}, at most '
              f'{DB_BATCH_MAX} a batch. A write refused for its version means '
              f'another session wrote that repository since the listing: list '
              f'again and run this again.')
        for i in range(0, len(writes), DB_BATCH_MAX):
            print(json.dumps(writes[i:i + DB_BATCH_MAX]))
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
