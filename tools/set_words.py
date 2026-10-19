#!/usr/bin/env python3
"""The one matcher for a practice set's own words -- the ones a set declares in its precedent-source.json `owned_words`, which belong in that set and nowhere a person who does not bring it reads -- used by the check that holds every other set to them and by the tests that hold engine output to the same (spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md part 3)

set_words.py -- a set's own words stay in that set.

Some sets bring a working method with its own vocabulary: step labels,
commands, branch names. A person who does not bring the set should never
meet those words in another set, a template or a person-facing document.
The engine does not know any set's words. A set declares them, as data, in
its own precedent-source.json:

    "owned_words": {
      "patterns": [
        {"kind": "a step label", "regex": "\\\\bphase [1-9] of 9\\\\b",
         "matches": ["phase 2 of 9"], "never_matches": ["phase two"]}
      ],
      "output_patterns": [ ...held only against printed engine output... ],
      "practice_links": ["a-slug-that-lives-in-the-set"]
    }

`matches` and `never_matches` are the set's own examples: the check runs
them, so a pattern that stops matching what its set says it should is a
finding in that set, not a silent pass everywhere else.

    python3 tools/set_words.py FILE...      # print every hit, exit 1 if any
    python3 tools/set_words.py --repo .     # the files the check scopes

A record -- todo/, record/, spec/, a gotcha or practice's ## Story,
WHATS_NEW.md, the dated approved_by and *_why fields -- says what happened
and may use any word; it is never in scope.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_MANIFEST = 'precedent-source.json'
KEY = 'owned_words'

# The places a rule or a person-facing message lives. Paths are relative to
# the repository root.
SCOPE_GLOBS = (
    'practices/*.md', 'local/practices/*.md', 'templates/**/*.md',
    'documentation/*.md', 'README.md', 'SETUP.md', 'INSTALL.md',
    'WHERE_THINGS_ARE.md', 'AGENTS.md', 'MAP.md', 'GLOSSARY.md', 'GEMINI.md',
    'reply_check.json', 'tools/our_language.json', 'gotchas/INDEX.md',
)

# Ledgers are records even where they sit among templates: a row says what
# happened on a date, in that day's words.
RECORD_NAMES = ('LEDGER.md', 'CHANGELOG.md', 'WHATS_NEW.md')


class Words:
    """One set's declared words, compiled. `problems` lists what is wrong
    with the declaration itself: a pattern that does not compile, or an
    example it does not match the way the set says it should."""

    def __init__(self, name, decl):
        self.name = name
        self.patterns, self.output_patterns, self.problems = [], [], []
        decl = decl if isinstance(decl, dict) else {}
        for key, into in (('patterns', self.patterns),
                          ('output_patterns', self.output_patterns)):
            for i, p in enumerate(decl.get(key) or []):
                where = f'{KEY}.{key}[{i}]'
                if not isinstance(p, dict) or not isinstance(p.get('regex'), str):
                    self.problems.append(f'{where} is not {{"kind", "regex"}}')
                    continue
                try:
                    rx = re.compile(p['regex'])
                except re.error as e:
                    self.problems.append(f'{where} does not compile: {e}')
                    continue
                kind = str(p.get('kind') or 'a word of this set')
                for ex in p.get('matches') or []:
                    if not rx.search(ex):
                        self.problems.append(f'{where} ({kind}) does not match '
                                             f'its own example {ex!r}')
                for ex in p.get('never_matches') or []:
                    if rx.search(ex):
                        self.problems.append(f'{where} ({kind}) matches {ex!r}, '
                                             f'which it says it never should')
                into.append((kind, rx))
        slugs = [s for s in decl.get('practice_links') or []
                 if isinstance(s, str) and re.fullmatch(r'[a-z0-9-]+', s)]
        if slugs:
            self.patterns.append((
                f'a link to a practice in {name}', re.compile(
                    r'\]\((?:[./\w-]*/)?(?:' + '|'.join(map(re.escape, slugs))
                    + r')\.md(?:#[\w-]*)?\)')))

    def __bool__(self):
        return bool(self.patterns or self.output_patterns)


def _manifest(path):
    try:
        man = json.loads((pathlib.Path(path) / SOURCE_MANIFEST).read_text(
            encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return man if isinstance(man, dict) else {}


def words_of(path):
    """-> the Words a source at `path` declares, or None when it declares
    none (or its manifest cannot be read)."""
    man = _manifest(path)
    if KEY not in man:
        return None
    return Words(str(man.get('name') or pathlib.Path(path).name), man[KEY])


def sets_with_words(root=ROOT):
    """-> [(name, path, Words, provides)] for every practice source in force
    for this repository and this person that declares its own words, the
    repository itself left out. A source not cloned here cannot say what its
    words are, so it is passed over."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_resolve as _pr
    except ImportError:
        return []
    out, seen = [], set()
    root = pathlib.Path(root).resolve()
    # The repository itself is left out by declared_source_paths(), by name
    # as well as by path (precedent_resolve.is_repository_itself): a
    # checkout of a set somewhere else -- the worktree --run-tests makes --
    # is that set (2026-10-18: the ladder set's full check on main judged
    # its own words).
    for path, _level, name, note in (_pr.vendored_source_paths(root)
                                     + _pr.declared_source_paths(root)):
        if note or not path:
            continue
        p = pathlib.Path(path).resolve()
        if p == root or p in seen:
            continue
        seen.add(p)
        w = words_of(p)
        if w is not None:
            out.append((name, p, w, _pr.source_provides(p)))
    return out


def _strip_story(lines):
    """A practice's or a gotcha's ## Story is a record: blank it, keeping
    line numbers true."""
    out, skipping = [], False
    for line in lines:
        if line.startswith('## '):
            skipping = line.strip().lower() == '## story'
        out.append('' if skipping else line)
    return out


def _blank_record_fields(lines):
    """Blank a practice's frontmatter `approved_by` block and the *_why
    fields beside a field: each quotes the decision that set it, dated, in
    the words of the day, which is a record."""
    out, in_ab = [], False
    for line in lines:
        if line.startswith(('approved_by:', 'applies_to_why:', 'gates_why:')):
            in_ab = True
            out.append('')
            continue
        if in_ab and (line.startswith(' ') or line.startswith('\t')):
            out.append('')
            continue
        in_ab = False
        out.append(line)
    return out


def _requires(text):
    m = re.search(r'^requires:\s*(.+)$', text, re.M)
    return set(re.findall(r'[\w-]+', m.group(1))) if m else set()


def _inactive_practice(text):
    """A practice that is not `status: active` is history: not in force."""
    m = re.search(r'^status:\s*(\S+)', text, re.M)
    return bool(m) and m.group(1).strip('"') != 'active'


def hits(text, patterns):
    """-> [(line number, kind, matched text)] for every pattern in `text`."""
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, pat in patterns:
            for m in pat.finditer(line):
                found.append((n, kind, m.group(0)))
    return found


def output_hits(text, words):
    """-> [(line number, kind, matched text)] for printed output: a set's
    file patterns and its output-only ones."""
    return hits(text, words.patterns + words.output_patterns)


def scoped_files(root=ROOT):
    root = pathlib.Path(root)
    seen = []
    for g in SCOPE_GLOBS:
        for p in sorted(root.glob(g)):
            if p.is_file() and p not in seen and p.name not in RECORD_NAMES:
                seen.append(p)
    return seen


def file_hits(path, words, provides=()):
    """-> hits of `words` in the file at `path`, records left out. A
    practice that `requires` a capability the owning set provides is in
    force only for a person who brings that set, so its words are theirs."""
    path = pathlib.Path(path)
    text = path.read_text(encoding='utf-8', errors='replace')
    if path.suffix == '.md' and text.startswith('---'):
        if _inactive_practice(text) or (_requires(text) & set(provides)):
            return []
        text = '\n'.join(_blank_record_fields(text.splitlines()))
    if path.suffix == '.md':
        text = '\n'.join(_strip_story(text.splitlines()))
    return hits(text, words.patterns)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('files', nargs='*')
    p.add_argument('--repo', default=None,
                   help='scan the files the check scopes in this repository')
    p.add_argument('--count', action='store_true',
                   help='one line per file: how many hits')
    args = p.parse_args(argv)
    root = pathlib.Path(args.repo or ROOT)
    files = ([pathlib.Path(f) for f in args.files] if args.files
             else scoped_files(root))
    total = 0
    for name, _path, words, provides in sets_with_words(root):
        for problem in words.problems:
            print(f'{name}: {problem}')
            total += 1
        for f in files:
            found = file_hits(f, words, provides)
            total += len(found)
            if args.count:
                if found:
                    print(f'{len(found):5d}  {f}  ({name})')
                continue
            for n, kind, text in found:
                print(f'{f}:{n}: {kind} of {name}: {text!r}')
    print(f'set_words: {total} hit(s) in {len(files)} file(s)', file=sys.stderr)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
