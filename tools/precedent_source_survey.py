#!/usr/bin/env python3
"""Should this repo declare a practice set it doesn't, or drop one it does? -- every repository the session can reach, read and given a verdict

precedent_source_survey.py -- vendor-update-runbook step 9, as a tool.

    python3 tools/precedent_source_survey.py --candidate OWNER/NAME [...]
    python3 tools/precedent_source_survey.py --repo PATH --candidate ...

WHY IT EXISTS (2026-11-01). Step 9 was prose: "list the practice sets this
account can reach, read each one's subject, and compare with precedent.json".
A session running Update Vendors in a practice set listed the account's
repositories, found one it had no clone of, and reported it as "not on disk,
so I didn't check whether it's a practice set" -- the step half done, and
nothing said so. The person had to ask. A step a session can skip without
anything noticing is a step that gets skipped (practice:
checkable-gets-checked).

THE CANDIDATES COME FROM THE SESSION. A hosted session learns which
repositories its account reaches from the `list_repos` tool, which no script
can call, so each one is passed in with `--candidate OWNER/NAME`. Every
source this repo already has in force is surveyed too, candidate or not.

WHAT IT READS. For each candidate, a clone on disk: the path of a source in
force whose origin is that repository, else `../NAME` or `../OWNER/NAME`
beside this repo, in any capitalization, checked against the clone's origin
(precedent_repo_id; case never decides). Inside it, `precedent-source.json`
is what makes a directory a practice set; its `subject` is what the set is
about, and a `retired` entry marks one that folded into others.

ONE LINE PER REPOSITORY, each with its verdict:

    THIS REPO        the repository being surveyed
    DECLARED         in this repo's precedent.json
    IN FORCE         through the person's individual set, or brought by one
    NOT A SET        a clone with no precedent-source.json: a project
    SHOULD ADD?      a practice set not in force here; its subject is printed,
                     for the session to judge against what this repo does
    SHOULD DROP?     a declared set that says it is retired (the update drops
                     it itself once no rule would be lost), or one the
                     candidate list -- the account's reach -- no longer holds
    NOT ON DISK      no clone found, so it was NOT checked: attach it
                     read-only, clone it beside this repo, run this again

NOT ON DISK is the failure this exists to stop: an unchecked repository is
not a passing one, so the exit status is 1 while any remain. A SHOULD ADD?
or SHOULD DROP? is a finding with a recommendation, never an open question
to the person (the-boildown); it exits 0, because it is judged, not fixed by
running anything.
"""
import argparse
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import precedent_repo_id as rid                              # noqa: E402

try:
    import precedent_resolve as pr                           # noqa: E402
except Exception as _e:                                      # noqa: BLE001
    pr = None
    _resolve_err = f'{type(_e).__name__}: {_e}'
else:
    _resolve_err = None

try:
    import precedent_source_credentials as psc               # noqa: E402
except Exception:                                            # noqa: BLE001
    psc = None

SOURCE_FILE = 'precedent-source.json'
VERDICTS = ('THIS REPO', 'DECLARED', 'IN FORCE', 'NOT A SET', 'SHOULD ADD?',
            'SHOULD DROP?', 'NOT ON DISK')


def origin_of(path):
    """-> the clone's origin URL, or '' when it has none or is no clone."""
    try:
        p = subprocess.run(['git', '-C', str(path), 'remote', 'get-url',
                            'origin'], capture_output=True, text=True,
                           timeout=30)
    except Exception:                                        # noqa: BLE001
        return ''
    return p.stdout.strip() if p.returncode == 0 else ''


def read_source_file(path):
    """-> the parsed precedent-source.json at `path`, or None for none."""
    f = pathlib.Path(path) / SOURCE_FILE
    if not f.is_file():
        return None
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _children(d, name):
    """-> entries of directory `d` whose name is `name` in any case."""
    try:
        return [c for c in d.iterdir()
                if c.is_dir() and rid.same_name(c.name, name)]
    except OSError:
        return []


def source_origin(root, src):
    """-> the repository a source in force came from: its clone's origin,
    or, for a copy vendored inside `root`, its `repo` key or the upstream
    repo its manifest records. A vendored copy's folder is part of the
    repository being surveyed, so asking git there answers with THIS
    repository's origin (2026-11-01: a voice repository's four vendored
    sets each came back SHOULD ADD?, though precedent.json declares all
    four)."""
    p = pathlib.Path(src['path'])
    root = pathlib.Path(root).resolve()
    try:
        inside = p.resolve() != root and root in p.resolve().parents
    except OSError:
        inside = False
    if not inside:
        return origin_of(p) if p.is_dir() else ''
    if src.get('repo'):
        return str(src['repo'])
    rel = p.resolve().relative_to(root).as_posix()
    for m in sorted((p.resolve().parent).glob('manifest*.json')):
        try:
            up = json.loads(m.read_text(encoding='utf-8')).get('upstream') or {}
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(up, dict) and up.get('repo') and \
                str(up.get('vendored_at') or '').strip('/') in (rel, ''):
            return str(up['repo'])
    return ''


def find_clone(spec, root, in_force=()):
    """-> a directory on disk that is a clone of `spec`, or None.

    A source in force whose clone's origin is `spec` wins; then a folder
    named for it beside `root`, or under a folder named for its owner. A
    folder that is a clone of some OTHER repository is never taken for
    this one, whatever it is called."""
    for src in in_force:
        p = pathlib.Path(src['path'])
        if p.is_dir() and rid.same_repo(spec, source_origin(root, src)
                                        or src.get('repo') or '',
                                        local_paths=True):
            return p
    parsed = rid.parse(spec)
    if not parsed:
        return None
    parent = pathlib.Path(root).resolve().parent
    places = list(_children(parent, parsed.name))
    if parsed.owner:
        for od in _children(parent, parsed.owner):
            places += _children(od, parsed.name)
    for p in places:
        o = origin_of(p)
        if not o or rid.same_repo(spec, o, local_paths=True):
            return p
    return None


def in_force_sources(repo, user_config=None):
    """-> [{level, name, path, declared, brought, repo}] for every source in
    force here, the declared ones marked. precedent_resolve answers which
    are in force, individual and brought sets included."""
    declared_names = []
    try:
        cfg = json.loads((pathlib.Path(repo) / 'precedent.json').read_text(
            encoding='utf-8'))
        declared_names = [str(e.get('name') or '') for e in
                          (cfg.get('sources') or []) if isinstance(e, dict)]
    except (OSError, ValueError, AttributeError):
        pass
    if pr is None:
        raise RuntimeError(f'precedent_resolve is not available here '
                           f'({_resolve_err}), so the sources in force could '
                           f'not be read')
    out = []
    for s in pr.load_config(repo, user_config=user_config):
        s = dict(s)
        s['declared'] = any(rid.same_name(s.get('name'), n)
                            for n in declared_names) and \
            pr.declared_level(s) != 'individual' and not s.get('brought')
        out.append(s)
    return out


def _declared_files_only(root, spec):
    """-> the name of a source precedent.json declares with exports_only
    that is `spec`, or None. Such a source is copied for its exported files
    and is not in force, so the resolver's list never carries it."""
    try:
        cfg = json.loads((pathlib.Path(root) / 'precedent.json').read_text(
            encoding='utf-8'))
    except (OSError, ValueError):
        return None
    for s in cfg.get('sources') or []:
        if not isinstance(s, dict) or not s.get('exports_only'):
            continue
        ident = s.get('repo') or source_origin(root, {
            'path': str(pathlib.Path(root) / str(s.get('path') or '')), **s})
        if ident and rid.same_repo(spec, ident, local_paths=True):
            return str(s.get('name') or ident)
    return None


def survey(repo, candidates=(), user_config=None):
    """-> [row]: one per candidate and per source in force, each
    {repo, verdict, detail}. Never raises on one repository's trouble: a
    row says what could not be read."""
    root = pathlib.Path(repo).resolve()
    here_origin = origin_of(root)
    sources = in_force_sources(root, user_config=user_config)
    rows, seen = [], []

    def matches_source(spec):
        for s in sources:
            o = source_origin(root, s)
            if rid.same_repo(spec, o or s.get('repo') or '', local_paths=True):
                return s
            if not o and not s.get('repo') and rid.parse(spec) and \
                    rid.same_name(rid.parse(spec).name, s.get('name')):
                return s
        return None

    for spec in candidates:
        spec = str(spec).strip()
        if not spec or any(rid.same_repo(spec, s) for s in seen):
            continue
        seen.append(spec)
        if here_origin and rid.same_repo(spec, here_origin, local_paths=True):
            rows.append({'repo': spec, 'verdict': 'THIS REPO',
                         'detail': 'the repository being surveyed'})
            continue
        src = matches_source(spec)
        if src is not None:
            rows.append(_row_for_source(spec, src))
            src['_surveyed'] = True
            continue
        files_only = _declared_files_only(root, spec)
        if files_only is not None:
            # Declared, but copied for its exported files alone: its rules
            # are not in force here, which is the declaration's point, so
            # it is never a set to add (2026-11-01: a voice repository's
            # files-only copy of a shared set came back SHOULD ADD?).
            rows.append({'repo': spec, 'verdict': 'DECLARED',
                         'detail': f'declared in precedent.json as '
                                   f'"{files_only}", files only '
                                   f'(exports_only): its exported files are '
                                   f'copied in, its rules are not in force here'})
            continue
        clone = find_clone(spec, root)
        name = rid.parse(spec).name if rid.parse(spec) else spec
        taken = [c for c in _children(root.parent, name) if origin_of(c)]
        if clone is None and taken:
            rows.append({'repo': spec, 'verdict': 'NOT ON DISK',
                         'detail': f'{taken[0]} is a clone of '
                                   f'{rid.owner_repo(origin_of(taken[0])) or origin_of(taken[0])}, '
                                   f'not of this one, so it was NOT checked: '
                                   f'clone it somewhere else beside this repo '
                                   f'and run this again'})
            continue
        if clone is None:
            rows.append({'repo': spec, 'verdict': 'NOT ON DISK',
                         'detail': f'no clone of it beside this repo, so it '
                                   f'was NOT checked: attach it read-only, '
                                   f'clone it to {root.parent}/'
                                   f'{rid.parse(spec).name if rid.parse(spec) else spec}, '
                                   f'and run this again'})
            continue
        data = read_source_file(clone)
        if data is None:
            rows.append({'repo': spec, 'verdict': 'NOT A SET',
                         'detail': f'{clone} has no {SOURCE_FILE}: a project '
                                   f'that uses the sets, not one of them'})
        elif data.get('retired'):
            rows.append({'repo': spec, 'verdict': 'NOT A SET',
                         'detail': f'a retired practice set '
                                   f'({_retired_text(data)}); nothing to add'})
        else:
            subject = str(data.get('subject') or '').strip() or \
                '(its precedent-source.json states no subject)'
            rows.append({'repo': spec, 'verdict': 'SHOULD ADD?',
                         'detail': f'a practice set not in force here, named '
                                   f'"{data.get("name") or clone.name}", about: '
                                   f'{subject}. Declare it if this repo does '
                                   f'that work; otherwise say why not'})

    for s in sources:
        if s.get('_surveyed'):
            continue
        p = pathlib.Path(s['path'])
        if p.resolve() == root:
            continue
        label = rid.owner_repo(source_origin(root, s)) if p.is_dir() else ''
        row = _row_for_source(label or s.get('repo') or s['name'], s)
        if candidates and s.get('declared') and not p.is_dir():
            # Declared, no clone, and not among the repositories the account
            # reaches: the one case the survey can call a drop. Lost access
            # to a private repository reads the same, so it stays a question
            # with a recommendation, never a removal.
            row['verdict'] = 'SHOULD DROP?'
            row['detail'] = (f'declared in precedent.json, but there is no '
                             f'clone at {p} and the account\'s repositories '
                             f'(--candidate) do not include it. Drop it if it '
                             f'is gone; if access was lost, get it back first')
        rows.append(row)
    return rows


def _retired_text(data):
    r = data.get('retired')
    if isinstance(r, dict):
        into = ', '.join(r.get('folded_into') or []) or 'no named set'
        return f'retired {r.get("date") or "on no recorded date"}, folded into {into}'
    return 'retired'


def _row_for_source(spec, s):
    p = pathlib.Path(s['path'])
    how = (f'declared in precedent.json ({s.get("level")})' if s.get('declared')
           else f'brought by {s["brought"]}' if s.get('brought') and
           isinstance(s.get('brought'), str)
           else 'brought by the individual set' if s.get('brought')
           else 'the person\'s individual set' if pr.declared_level(s) == 'individual'
           else f'in force ({s.get("level")})')
    if not p.is_dir():
        if s.get('declared'):
            return {'repo': spec, 'verdict': 'NOT ON DISK',
                    'detail': f'{how}, but there is no clone at {p}: clone it '
                              f'there (runbook step 10(c)) and run this again; '
                              f'if the account can no longer reach it at all, '
                              f'that is SHOULD DROP? -- but lost access to a '
                              f'private repository looks the same, so ask'}
        return {'repo': spec, 'verdict': 'NOT ON DISK',
                'detail': f'{how}, but there is no clone at {p}'}
    data = read_source_file(p)
    if s.get('declared') and data and data.get('retired'):
        return {'repo': spec, 'verdict': 'SHOULD DROP?',
                'detail': f'{how}, and it says it is retired '
                          f'({_retired_text(data)}). The update drops it '
                          f'itself once every rule it holds is in force '
                          f'elsewhere; one it cannot drop names the rule left'}
    verdict = 'DECLARED' if s.get('declared') else 'IN FORCE'
    return {'repo': spec, 'verdict': verdict, 'detail': how}


def report(rows, out=sys.stdout):
    width = max([len(r['repo']) for r in rows] + [10])
    for r in rows:
        print(f"{r['verdict']:<13} {r['repo']:<{width}}  {r['detail']}",
              file=out)
    unchecked = [r for r in rows if r['verdict'] == 'NOT ON DISK']
    finds = [r for r in rows if r['verdict'] in ('SHOULD ADD?', 'SHOULD DROP?')]
    print(f'precedent_source_survey: {len(rows)} repositor'
          f'{"y" if len(rows) == 1 else "ies"} surveyed, {len(finds)} '
          f'finding(s) to judge, {len(unchecked)} NOT checked (an unchecked '
          f'repository is not a passing one).', file=out)
    if not rows:
        print('precedent_source_survey: nothing to survey -- pass each '
              'repository the account reaches with --candidate OWNER/NAME '
              '(in a hosted session, from list_repos).', file=out)


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--repo', default=str(
        psc.consuming_repo_root(ROOT) if hasattr(psc, 'consuming_repo_root')
        else ROOT))
    ap.add_argument('--candidate', action='append', default=[],
                    metavar='OWNER/NAME')
    ap.add_argument('--user-config', default=None)
    ap.add_argument('--help', '-h', action='store_true')
    args = ap.parse_args(argv)
    if args.help:
        print((__doc__ or '').strip())
        return 0
    try:
        rows = survey(args.repo, args.candidate, user_config=args.user_config)
    except Exception as e:                                   # noqa: BLE001
        print(f'precedent_source_survey: could not read this repo\'s sources '
              f'({type(e).__name__}: {e}), so nothing was surveyed.',
              file=sys.stderr)
        return 2
    report(rows)
    if not args.candidate:
        print('precedent_source_survey: no --candidate given, so only the '
              'sources already in force were read. Step 9 is not done until '
              'every repository the account reaches is passed in.')
        return 1
    return 1 if any(r['verdict'] == 'NOT ON DISK' for r in rows) else 0


if __name__ == '__main__':
    sys.exit(main())
