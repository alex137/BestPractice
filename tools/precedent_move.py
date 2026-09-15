#!/usr/bin/env python3
"""precedent_move.py -- move an existing practice from one level to another.

  python3 tools/precedent_move.py --slug SLUG \\
      --from individual|team --from-path PATH \\
      --to individual|team|universal --to-path PATH \\
      --approved-by NAME [--strength decided|assented] [--story TEXT] [--dry-run]

Run it from a Precedent checkout: the sets and the consuming repositories
do not vendor it (the rehearsal of 2026-09-14 spent its first minutes
looking for a copy in the set), and every --from-path / --to-path is a
path to the set, absolute or relative to where you run it.

The two-step move spec/MOVING_PRACTICES.md describes, done in the one order
that is safe and with nothing left to remember:

  1. LAND the practice at the destination, as its own file, carrying the
     Rule, Detail, Why and Story exactly as they are -- this is vetted text,
     not a new draft -- with the destination level's own approval recorded
     (`--approved-by`; a listed approver for a team set).
  2. DEDUPLICATE the copy at the source: `status: deduplicated`,
     `in_force_at: <the slug>`, and one dated line appended to its ## Story
     saying where it went and who approved it. Never a delete: the resolver
     drops a non-active practice before materialization, and the record of
     where the rule now lives is what a consumer's `precedent_show` reports.

Both sets' generated views are regenerated afterwards, where each set
carries build_views.py. Nothing is committed; the two sets are yours to
commit and publish, and a consumer picks the move up on its next sync.

WHY A TOOL (practice: cite-the-incident). The procedure said to run the
creation pipeline with the existing practice's text as the candidate's
content -- and precedent_candidate.py takes one `--proposed-rule` string,
so an existing file's four sections had no way in, and every move was a
hand copy with the deduplication done from memory or forgotten. Morgan,
2026-09-14: he had "had bumps doing that". The document itself named a
`precedent_move.py` that "does both atomically, and enforces the ordering"
as the missing piece; this is it.

WHAT IT REFUSES, each with its own message: a source practice that is not
`status: active`; an empty ## Story at the source with no `--story` to fill
it (a move is the last moment the original context is in front of
somebody, and catalogue-carries-stories would hold the destination red);
a destination that already carries the slug; a team destination whose
approvers.json does not list `--approved-by`; a `checked_by` naming a check
script the destination does not have (the script and its test move by hand
first -- see spec/PRIVATE_ENFORCEMENT_BRIEF.md); and `--from universal`,
which is the one direction the design does not offer (demoting a published
rule is a decision for a pull request, not a tool).

UNIVERSAL AS THE DESTINATION drafts only: the file is written into the
Precedent clone's practices/ and the source is left ACTIVE, because the
landing there is the pull request being merged by someone else, and a
source deduplicated before that lands has a rule in force nowhere. The
clone's own generated surfaces are regenerated (build_views.py, doc_sync.py
--write) so its deep check is green on the draft. Run this tool again with
`--dedupe-only` once the PR has merged AND every repository consuming the
source set has taken the new universal catalogue -- a consumer still
vendoring the old one sees the rule in neither source, and its sync refuses
to write until it is refreshed (INSTALL.md \u00a72 step 0, "Update Vendors").

Exit 0 on a completed move (or a completed draft); 1 on a refusal, with the
reason on stderr and nothing written.
"""

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp    # noqa: E402
import precedent_time           # noqa: E402  (practice: timestamps-carry-offset)

LEVELS = ('individual', 'team', 'universal')
STRENGTHS = ('decided', 'assented')


class MoveRefused(Exception):
    pass


def _practice_path(root, slug):
    return pathlib.Path(root).resolve() / 'practices' / f'{slug}.md'


def _read(path):
    try:
        fm, sections = sp._read_practice_file(path)
    except Exception as e:                                  # noqa: BLE001
        raise MoveRefused(f'{path} does not parse as a practice file: {e}')
    return fm, sections


def _field(fm, key):
    v = fm.get(key)
    if v is None:
        return ''
    return str(v).strip().strip('"')


def _check_team_approver(repo, name):
    f = pathlib.Path(repo) / 'approvers.json'
    if not f.is_file():
        raise MoveRefused(f'{f} does not exist, so no approver can be verified '
                          f'for a team destination')
    approvers = json.loads(f.read_text(encoding='utf-8')).get('approvers', [])
    names = {a.get('name') for a in approvers} | {a.get('github') for a in approvers}
    if name not in names:
        raise MoveRefused(f'{name!r} is not in {f} ({sorted(n for n in names if n)}) '
                          f'-- landing in a team set needs a listed approver')


def _check_checked_by(fm, to_level, to_path):
    checked_by = _field(fm, 'checked_by')
    if not checked_by or checked_by == 'null':
        return
    if to_level == 'universal':
        import precedent_land as pl
        pl._verify_checked_by_universal(checked_by, _field(fm, 'slug'))
        return
    name = pathlib.Path(checked_by).name
    script = pathlib.Path(to_path) / 'tools' / 'checks' / name
    stem = name[len('check_'):-3] if name.startswith('check_') and name.endswith('.py') else name
    test = pathlib.Path(to_path) / 'tools' / 'checks' / 'tests' / f'test_{stem}.sh'
    if not script.is_file() or not test.is_file():
        raise MoveRefused(
            f'the practice declares checked_by: {checked_by}, and the destination '
            f'has no {script.relative_to(to_path)} with a '
            f'{test.relative_to(to_path)} beside it. Move the check script and '
            f'its test first (spec/PRIVATE_ENFORCEMENT_BRIEF.md), then the practice; '
            f'a checked_by naming a check the set cannot run is a coverage claim '
            f'nobody tested')


def _rewrite_frontmatter(text, updates):
    """Rewrite named top-level frontmatter fields in place, byte-for-byte
    elsewhere. A field absent from the frontmatter is appended before the
    closing fence. `updates` values are the raw text to put after the colon."""
    end = text.find('\n---\n', 4)
    fm_text, body = text[4:end], text[end:]
    lines = fm_text.split('\n')
    seen = set()
    out = []
    for line in lines:
        m = re.match(r'^([A-Za-z_]+):(\s*)(.*)$', line)
        if m and m.group(1) in updates:
            key = m.group(1)
            pad = m.group(2) or ' '
            out.append(f'{key}:{pad}{updates[key]}')
            seen.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f'{key}: {value}')
    return '---\n' + '\n'.join(out) + body


def _append_story(text, line):
    """Append one paragraph to the ## Story section, creating the section
    when the file has none."""
    if re.search(r'^## Story\s*$', text, re.M):
        return text.rstrip('\n') + '\n\n' + line + '\n'
    return text.rstrip('\n') + '\n\n## Story\n' + line + '\n'


def _regenerate_universal(clone):
    """-> str. A Precedent clone's own generated surfaces after a draft lands
    in its practices/: build_views.py (AGENTS.md, MAP.md, GLOSSARY.md) and
    doc_sync.py --write (spec/LOADER.md's catalogue and the other derived
    sections). Both, because the rehearsal of 2026-09-14 that drafted a
    practice by hand found the clone's own deep check red on exactly those
    two until they were run, and nothing had said so."""
    clone = pathlib.Path(clone)
    out = []
    for rel, args in (('tools/build_views.py', []), ('tools/doc_sync.py', ['--write'])):
        script = clone / rel
        if not script.is_file():
            out.append(f'{rel}: not in {clone}, so not run -- is that a Precedent clone?')
            continue
        r = subprocess.run([sys.executable, '-B', str(script), *args], cwd=str(clone),
                           capture_output=True, text=True)
        last = (r.stdout + r.stderr).strip().splitlines()
        out.append(f'{rel}{" " + " ".join(args) if args else ""}: '
                   + ('OK' if r.returncode == 0 else (last[-1] if last else f'exit {r.returncode}')))
    return '; '.join(out)


def _regenerate(set_root):
    bv = pathlib.Path(set_root) / 'tools' / 'build_views.py'
    if not bv.is_file():
        return f'{set_root}: carries no tools/build_views.py, so its views were not regenerated -- run its own generator'
    r = subprocess.run([sys.executable, '-B', str(bv)], cwd=str(set_root),
                       capture_output=True, text=True)
    last = (r.stdout + r.stderr).strip().splitlines()
    return f'{set_root}: ' + (last[-1] if last else f'build_views exit {r.returncode}')


def move(slug, from_level, from_path, to_level, to_path, approved_by,
         strength=None, story=None, dry_run=False, dedupe_only=False, say=print):
    if from_level not in LEVELS or to_level not in LEVELS:
        raise MoveRefused(f'levels are one of {LEVELS}')
    if from_level == 'universal':
        raise MoveRefused('moving a practice OUT of universal is not a designed path '
                          '(spec/MOVING_PRACTICES.md, "The asymmetry that already exists"): '
                          'a rule published to every adopter is withdrawn by a pull '
                          'request that says why, not by a tool')
    if from_level == to_level and pathlib.Path(from_path).resolve() == pathlib.Path(to_path).resolve():
        raise MoveRefused('source and destination are the same set')
    if strength is not None and strength not in STRENGTHS:
        raise MoveRefused(f'--strength is one of {STRENGTHS}')
    if not approved_by and not dedupe_only:
        raise MoveRefused('--approved-by NAME is required: the destination level\'s own '
                          'approval is what makes this a move rather than a copy')

    src = _practice_path(from_path, slug)
    if not src.is_file():
        raise MoveRefused(f'{src} does not exist')
    fm, sections = _read(src)
    today = precedent_time.today(ROOT)  # practice: timestamps-carry-offset
    dest = _practice_path(to_path, slug)

    if dedupe_only:
        if not dest.is_file():
            raise MoveRefused(f'--dedupe-only, but {dest} does not exist: nothing is '
                              f'in force at the destination yet, so the source copy '
                              f'may not be withdrawn')
        dfm, _ = _read(dest)
        if _field(dfm, 'status') not in ('', 'active'):
            raise MoveRefused(f'{dest} is status: {_field(dfm, "status")}, not active -- '
                              f'the rule would be in force nowhere')
    else:
        status = _field(fm, 'status') or 'active'
        if status != 'active':
            raise MoveRefused(f'{src} is status: {status} -- only an active practice '
                              f'moves; a withdrawn one already records where it went')
        if not (sections.get('story') or '').strip() and not story:
            raise MoveRefused(f'{src} has an empty ## Story and no --story was given. '
                              f'Fill it before landing, not after: a move is the last '
                              f'moment the original context is in front of somebody, '
                              f'and catalogue-carries-stories holds the destination '
                              f'red until it is filled anyway')
        if dest.is_file():
            raise MoveRefused(f'{dest} already exists -- refusing to overwrite. If it is '
                              f'the same rule, deduplicate the source with --dedupe-only')
        if to_level == 'team':
            _check_team_approver(to_path, approved_by)
        _check_checked_by(fm, to_level, to_path)

    from_name = pathlib.Path(from_path).resolve().name
    to_name = pathlib.Path(to_path).resolve().name
    plan = []

    if not dedupe_only:
        text = src.read_text(encoding='utf-8')
        if story and not (sections.get('story') or '').strip():
            text = _append_story(text, story)
        old_approved = _field(fm, 'approved_by')
        approval = (f'"{approved_by}, {today}, moved from the {from_level} set '
                    f'{from_name}' + (f' (there: {old_approved})' if old_approved else '') + '"')
        updates = {'status': 'active', 'in_force_at': 'null',
                   'added': f'"{today}"', 'approved_by': approval}
        if to_level == 'universal':
            updates['approved_by'] = (f'"pending PR review -- drafted {today} by {approved_by}, '
                                      f'moved from the {from_level} set {from_name}"')
        if strength:
            updates['strength'] = strength
        new_text = _rewrite_frontmatter(text, updates)
        plan.append(('write', dest, new_text))

    if to_level != 'universal' or dedupe_only:
        src_text = src.read_text(encoding='utf-8')
        line = (f'Moved to the {to_level} set `{to_name}` on {today}'
                + (f', approved there by {approved_by}' if approved_by else '')
                + f'. This copy is deduplicated; the rule is in force there as `{slug}`.')
        src_new = _rewrite_frontmatter(src_text, {'status': 'deduplicated',
                                                  'in_force_at': slug})
        src_new = _append_story(src_new, line)
        plan.append(('write', src, src_new))

    if dry_run:
        for _op, path, _content in plan:
            say(f'would write {path}')
        say('dry run: nothing written')
        return

    # LAND FIRST, then withdraw the source: if the second write fails, the
    # rule is in force at both ends -- a duplication, which the resolver
    # settles by precedence -- and never at neither.
    for _op, path, content in plan:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        _read(path)      # the written file must parse, or say so now
        say(f'wrote {path}')

    for set_root in ({str(pathlib.Path(to_path).resolve()), str(pathlib.Path(from_path).resolve())}
                     if to_level != 'universal' else {str(pathlib.Path(from_path).resolve())} if dedupe_only else set()):
        say(f'  {_regenerate(set_root)}')
    if to_level == 'universal' and not dedupe_only:
        say(f'  {to_path}: {_regenerate_universal(to_path)}')

    # practice: disclose-landing
    if to_level == 'universal' and not dedupe_only:
        say(f'DISCLOSE TO THE HUMAN: `{slug}` is DRAFTED into {dest} and not yet in force '
            f'anywhere new. Commit it on a branch of that Precedent clone and open a pull '
            f'request; the source copy in the {from_level} set {from_name} stays ACTIVE '
            f'until that merges. Run this tool again with --dedupe-only to withdraw the '
            f'source copy only once the pull request has merged AND every repository '
            f'consuming {from_name} has taken the new universal catalogue (INSTALL.md '
            f'\u00a72 step 0, or "Update Vendors"): a consumer that still vendors the '
            f'old catalogue sees the rule in neither source, and its next sync refuses.')
    elif dedupe_only:
        say(f'DISCLOSE TO THE HUMAN: `{slug}` is now deduplicated in the {from_level} set '
            f'{from_name}; the rule is in force from the {to_level} set {to_name}.')
    else:
        say(f'DISCLOSE TO THE HUMAN: `{slug}` now lives in the {to_level} set {to_name}, '
            f'approved by {approved_by}, and is in force from there; its copy in the '
            f'{from_level} set {from_name} is deduplicated and points at it. Commit both '
            f'sets; a consumer takes the move on its next sync.')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0
    opts = {'--slug': None, '--from': None, '--from-path': None, '--to': None,
            '--to-path': None, '--approved-by': None, '--strength': None, '--story': None}
    flags = {'--dry-run': False, '--dedupe-only': False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in flags:
            flags[a] = True
        elif a in opts:
            i += 1
            if i >= len(argv):
                print(f'precedent_move FAIL: {a} needs a value', file=sys.stderr)
                return 1
            opts[a] = argv[i]
        else:
            print(f'precedent_move FAIL: unknown argument {a!r}', file=sys.stderr)
            return 1
        i += 1
    missing = [k for k in ('--slug', '--from', '--from-path', '--to', '--to-path') if not opts[k]]
    if missing:
        print(f'precedent_move FAIL: missing {", ".join(missing)}', file=sys.stderr)
        return 1
    try:
        move(opts['--slug'], opts['--from'], opts['--from-path'], opts['--to'],
             opts['--to-path'], opts['--approved-by'], strength=opts['--strength'],
             story=opts['--story'], dry_run=flags['--dry-run'],
             dedupe_only=flags['--dedupe-only'])
    except MoveRefused as e:
        print(f'precedent_move FAIL: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
