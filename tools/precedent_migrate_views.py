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
    python3 tools/precedent_migrate_views.py --repo DIR --split [--check]
        turn MAP.source.md / GLOSSARY.source.md into the directories
        MAP.source/ / GLOSSARY.source/, one file per heading and one per
        table row, so two branches adding rows never touch the same file
        (build_views.py, THE SOURCE AS A DIRECTORY)

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
        if bv.has_own_source(repo, source):
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
        # Only a view that is here, with the source it is built from: an entry
        # naming a missing source sends a reader nowhere, and
        # generated-files-registered refuses it (a consumer with no root
        # glossary, 2026-10-03). A labelled view with no source still joins
        # the list below, from its own label.
        if not ((repo / view).is_file() and bv.has_own_source(repo, source)):
            continue
        sdir = bv.source_dir_name(source)
        files.append({'path': view, 'generated_by': 'tools/build_views.py',
                      'edit_instead': bv.own_source_label(repo, source),
                      'inputs': [source, f'{sdir}/*', 'practices/*.md', '*.json'],
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
        # joins the list here. One whose views a vendor update had already
        # overwritten has no source file yet: it gets an empty one, as a
        # fresh install would, so the list names a file that exists and a
        # commit that edits it rebuilds the view. Without both, the commit
        # backstop rebuilt nothing there (found 2026-10-03 rehearsing a
        # consumer overwritten on 2026-09-15).
        made = [s for v, s in VIEWS if not bv.has_own_source(repo, s)
                and (repo / v).is_file() and bv.is_generated_view(repo / v)]
        if made:
            for s in made:
                (repo / s).write_text('', encoding='utf-8')
            r = subprocess.run([sys.executable, str(HERE / 'build_views.py'), '--repo',
                                str(repo), '--views-only'], capture_output=True, text=True)
            if r.returncode != 0:
                for s in made:
                    (repo / s).unlink(missing_ok=True)
                say(f'precedent_migrate_views: could not regenerate the views with '
                    f'empty {", ".join(made)}, so none was written. '
                    f'{(r.stdout + r.stderr).strip()[-400:]}')
                return 1
            say(f'precedent_migrate_views: {", ".join(made)} written empty -- the '
                f'views were already generated; what this repository says about '
                f'itself goes there, and the view follows it at commit.')
        if any(bv.has_own_source(repo, s) for _v, s in VIEWS):
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
    # A view this repository never had, with no source, is never added here:
    # build_views --views-only skips it (a consumer whose glossary lives in
    # docs/ came out with a second one at its root, 2026-10-03), so there is
    # nothing to clean up after the build.
    write_list(repo)
    for view, source, _t in todo:
        say(f'precedent_migrate_views: {view} -> {source}, word for word; {view} is now '
            f'generated from it plus the catalogue and the engine. Edit {source}, never '
            f'{view}.')
    return 0


# ---- --split: one file per heading and per table row ----------------------
import re as _re

_HEADING = _re.compile(r'^#{1,6}\s')
_FENCE = _re.compile(r'^\s*(```|~~~)')
_TABLE_SEP = _re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$')


def _slug(text, fallback):
    text = _re.sub(r'\]\([^)]*\)', ']', text)          # drop link targets
    text = _re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return (text[:48].rstrip('-')) or fallback


def _chunks(text):
    """-> [(heading line or '', [lines])], split at headings outside code."""
    out, cur, head, fence = [], [], '', False
    for line in text.split('\n'):
        if _FENCE.match(line):
            fence = not fence
        if not fence and _HEADING.match(line) and cur:
            out.append((head, cur))
            cur, head = [], line
        elif not fence and _HEADING.match(line):
            head = line
        cur.append(line)
    if cur:
        out.append((head, cur))
    return out


def _strip_blank(lines):
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


def _largest_table(lines):
    """-> (separator index, first row, end) of the table with most rows."""
    best, fence = None, False
    i = 0
    while i < len(lines):
        if _FENCE.match(lines[i]):
            fence = not fence
        if (not fence and i > 0 and _TABLE_SEP.match(lines[i])
                and lines[i - 1].lstrip().startswith('|')):
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith('|'):
                j += 1
            if best is None or (j - i - 1) > (best[2] - best[1]):
                best = (i, i + 1, j)
            i = j
            continue
        i += 1
    return best


def split_entries(text):
    """-> {relative path: content} for a source text, by the assembly rules
    in build_views.py. A section is split at its largest table only when the
    split reassembles to the same words; otherwise it stays one file."""
    files = {}
    for n, (head, lines) in enumerate(_chunks(text.strip('\n')), 1):
        lines = _strip_blank(lines)
        if not lines:
            continue
        name = f'{n * 10:04d}-{_slug(head.lstrip("#"), "intro")}'
        whole = '\n'.join(lines)
        t = _largest_table(lines)
        if t is None or t[2] - t[1] < 2:
            files[f'{name}.md'] = whole + '\n'
            continue
        sep, first, end = t
        part = {f'{name}/{bv.SECTION_HEAD}': '\n'.join(lines[:sep + 1]) + '\n'}
        seen = set()
        for k, row in enumerate(lines[first:end], 1):
            cells = [c for c in row.strip().strip('|').split('|')]
            slug = _slug(cells[0] if cells else '', 'row')
            base, m = slug, 2
            while slug in seen:
                slug, m = f'{base}-{m}', m + 1
            seen.add(slug)
            part[f'{name}/{k * 10:04d}-{slug}.md'] = row + '\n'
        tail = _strip_blank(lines[end:])
        if tail:
            part[f'{name}/{bv.SECTION_TAIL}'] = '\n'.join(tail) + '\n'
        # Keep the split only if it reassembles to this section's own text.
        rebuilt = '\n'.join(lines[:sep + 1] + lines[first:end])
        if tail:
            rebuilt += '\n\n' + '\n'.join(tail)
        if rebuilt == whole:
            files.update(part)
        else:
            files[f'{name}.md'] = whole + '\n'
    return files


def _same_words(a, b):
    norm = lambda t: _re.sub(r'\n{3,}', '\n\n', t.strip('\n'))
    return norm(a) == norm(b)


def split(repo, check=False, say=print):
    """Turn each one-file source into its directory form. -> 0 done or
    nothing to do, 1 refused (nothing changed)."""
    import shutil, tempfile
    repo = pathlib.Path(repo)
    did = 0
    for view, source in VIEWS:
        f, d = repo / source, repo / bv.source_dir_name(source)
        if not f.is_file() or d.exists():
            continue
        text = f.read_text(encoding='utf-8')
        entries = split_entries(text)
        tmp = pathlib.Path(tempfile.mkdtemp(prefix='split-', dir=repo))
        try:
            for rel, content in entries.items():
                (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
                (tmp / rel).write_text(content, encoding='utf-8')
            if not _same_words(bv.assemble_source_dir(tmp), text):
                say(f'precedent_migrate_views: REFUSED -- {source} would not '
                    f'reassemble word for word from a directory; nothing changed.')
                return 1
            if check:
                say(f'would split {source} into {d.name}/ ({len(entries)} files)')
                continue
            tmp.rename(d)
            tmp = None
            f.unlink()
            did += 1
            say(f'precedent_migrate_views: {source} -> {d.name}/, {len(entries)} '
                f'files; add a row as a new file between two others (0015- goes '
                f'between 0010- and 0020-).')
        finally:
            if tmp is not None:
                shutil.rmtree(tmp, ignore_errors=True)
    if did:
        r = subprocess.run([sys.executable, str(HERE / 'build_views.py'), '--repo',
                            str(repo), '--views-only'], capture_output=True, text=True)
        if r.returncode != 0:
            say(f'precedent_migrate_views: the views did not rebuild: '
                f'{(r.stdout + r.stderr).strip()[-400:]}')
            return 1
        write_list(repo)
    elif not check:
        say('precedent_migrate_views: nothing to split.')
    return 0


def main(argv):
    if '--help' in argv or '-h' in argv:
        print(__doc__.strip())
        return 0
    if '--repo' not in argv or argv.index('--repo') + 1 >= len(argv):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    repo = pathlib.Path(argv[argv.index('--repo') + 1]).resolve()
    restore = (argv[argv.index('--restore-map-from') + 1]
               if '--restore-map-from' in argv else None)
    if '--split' in argv:
        return split(repo, check='--check' in argv)
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
