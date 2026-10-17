#!/usr/bin/env python3
"""Files this repository received from upstream that were edited here, and
the recorded answer for each (practice: upstream-bug-stops-here).

    python3 tools/upstream_edits.py              # list every one, and why it counts
    python3 tools/upstream_edits.py --guard PATH # exit 3, with the reason, when
                                                 # editing PATH needs an answer first

WHY (Morgan, 2026-10-17, strength: decided, "Act" on the plan). The rule
said to classify a change as upstream or local before making it, and
nothing held anyone to it: a session read it and edited the shipped copy
anyway, the next sync or Update Vendors put upstream's copy back, and a
different fix for the same problem had often been made upstream in the
meantime. So every edit to an upstream-owned file needs one of three
answers, and the full check refuses a tree where one is missing:

  * upstream already fixed it -- take upstream's copy (delete the file and
    sync, or Update Vendors). No entry: the file matches again.
  * it belongs upstream -- carry the fix up, and record it here as
    `owed-upstream` with the link to the pull request or issue that does.
  * it is a local need -- meet it some other way (a setting, a file of
    this repository's own), and only where that is impossible record it
    as `local-need`, saying how the need is met and with the person's own
    approval, quoted with its date.

The answers live in precedent.json:

  "upstream_edits": {
    "tools/human_voice_check.py": {
      "answer": "owed-upstream",
      "detail": "https://github.com/OWNER/SET/pull/12 carries it to the set"
    }
  }

WHAT COUNTS AS UPSTREAM-OWNED. Exactly what the two delivery records say
was delivered, with the hash each recorded: tools/ENGINE_MANIFEST.json
(engine files under tools/, its hook files under .claude/hooks/) and the
sync's MANIFEST.json (shipped files, harness adapters, materialized
checks). A file nobody recorded is this repository's own, and the
repository that is upstream -- BestPractice, a practice set's own engine
-- has neither record for the files it authors, so nothing here fires
there.
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_KEY = 'upstream_edits'
ANSWERS = ('owed-upstream', 'local-need')
_URL_RE = re.compile(r'https?://\S+')
_DATE_RE = re.compile(r'\b20\d\d-\d\d-\d\d\b')
THREE_ANSWERS = (
    'answer first: (1) upstream already fixed it -- take its copy (delete '
    'the file and sync, or Update Vendors); (2) it belongs upstream -- '
    'carry the fix there and record it as "owed-upstream" with the link, '
    f'under "{REGISTRY_KEY}" in precedent.json; (3) a local need -- meet it '
    'another way (a setting, a file of this repository\'s own), and only '
    'where that is impossible record "local-need", how the need is met, and '
    'the person\'s quoted approval with its date')


def _read_json(path):
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _sha(path, short=False):
    h = hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
    return h[:16] if short else h


def owned(root=ROOT):
    """-> {repo-relative path: (where it came from, recorded hash, short)}
    for every file a delivery record says was delivered here."""
    root = pathlib.Path(root)
    out = {}
    engine = _read_json(root / 'tools' / 'ENGINE_MANIFEST.json')
    for name, want in (engine.get('sha256') or {}).items():
        if isinstance(want, str):
            out[f'tools/{name}'] = ('the vendored engine', want, False)
    for name, want in (engine.get('hooks_sha256') or {}).items():
        if isinstance(want, str):
            out[f'.claude/hooks/{name}'] = ('the vendored engine', want, False)
    synced = _read_json(root / 'MANIFEST.json')
    for key, what in (('ships', 'a practice set'), ('adapters', 'a practice set'),
                      ('checks', 'a practice set')):
        for row in synced.get(key) or []:
            if isinstance(row, dict) and isinstance(row.get('path'), str) \
                    and isinstance(row.get('sha256_16'), str):
                src = row.get('source')
                out[row['path']] = (f"{what} ({src})" if src else what,
                                    row['sha256_16'], True)
    return out


def edited(root=ROOT):
    """-> [(path, where it came from)] for each upstream-owned file whose
    content is no longer what was delivered. A missing file is not an
    edit: the delivery's own drift report names it."""
    root = pathlib.Path(root)
    found = []
    for rel, (src, want, short) in sorted(owned(root).items()):
        path = root / rel
        if path.is_file() and _sha(path, short) != want:
            found.append((rel, src))
    return found


def registry(root=ROOT):
    """-> ({path: entry}, [problem]) from precedent.json."""
    data = _read_json(pathlib.Path(root) / 'precedent.json').get(REGISTRY_KEY)
    if data is None:
        return {}, []
    if not isinstance(data, dict):
        return {}, [f'precedent.json "{REGISTRY_KEY}" must be an object '
                    f'mapping each path to its answer']
    entries, problems = {}, []
    for rel, e in data.items():
        if not isinstance(e, dict) or e.get('answer') not in ANSWERS:
            problems.append(f'{rel}: its "{REGISTRY_KEY}" entry needs an '
                            f'"answer" of {" or ".join(ANSWERS)}')
            continue
        detail = str(e.get('detail') or '')
        if e['answer'] == 'owed-upstream' and not _URL_RE.search(detail):
            problems.append(f'{rel}: "owed-upstream" needs the link to the '
                            f'pull request or issue that carries it up, in '
                            f'"detail"')
            continue
        if e['answer'] == 'local-need':
            approved = str(e.get('approved') or '')
            if not detail.strip():
                problems.append(f'{rel}: "local-need" needs "detail": how the '
                                f'need is met, and why it cannot be met '
                                f'without editing this file')
                continue
            if '"' not in approved or not _DATE_RE.search(approved):
                problems.append(f'{rel}: "local-need" needs "approved": the '
                                f'person\'s own words, quoted, with the date')
                continue
        entries[rel] = e
    return entries, problems


def findings(root=ROOT):
    """-> [str]: each edit with no answer, each malformed answer, and each
    answer for a file that is no longer edited (remove it: the file
    matches upstream again)."""
    entries, problems = registry(root)
    edits = edited(root)
    out = list(problems)
    for rel, src in edits:
        if rel not in entries:
            out.append(f'{rel}: received from {src} and edited here, with no '
                       f'recorded answer -- {THREE_ANSWERS}')
    still = {rel for rel, _ in edits}
    for rel in sorted(entries):
        if rel not in still:
            out.append(f'{rel}: has a "{REGISTRY_KEY}" entry but matches what '
                       f'upstream delivered -- remove the entry')
    return out


def guard(path, root=ROOT):
    """-> why editing `path` needs an answer first, or None."""
    root = pathlib.Path(root).resolve()
    try:
        rel = pathlib.Path(path).resolve().relative_to(root).as_posix()
    except ValueError:
        return None
    src = owned(root).get(rel)
    if src is None or rel in registry(root)[0]:
        return None
    return (f'{rel} was received from {src[0]}: an edit here is undone by the '
            f'next sync or Update Vendors, and the fix usually belongs '
            f'upstream (practice: upstream-bug-stops-here). Do not edit it '
            f'until it has an answer -- {THREE_ANSWERS}. Once the answer is '
            f'recorded, this edit is allowed.')


def main(argv):
    if '--help' in argv or '-h' in argv:
        print(__doc__)
        return 0
    if '--guard' in argv:
        i = argv.index('--guard')
        if i + 1 >= len(argv):
            print('upstream_edits: --guard needs a path', file=sys.stderr)
            return 2
        why = guard(argv[i + 1])
        if why:
            print(why)
            return 3
        return 0
    found = findings()
    for line in found:
        print(line)
    # Owed upstream is answered, not finished: named on every run until the
    # upstream fix lands and the file matches again, when the entry is stale
    # and the check asks for it to go.
    for rel, e in sorted(registry()[0].items()):
        if e['answer'] == 'owed-upstream':
            print(f'owed upstream: {rel} -- {e.get("detail", "")}')
    if not found:
        print('upstream_edits: every upstream-owned file matches what was '
              'delivered, or carries its recorded answer.')
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
