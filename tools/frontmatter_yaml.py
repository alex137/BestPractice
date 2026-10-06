#!/usr/bin/env python3
"""The real-YAML frontmatter parser doc_lint.py and verify_harness.py both check against, shared so the two never drift

frontmatter_yaml.py -- shared real-YAML frontmatter check, called from
both tools/verify_harness.py (check_frontmatter_is_real_yaml, deep check)
and tools/doc_lint.py (light check, gated on touched files: (practice:
two-check-levels), whose Install section folds a repo's own JSON/YAML
syntax checks into the fast pass rather than leaving them deep-only). One
parser, two call sites, so a fix or a new edge case lands once instead of
drifting between two copies.

It also holds FIELD_ORDER, the one written-down order of a practice file's
frontmatter fields, and the fixer that puts a file into it:

    python3 tools/frontmatter_yaml.py --fix-order [PATH ...]
    python3 tools/frontmatter_yaml.py --check-order [PATH ...]
    python3 tools/frontmatter_yaml.py --fix-staged

`--fix-staged` is what the engine's commit hook runs, so the order is kept
rather than checked after the fact (2026-10-05: the field-order check sat
warning-only for nine days waiting for a fixer nothing ever ran). It never
refuses a commit, and it touches a staged practices/*.md file only when all
of these hold: the repository declares itself a practice source (its own
precedent-source.json), another source does not own the file, the working
copy is exactly what is staged (rewriting and re-staging a partly staged
file would pull unstaged edits into the commit -- practice:
repair-cannot-discard-work), and the file carries no field this copy of the
engine does not know (an older copy would push a newer field to the end).
Anything it leaves alone is left to the check.

With no PATH both cover this repo's own practices/*.md, leaving out any a
committed MANIFEST.json says another source owns (those are copies, fixed
where they are authored). precedent_check.py's `frontmatter-field-order`
reads the same constant, and spec/PRACTICE_FORMAT.md's example is held to
it by that check, so the order lives here once.

This repo's own frontmatter reader takes everything after a line's first
colon and is happy with `title: Build/buy: decompose before deciding`.
PyYAML is not -- the second colon opens a nested mapping and it rejects the
whole block. A format whose only conforming parser is its author's is not a
format, so both the fast and the full check hold every scanned file's
frontmatter to a real parser, not just this repo's own reader.
"""
import json
import pathlib
import re
import sys

try:
    import yaml as _yaml
    HAVE_YAML = True
except ImportError:
    _yaml = None
    HAVE_YAML = False

_FENCE_RE = re.compile(r'---\n(.*?)\n---\n', re.S)


def frontmatter_yaml_error(text):
    """None if TEXT claims no --- frontmatter, PyYAML is unavailable, or the
    frontmatter is valid; otherwise a one-line reason a real YAML parser
    rejected it. A caller that must tell "PyYAML missing" apart from "valid"
    checks HAVE_YAML itself before calling this."""
    if not HAVE_YAML or not text.startswith('---\n'):
        return None
    m = _FENCE_RE.match(text)
    if not m:
        return 'opens a --- fence that is never closed'
    try:
        _yaml.safe_load(m.group(1))
    except Exception as e:
        return str(e).split('\n')[0]
    return None


# --------------------------------------------------------------------------
# Field order. practice-file frontmatter, spec/PRACTICE_FORMAT.md "The Shape".
# --------------------------------------------------------------------------
#
# WHY IT IS CODE (2026-09-26). The spec set this order and nothing checked
# it. When `ships:` rolled out, a handoff message told a shared set to put
# it "under applies_to"; the spec puts it after checked_by. The set followed
# the message and had to undo the move, and a count that day found 49 of 151
# practices here out of order, and some in every set. Morgan ruled the
# spec's order stands, so it is written down once, here, and checked.
#
# A field not listed here is reported by the check rather than guessed at.
# The fixer moves one to the end, after every listed field, keeping the
# relative order such fields had.
FIELD_ORDER = (
    'slug',
    'title',
    'tier',
    'severity',
    # How binding the practice is, and who set that: absent means Protocol
    # (tools/practice_standing.py; spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md).
    'standing',
    'standing_by',
    'scope',
    'applies_to',
    # Why applies_to is what it is -- moved here from tools/routing_scope.json
    # on 2026-09-29, so a practice cannot arrive or leave without it.
    'applies_to_why',
    'occasion',
    'gates',
    'gates_why',
    'index_clause',
    'index_required',
    'checked_by',
    'ships',
    # A Claude Code hook the practice needs wired, running a file it ships
    # (build_views.practice_hooks; precedent_sync_views.py adds it).
    'hooks',
    'defines',
    # The documents a practice exists to uphold -- a risk register, a
    # policy page -- as paths or links. Informational: no engine reads it.
    # A project repository used it before the spec listed it, and every
    # check warned (2026-10-06).
    'upholds',
    'command',
    'status',
    'in_force_at',
    'expires',
    'requires',
    # Who a session shows the practice to: absent for everyone, `code-owners`
    # for the repository's code owners only (tools/precedent_audience.py).
    'visible_to',
    'supersedes',
    'overrides',
    'added',
    'approved_by',
    'strength',
    'source_practice_number',
    # Read by split_practices.py's rebuild: practices 47-52 open on bare
    # prose in the original catalogue, and this keeps the rebuild from
    # adding a "**Rule.**" label they never had.
    'source_rule_unlabeled',
)

_KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_-]*)[ \t]*:')


def _field_blocks(fm_text):
    """(preamble, [(key, lines)], trailer) for the lines between the fences.

    A field's block is its key line plus every line after it that is not
    another column-0 key: indented continuations of a folded scalar, list
    items, blank lines. A column-0 `#` comment belongs to the field BELOW it,
    since that is the one it describes; comments after the last field stay
    at the end."""
    preamble, blocks, pending = [], [], []
    for line in fm_text.split('\n'):
        m = _KEY_RE.match(line)
        if m:
            blocks.append((m.group(1), pending + [line]))
            pending = []
        elif not blocks:
            preamble.append(line)
        elif line.startswith('#') or pending:
            pending.append(line)
        else:
            blocks[-1][1].append(line)
    return preamble, blocks, pending


def _split(text):
    if not text.startswith('---\n'):
        return None
    m = _FENCE_RE.match(text)
    if not m:
        return None
    return m.group(1), text[m.end(1):]


def _rank(key):
    return FIELD_ORDER.index(key) if key in FIELD_ORDER else len(FIELD_ORDER)


# A REPOSITORY MAY DECLARE FIELDS OF ITS OWN (2026-10-06). precedent.json's
# `own_frontmatter_fields` lists frontmatter keys this repository's own
# tooling reads, so its practices may carry them without a warning on every
# run. Reported from a consumer: nine of its repo-local practices carry a
# field its own check reads, and once unlisted fields warned again they
# warned on every run, for ever, with no way to say the field was meant.
# Declared fields sort after every field the spec lists (_rank already puts
# any key FIELD_ORDER does not know last), and a declared name the spec
# lists is ignored -- the spec's meaning wins.
OWN_FIELDS_KEY = 'own_frontmatter_fields'


def own_fields(root):
    """-> the frontmatter keys `root`'s precedent.json declares as its own,
    less any FIELD_ORDER already lists. () when it declares none."""
    import json
    try:
        data = json.loads((pathlib.Path(root) / 'precedent.json')
                          .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return ()
    got = data.get(OWN_FIELDS_KEY) if isinstance(data, dict) else None
    if not isinstance(got, list):
        return ()
    return tuple(k for k in got if isinstance(k, str) and k
                 and k not in FIELD_ORDER)


def unlisted_fields(text, own=()):
    """Frontmatter keys in TEXT that FIELD_ORDER does not list and the
    repository has not declared as its own (`own`, from own_fields())."""
    parts = _split(text)
    if parts is None:
        return []
    return [k for k, _ in _field_blocks(parts[0])[1]
            if k not in FIELD_ORDER and k not in own]


def field_order_problem(text):
    """None if TEXT's frontmatter is already in FIELD_ORDER (or it has none);
    otherwise one line naming the first field that is out of place."""
    parts = _split(text)
    if parts is None:
        return None
    keys = [k for k, _ in _field_blocks(parts[0])[1]]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    if dupes:
        return (f'carries {", ".join(f"`{k}:`" for k in dupes)} more than '
                f'once, which a YAML parser reads as the last one only')
    for a, b in zip(keys, keys[1:]):
        if _rank(b) < _rank(a):
            return f'`{b}:` comes after `{a}:`, and the spec puts it before'
    return None


def reorder_fields(text):
    """TEXT with its frontmatter fields in FIELD_ORDER and nothing else
    changed: every line keeps its bytes (values, comments, the padding that
    aligns them), only whole field blocks move, and the body is untouched.
    Returns TEXT itself when it has no frontmatter, is already in order, or
    repeats a key (which one of the copies is meant is a person's call).

    It asserts its own promise rather than trusting it: the same lines, the
    same body, and -- where PyYAML is installed -- the same parsed mapping,
    or it raises instead of returning a rewrite."""
    parts = _split(text)
    if parts is None:
        return text
    fm_text, rest = parts
    preamble, blocks, trailer = _field_blocks(fm_text)
    keys = [k for k, _ in blocks]
    if len(set(keys)) != len(keys):
        return text
    ordered = [b for _, b in sorted(enumerate(blocks),
                                    key=lambda ib: (_rank(ib[1][0]), ib[0]))]
    new_fm = '\n'.join(preamble + [ln for _, lines in ordered for ln in lines]
                       + trailer)
    new = '---\n' + new_fm + rest
    if new == text:
        return text
    assert sorted(new_fm.split('\n')) == sorted(fm_text.split('\n')), \
        'reorder_fields changed a line, not just the order'
    assert new.endswith(rest), 'reorder_fields touched the body'
    if HAVE_YAML:
        try:
            before = _yaml.safe_load(fm_text)
        except Exception:
            before = None
        if before is not None:
            assert _yaml.safe_load(new_fm) == before, \
                'reorder_fields changed what the frontmatter parses to'
    return new


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _foreign_slugs(root):
    """Slugs a committed MANIFEST.json says another source owns -- the same
    reading as precedent_check.py's _foreign_practice."""
    manifest = root / 'MANIFEST.json'
    try:
        entries = json.loads(manifest.read_text(encoding='utf-8')).get('practices', [])
    except (OSError, ValueError):
        return set()
    return {e.get('slug') for e in entries if e.get('level') != 'repo-local'}


def own_practice_files(root=None):
    root = root or ROOT
    foreign = _foreign_slugs(root)
    return [p for p in sorted((root / 'practices').glob('*.md'))
            if p.stem not in foreign]


def _git(root, *args):
    import subprocess
    return subprocess.run(['git', '-C', str(root), *args],
                          capture_output=True, text=True)


def fix_staged(root=None):
    """Put the staged practice files of the repository at ROOT (default:
    the one the current directory is in) in field order and re-stage them.
    -> the list of paths it reordered. Never raises for a file it cannot
    fix: it skips it, says why, and leaves it to the check."""
    if root is None:
        top = _git(pathlib.Path.cwd(), 'rev-parse', '--show-toplevel')
        if top.returncode != 0:
            return []
        root = pathlib.Path(top.stdout.strip())
    root = pathlib.Path(root)
    if not (root / 'precedent-source.json').is_file():
        return []
    staged = _git(root, 'diff', '--cached', '--name-only', '--diff-filter=AM',
                  '--', 'practices/*.md').stdout.split()
    foreign = _foreign_slugs(root)
    fixed = []
    for rel in staged:
        p = root / rel
        if p.parent.name != 'practices' or p.stem in foreign or not p.is_file():
            continue
        if _git(root, 'diff', '--quiet', '--', rel).returncode != 0:
            print(f'frontmatter_yaml: {rel} is only partly staged -- left '
                  f'for the field-order check')
            continue
        text = p.read_text(encoding='utf-8')
        unknown = unlisted_fields(text, own_fields(root))
        if unknown:
            print(f'frontmatter_yaml: {rel} carries {", ".join(unknown)}, '
                  f'which this copy of the engine does not know -- left alone')
            continue
        try:
            new = reorder_fields(text)
        except AssertionError as e:
            print(f'frontmatter_yaml: {rel} not reordered ({e})')
            continue
        if new == text:
            continue
        p.write_text(new, encoding='utf-8')
        _git(root, 'add', '--', rel)
        fixed.append(rel)
        print(f'frontmatter_yaml: put {rel} in field order and re-staged it')
    return fixed


def main(argv):
    if argv and argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    if argv and argv[0] == '--fix-staged':
        fix_staged()
        return 0
    if not argv or argv[0] not in ('--fix-order', '--check-order'):
        print(__doc__)
        return 2
    fix = argv[0] == '--fix-order'
    paths = [pathlib.Path(a) for a in argv[1:]] or own_practice_files()
    changed, stuck = [], []
    for p in paths:
        text = p.read_text(encoding='utf-8')
        problem = field_order_problem(text)
        if problem is None:
            continue
        new = reorder_fields(text)
        if new == text:
            stuck.append((p, problem))
            continue
        changed.append(p)
        if fix:
            p.write_text(new, encoding='utf-8')
    verb = 'reordered' if fix else 'out of order'
    for p in changed:
        print(f'  {verb}: {p}')
    for p, problem in stuck:
        print(f'  NOT FIXED: {p}: {problem}')
    print(f'frontmatter field order: {len(changed)} file(s) {verb}, '
          f'{len(stuck)} left for a person, of {len(paths)} checked')
    if stuck or (changed and not fix):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
