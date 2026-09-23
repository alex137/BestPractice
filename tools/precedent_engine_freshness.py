#!/usr/bin/env python3
"""Say whether anything this repo vendors or resolves live has fallen behind
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
push and merge moments. It PRINTS and never refreshes anything -- the same
shape precedent_upstream_check.py has had since 2026-09-08, at Morgan's own
request: "I don't want it to merge invisibly, I'd like to do it in a session
when I'm there."

  python3 tools/precedent_engine_freshness.py           # every source, one row each
  python3 tools/precedent_engine_freshness.py --files   # + which engine files changed
  python3 tools/precedent_engine_freshness.py --quiet   # only rows that are behind

EXIT STATUS IS 0 IN EVERY CASE, including no network, no manifest and a
malformed one. A session start that a network hiccup can block is worse than
the staleness it was guarding against (practice: fail-gracefully). What that
practice requires instead is that the outcomes never render alike: a row is
`current`, `BEHIND`, or `NOT VERIFIED`, and unknown is never printed as
current. `--quiet` prints only BEHIND rows, so a repo whose every source is
current -- or unreachable -- says nothing; the full run is where unreachable
is spelled out. `--files` needs to fetch upstream objects and is therefore
NOT what the hook runs.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

MANIFEST = pathlib.Path('tools') / 'ENGINE_MANIFEST.json'
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


def upstream_tip(repo_url, branch):
    rc, out = _git('ls-remote', repo_url, f'refs/heads/{branch}')
    if rc != 0 or not out:
        return None
    return out.split()[0]


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


def declared_sources(root):
    """-> (sources, notes): every source precedent.json declares plus the
    person's own individual set from their user config, each as
    {level, name, path (resolved), repo (optional)}.

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
    if user_cfg.is_file():
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
        rows.append({'label': 'vendored engine (tools/)', 'kind': 'engine',
                     'problem': why})
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
    "templates/github-actions/precedent-check.yml.template changed
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
    behind = unverified = current = 0
    for row in rows:
        if row.get('problem'):
            unverified += 1
            if not quiet:
                print(f"freshness: not checked -- {row['label']}: "
                      f"{row['problem']}", file=out)
            continue
        key = (row['url'], row['branch'])
        if key not in tips:
            tips[key] = upstream_tip(*key)
        tip = tips[key]
        if tip is None:
            unverified += 1
            if not quiet:
                print(f"freshness: NOT VERIFIED -- {row['label']}: could not "
                      f"reach {row['url']} ({row['branch']}). Whether it is "
                      f"current is unknown this session.", file=out)
            continue
        if tip == row['recorded']:
            current += 1
            if not quiet:
                print(f"freshness: current -- {row['label']} matches "
                      f"{row['branch']} at {row['recorded'][:12]}", file=out)
            continue
        behind += 1
        head = ('ENGINE BEHIND UPSTREAM' if row['kind'] == 'engine'
                else 'BEHIND UPSTREAM')
        print(f"{head}: {row['label']} has {row['recorded'][:12]}; "
              f"{row['url']} {row['branch']} is now at {tip[:12]}.", file=out)
        if row['kind'] == 'live':
            print(f"  Its practices load from that clone as it stands, so "
                  f"until it is fetched this session runs on stale rules: "
                  f"git -C {row['path']} pull --ff-only", file=out)
        if row['kind'] == 'engine' and with_files:
            _engine_detail(root, row, tip, out)
    if behind:
        print('  Nothing has been changed -- this is a notice. To take it: '
              '"Update Vendors" (practices/vendor-update-runbook.md).', file=out)
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
                    help='print only the rows that are actually behind')
    a = ap.parse_args(argv)
    return report(a.root, with_files=a.files, quiet=a.quiet)


if __name__ == '__main__':
    sys.exit(main())
