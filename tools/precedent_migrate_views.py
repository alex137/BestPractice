#!/usr/bin/env python3
"""Moves a hand-written MAP.md and GLOSSARY.md into their sources, and splits any index many threads add rows to into a directory of one file per row, joined back into the file people read

precedent_migrate_views.py -- the one-time migration of
spec/GENERATED_FILES_PLAN.md step 5 (Morgan, 2026-10-03: MAP.md and
GLOSSARY.md are generated in every repository, never hand-edited, and a
repository that uses Precedent keeps everything it wrote).

    python3 tools/precedent_migrate_views.py --repo DIR            migrate, then regenerate
    python3 tools/precedent_migrate_views.py --repo DIR --check    say what it would do; change nothing
    python3 tools/precedent_migrate_views.py --repo DIR --find-lost
        say, for MAP.md and GLOSSARY.md, the last hand-written version in
        git history and every heading and table row of it that neither the
        source nor the view carries now; changes nothing. Exit 1 when
        something is missing
    python3 tools/precedent_migrate_views.py --repo DIR --restore-from REV
        views a writer already overwrote: take MAP.source.md and
        GLOSSARY.source.md from MAP.md and GLOSSARY.md as they stood at REV
        (the person picks REV; --find-lost names the likely one). A view
        that was already generated at REV is skipped and said; a source
        that exists and is not empty is never written over.
        --restore-map-from REV does the map alone, as before
    python3 tools/precedent_migrate_views.py --repo DIR --split [--check]
        turn MAP.source.md / GLOSSARY.source.md into the directories
        MAP.source/ / GLOSSARY.source/, one file per heading and one per
        table row, so two branches adding rows never touch the same file
        (build_views.py, THE SOURCE AS A DIRECTORY)
    python3 tools/precedent_migrate_views.py --repo DIR --split-file PATH [--check]
        the same split for ANY Markdown index made of headings and pipe
        tables (practice: shared-index-is-a-directory): PATH stays where it
        is as the generated view, and its text moves into the directory
        PATH without .md (docs/INDEX.md -> docs/INDEX/), one file per
        heading and per table row. Refused unless the directory rebuilds
        PATH byte for byte; --normalize-blank-lines accepts a file whose
        only difference is blank lines (two or more between blocks, or none
        above a heading). A row's file name drops a version token its first
        cell ends with (plan_v1.md -> ...-plan.md). The view is registered in
        tools/generated_files.json where the repository keeps one.
    python3 tools/precedent_migrate_views.py --repo DIR --join SRC --out PATH [--check] [--force]
        rebuild PATH from the directory SRC -- what a consuming repository's
        build and its commit backstop run; --check exits 1 when PATH is out
        of date and changes nothing. A line typed into PATH by hand that no
        entry file holds is never overwritten silently: the join refuses and
        names it, and --force overrides once it has been moved into SRC.
        The old wording of an entry reworded in SRC is not such a line: what
        SRC's recent commits held counts as SRC.

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

A view already generated, with no source yet, gets an empty source -- but
only when its history holds no hand-written version with entries the view
has lost. When it does, the migration refuses and names the commit to
restore from: on 2026-10-05 it wrote a consumer's MAP.source.md and
GLOSSARY.source.md empty a month after a writer had erased the text they
should have held, and nothing looked in history (a consumer's root-issues
report, 2026-10-19). --accept-loss writes them empty anyway, for a person
who has read what is listed and decided.

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


def _empty_source(repo, source):
    """True when `source` is a file holding nothing but whitespace: the
    placeholder an earlier migration wrote, which a restore may fill."""
    p = pathlib.Path(repo) / source
    return p.is_file() and not p.read_text(encoding='utf-8').strip()


def plan(repo, restore_from=None, restore_views=('MAP.md',), say=print):
    """-> [(view, source, text to write into source)] -- what migrating
    `repo` would do. A view already migrated, missing, or generated (and
    not being restored) needs nothing. `restore_views` are the views a
    `restore_from` applies to."""
    repo = pathlib.Path(repo)
    out = []
    restoring = [v for v, _s in VIEWS if restore_from and v in restore_views]
    for view, source in VIEWS:
        vp = repo / view
        restore = view in restoring
        if bv.has_own_source(repo, source) and not (restore and _empty_source(repo, source)):
            if restore:
                raise SystemExit(f'precedent_migrate_views: {bv.own_source_label(repo, source)} '
                                 f'already exists and holds text, so nothing was restored over it; '
                                 f'bring back what you need from {restore_from} into it '
                                 f'by hand (--find-lost lists it).')
            continue
        if restore:
            r = subprocess.run(['git', '-C', str(repo), 'show', f'{restore_from}:{view}'],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit(f'precedent_migrate_views: {view} is not at {restore_from}: '
                                 f'{r.stderr.strip()[:200]}')
            if bv._ANY_GENERATED_LABEL.match(r.stdout[:2000]):
                if len(restoring) == 1:
                    raise SystemExit(f'precedent_migrate_views: {view} at {restore_from} is '
                                     f'already generated; name a commit from before it was '
                                     f'overwritten (--find-lost names one).')
                say(f'precedent_migrate_views: {view} at {restore_from} is already '
                    f'generated, so it is not restored from there.')
                continue
            out.append((view, source, r.stdout))
            continue
        if not vp.is_file() or bv.is_generated_view(vp):
            continue
        out.append((view, source, vp.read_text(encoding='utf-8')))
    return out


def find_lost(repo, say=print):
    """Report, per view, what --find-lost promises. -> 0 nothing missing,
    1 something is."""
    repo = pathlib.Path(repo)
    missing = 0
    for view, _source in VIEWS:
        found = bv.lost_hand_entries(repo, view)
        if found is None:
            say(f'{view}: {bv.view_owner(repo, view)}; no earlier hand-written version '
                f'was replaced, so nothing to compare.')
            continue
        sha, lines = found
        if not lines:
            say(f'{view}: every heading and row of its last hand-written version '
                f'({sha[:10]}) is still here.')
            continue
        missing += 1
        say(f'{view}: {len(lines)} heading(s) or row(s) of its last hand-written version '
            f'({sha[:10]}) are in neither {view} nor its source now. Each is either '
            f'dropped on purpose or lost; restore what was lost into the source:')
        for line in lines:
            say(f'    {line[:200]}')
    return 1 if missing else 0


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


def migrate(repo, restore_from=None, say=print, restore_views=('MAP.md',),
            accept_loss=False):
    """Migrate `repo`. -> 0 done or nothing to do, 1 refused (nothing left
    changed)."""
    repo = pathlib.Path(repo)
    todo = plan(repo, restore_from, restore_views, say)
    if not todo:
        # A repository already on source files keeps its list complete: a
        # fresh install writes the sources itself, and a later labelled file
        # joins the list here. One whose views a vendor update had already
        # overwritten has no source file yet: it gets an empty one, as a
        # fresh install would, so the list names a file that exists and a
        # commit that edits it rebuilds the view. Without both, the commit
        # backstop rebuilt nothing there (found 2026-10-03 rehearsing a
        # consumer overwritten on 2026-09-15).
        made = [s for v, s in VIEWS if bv.view_owner(repo, v) == bv.OWNER_ENGINE]
        # A view a writer turned from hand-written into generated may hold
        # less than it did; an empty source then makes the loss permanent
        # with no word said (2026-10-05). Look in history first.
        erased = {}
        for v, s in VIEWS:
            if s in made:
                found = bv.lost_hand_entries(repo, v)
                if found and found[1]:
                    erased[v] = found
        if erased and not accept_loss:
            for v, (sha, lines) in erased.items():
                say(f'precedent_migrate_views: REFUSED -- {v} was hand-written until a '
                    f'writer replaced it with a generated one, and {len(lines)} heading(s) '
                    f'or row(s) of its last hand-written version ({sha[:10]}) are not in it '
                    f'now. Writing an empty source would make that loss permanent.')
            # The newest of those commits holds every view's last hand-written
            # copy at once, so one restore brings all of them back.
            newest = max((sha for sha, _l in erased.values()), key=lambda c: subprocess.run(
                ['git', '-C', str(repo), 'show', '-s', '--format=%ct', c],
                capture_output=True, text=True).stdout.strip() or '0')
            say(f'precedent_migrate_views: --find-lost lists what is missing. Restore with '
                f'--restore-from {newest}, or put back what matters by hand, or pass '
                f'--accept-loss once a person has read that list and decided.')
            return 1
        if made:
            for s in made:
                (repo / s).write_text('', encoding='utf-8')
            # These views were already generated with no source to compare
            # against, so nothing in them can be told apart as typed by hand:
            # --force, as a fresh install's first build.
            r = subprocess.run([sys.executable, str(HERE / 'build_views.py'), '--repo',
                                str(repo), '--views-only', '--force'],
                               capture_output=True, text=True)
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
    # Restoring from a named commit replaces the view by the person's
    # choice, so its current lines are not hand edits to protect: --force.
    r = subprocess.run([sys.executable, str(HERE / 'build_views.py'), '--repo', str(repo),
                        '--views-only', *(['--force'] if restore_from else [])],
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


# A version token at the end of a slug, with any file-extension word after
# it: a row naming plan_v1.md was filed as ...-plan-v1-md.md, a name the
# repository's own no-version-suffix check then refuses (a downstream repo,
# 2026-10-12). The tokens are that check's version tokens (v1, version2,
# rev3); its state words (final, draft, ...) are ordinary English and stay.
_EXT_WORDS = ('md|markdown|txt|html?|pdf|docx?|xlsx?|xlsm|csv|tsv|pptx?|json|ya?ml|py|'
              'sh|js|ts|png|jpe?g|svg')
_VERSION_TAIL = _re.compile(rf'-(?:v\d+|version\d*|rev\d+)(?:-(?:{_EXT_WORDS}))?$')


def _drop_version_tail(text):
    while _VERSION_TAIL.search(text):
        text = _VERSION_TAIL.sub('', text)
    return text


def _slug(text, fallback):
    text = _re.sub(r'\]\([^)]*\)', ']', text)          # drop link targets
    text = _re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    text = _drop_version_tail('-' + text)[:49].rstrip('-')
    return _drop_version_tail(text).lstrip('-') or fallback


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
    """True when `a` and `b` differ at most in blank lines. The assembly puts
    one blank line between blocks, so a source with two or more there, or
    none -- a heading straight under a paragraph line (a downstream repo,
    2026-10-12) -- reassembles with the same words in different blank lines,
    which --normalize-blank-lines accepts; any other change is a change of
    words."""
    norm = lambda t: [l for l in t.split('\n') if l.strip()]
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


# ---- --split-file / --join: any index kept as a directory ---------------
# Practice: shared-index-is-a-directory (Alex, 2026-10-12: "yes do the
# directory split"). The 2026-10-04 split above covered MAP and GLOSSARY
# only, and a downstream branch then failed to land twice on conflicts in two
# other hand-edited tables every thread adds a row to. One mechanism, one
# tool: the split is split_entries() above and the join is
# build_views.assemble_source_dir(), the same code MAP.source/ goes through.
JOIN_TOOL = 'tools/precedent_migrate_views.py'
_LABEL_ONLY = _re.compile(r'^(?:generated_by|edit_instead|note):')


def index_dir_for(path):
    """'docs/INDEX.md' -> 'docs/INDEX' (the directory an index splits into)."""
    path = pathlib.Path(path)
    return path.with_suffix('') if path.suffix == '.md' else path.with_name(path.name + '.d')


def _rel(repo, p):
    p = pathlib.Path(p)
    p = p if p.is_absolute() else pathlib.Path(repo) / p
    return p.resolve().relative_to(pathlib.Path(repo).resolve()).as_posix()


def join_label(repo, src_rel, out_rel):
    eng = _engine_rel(repo)
    return bv.generated_label(JOIN_TOOL, f'{src_rel}/',
                              f'python3 {eng}/precedent_migrate_views.py --repo . '
                              f'--join {src_rel} --out {out_rel}')


def join_text(repo, src_rel, out_rel):
    """-> the whole view: the label, a blank line, then the directory's text
    exactly as assemble_source_dir() puts it together, ending in one newline."""
    body = bv.assemble_source_dir(pathlib.Path(repo) / src_rel)
    return '\n'.join(join_label(repo, src_rel, out_rel)) + '\n\n' + body + '\n'


def view_body(text):
    """-> a joined view's text without its label (the original file's
    text, for a view this tool wrote)."""
    if text.startswith('---\n') and '\n---\n' in text[4:]:
        head, rest = text[4:].split('\n---\n', 1)
        if _re.search(r'^generated_by:', head, _re.M):
            return rest[1:] if rest.startswith('\n') else rest
    return text


def join_entry(repo, src_rel, out_rel):
    """-> the tools/generated_files.json entry for a joined view."""
    eng = _engine_rel(repo)
    tool = f'{eng}/precedent_migrate_views.py'
    args = ['--repo', '.', '--join', src_rel, '--out', out_rel]
    return {'path': out_rel, 'generated_by': JOIN_TOOL,
            'edit_instead': f'{src_rel}/*', 'inputs': [f'{src_rel}/*'],
            'regenerate': f'python3 {tool} ' + ' '.join(args),
            'check': [tool, *args, '--check']}


def join(repo, src, out, check=False, force=False, say=print):
    """Rebuild `out` from the directory `src`. -> 0 current or written,
    1 out of date (--check) or refused, 2 usage."""
    repo = pathlib.Path(repo).resolve()
    src_rel, out_rel = _rel(repo, src), _rel(repo, out)
    d, view = repo / src_rel, repo / out_rel
    if not d.is_dir():
        say(f'precedent_migrate_views: {src_rel}/ is not a directory.')
        return 2
    new = join_text(repo, src_rel, out_rel)
    old = view.read_text(encoding='utf-8') if view.is_file() else None
    if old == new:
        if check:
            say(f'{out_rel} is current with {src_rel}/')
        return 0
    if check:
        say(f'{out_rel} is out of date with {src_rel}/ -- run '
            f'{join_entry(repo, src_rel, out_rel)["regenerate"]}')
        return 1
    # Old wording of an entry reworded in the directory is no hand edit: the
    # directory's recent history counts as source (build_views.HISTORY_COMMITS).
    lost = bv.hand_edits_against(repo, view_body(old), new, sorted(d.rglob('*.md')),
                                 skip=_LABEL_ONLY, history=[d], view=view) if old else []
    if lost and not force:
        say(f'precedent_migrate_views: REFUSED -- {out_rel} has lines no file in '
            f'{src_rel}/ holds, typed into the view by hand. Move each into its own '
            f'entry file in {src_rel}/ (then this rebuild keeps it), or pass --force '
            f'to drop them:\n  ' + '\n  '.join(lost[:20])
            + f'\nA line named that is old wording you changed in {src_rel}/ before '
              f'it was ever committed is not a hand edit: --force is safe for it.')
        return 1
    view.parent.mkdir(parents=True, exist_ok=True)
    view.write_text(new, encoding='utf-8')
    return 0


def split_file(repo, path, check=False, normalize=False, say=print):
    """Turn the index `path` into a directory beside it, keeping `path` as
    the view generated from it. -> 0 done, 1 refused (nothing changed)."""
    import shutil, tempfile
    repo = pathlib.Path(repo).resolve()
    rel = _rel(repo, path)
    f = repo / rel
    d = index_dir_for(f)
    src_rel = d.relative_to(repo).as_posix()
    if not f.is_file() or f.suffix != '.md':
        say(f'precedent_migrate_views: {rel} is not a Markdown file here.')
        return 1
    if d.exists():
        say(f'precedent_migrate_views: {src_rel}/ already exists; nothing changed.')
        return 1
    text = f.read_text(encoding='utf-8')
    if text.startswith('---\n'):
        say(f'precedent_migrate_views: REFUSED -- {rel} opens with frontmatter'
            + (' and is generated already: split its source, not the view.'
               if _re.search(r'^generated_by:', text.split('\n---\n', 1)[0], _re.M)
               else ', which the view\'s own label would collide with; move it '
                    'into the text and try again.'))
        return 1
    entries = split_entries(text)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='split-', dir=f.parent))
    try:
        for erel, content in entries.items():
            (tmp / erel).parent.mkdir(parents=True, exist_ok=True)
            (tmp / erel).write_text(content, encoding='utf-8')
        body = bv.assemble_source_dir(tmp) + '\n'
        if body != text:
            if not _same_words(body, text):
                say(f'precedent_migrate_views: REFUSED -- {rel} would not reassemble '
                    f'word for word from a directory; nothing changed.')
                return 1
            if not normalize:
                say(f'precedent_migrate_views: REFUSED -- {rel} reassembles with the '
                    f'same words but different blank lines (the view keeps one blank '
                    f'line between blocks and one newline at the end). Pass '
                    f'--normalize-blank-lines to accept that; nothing changed.')
                return 1
        rows = sum(1 for e in entries if '/' in e
                   and not e.endswith((bv.SECTION_HEAD, bv.SECTION_TAIL)))
        if check:
            say(f'would split {rel} into {src_rel}/ ({len(entries)} files, {rows} '
                f'table rows) and generate {rel} from it')
            return 0
        tmp.rename(d)
        tmp = None
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)
    if join(repo, src_rel, rel, force=True, say=say) != 0 or \
            view_body(f.read_text(encoding='utf-8')) != body:
        shutil.rmtree(d, ignore_errors=True)
        f.write_text(text, encoding='utf-8')
        say(f'precedent_migrate_views: REFUSED -- the rebuilt {rel} did not match; '
            f'everything was put back as it was.')
        return 1
    import precedent_regenerate as rg
    added = rg.register(repo, [join_entry(repo, src_rel, rel)])
    say(f'precedent_migrate_views: {rel} -> {src_rel}/, {len(entries)} files '
        f'({rows} table rows); {rel} is now generated from it'
        + (', and listed in tools/generated_files.json' if added else '') + '. '
        f'Add an entry as a new file between two others (0015- goes between 0010- '
        f'and 0020-), then run: {join_entry(repo, src_rel, rel)["regenerate"]}')
    return 0


def _arg(argv, flag):
    if flag in argv and argv.index(flag) + 1 < len(argv):
        return argv[argv.index(flag) + 1]
    return None


def main(argv):
    if '--help' in argv or '-h' in argv:
        print(__doc__.strip())
        return 0
    if '--repo' not in argv or argv.index('--repo') + 1 >= len(argv):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    repo = pathlib.Path(argv[argv.index('--repo') + 1]).resolve()
    restore = (_arg(argv, '--restore-from') or _arg(argv, '--restore-map-from'))
    restore_views = (tuple(v for v, _s in VIEWS) if '--restore-from' in argv
                     else ('MAP.md',))
    if '--find-lost' in argv:
        return find_lost(repo)
    if '--split-file' in argv:
        path = _arg(argv, '--split-file')
        if not path:
            print(__doc__.strip(), file=sys.stderr)
            return 2
        return split_file(repo, path, check='--check' in argv,
                          normalize='--normalize-blank-lines' in argv)
    if '--join' in argv:
        src, out = _arg(argv, '--join'), _arg(argv, '--out')
        if not (src and out):
            print(__doc__.strip(), file=sys.stderr)
            return 2
        return join(repo, src, out, check='--check' in argv, force='--force' in argv)
    if '--split' in argv:
        return split(repo, check='--check' in argv)
    if '--check' in argv:
        todo = plan(repo, restore, restore_views)
        for view, source, _t in todo:
            print(f'would move {view} into {source} and generate {view} from it')
        if not todo:
            print('nothing to migrate')
        return 0
    return migrate(repo, restore, restore_views=restore_views,
                   accept_loss='--accept-loss' in argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
