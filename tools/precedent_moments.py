#!/usr/bin/env python3
"""Which practices key on the Boildown's two named moments, and which restate one in their own words instead of naming it

precedent_moments.py -- the one owner of "the archive-line reply" and "the
closing reply" (practice: the-boildown, "Moments other practices key on").

WHY THIS EXISTS (2026-10-20). On 2026-10-18 the-boildown changed what those
two moments are: the archive line may end any reply, and the closing items
wait for the reply that answers "Archive" or "Archive?". Practices that keyed
on the moments had copied the old wording into their own occasion, gate
note and tool text, so the change broke them silently, twice in two days:
Boildown item 6's delete links stopped appearing (fixed 2026-10-19, after
about seventy landed branches piled up), and the ladder set's branch cleanup
page was re-keyed to the reply answering "Archive", which the person rarely
types (fixed 2026-10-20). Each was patched where it showed. This tool and
the check that runs it (precedent_check.py, boildown-moments-named) are the
fix at the cause: a dependent names the moment, the-boildown alone says
what it is, and a change to either moment starts from this list of who
has to follow.

WHAT IT READS, per practices/ tree given (default: this repository's own,
plus every sibling checkout beside it that has one): each practice in force
other than the-boildown itself -- its frontmatter `title`, `occasion`,
`index_clause`, `gates_why` and `applies_to_why`; the `note` of each of its
entries in that tree's reply_check.json; and every tool its `ships:` or a
reply_check.json `note_from_tool` names. Prose sections and Story are not
read: history may quote the old wording, and a rule body may explain the
moment it names.

  python3 tools/precedent_moments.py            # dependents and restatements
  python3 tools/precedent_moments.py ROOT ...   # those trees only
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))

OWNER = 'the-boildown'

# name -> the wording that restates it instead of naming it. The names are
# the-boildown's; a dependent writes "the archive-line reply (the-boildown)".
MOMENTS = {
    'archive-line reply': re.compile(
        r'you can archive this session|'
        r'says?,? (?:that )?the session can be archived', re.I),
    'closing reply': re.compile(
        r'answers?\s+\\?["“]Archive|"Archive\??" or "Archive\??"', re.I),
}

FIELDS = ('title', 'occasion', 'index_clause', 'gates_why', 'applies_to_why')


def default_roots():
    roots = [ROOT]
    for sib in sorted(ROOT.parent.iterdir()):
        if sib != ROOT and (sib / 'practices').is_dir() and (sib / '.git').exists():
            roots.append(sib)
    return roots


def _texts(root, fm, slug, notes, tools):
    """-> [(where, text)] for one practice: its frontmatter fields, its
    reply_check notes, the tools it ships or runs."""
    import build_views as bv
    out = [(f'{f}:', str(fm.get(f) or '')) for f in FIELDS]
    out += [('reply_check.json note', n) for n in notes.get(slug, [])]
    for rel in sorted(set(bv.ships_paths(fm)) | set(tools.get(slug, []))):
        p = root / rel
        if p.is_file() and p.suffix == '.py':
            out.append((rel, p.read_text(encoding='utf-8', errors='replace')))
    return out


def _reply_check(root):
    notes, tools = {}, {}
    try:
        reqs = json.loads((root / 'reply_check.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return notes, tools
    for r in reqs if isinstance(reqs, list) else []:
        slug = r.get('practice')
        if not slug:
            continue
        if isinstance(r.get('note'), str):
            notes.setdefault(slug, []).append(r['note'])
        run = (r.get('note_from_tool') or {}).get('run')
        if isinstance(run, str):
            tools.setdefault(slug, []).append(run.split()[0])
    return notes, tools


def scan(roots=None, skip=lambda rel: False):
    """-> (dependents, restatements).

    dependents:   [(root, slug, moment)] -- names a moment, the way to key on it
    restatements: [(root, rel_file, slug, moment, where, excerpt)]

    `skip(rel)` drops a practice file this tree received rather than wrote
    (the check passes precedent_check._foreign_practice)."""
    import build_views as bv
    dependents, restatements = [], []
    for root in roots or default_roots():
        pdir = root / 'practices'
        if not pdir.is_dir():
            continue
        notes, tools = _reply_check(root)
        for fm, _s, f in bv.load_practices(pdir, in_force_only=True,
                                           announce=False):
            slug = fm.get('slug', pathlib.Path(f).stem)
            rel = str(pathlib.Path(f).resolve().relative_to(root.resolve()))
            if slug == OWNER or skip(rel):
                continue
            texts = _texts(root, fm, slug, notes, tools)
            for name, pat in MOMENTS.items():
                if any(name in t for w, t in texts if w.endswith(':')):
                    dependents.append((root, slug, name))
                for where, t in texts:
                    m = pat.search(t)
                    if m:
                        a = max(0, m.start() - 40)
                        restatements.append(
                            (root, rel, slug, name, where,
                             ' '.join(t[a:m.end() + 40].split())))
    return dependents, restatements


def main(argv):
    roots = [pathlib.Path(a).resolve() for a in argv] or None
    dependents, restatements = scan(roots)
    print('Practices keyed on a moment by name (these follow a change to it):')
    for root, slug, name in dependents or []:
        print(f'  {root.name}: {slug} -> the {name}')
    if not dependents:
        print('  none')
    print('Restating a moment instead of naming it (move each to the name):')
    for root, rel, slug, name, where, ex in restatements:
        print(f'  {root.name}/{rel} ({where}): the {name} -- "...{ex}..."')
    if not restatements:
        print('  none')
    return 1 if restatements else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
