#!/usr/bin/env python3
"""Says whether anything this repo vendors or resolves live has fallen behind its upstream — every source precedent.json declares (the engine, each vendored tree, each live sibling clone), one row each; the one check that looks outward; prints, never refreshes

Say whether anything this repo vendors or resolves live has fallen behind
the upstream it came from -- every declared source, not only the engine.

THE GAP THIS CLOSES. Every check in this system runs inside one repository.
Nothing compared a consuming repo against the upstream it vendored from, so
a fix merged upstream reached an installed repo only when somebody
remembered to run "Update Vendors" there -- and nothing anywhere said which
repos had not. Measured 2026-09-20: 18 of 22 repositories had never taken
one. That is also why running a deep check could never find a stale vendored
tree; not a gap in its passes, a gap in what any pass could see.

WHY IT READS precedent.json AND NOT ONE MANIFEST (2026-09-23). The first
version read tools/ENGINE_MANIFEST.json and nothing else, and the classic
notice (checkin.py fresh) read process/manifest.json and nothing else. A
consumer that declared a second shared set -- its practices resolved live
from a sibling clone, its code vendored under process/<name>/ with its own
manifest -- had no freshness check on either half, and nothing said so: the
set was a second thing to remember, and it was not remembered. A source is
covered from the moment it is declared, or it is not covered. So this reads
the declaration and works out, per source, every way it is reached here:

  engine    tools/ENGINE_MANIFEST.json -- the vendored Precedent engine
  vendored  process/manifest.json (the universal tree) or
            process/manifest_<name>.json (a shared set's code dirs) --
            local truth is the commit the manifest records
  live      a git work tree at the source's declared path -- its practices
            load from whatever that clone holds, so local truth is the
            clone's HEAD and a stale clone loads stale rules

One `git ls-remote` per (repo, branch) gives the upstream tip for all three.
Repo-local sources have no upstream and are skipped; a universal source
declared at this repo's own root (a self-hosted catalogue) is this repo's
own branch, which the freshness guard already covers.

A REMINDER IS WHAT ALREADY FAILED, so this is built to run without being
remembered: from the session-start bootstrap, and from precedent_gate.py's
push and merge moments. It PRINTS and never refreshes anything -- the
shape the upstream-carry notice had (2026-09-08 to 2026-09-27), at Morgan's
own request: "I don't want it to merge invisibly, I'd like to do it in a session
when I'm there."

  python3 tools/precedent_engine_freshness.py           # every source, one row each
  python3 tools/precedent_engine_freshness.py --files   # + which engine files changed
  python3 tools/precedent_engine_freshness.py --quiet   # behind rows + a not-verified count

EXIT STATUS IS 0 IN EVERY CASE, including no network, no manifest and a
malformed one. A session start that a network hiccup can block is worse than
the staleness it was guarding against (practice: fail-gracefully). What that
practice requires instead is that the outcomes never render alike: a row is
`current`, `BEHIND`, or `NOT VERIFIED`, and unknown is never printed as
current. `--quiet` prints the BEHIND rows and, when any source could not be
verified, ONE line saying how many and that the full run names them -- so a
repo whose every source is current says nothing, and one whose sources are
unreachable says so rather than reading as current. That line was missing
until 2026-09-28: --quiet printed nothing for an unreachable source, which
is exactly what current looks like to a session start -- the failure the
maintainers' drift-notice rule names. The full run is where each
unverified row is spelled out. A repo with no engine manifest at all -- the
engine's own origin, or one that never vendored it -- has no engine row to
verify, so that one row is not counted there. `--files` needs to fetch
upstream objects and is therefore NOT what the hook runs.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

MANIFEST = pathlib.Path('tools') / 'ENGINE_MANIFEST.json'
# The section 0 catalogue's own sync record (precedent_update.CATALOGUE_SYNC_NAME).
CATALOGUE_SYNC = 'CATALOGUE_SYNC.json'
REPO_CONFIG = 'precedent.json'
DEFAULT_USER_CONFIG = '~/.config/precedent/config.json'
USER_CONFIG_ENV = 'PRECEDENT_USER_CONFIG'


def _git(*args, cwd=None, timeout=25):
    """-> (rc, stdout). Never raises: a missing git, a timeout and a failed
    fetch are all the same answer here, "could not look"."""
    try:
        p = subprocess.run(('git',) + args, cwd=cwd, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ''


def _read_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding='utf-8')), None
    except (OSError, ValueError) as e:
        return None, f'{path} could not be read ({type(e).__name__})'


def read_manifest(root):
    """The vendored engine's own manifest (tools/ENGINE_MANIFEST.json)."""
    f = pathlib.Path(root) / MANIFEST
    if not f.is_file():
        return None, (f'no {MANIFEST} -- this repo has never vendored the '
                      f'engine, or is the engine\'s own origin')
    return _read_json(f)


def upstream_tip(repo_url, branch, clone=None):
    """-> the commit `branch` names at `repo_url`, or None.

    Asked from INSIDE `clone`, against its `origin`, when there is a clone
    whose origin is that URL: a private source's credential is a
    credential.helper in that clone's own .git/config, so the bare URL run
    from anywhere else fails ("could not read Username ... terminal
    prompts disabled"), and every session printed NOT VERIFIED for a
    source it could have read (2026-09-30). The bare URL only when there
    is no such clone."""
    if clone:
        rc, origin = _git('remote', 'get-url', 'origin', cwd=clone)
        if rc == 0 and origin and origin == repo_url:
            rc, out = _git('ls-remote', 'origin', f'refs/heads/{branch}', cwd=clone)
            if rc == 0 and out:
                return out.split()[0]
    rc, out = _git('ls-remote', repo_url, f'refs/heads/{branch}')
    if rc != 0 or not out:
        return None
    return out.split()[0]


def refresh_remedy(root, clone):
    """-> the command that brings a practice-set clone current, as a person
    or session can run it from `root`.

    Never a bare `git -C <clone> pull --ff-only`: the session-start refresh
    leaves engine output uncommitted in every source clone, so that pull
    refuses ("Your local changes ... would be overwritten") -- it did on
    all four attached sources (2026-09-30). precedent_refresh_sources.py
    --apply discards that engine output and fast-forwards. It lives only in
    a BestPractice clone, so this names the copy that exists: this repo's
    own, a BestPractice clone beside it, or else says where to run it."""
    root = pathlib.Path(root).resolve()
    here = pathlib.Path(__file__).resolve().parent / 'precedent_refresh_sources.py'
    for tool in (root / 'tools' / 'precedent_refresh_sources.py',
                 root.parent / 'BestPractice' / 'tools' / 'precedent_refresh_sources.py',
                 here):
        if tool.is_file():
            shown = (tool.relative_to(root) if tool.is_relative_to(root) else tool)
            return f'python3 {shown} --apply --path {clone}'
    return (f'from a BestPractice clone: python3 tools/precedent_refresh_sources.py '
            f'--apply --path {clone}')


# --------------------------------------------------------------------------
# What this repo declares, and every way each declared source is reached.

def _normalize_level(level):
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_resolve as _pr
        return _pr.normalize_level(level)
    except Exception:                                        # noqa: BLE001
        return {'team': 'shared'}.get(str(level or '').strip().lower(),
                                      str(level or '').strip().lower())


def declared_sources(root, user=True):
    """-> (sources, notes): every source precedent.json declares plus the
    person's own individual set from their user config, each as
    {level, name, path (resolved), repo (optional)}. user=False leaves the
    user config out: what the repo itself declares, the same on every
    machine.

    Deliberately NOT precedent_resolve.load_config(): that call self-heals
    (it may clone a missing source), and a freshness notice that clones
    things at session start is doing the deliberate step it exists to
    announce. This reads the two files and nothing else."""
    root = pathlib.Path(root).resolve()
    sources, notes = [], []
    cfg_path = root / REPO_CONFIG
    if cfg_path.is_file():
        cfg, why = _read_json(cfg_path)
        if cfg is None:
            notes.append(why)
        else:
            for entry in cfg.get('sources') or []:
                if not isinstance(entry, dict) or not entry.get('path'):
                    continue
                p = pathlib.Path(os.path.expandvars(str(entry['path']))).expanduser()
                p = (p if p.is_absolute() else root / p).resolve()
                src = {'level': _normalize_level(entry.get('level')),
                       'name': str(entry.get('name') or entry.get('level')),
                       'path': p}
                if entry.get('repo'):
                    src['repo'] = str(entry['repo']).strip()
                sources.append(src)
    user_cfg = pathlib.Path(os.environ.get(USER_CONFIG_ENV,
                                           DEFAULT_USER_CONFIG)).expanduser()
    if user and user_cfg.is_file():
        cfg, why = _read_json(user_cfg)
        if cfg is None:
            notes.append(why)
        else:
            ind = cfg.get('individual') or {}
            if isinstance(ind, dict) and ind.get('path'):
                src = {'level': 'individual',
                       'name': str(ind.get('name') or 'individual'),
                       'path': pathlib.Path(ind['path']).expanduser().resolve()}
                if ind.get('repo_url'):
                    src['repo'] = str(ind['repo_url']).strip()
                sources.append(src)
    return sources, notes


def _vendored_manifest_path(root, src):
    """process/manifest.json holds the universal tree; a named set's code
    dirs are tracked by process/manifest_<name>.json (checkin.py's
    convention)."""
    root = pathlib.Path(root)
    if src['level'] == 'universal':
        return root / 'process' / 'manifest.json'
    return root / 'process' / f"manifest_{src['name']}.json"


def _live_clone(path, root):
    """-> {url, branch, head} when `path` is the top of its own git work
    tree (a sibling clone the practices load from), else None. The repo's
    own root is never a live clone of a source: that is this repo's branch,
    and the freshness guard already watches it."""
    path = pathlib.Path(path)
    if not path.is_dir() or path.resolve() == pathlib.Path(root).resolve():
        return None
    rc, top = _git('rev-parse', '--show-toplevel', cwd=path)
    if rc != 0 or not top or pathlib.Path(top).resolve() != path.resolve():
        return None
    _, head = _git('rev-parse', 'HEAD', cwd=path)
    _, url = _git('remote', 'get-url', 'origin', cwd=path)
    _, branch = _git('rev-parse', '--abbrev-ref', 'HEAD', cwd=path)
    if branch in ('', 'HEAD'):
        _, ref = _git('symbolic-ref', '--short', 'refs/remotes/origin/HEAD',
                      cwd=path)
        branch = ref.split('/', 1)[1] if '/' in ref else ''
    return {'url': url, 'branch': branch, 'head': head}


def collect_targets(root='.'):
    """-> list of rows, one per way a declared source is reached here:
    {label, kind, url, branch, recorded, problem}. `problem` set means the
    row cannot be compared and says why; the caller prints it as
    not-checked, never as current."""
    root = pathlib.Path(root).resolve()
    rows = []

    manifest, why = read_manifest(root)
    if manifest is None:
        # No manifest file at all is not an unverified source: nothing was
        # vendored, so nothing can be stale. A malformed one is unverified.
        rows.append({'label': 'vendored engine (tools/)', 'kind': 'engine',
                     'problem': why,
                     'nothing_vendored': not (pathlib.Path(root)
                                              / MANIFEST).is_file()})
    else:
        url, branch, recorded = (manifest.get('source_repo'),
                                 manifest.get('source_branch'),
                                 manifest.get('source_commit'))
        if url and branch and recorded:
            rows.append({'label': 'vendored engine (tools/)', 'kind': 'engine',
                         'url': url, 'branch': branch, 'recorded': recorded,
                         'manifest': manifest})
        else:
            rows.append({'label': 'vendored engine (tools/)', 'kind': 'engine',
                         'problem': 'the manifest does not record source_repo, '
                                    'source_branch and source_commit'})

    sources, notes = declared_sources(root)
    for n in notes:
        rows.append({'label': REPO_CONFIG, 'kind': 'config', 'problem': n})
    for src in sources:
        if src['level'] == 'repo-local':
            continue
        who = f"{src['name']} ({src['level']})"
        reached = 0
        mp = _vendored_manifest_path(root, src)
        if mp.is_file():
            reached += 1
            m, why = _read_json(mp)
            up = (m or {}).get('upstream') or {}
            where = up.get('vendored_at') or str(src['path'].relative_to(root)
                                                  if src['path'].is_relative_to(root)
                                                  else src['path'])
            label = f'{who} vendored at {where}'
            if m is None:
                rows.append({'label': label, 'kind': 'vendored', 'problem': why})
            elif up.get('repo') and up.get('branch') and up.get('commit'):
                rows.append({'label': label, 'kind': 'vendored',
                             'url': up['repo'], 'branch': up['branch'],
                             'recorded': up['commit']})
            else:
                rows.append({'label': label, 'kind': 'vendored',
                             'problem': f'{mp.relative_to(root)} records no '
                                        f'upstream repo, branch and commit'})
        # A section 0 catalogue (a copy of the universal practices inside
        # this repository) records its own sync in CATALOGUE_SYNC.json, which
        # precedent_update.py writes: the commit it was replaced from, of the
        # same repository and branch the engine comes from. Until 2026-10-04
        # nothing here read it, and a consumer holding 159 practices there
        # was told at every session start that they were absent.
        sync = src['path'] / CATALOGUE_SYNC
        if not mp.is_file() and sync.is_file():
            reached += 1
            m, why = _read_json(sync)
            commit = (m or {}).get('source_commit')
            where = (str(src['path'].relative_to(root))
                     if src['path'].is_relative_to(root) else str(src['path']))
            label = f'{who} vendored at {where}'
            url = (manifest or {}).get('source_repo')
            branch = (manifest or {}).get('source_branch')
            if m is None:
                rows.append({'label': label, 'kind': 'vendored', 'problem': why})
            elif commit and url and branch:
                rows.append({'label': label, 'kind': 'vendored', 'url': url,
                             'branch': branch, 'recorded': commit})
            else:
                rows.append({'label': label, 'kind': 'vendored',
                             'problem': f'{CATALOGUE_SYNC} records no source_commit, '
                                        f'or the engine manifest names no repository '
                                        f'and branch to compare it with'})
        live = _live_clone(src['path'], root)
        if live is not None:
            reached += 1
            label = f"{who} live clone at {src['path']}"
            url = live['url'] or (src.get('repo') if '://' in str(src.get('repo', '')) else '')
            if not url:
                rows.append({'label': label, 'kind': 'live',
                             'problem': 'the clone has no origin remote and the '
                                        'declaration names no full repository URL'})
            elif not live['branch']:
                rows.append({'label': label, 'kind': 'live',
                             'problem': 'the clone is on no branch and origin '
                                        'declares no HEAD to compare against'})
            else:
                rows.append({'label': label, 'kind': 'live', 'url': url,
                             'branch': live['branch'], 'recorded': live['head'],
                             'path': str(src['path'])})
        if reached == 0 and src['path'].resolve() != root:
            rows.append({'label': f"{who} at {src['path']}", 'kind': 'absent',
                         'problem': 'declared, but neither a vendored manifest '
                                    'nor a git clone is there -- its practices '
                                    'are absent this session, not merely stale'})
    return rows


# --------------------------------------------------------------------------
# Which source a path in this repo was copied from (2026-10-06).
#
# A session that hits a bug in a vendored file has to fix it where the file
# comes from, not here (practice: upstream-fix). The two tools that act on
# that -- doc_lint.py's check on an open item that is really an upstream
# fix, and upstream_fix.py, which sets the fix up in the source's clone --
# both need to know which paths here are copies and of what. The answer is
# the same manifests and declarations collect_targets() reads above, so it
# is worked out here, once.

# Fallbacks for a tree whose vendoring tool is not importable; the live
# values are precedent_vendor_engine.HOOK_SOURCE_DIR / HOOK_DEST_DIR.
_HOOK_DIRS_FALLBACK = ('templates/harness/claude-code/hooks', '.claude/hooks')


def _hook_dirs():
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_vendor_engine as _pve
        return _pve.HOOK_SOURCE_DIR, _pve.HOOK_DEST_DIR
    except Exception:                                        # noqa: BLE001
        return _HOOK_DIRS_FALLBACK


def _repo_basename(repo):
    """'https://github.com/o/Name.git' or 'Name' -> 'Name'."""
    return str(repo or '').rstrip('/').rsplit('/', 1)[-1].removesuffix('.git')


def _source_clone(root, src_path, repo):
    """-> the local clone a fix to `repo` is made in, or None: the source's
    declared path when that is a git work tree outside this repo (a live
    sibling clone), else a clone named after the repository beside this
    repo, the layout INSTALL.md and add_repo both produce."""
    root = pathlib.Path(root).resolve()
    cands = []
    if src_path is not None and not pathlib.Path(src_path).resolve().is_relative_to(root):
        cands.append(pathlib.Path(src_path))
    if _repo_basename(repo):
        cands.append(root.parent / _repo_basename(repo))
    for c in cands:
        if _live_clone(c, root) is not None:
            return c.resolve()
    return None


def vendored_entries(root='.'):
    """-> list of {local, upstream, source, repo, branch, clone}: one per
    vendored engine file (`local` a file path) and one per vendored tree
    (`local` a prefix ending in '/'). `upstream` is the matching path in the
    source repository (a prefix for a tree). `repo`, `branch` and `clone`
    are None when nothing here records them. Never raises."""
    root = pathlib.Path(root).resolve()
    out = []
    manifest, _ = read_manifest(root)
    eng_url = eng_branch = None
    if isinstance(manifest, dict):
        eng_url = manifest.get('source_repo')
        eng_branch = manifest.get('source_branch')
        clone = _source_clone(root, None, eng_url)
        hook_src, hook_dest = _hook_dirs()
        for names, here, there in ((manifest.get('files'), 'tools', 'tools'),
                                   (manifest.get('hook_files'), hook_dest, hook_src)):
            for n in names or []:
                out.append({'local': f'{here}/{n}', 'upstream': f'{there}/{n}',
                            'source': 'engine', 'repo': eng_url,
                            'branch': eng_branch, 'clone': clone})
    sources, _ = declared_sources(root, user=False)
    seen = set()
    for src in sources:
        p = src['path']
        if src['level'] == 'repo-local' or p == root or not p.is_relative_to(root):
            continue
        local = p.relative_to(root).as_posix().rstrip('/') + '/'
        url, branch = src.get('repo'), None
        mp = _vendored_manifest_path(root, src)
        m, _ = _read_json(mp) if mp.is_file() else (None, None)
        up = (m or {}).get('upstream') if isinstance(m, dict) else None
        if isinstance(up, dict) and up.get('repo'):
            url, branch = up['repo'], up.get('branch')
        elif (p / CATALOGUE_SYNC).is_file():
            url, branch = eng_url, eng_branch
        seen.add(local)
        out.append({'local': local, 'upstream': '', 'source': src['name'],
                    'repo': url, 'branch': branch,
                    'clone': _source_clone(root, None, url)})
    # Anything else the one authority on mirrors names (a section 1 tree
    # with no source declared for it) is a copy too, of the universal tree.
    try:
        import precedent_resolve as _pr
        prefixes = _pr.mirrored_prefixes(root)
    except Exception:                                        # noqa: BLE001
        prefixes = ()
    m, _ = _read_json(root / 'process' / 'manifest.json')
    up = (m or {}).get('upstream') if isinstance(m, dict) else None
    up = up if isinstance(up, dict) else {}
    for local in prefixes:
        if local not in seen:
            url = up.get('repo') or eng_url
            out.append({'local': local, 'upstream': '', 'source': 'precedent',
                        'repo': url, 'branch': up.get('branch') or eng_branch,
                        'clone': _source_clone(root, None, url)})
    return out


def origin_of(root, rel):
    """-> the vendored_entries() row `rel` (a repo-relative path) was copied
    from, with `upstream` resolved to that file's path in the source, or
    None when `rel` is this repo's own."""
    rel = str(rel).replace('\\', '/')
    while rel.startswith('./'):
        rel = rel[2:]
    best, depth = None, -1
    for e in vendored_entries(root):
        if e['local'].endswith('/'):
            if rel.startswith(e['local']) and len(e['local']) > depth:
                best = dict(e, local=rel,
                            upstream=e['upstream'] + rel[len(e['local']):])
                depth = len(e['local'])
        elif rel == e['local']:
            return dict(e)
    return best


def source_mentions(root='.'):
    """-> the strings that name, in prose, a repository this repo takes
    something from: each declared shared or individual set's name, and the
    name and github.com/<owner>/<repo> form of every repository a vendored
    path comes from. The universal source's own `name` is left out: it is a
    common word, and its repository is named through the engine manifest."""
    root = pathlib.Path(root).resolve()
    terms = set()
    sources, _ = declared_sources(root, user=False)
    repos = [e['repo'] for e in vendored_entries(root)]
    for src in sources:
        if src['level'] == 'repo-local' or src['path'] == root:
            continue
        if src['level'] != 'universal':
            terms.add(src['name'])
        repos.append(src.get('repo'))
    for r in repos:
        if not r:
            continue
        terms.add(_repo_basename(r))
        if 'github.com/' in r:
            terms.add('github.com/' + r.split('github.com/', 1)[1]
                      .rstrip('/').removesuffix('.git'))
    return sorted(t for t in terms if t)


# --------------------------------------------------------------------------
# The engine row's optional detail: which files moved.

def changed_files(root, repo_url, recorded, tip, tracked):
    """-> (added, removed, changed) among the files this manifest tracks, or
    None when upstream objects could not be fetched. Deliberately separate
    from the notice: this costs a network fetch of real objects, and the
    notice must stay cheap enough to run at every session start."""
    rc, _ = _git('fetch', '--quiet', '--depth', '50', repo_url, tip, cwd=root)
    if rc != 0:
        rc, _ = _git('fetch', '--quiet', repo_url, tip, cwd=root)
        if rc != 0:
            return None
    rc, out = _git('diff', '--name-status', f'{recorded}..{tip}', cwd=root)
    if rc != 0:
        return None
    # NOT filtered to what this manifest ALREADY tracks, and that was the
    # first version's bug. A file upstream started shipping since this repo
    # vendored is not in this manifest yet -- so filtering by `tracked`
    # dropped exactly the case that matters most, "upstream now has
    # something you do not have". Caught by running it against a real repo
    # and noticing leak_gate.py and very_deep_check.py, both newly vendored
    # that same day, absent from the output.
    #
    # So: everything under tools/ and templates/github-actions/, whether or
    # not this repo has it. `tracked` is kept only to mark which lines this
    # repo is already carrying, since "changed under you" and "new to you"
    # read differently to somebody deciding whether to refresh.
    tracked = {f'tools/{n}' for n in tracked}
    added, removed, changed = [], [], []
    for line in out.splitlines():
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        status, path = parts[0][:1], parts[-1]
        if not (path.startswith('tools/')
                or path.startswith('templates/github-actions/')):
            continue
        mark = path if path in tracked else f'{path} (NOT YET VENDORED HERE)'
        (added if status == 'A' else removed if status == 'D'
         else changed).append(mark)
    return sorted(added), sorted(removed), sorted(changed)


def workflow_impact(root, names):
    """-> [(template, installed_as, present)] for each changed CI template
    that this repo actually installs a workflow from.

    THE LINE THAT CLOSES THE LOOP. Without it the report says
    "templates/github-actions/light-check.yml.template changed
    upstream" and stops, and the reader has to know by heart which file in
    their own .github/workflows/ that template produces. That gap is not
    theoretical: the one-job CI templates landed upstream on 2026-09-20 and
    four repos kept billing the three-job shape, because "a template
    changed" and "the workflow I am being billed for is stale" read as
    different facts (spec/BILLING_FLOOR.md).

    Best-effort by design, like everything else here. The mapping lives in
    precedent_vendor_engine.CI_WORKFLOW_TEMPLATES; a repo whose vendored
    engine predates that module, or whose manifest records no kind, gets
    no impact lines and the rest of the report is unaffected."""
    try:
        import precedent_vendor_engine as _ve
        mapping = _ve.CI_WORKFLOW_TEMPLATES
    except Exception:
        return []
    root = pathlib.Path(root)
    bare = {n.split(' ')[0] for n in names}
    rows = []
    for _kind, pairs in sorted(mapping.items()):
        for tmpl, installed_as in pairs:
            if f'templates/github-actions/{tmpl}' not in bare:
                continue
            if not (root / installed_as).is_file():
                continue          # this repo does not install that one
            row = (tmpl, installed_as)
            if row not in [(a, b) for a, b, _ in rows]:
                rows.append((tmpl, installed_as, True))
    return rows


def _engine_detail(root, row, tip, out):
    result = changed_files(root, row['url'], row['recorded'], tip,
                           (row.get('manifest') or {}).get('files') or [])
    if result is None:
        print('  (could not fetch upstream objects, so WHICH files moved '
              'is unknown -- the commit difference above still stands)',
              file=out)
        return
    added, removed, changed = result
    for label, names in (('added upstream', added),
                         ('REMOVED upstream', removed),
                         ('changed upstream', changed)):
        if names:
            print(f'  {label} ({len(names)}): {", ".join(names)}', file=out)
    if not (added or removed or changed):
        print('  no tracked engine file or CI template changed between '
              'those commits', file=out)
    impact = workflow_impact(root, added + removed + changed)
    for tmpl, installed_as, _present in impact:
        print(f'  -> YOU ARE RUNNING THE OLD ONE: {installed_as} in this '
              f'repo was installed from {tmpl}, which is among the changes '
              f'above. Every run of it until the next "Update Vendors" is '
              f'the superseded shape.', file=out)


def report(root='.', with_files=False, quiet=False, out=sys.stdout):
    """One row per way a declared source is reached. Returns 0 always."""
    rows = collect_targets(root)
    tips = {}
    behind = unverified = current = engine_behind = 0
    unverified_sources = 0        # what --quiet reports: no engine row there
    for row in rows:              # to verify is not a source left unverified
        if row.get('problem'):
            unverified += 1
            if not row.get('nothing_vendored'):
                unverified_sources += 1
            if not quiet:
                print(f"freshness: not checked -- {row['label']}: "
                      f"{row['problem']}", file=out)
            continue
        key = (row['url'], row['branch'])
        if key not in tips or (tips[key] is None and row.get('path')):
            tips[key] = upstream_tip(*key, clone=row.get('path'))
        tip = tips[key]
        if tip is None:
            unverified += 1
            unverified_sources += 1
            if not quiet:
                print(f"freshness: NOT VERIFIED -- {row['label']}: could not "
                      f"reach {row['url']} ({row['branch']}). Whether it is "
                      f"current is unknown this session.", file=out)
            continue
        if tip != row['recorded'] and row['kind'] == 'live' and row.get('path'):
            # RE-READ BEFORE SAYING BEHIND (2026-10-06). A consumer's session
            # start reported three set clones BEHIND that were current minutes
            # later, before the session itself had run anything that moves a
            # clone. Its cause is not established (see
            # todo-2026-10-06-freshness-notice-said-behind-for-current-clones);
            # whatever moved them, a clone read once at the top of this run can
            # be out of date by the time its row is printed, so the clone is
            # read again here and judged on what it holds now.
            again = _live_clone(row['path'], root)
            if again and again.get('head'):
                row['recorded'] = again['head']
        if tip == row['recorded']:
            current += 1
            if not quiet:
                print(f"freshness: current -- {row['label']} matches "
                      f"{row['branch']} at {row['recorded'][:12]}", file=out)
            continue
        behind += 1
        engine_behind += row['kind'] == 'engine'
        head = ('ENGINE BEHIND UPSTREAM' if row['kind'] == 'engine'
                else 'BEHIND UPSTREAM')
        print(f"{head}: {row['label']} has {row['recorded'][:12]}; "
              f"{row['url']} {row['branch']} is now at {tip[:12]}.", file=out)
        if row['kind'] == 'live':
            print(f"  Its practices load from that clone as it stands, so "
                  f"until it is brought current this session runs on stale "
                  f"rules. The session-start refresh fast-forwards a clone it "
                  f"can, so this one has changes of its own, another branch "
                  f"or commits of its own, or the refresh has not run: "
                  f"{refresh_remedy(root, row['path'])}", file=out)
        if row['kind'] == 'engine' and with_files:
            _engine_detail(root, row, tip, out)
    if engine_behind:
        # "Update Vendors" moves a vendored engine or catalogue; a live
        # clone behind its own origin takes the pull named on its own line,
        # and pointing it here sent sessions to the wrong fix (2026-09-30).
        print('  Nothing has been changed -- this is a notice. At a merge, '
              'python3 tools/precedent_merge_vendors.py takes it as a commit '
              'of its own; otherwise "Update Vendors". Both are in '
              'practices/vendor-update-runbook.md.', file=out)
    if quiet and unverified_sources:
        print(f'freshness: NOT VERIFIED -- {unverified_sources} source(s) '
              f'could not be checked this session; run python3 '
              f'tools/precedent_engine_freshness.py for which (not verified '
              f'is not current)', file=out)
    if not quiet:
        print(f'freshness: {len(rows)} row(s) -- {current} current, '
              f'{behind} behind, {unverified} not verified (not verified is '
              f'not current)', file=out)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('--root', default='.')
    ap.add_argument('--files', action='store_true',
                    help='also name which tracked engine files moved (needs a fetch)')
    ap.add_argument('--quiet', action='store_true',
                    help='print only the rows that are behind, plus one line '
                         'when any source could not be verified')
    a = ap.parse_args(argv)
    return report(a.root, with_files=a.files, quiet=a.quiet)


if __name__ == '__main__':
    sys.exit(main())
