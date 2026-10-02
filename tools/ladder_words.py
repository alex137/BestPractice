#!/usr/bin/env python3
"""ladder_words.py -- the one matcher for the five-stage ladder's own words
(spec/LADDER_OPT_IN_PLAN.md D7, "Check E").

The ladder is a working method a person opts into by bringing the set that
provides it. Its words -- the stage labels, the release commands, the branch
tiers -- belong in that set and nowhere a person off the ladder reads. This
module says which words those are, once, so the check that holds the
rule-bearing files to it and the tests that hold engine OUTPUT to it cannot
disagree.

    python3 tools/ladder_words.py FILE...      # print every hit, exit 1 if any
    python3 tools/ladder_words.py --repo .     # the files Check E scopes

STRICT words only. "Consider", "Act" and "Produce" are ordinary English and
never match on their own, nor does a lowercase "brainstorm"; a stage name
counts only beside its step label, and a command only when it is quoted or
bold, the way a command is written. A record -- todo/, record/, spec/, a
gotcha or practice's ## Story, WHATS_NEW.md -- says what happened and may
use any word; it is never in scope.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The slugs that live in the ladder set (spec/LADDER_OPT_IN_PLAN.md D1). A
# link to one of them from outside the set points at a file that is not
# there for a person who does not bring it.
LADDER_SLUGS = (
    'act', 'brainstorm-holds-commits', 'checks-follow-the-tier',
    'chief-of-staff', 'consider', 'debut', 'go-merge', 'go-update',
    'merge-authorization-keyword', 'plan-it', 'primary-branch', 'produce',
    'promote', 'push-directly', 'relayed-authorization',
    'stage-word-carries-its-step', 'tier-branch', 'write-it-up',
)

_COMMANDS = (r'Booked|Book it|Go update|Brainstorm|Plan it|Write it up|'
             r'Debut|Make live|Promote(?: \d)?')
PATTERNS = (
    ('a step label', re.compile(r'\bstep [1-5N] of 5\b')),
    ('a numbered Promote', re.compile(r'\bPromote [1-5N]\b')),
    ('a stage beside its step', re.compile(
        r'\b(?:Consider|Act|Booked|Debut|Produce)\s*\(step\b')),
    ('a ladder command, quoted or bold', re.compile(
        r'(?:\*\*|["“])(?:' + _COMMANDS + r')(?:\*\*|["”])')),
    ('a branch tier', re.compile(r'\bpre-staging\b')),
    # The command words themselves, capitalised as a command is written.
    # Lowercase "promote" or "booked" in ordinary prose does not match.
    ('a ladder command', re.compile(
        r'\b(?:Booked|Debut|Promote[sd]?|Promotion|Go update|Book it|'
        r'Shared Save|Make live)\b')),
    ('a link to a practice in the ladder set', re.compile(
        r'\]\((?:[./\w-]*/)?(?:' + '|'.join(map(re.escape, LADDER_SLUGS))
        + r')\.md(?:#[\w-]*)?\)')),
)

# Engine OUTPUT is held to one more word than the files: the tier
# "staging" as a branch name. In a file it is too often the ordinary word,
# or a record of a repository's own branch; in a message printed to a
# person off the ladder it is a tier they do not have.
OUTPUT_PATTERNS = PATTERNS + (
    ('a branch tier', re.compile(r'\bstaging\b')),
)


def output_hits(text):
    """-> [(line number, kind, matched text)] for printed output."""
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, pat in OUTPUT_PATTERNS:
            for m in pat.finditer(line):
                found.append((n, kind, m.group(0)))
    return found


# What Check E holds to the rule (D7): the places a rule or an engine
# message lives. Paths are relative to the repository root.
SCOPE_GLOBS = (
    'practices/*.md', 'local/practices/*.md', 'templates/**/*.md',
    'documentation/*.md', 'README.md', 'SETUP.md', 'INSTALL.md',
    'WHERE_THINGS_ARE.md', 'AGENTS.md', 'MAP.md', 'GLOSSARY.md', 'GEMINI.md',
    'reply_check.json', 'tools/our_language.json', 'gotchas/INDEX.md',
)


def _strip_story(text):
    """A practice's or a gotcha's ## Story is a record: leave it out."""
    out, skipping = [], False
    for line in text.splitlines(keepends=True):
        if line.startswith('## '):
            skipping = line.strip().lower() in ('## story',)
        if not skipping:
            out.append(line)
    return ''.join(out)


def hits(text):
    """-> [(line number, kind, matched text)] for every ladder word."""
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, pat in PATTERNS:
            for m in pat.finditer(line):
                found.append((n, kind, m.group(0)))
    return found


# Ledgers are records even where they sit among templates: a row says what
# happened on a date, in that day's words.
RECORD_NAMES = ('LEDGER.md', 'CHANGELOG.md', 'WHATS_NEW.md')


def scoped_files(root=ROOT):
    root = pathlib.Path(root)
    seen = []
    for g in SCOPE_GLOBS:
        for p in sorted(root.glob(g)):
            if p.is_file() and p not in seen and p.name not in RECORD_NAMES:
                seen.append(p)
    return seen


def _is_record_line_block(lines):
    """Blank a practice's frontmatter `approved_by` block: it quotes the
    decision as it was made, in the words of the day, which is a record."""
    out, in_ab = [], False
    for i, line in enumerate(lines):
        # approved_by, and the *_why fields beside a field: each quotes the
        # decision that set it, dated, in the words of the day.
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


def _ladder_only(text):
    """A practice whose frontmatter says `requires: ["ladder"]` is in force
    only for a person on the ladder, so its words are the ladder's own."""
    m = re.search(r'^requires:\s*(.+)$', text, re.M)
    return bool(m) and 'ladder' in m.group(1)


def _inactive_practice(text):
    """A practice that is not `status: active` is history: not in force."""
    m = re.search(r'^status:\s*(\S+)', text, re.M)
    return bool(m) and m.group(1).strip('"') != 'active'


def file_hits(path):
    path = pathlib.Path(path)
    text = path.read_text(encoding='utf-8', errors='replace')
    if path.suffix == '.md' and text.startswith('---') and (
            _inactive_practice(text) or _ladder_only(text)):
        return []
    if path.suffix == '.md' and text.startswith('---'):
        text = '\n'.join(_is_record_line_block(text.splitlines()))
    if path.suffix == '.md':
        # Line numbers must stay true, so blank the Story rather than cut it.
        kept = _strip_story(text)
        if kept != text:
            lines, keep, skipping = [], [], False
            for line in text.splitlines():
                if line.startswith('## '):
                    skipping = line.strip().lower() == '## story'
                lines.append('' if skipping else line)
            text = '\n'.join(lines)
    return hits(text)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('files', nargs='*')
    p.add_argument('--repo', default=None,
                   help='scan the files Check E scopes in this repository')
    p.add_argument('--count', action='store_true',
                   help='one line per file: how many hits')
    args = p.parse_args(argv)
    files = ([pathlib.Path(f) for f in args.files] if args.files
             else scoped_files(args.repo or ROOT))
    total = 0
    for f in files:
        found = file_hits(f)
        total += len(found)
        if args.count:
            if found:
                print(f'{len(found):5d}  {f}')
            continue
        for n, kind, text in found:
            print(f'{f}:{n}: {kind}: {text!r}')
    print(f'ladder_words: {total} hit(s) in {len(files)} file(s)',
          file=sys.stderr)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
