#!/usr/bin/env python3
"""leak_gate.py — the hard-failing leak gate
(PRACTICE_ENGINE_PLAN.md, "The Verification Harness": "Leak gate — no
individual- or team-level term appears anywhere in Precedent.
RPP's private-repo-scrub machinery generalized from words to sources,
hard-failing rather than warning.")

WHY THIS RUNS AT PUSH TIME AND NOT AT MERGE TIME. The plan originally put
this at phase 3 because Precedent was to be a fork, "private initially" --
a leak could be caught and force-pushed away before anyone outside could
see it. Precedent is now a branch of BestPractice, which is public, so
**every push is publication, into a repo we do not own**. There is no
grace period and nothing to force-push away. The gate therefore has to run
before the bytes leave the machine, not before a merge.

TWO LAYERS, AND ONLY ONE OF THEM CAN LIVE HERE.

  STRUCTURAL (this file, always on, runs in CI). Precedent holds universal
  practices and nothing else. Anything shaped like private-source content
  fails: a practice file outside practices/, a path belonging to an
  individual or team set, a practice whose frontmatter claims a non-
  universal source, a personal email address, an absolute home directory.
  These patterns are safe to publish because they describe SHAPES, not
  anyone's actual vocabulary.

  VOCABULARY (an external blocklist, local only). The real leak gate
  catches private words -- client names, code words, internal identifiers.
  **That list cannot live in the repo it protects.** A blocklist of secret
  terms, committed to a public repo, publishes the secrets it exists to
  guard. This is the same reason practice 15 (`scrub-gate`) keeps the
  blocklist in the private dependent repo and scans the public vendored
  tree from there, and it generalizes unchanged.

  So the blocklist is named by PRECEDENT_LEAK_BLOCKLIST (a path outside
  this repo, e.g. in the individual set). When it is set, its patterns are
  applied and a hit is fatal. When it is NOT set, this gate says so
  loudly rather than reporting a clean pass it did not earn -- silence
  about an unrun check is exactly the failure mode the plan's evidence
  table names ("checkin.py fresh is silent on failure, so unreachable
  reads as 'current'").

CI runs the structural layer only, because CI has no access to a private
blocklist. That is a real limit, stated rather than papered over: CI is
the backstop that cannot be bypassed, the local hook is the one that knows
the words. Neither alone is the whole gate.

Run:
  python3 tools/leak_gate.py                  # whole tracked tree
  python3 tools/leak_gate.py --staged         # what is staged for commit
  python3 tools/leak_gate.py --range A..B     # what a push would send
  python3 tools/leak_gate.py --explain        # what is checked, and what is not
Exit: 0 clean, 1 on any hit or on a misconfigured blocklist.
"""
import os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCKLIST_ENV = 'PRECEDENT_LEAK_BLOCKLIST'

# Paths that must never exist in Precedent. Levels are repositories, not
# directories (the plan's "Source -- Who a Practice Belongs To"), so a
# directory shaped like a private set here means someone took the shortcut
# the plan exists to prevent.
FORBIDDEN_PATHS = [
    (re.compile(r'(^|/)(individual|personal|private)/'),
     'an individual-level directory -- individual practices live in their own '
     'private repo, never in Precedent'),
    (re.compile(r'(^|/)team[-_/]'),
     'a team-level path -- team practices live in one private repo per team'),
    (re.compile(r'(^|/)precedent-(individual|team-)'),
     'a vendored copy of a private practice set'),
    (re.compile(r'(^|/)(candidates|outbox)/'),
     'a candidates/outbox directory -- these hold unreviewed drafts that may '
     'carry private context (plan, Stage 2)'),
]

# Content shapes that are private by construction, and safe to name here
# because they are shapes rather than anyone's actual vocabulary.
FORBIDDEN_CONTENT = [
    # example.com/.org are the reserved documentation domains, and a GitHub
    # noreply address is by construction not a private one -- both appear in
    # templates as placeholders and are not leaks.
    (re.compile(r'\b(?!noreply@)[\w.+-]+@(?!example\.(?:com|org)\b)'
                r'(?!users\.noreply\.github\.com\b)[\w-]+\.[\w.-]+\b'),
     'an email address'),
    # Requires a real username SEGMENT after the prefix, not just the prefix:
    # without that, this rule matched its own source in this file and the gate
    # failed on a clean tree. A rule that cannot scan the file defining it is
    # a rule nobody will leave switched on. /home/user is this sandbox's own
    # working root, not a person's directory.
    (re.compile(r'(?:/Users/|/home/(?!user[/\s]|user$)|[A-Za-z]:\\\\Users\\\\)'
                r'[A-Za-z0-9._-]+[/\\]'),
     "an absolute path inside someone's home directory"),
    (re.compile(r'^\s*(source|level)\s*:\s*["\']?(individual|team)', re.M),
     'a practice claiming a non-universal source'),
]

SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv'}
TEXT_SUFFIXES = {'.md', '.py', '.json', '.txt', '.sh', '.yml', '.yaml', '.html',
                 '.css', '.js', '.toml', '.cfg', '.template', ''}


def _git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args],
                          capture_output=True, text=True).stdout


def files_to_check(mode, rev_range):
    if mode == 'staged':
        names = _git('diff', '--cached', '--name-only', '--diff-filter=ACMR').split('\n')
    elif mode == 'range':
        names = _git('diff', '--name-only', '--diff-filter=ACMR', rev_range).split('\n')
    else:
        # Tracked files PLUS untracked, non-ignored ones. A file that is one
        # `git add` away from being published is exactly what someone running
        # this by hand wants to know about; reporting "clean" because it is
        # not staged yet is the wrong answer to the question being asked.
        # (Caught by testing the path rules with untracked fixtures and
        # watching them pass.)
        names = (_git('ls-files').split('\n')
                 + _git('ls-files', '--others', '--exclude-standard').split('\n'))
    return sorted({n for n in names if n.strip()})


def is_texty(rel):
    p = pathlib.Path(rel)
    return p.suffix.lower() in TEXT_SUFFIXES and not any(d in p.parts for d in SKIP_DIRS)


def load_blocklist():
    """-> (patterns, source_description, configured). See the module docstring
    for why this list lives outside the repo."""
    raw = os.environ.get(BLOCKLIST_ENV, '').strip()
    if not raw:
        return [], None, False
    path = pathlib.Path(raw).expanduser()
    if not path.exists():
        sys.exit(f"leak gate FAIL: {BLOCKLIST_ENV} points at {path}, which does not "
                 f"exist. A configured-but-missing blocklist is a check that did not "
                 f"run; it is not a pass. Fix the path or unset the variable "
                 f"deliberately.")
    try:
        resolved = path.resolve()
        resolved.relative_to(ROOT)
    except ValueError:
        pass  # outside the repo, which is the point
    else:
        sys.exit(f"leak gate FAIL: the blocklist at {path} is INSIDE Precedent. A list "
                 f"of private terms committed to a public repo publishes the terms it "
                 f"exists to protect. Keep it in the private set (see practice 15, "
                 f"scrub-gate) and point {BLOCKLIST_ENV} at it there.")
    pats = []
    for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            pats.append(re.compile(line, re.I))
        except re.error as e:
            sys.exit(f"leak gate FAIL: {path}:{i} is not a valid regex ({e}): {line}")
    return pats, str(path), True


def scan(files, blocklist):
    hits = []
    for rel in files:
        for pat, why in FORBIDDEN_PATHS:
            if pat.search(rel):
                hits.append((rel, 0, why, rel))
        full = ROOT / rel
        if not full.exists() or not is_texty(rel):
            continue
        try:
            text = full.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for pat, why in FORBIDDEN_CONTENT:
            for m in pat.finditer(text):
                line_no = text.count('\n', 0, m.start()) + 1
                hits.append((rel, line_no, why, m.group(0).strip()[:70]))
        for pat in blocklist:
            for m in pat.finditer(text):
                line_no = text.count('\n', 0, m.start()) + 1
                hits.append((rel, line_no, f'blocklist /{pat.pattern}/',
                             m.group(0).strip()[:70]))
    return hits


def main():
    args = sys.argv[1:]
    if '--explain' in args:
        print(__doc__)
        return 0
    mode, rev_range = 'tree', None
    if '--staged' in args:
        mode = 'staged'
    if '--range' in args:
        i = args.index('--range') + 1
        if i >= len(args):
            sys.exit('leak gate FAIL: --range needs a revision range, e.g. origin/main..HEAD')
        mode, rev_range = 'range', args[i]

    blocklist, source, configured = load_blocklist()
    files = files_to_check(mode, rev_range)
    hits = scan(files, blocklist)

    for rel, line, why, sample in hits:
        where = f"{rel}:{line}" if line else rel
        print(f"LEAK: {where}: {why} -- {sample!r}")

    scope = {'tree': 'the tracked tree', 'staged': 'the staged changes',
             'range': f'the range {rev_range}'}[mode]
    if hits:
        print(f"\nleak gate FAIL: {len(hits)} hit(s) in {scope}. Nothing is pushed. "
              f"Precedent is a branch of a PUBLIC repo -- a push is a publication, "
              f"and it cannot be taken back.")
        return 1

    if configured:
        print(f"leak gate OK: {len(files)} file(s) in {scope} clean against "
              f"{len(FORBIDDEN_PATHS)} path rule(s), {len(FORBIDDEN_CONTENT)} content "
              f"rule(s) and {len(blocklist)} blocklist pattern(s) from {source}.")
    else:
        print(f"leak gate PARTIAL: {len(files)} file(s) in {scope} clean against the "
              f"{len(FORBIDDEN_PATHS)} path and {len(FORBIDDEN_CONTENT)} content rules "
              f"-- the STRUCTURAL layer only.")
        print(f"  The vocabulary layer did not run: {BLOCKLIST_ENV} is unset, so no "
              f"private-term blocklist was applied. This is expected in CI, which has "
              f"no access to a private list, and expected before phase 3 creates one. "
              f"It is reported rather than passed over silently: a clean structural "
              f"scan is not evidence that no private word is present.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
