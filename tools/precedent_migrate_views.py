#!/usr/bin/env python3
"""Moves a repository's hand-written MAP.md and GLOSSARY.md into their source files, word for word, and generates both from then on

precedent_migrate_views.py -- the one-time migration of
spec/GENERATED_FILES_PLAN.md step 5 (Morgan, 2026-10-03: MAP.md and
GLOSSARY.md are generated in every repository, never hand-edited, and a
repository that uses Precedent keeps everything it wrote).

    python3 tools/precedent_migrate_views.py --repo DIR            migrate, then regenerate
    python3 tools/precedent_migrate_views.py --repo DIR --check    say what it would do; change nothing
    python3 tools/precedent_migrate_views.py --repo DIR --restore-map-from REV
        a map a vendor update already overwrote: take MAP.source.md from
        MAP.md as it stood at REV (the person picks REV)

For each of MAP.md and GLOSSARY.md that is hand-written -- it carries no
`generated_by: tools/build_views.py` label -- and has no source file yet,
the whole file moves into MAP.source.md / GLOSSARY.source.md exactly as it
is, then build_views.py regenerates the view: the repository's own text
first, word for word, then the sections generated from the practice
catalogue and the engine. Afterwards the generated view must contain the
original text unchanged, or the migration is undone and says so (practice:
repair-cannot-discard-work). It also writes the repository's own
tools/generated_files.json entries for both views, so a commit that changes
a source rebuilds them.

Exit 0 migrated or nothing to do; 1 a view could not be migrated without
loss (nothing is left changed); 2 a usage error.
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_views as bv  # noqa: E402

VIEWS = (('MAP.md', bv.MAP_SOURCE), ('GLOSSARY.md', bv.GLOSSARY_SOURCE))


def _engine_rel(repo):
    """-> this engine's directory relative to `repo` ('tools' or
    'process/upstream/tools'), for the commands the list records."""
    try:
        return str(HERE.relative_to(pathlib.Path(repo).resolve()))
    except ValueError:
        return 'tools'


def plan(repo, restore_from=None):
    """-> [(view, source, text to write into source)] -- what migrating
    `repo` would do. A view already migrated, missing, or generated (and
    not being restored) needs nothing."""
    repo = pathlib.Path(repo)
    out = []
    for view, source in VIEWS:
        vp, sp = repo / view, repo / source
        if sp.is_file():
            if view == 'MAP.md' and restore_from:
                raise SystemExit(f'precedent_migrate_views: {source} already exists, so '
                                 f'nothing was restored over it; bring back what you '
                                 f'need from {restore_from} into it by hand.')
            continue
        if view == 'MAP.md' and restore_from:
            r = subprocess.run(['git', '-C', str(repo), 'show', f'{restore_from}:{view}'],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit(f'precedent_migrate_views: {view} is not at {restore_from}: '
                                 f'{r.stderr.strip()[:200]}')
            if bv.GENERATED_BY_RE.match(r.stdout[:2000]):
                raise SystemExit(f'precedent_migrate_views: {view} at {restore_from} is '
                                 f'already generated; name a commit from before it was '
                                 f'overwritten.')
            out.append((view, source, r.stdout))
            continue
        if not vp.is_file() or bv.is_generated_view(vp):
            continue
        out.append((view, source, vp.read_text(encoding='utf-8')))
    return out


def write_list(repo):
    """Add MAP.md and GLOSSARY.md to the repository's own
    tools/generated_files.json, keeping whatever else it lists."""
    repo = pathlib.Path(repo)
    eng = _engine_rel(repo)
    path = repo / 'tools' / 'generated_files.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    except ValueError:
        data = {}
    files = [e for e in data.get('files') or [] if e.get('path') not in ('MAP.md', 'GLOSSARY.md')
             or e.get('part')]
    for view, source in VIEWS:
        files.append({'path': view, 'generated_by': 'tools/build_views.py',
                      'edit_instead': source,
                      'inputs': [source, 'practices/*.md', '*.json'],
                      'regenerate': f'python3 {eng}/build_views.py --repo . --views-only',
                      'check': [f'{eng}/build_views.py', '--repo', '.', '--views-only',
                                '--check']})
    data.setdefault('_comment', [
        "Every file a tool here writes wholesale: what precedent_check.py's",
        "generated-files-registered checks and what the commit backstop",
        "rebuilds when one of its inputs changes. Never edit those files by",
        "hand: change their sources and let them be rebuilt. This list is",
        "this repository's own."])
    import precedent_regenerate as rg
    files += rg.labelled_entries(repo, eng, {e.get('path') for e in files
                                             if not e.get('part')})
    data['files'] = files
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return path


def migrate(repo, restore_from=None, say=print):
    """Migrate `repo`. -> 0 done or nothing to do, 1 refused (nothing left
    changed)."""
    repo = pathlib.Path(repo)
    todo = plan(repo, restore_from)
    if not todo:
        # A repository already on source files keeps its list complete: a
        # fresh install writes the sources itself, and a later labelled file
        # joins the list here.
        if any((repo / s).is_file() for _v, s in VIEWS):
            write_list(repo)
        say('precedent_migrate_views: nothing to migrate -- MAP.md and GLOSSARY.md '
            'are already generated from their sources, or absent.')
        return 0
    before = {v: (repo / v).read_bytes() if (repo / v).is_file() else None for v, _ in VIEWS}
    for _view, source, text in todo:
        (repo / source).write_text(text, encoding='utf-8')
    r = subprocess.run([sys.executable, str(HERE / 'build_views.py'), '--repo', str(repo),
                        '--views-only'],
                       capture_output=True, text=True)
    lost = []
    for view, source, text in todo:
        now = (repo / view).read_text(encoding='utf-8') if (repo / view).is_file() else ''
        if r.returncode != 0 or text.rstrip('\n') not in now:
            lost.append(view)
    if lost:
        for view, source, _t in todo:
            (repo / source).unlink(missing_ok=True)
        for view, data in before.items():
            if data is not None:
                (repo / view).write_bytes(data)
        say(f'precedent_migrate_views: REFUSED -- {", ".join(lost)} would not carry its '
            f'text unchanged after regeneration, so everything was put back as it was. '
            f'{(r.stdout + r.stderr).strip()[-400:]}')
        return 1
    write_list(repo)
    for view, source, _t in todo:
        say(f'precedent_migrate_views: {view} -> {source}, word for word; {view} is now '
            f'generated from it plus the catalogue and the engine. Edit {source}, never '
            f'{view}.')
    return 0


def main(argv):
    if '--repo' not in argv or argv.index('--repo') + 1 >= len(argv):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    repo = pathlib.Path(argv[argv.index('--repo') + 1]).resolve()
    restore = (argv[argv.index('--restore-map-from') + 1]
               if '--restore-map-from' in argv else None)
    if '--check' in argv:
        todo = plan(repo, restore)
        for view, source, _t in todo:
            print(f'would move {view} into {source} and generate {view} from it')
        if not todo:
            print('nothing to migrate')
        return 0
    return migrate(repo, restore)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
