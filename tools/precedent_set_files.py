#!/usr/bin/env python3
"""The one list of files the engine reads from a practice set's own folder, and whether a copy of the set carries each (spec/SET_COPY_CARRIES_WHAT_THE_ENGINE_READS_PLAN.md)

precedent_set_files.py -- SET_FILES, the registry of per-set files.

WHY THIS EXISTS (2026-11-01). A repository can keep a COPY of a shared set
under process/<name>/, and then the engine treats the copy's folder as the
set: every tool that reads a file "from the source's own folder" reads it
from the copy. The shared-set copier (tools/checkin.py) carried a hand-kept
tuple of such files, `SOURCE_CONFIGS = ('reply_check.json',
'close_detect.json')`, which mirrored two readers by hand. The day it was
written a third reader already existed -- precedent_vocabulary.py reads
our_language.json from each source -- and a voice repository's copy of the
ladder set never carried it, so the set's own words never reached that
repository's vocabulary list, and nothing said so.

So the readers and the copier now share ONE list:

  - every reader takes its file name from here (`set_file(key)`);
  - checkin.py copies every entry marked `ship` that the set has;
  - Update Vendors and the consumer check `set-copy-complete` compare a
    copy against the set at the commit it was copied from;
  - precedent_check's `set-file-registered` (in BestPractice) refuses a
    tools/*.py read from a source's folder whose name is not listed here;
  - `set-file-decided` (in a practice set) refuses a top-level file of
    the set that is neither listed here, nor named by a rule, nor among the
    standard set-repository files below, nor kept home under `stays`.

NO IMPORTS, ON PURPOSE. precedent_reply_check.py runs on every stop of every
session and takes its config name from here; this module must cost nothing
to import (plan, review Q1).

`copy` says what a whole copy of a set does with an entry:
  ship        carried by every whole copy that finds it in the set
  folder      a folder read from the set; carried by its own copier rule
              (practices/ always, tools/checks/ when a rule needs it)
  stays       read from a set's own checkout only, never from a copy
  individual  read only from an individual set, which is never copied
  universal   read only from the universal source's own copy
"""

SET_FILES = (
    {'key': 'source_manifest', 'name': 'precedent-source.json', 'copy': 'ship',
     'read_by': 'tools/precedent_resolve.py (SOURCE_MANIFEST), tools/checkin.py',
     'why': "what makes a folder a set: its name, level, exports, carries"},
    {'key': 'reply_check', 'name': 'reply_check.json', 'copy': 'ship',
     'read_by': 'tools/precedent_reply_check.py, tools/precedent_check.py',
     'why': "the set's reply-gate requirements, enforced when a turn ends"},
    {'key': 'close_detect', 'name': 'close_detect.json', 'copy': 'ship',
     'read_by': 'tools/precedent_close_detect.py',
     'why': "the set's close-detection rules"},
    {'key': 'our_language', 'name': 'our_language.json', 'copy': 'ship',
     'read_by': 'tools/precedent_vocabulary.py',
     'why': "the set's own words, for the vocabulary list"},
    {'key': 'built_from', 'name': 'BUILT_FROM.json', 'copy': 'ship',
     'read_by': 'tools/precedent_update.py (built_from_differences)',
     'why': "what the set's compiled exports were built from, so a stale "
            "compiled copy is heard about"},
    {'key': 'precedent_json', 'name': 'precedent.json', 'copy': 'stays',
     'read_by': 'tools/precedent_materialize.py (adapters), tools/precedent_resolve.py',
     'why': "the set repository's own install; a declaration a copy must "
            "carry belongs in precedent-source.json instead, so "
            "set-file-decided refuses a shared set whose precedent.json "
            "declares `adapters`"},
    {'key': 'identity', 'name': 'identity.json', 'copy': 'individual',
     'read_by': 'tools/precedent_materialize.py, tools/precedent_identity.py',
     'why': "the person an individual set belongs to; never copied"},
    {'key': 'catalogue_sync', 'name': 'CATALOGUE_SYNC.json', 'copy': 'universal',
     'read_by': 'tools/precedent_engine_freshness.py',
     'why': "a universal catalogue copy's own sync record; written into the "
            "copy by Update Vendors, never part of a shared set"},
    {'key': 'practices', 'name': 'practices', 'copy': 'folder',
     'read_by': 'every reader of a set',
     'why': "the set's rules; always carried"},
    {'key': 'checks', 'name': 'tools/checks', 'copy': 'folder',
     'read_by': 'tools/precedent_check.py, tools/precedent_materialize.py',
     'why': "the check scripts the set's rules run; carried when a rule needs them"},
    {'key': 'tools', 'name': 'tools', 'copy': 'folder',
     'read_by': 'tools/precedent_resolve.py, tools/precedent_materialize.py',
     'why': "a set's own engine copy and the scripts its rules name; only "
            "what a rule names is carried (files_rules_name below)"},
    {'key': 'bootstrap', 'name': 'bootstrap', 'copy': 'folder',
     'read_by': 'tools/precedent_materialize.py (adapters)',
     'why': "an individual set's adapter scripts; individual sets are never copied"},
)

# The files and folders every practice-set repository has for itself: its
# own install, reviewers, instructions and records. They stay home without a
# `stays` line, so a set needs no commit before the engine reaches it
# (plan, "Rollout, adjusted"). A dot-entry (.git, .github, .claude,
# .gitignore, .precedent) is the repository's own machinery and is never a
# question either.
STANDARD_STAYS_FILES = (
    'AGENTS.md', 'CLAUDE.md', 'CODEOWNERS', 'GEMINI.md', 'GLOSSARY.md',
    'GLOSSARY.source.md', 'MAP.md', 'MAP.source.md', 'README.md', 'TODO.md',
    'approvers.json', 'leak-blocklist.txt', 'precedent.json',
)
STANDARD_STAYS_FOLDERS = (
    'gotchas', 'record', 'spec', 'todo', 'tools',
)

# The key a practice set's precedent-source.json uses to keep a top-level
# file home, with a reason: {"stays": {"NOTES.md": "this repository's own"}}.
STAYS_KEY = 'stays'

# The keys a copy's process/manifest_<name>.json records under `upstream`,
# in the same write as the copy itself: the registered files the copy
# carries, and the set's commit they were copied from.
RECORD_KEY = 'set_files'
RECORD_COMMIT_KEY = 'set_files_commit'

# Written into a practice set's tools/ENGINE_MANIFEST.json by its first
# Update Vendors with this engine: from then on set-file-decided is strict
# there; before it, an undecided file is a note (plan, second review, 3).
DECIDED_MARKER_KEY = 'set_files_decided'

_BY_KEY = {e['key']: e for e in SET_FILES}


def set_file(key):
    """-> the registered name for `key`. A KeyError for an unregistered key
    is the point: a reader cannot name a file this list does not hold."""
    return _BY_KEY[key]['name']


def entry(key):
    return dict(_BY_KEY[key])


def ship_files():
    """-> the names a whole copy carries when the set has them."""
    return tuple(e['name'] for e in SET_FILES if e['copy'] == 'ship')


def by_name(name):
    """-> the entry registered under file or folder `name`, else None."""
    for e in SET_FILES:
        if e['name'] == name:
            return dict(e)
    return None


def registered(rel):
    """True when set-relative path `rel` is a registered file, or sits in a
    registered folder."""
    rel = str(rel).strip().strip('/')
    for e in SET_FILES:
        n = e['name']
        if rel == n or (e['copy'] == 'folder' and rel.startswith(n + '/')):
            return True
    return False


def standard_stays(name, is_dir):
    """True when top-level entry `name` is one every set repository keeps
    for itself."""
    if name.startswith('.'):
        return True
    return name in (STANDARD_STAYS_FOLDERS if is_dir else STANDARD_STAYS_FILES)


def files_rules_name(set_dir):
    """-> the paths, relative to the set, that its own practices need
    beside them: tools/checks/ when the set has one, and every file a
    practice names in `ships`, `checked_by` or a hook's `run`. A hook script
    in a folder of its own under tools/ (tools/<name>/x.py) brings that
    folder, since such a script imports its neighbours."""
    import json, pathlib
    set_dir = pathlib.Path(set_dir)
    out = []
    if (set_dir / 'tools' / 'checks').is_dir():
        out.append('tools/checks')
    try:
        import split_practices as _sp
    except ImportError:
        return out

    def _list(raw):
        if isinstance(raw, list):
            return raw
        try:
            got = json.loads(raw) if isinstance(raw, str) and raw.strip() else None
        except ValueError:
            return []
        return got if isinstance(got, list) else []

    for f in sorted((set_dir / 'practices').glob('*.md')):
        try:
            fm, _sections = _sp._read_practice_file(f)
        except Exception:                                    # noqa: BLE001
            continue
        named = [x for x in _list(fm.get('ships')) if isinstance(x, str)]
        named += [h.get('run') for h in _list(fm.get('hooks'))
                  if isinstance(h, dict) and isinstance(h.get('run'), str)]
        cb = str(fm.get('checked_by') or '').strip().strip('"\'')
        if cb and cb != 'null':
            named.append(cb)
        for rel in named:
            parts = pathlib.PurePosixPath(rel.strip().strip('/')).parts
            if not parts or '..' in parts or not (set_dir / rel).exists():
                continue
            if len(parts) > 2 and parts[0] == 'tools' and parts[1] != 'checks':
                rel = '/'.join(parts[:2])
            rel = pathlib.PurePosixPath(rel).as_posix()
            if rel not in out and not any(rel.startswith(o + '/') for o in out):
                out.append(rel)
    return out


def set_file_decisions(root):
    """-> (undecided [name], adapters bool, loose [line]) for the set at `root`:
    each top-level tracked entry that is none of registered, practices/ or
    precedent-source.json, named by a rule, exported, carried or listed as
    code, among the files every set repository keeps for itself, or kept
    home under precedent-source.json's `stays` with a reason; and whether
    its precedent.json declares `adapters`, which a copy never carries; and
    each `stays` line with no reason or naming nothing there."""
    import json, pathlib, subprocess
    root = pathlib.Path(root)
    try:
        manifest = json.loads((root / set_file('source_manifest')).read_text(
            encoding='utf-8'))
    except (OSError, ValueError):
        manifest = {}
    raw = manifest.get(STAYS_KEY) if isinstance(manifest, dict) else None
    raw = raw if isinstance(raw, dict) else {}
    stays = {str(k).strip('/') for k, v in raw.items() if str(v or '').strip()}
    named = set()
    for rel in list(manifest.get('exports') or []) + list(manifest.get('code') or []) \
            + [str((c or {}).get('path') or '') for c in manifest.get('carries') or []
               if isinstance(c, dict)]:
        first = str(rel).strip().strip('/').split('/')[0]
        if first:
            named.add(first)
    try:
        named |= {str(r).split('/')[0] for r in files_rules_name(root)}
    except Exception:                                         # noqa: BLE001
        pass                    # no split_practices beside this copy
    r = subprocess.run(['git', '-C', str(root), 'ls-files'],
                       capture_output=True, text=True)
    tops = {}
    for rel in r.stdout.splitlines():
        parts = rel.split('/')
        tops[parts[0]] = tops.get(parts[0], False) or len(parts) > 1
    undecided = sorted(
        name for name, is_dir in tops.items()
        if not (by_name(name) or name in named or name in stays
                or standard_stays(name, is_dir)))
    try:
        own = json.loads((root / set_file('precedent_json')).read_text(
            encoding='utf-8'))
    except (OSError, ValueError):
        own = {}
    # A `stays` line with no reason, or naming nothing the set holds, has
    # come loose from the tree (practice: checks-carry-a-declared-decline).
    loose = sorted(f'{k}: no reason given' if not str(v or '').strip()
                   else f'{k}: names nothing this set holds'
                   for k, v in raw.items()
                   if not str(v or '').strip() or str(k).strip('/') not in tops)
    return (undecided, bool(isinstance(own, dict) and own.get('adapters')),
            loose)


# ---------------------------------------------------------------------------
# Copy completeness: one implementation, for Update Vendors and for the
# consumer check `set-copy-complete`. Imports stay inside the functions, so
# importing this module still costs the reply check nothing.
# ---------------------------------------------------------------------------

def _git_out(clone, *args):
    import subprocess
    r = subprocess.run(['git', '-C', str(clone), *args], capture_output=True)
    return r.returncode, r.stdout


def kept_paths(repo):
    """-> {repo-relative path: reason} that precedent.json's
    kept_template_divergences keeps on purpose: a kept local edit to a copied
    file is reported as kept, never as a copy that differs."""
    import json, pathlib
    try:
        d = json.loads((pathlib.Path(repo) / 'precedent.json').read_text(
            encoding='utf-8')).get('kept_template_divergences') or {}
    except (OSError, ValueError, AttributeError):
        return {}
    if not isinstance(d, dict):
        return {}
    return {str(k): str((v or {}).get('reason') or '').strip()
            for k, v in d.items() if isinstance(v, dict)}


def copy_completeness(repo, entry, clone=None):
    """-> a dict judging one copied-in set's copy against the registry:

      state    'exports_only'  taken for its exports alone; nothing to judge
               'predates'      no set_files record: made by an engine from
                               before the registry -- an advisory, never a
                               finding; the next Update Vendors fills it
               'complete'      every registered file the set had at the
                               recorded commit is in the copy, byte for byte
               'incomplete'    one is missing or differs (`missing`, `differs`)
               'unverified'    the recorded commit cannot be read here, so
                               only presence against the record was checked
      missing  [(file, why it matters)]
      differs  [(file, why it matters)]
      kept     [(file, reason)] -- kept on purpose (kept_template_divergences)
      would_fill [file] -- for 'predates': what the set has that the copy lacks
      commit   the commit compared against, or None
      note     one sentence for the person

    `clone` is the set's own clone, or None when none is on this machine.
    Compared against the commit the copy's manifest records, never the
    clone's working tree, which moves after an update (plan review, 5)."""
    import json, pathlib
    repo = pathlib.Path(repo)
    name = entry.get('name')
    out = {'state': 'complete', 'missing': [], 'differs': [], 'kept': [],
           'would_fill': [], 'commit': None, 'note': ''}
    if entry.get('exports_only') is True:
        out['state'] = 'exports_only'
        return out
    copy = repo / str(entry.get('path') or '')
    try:
        up = json.loads((repo / 'process' / f'manifest_{name}.json').read_text(
            encoding='utf-8')).get('upstream') or {}
    except (OSError, ValueError, AttributeError):
        up = {}
    recorded = up.get(RECORD_KEY)
    commit = up.get(RECORD_COMMIT_KEY)
    set_root = str(entry.get('set_root') or '').strip().strip('/')
    kept = kept_paths(repo)
    why = {e['name']: e['why'] for e in SET_FILES}

    def at_commit(c, rel):
        """-> the file's bytes at commit `c` in the clone, b'' when the set
        does not hold it there, None when the commit cannot be read."""
        if clone is None or not c:
            return None
        rc, _ = _git_out(clone, 'cat-file', '-e', f'{c}^{{commit}}')
        if rc != 0:
            return None
        inside = f'{set_root}/{rel}' if set_root else rel
        rc, data = _git_out(clone, 'show', f'{c}:{inside}')
        return data if rc == 0 else b''

    if recorded is None and not commit:
        out['state'] = 'predates'
        base = up.get('commit')
        for rel in ship_files():
            data = at_commit(base, rel)
            if data and not (copy / rel).is_file():
                out['would_fill'].append(rel)
        fill = (f": it will add {', '.join(out['would_fill'])}"
                if out['would_fill'] else '')
        out['note'] = (f'this copy of {name} predates the set-files registry; '
                       f'the next Update Vendors fills it{fill}')
        return out
    out['commit'] = commit
    readable = at_commit(commit, set_file('source_manifest')) is not None
    names = list(ship_files()) if readable else list(recorded or [])
    for rel in names:
        here = copy / rel
        where = f"{entry.get('path')}/{rel}".lstrip('/')
        if where in kept:
            out['kept'].append((rel, kept[where]))
            continue
        if readable:
            data = at_commit(commit, rel)
            if not data:
                continue        # the set does not hold it: nothing to carry
            if not here.is_file():
                out['missing'].append((rel, why.get(rel, '')))
            elif here.read_bytes() != data:
                out['differs'].append((rel, why.get(rel, '')))
        elif not here.is_file():
            out['missing'].append((rel, why.get(rel, '')))
    if out['missing'] or out['differs']:
        out['state'] = 'incomplete'
        bits = [f'{r} is missing ({w})' for r, w in out['missing']]
        bits += [f'{r} differs from the set at {str(commit)[:12]} ({w})'
                 for r, w in out['differs']]
        out['note'] = (f'the copy of {name} is not what the set held: '
                       f'{"; ".join(bits)}. Run Update Vendors to copy it again')
    elif not readable:
        out['state'] = 'unverified'
        out['note'] = (f'the copy of {name} holds every file its record lists, '
                       f'but its commit {str(commit or "")[:12] or "(none)"} '
                       f'cannot be read here'
                       + (' (no clone of the set on this machine)'
                          if clone is None else '')
                       + ', so it could not be compared byte for byte')
    return out
