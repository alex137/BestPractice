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

  VOCABULARY, in two halves. This layer catches WORDS rather than shapes.

    The DEFAULT half (tools/leak-blocklist.default.txt) is committed and
    always applied -- terms that are unsafe to publish and safe to name,
    profanity first among them, in a repo whose documents are read by
    people outside the project. Nothing there is a secret, so committing it
    costs nothing.

    Its second job is the important one: it makes this layer actually RUN.
    Until 2026-09-06 the whole layer was skipped whenever
    PRECEDENT_LEAK_BLOCKLIST was unset -- every CI run, every fresh clone --
    so the code that loads, compiles and scans with patterns was exercised
    only by the harness, and the gate reported PARTIAL forever. A mechanism
    that runs only in its own tests is one nobody finds out is broken.

    The PRIVATE half catches private words -- client names, code words,
    internal identifiers -- and **that list cannot live in the repo it
    protects.** A blocklist of secret terms, committed to a public repo,
    publishes the secrets it exists to guard, and load_blocklist() refuses
    one located inside this repository for exactly that reason. This is the
    same reason (practice: scrub-gate) keeps the blocklist in the private
    dependent repo and scans the public vendored tree from there.

    It is named by PRECEDENT_LEAK_BLOCKLIST (a path outside this repo, e.g.
    in the individual set), and is MERGED with the default, never a
    replacement for it. When it is not set the gate still reports OK -- the
    layer did run -- but says plainly that only the publishable half was
    checked. That sentence is not decoration: a clean scan against
    publishable terms is not evidence that no private word is present, and
    dropping it would leave the old silence with better wording.

  Once you HAVE a list, an unrun vocabulary layer must not exit 0 like a
  pass. `git config precedent.requireVocabulary true` in your clone (or
  --require-vocabulary) makes a missing PRECEDENT_LEAK_BLOCKLIST fatal, so
  losing the variable in a new shell fails the push instead of quietly
  downgrading it to the structural half.

CI runs the structural layer and the DEFAULT vocabulary half; it cannot run
the private half, having no access to a private list. That is a real limit, stated rather than papered over: CI is
the backstop that cannot be bypassed, the local hook is the one that knows
the words. Neither alone is the whole gate.

WHAT "WHAT A PUSH WOULD SEND" MEANS, since getting this wrong is how a
push-time gate passes on a publication. A push sends every COMMIT in the
range, not the tree they end at, so --range walks the range commit by
commit, reads each blob out of git rather than off disk, and scans every
commit MESSAGE too. --staged likewise reads the staged blob, not the
working-tree file. Three separate misses were found by testing this rather
than reading it -- see the comment above units_to_scan.

Run:
  python3 tools/leak_gate.py                  # whole tracked tree
  python3 tools/leak_gate.py --staged         # what is staged for commit
  python3 tools/leak_gate.py --range A..B     # what a push would send
  python3 tools/leak_gate.py --range "SHA --not --remotes"   # a new branch
  python3 tools/leak_gate.py --require-vocabulary            # fail if unrun
  python3 tools/leak_gate.py --explain        # what is checked, and what is not
Exit: 0 clean, 1 on any hit, on a misconfigured blocklist, or on an unrun
vocabulary layer this clone declared it needs.
"""
import os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCKLIST_ENV = 'PRECEDENT_LEAK_BLOCKLIST'

# The committed, publishable half of the vocabulary layer. See the header of
# the file itself for why this one may live inside the repo when the private
# one may not, and why its existence is what makes the vocabulary layer
# actually RUN rather than be skipped whenever no private list is configured.
DEFAULT_BLOCKLIST = pathlib.Path(__file__).resolve().parent / 'leak-blocklist.default.txt'

# Paths that must never exist in Precedent. Levels are repositories, not
# directories (the plan's "Source -- Who a Practice Belongs To"), so a
# directory shaped like a private set here means someone took the shortcut
# the plan exists to prevent.
FORBIDDEN_PATHS = [
    # re.I throughout: a directory a person names by hand -- Team-Nightjar/,
    # Individual/, Candidates/ -- is exactly as forbidden as its lowercase
    # spelling, and the case-sensitive versions of these four passed every
    # such path silently until a deep-check audit planted one and watched
    # the gate exit 0.
    (re.compile(r'(^|/)(individual|personal|private)/', re.I),
     'an individual-level directory -- individual practices live in their own '
     'private repo, never in Precedent'),
    (re.compile(r'(^|/)team[-_/]', re.I),
     'a team-level path -- team practices live in one private repo per team'),
    (re.compile(r'(^|/)precedent-(individual|team-)', re.I),
     'a vendored copy of a private practice set'),
    (re.compile(r'(^|/)(candidates|outbox)/', re.I),
     'a candidates/outbox directory -- these hold unreviewed drafts that may '
     'carry private context (plan, Stage 2)'),
]

# Exactly one path is exempt from FORBIDDEN_PATHS, by full path, and it is
# not a loophole: it is the canonical SessionStart hook every consuming
# project is TOLD to install, at a name tools/precedent_resolve.py fixes in
# code (INDIVIDUAL_BOOTSTRAP_HOOK) and INSTALL.md publishes. Its basename
# begins with 'precedent-individual', so the vendored-private-set rule above
# matched it -- that rule means a DIRECTORY holding a private set's content
# (its own comment says so), and it was matching a filename that merely
# starts with the same text.
#
# 2026-09-06: this fired the moment BestPractice installed its own copy of
# that hook, refusing a file the project's own instructions require. Exempting
# the one known path, rather than loosening the pattern to require a trailing
# '/', keeps the rule's full strength for every other name -- a file called
# precedent-individual-notes.md is still refused.
#
# The hook contains no private practice content: it is a wrapper naming the
# set's git remote, which this repository already publishes in a dozen spec
# documents. Whether THAT wider disclosure is intended is a separate open
# question (spec/PRELAUNCH_AUDIT.md raises it for the project's own prior notes repository);
# this exemption does not settle it and does not widen it.
#
# verify_harness.py asserts this string still equals precedent_resolve's own
# constant, so the exemption cannot drift from where the engine looks.
ALLOWED_PATHS = frozenset({'.claude/hooks/precedent-individual-bootstrap.sh'})

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
    # Anchored to the END of the line (an optional quote/comment aside) so
    # this only matches a line that IS a `key: value` pair -- the shape a
    # leaked practice's frontmatter would actually have. Before this end
    # anchor existed, the pattern only checked the START of the line, so
    # ordinary capitalized prose beginning a line with "Source:" or "Level:"
    # -- a completely normal sentence or heading style, nothing to do with a
    # practice's frontmatter -- hard-failed the always-on structural gate
    # that runs in CI on every branch. Confirmed: "Source: Individual
    # contributions to this open-source library are always welcome" passed
    # clean before the case-insensitivity fix (case-sensitive "Source"
    # didn't match "source"), then started failing once that fix landed,
    # because nothing scoped the match to an actual frontmatter-shaped line.
    (re.compile(r'^\s*(source|level)\s*:\s*["\']?(individual|team)["\']?'
               r'\s*(#.*)?$', re.M | re.I),
     'a practice claiming a non-universal source'),
]

SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv'}
TEXT_SUFFIXES = {'.md', '.py', '.json', '.txt', '.sh', '.yml', '.yaml', '.html',
                 '.css', '.js', '.toml', '.cfg', '.template', ''}


def _git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args],
                          capture_output=True, text=True).stdout


def _git_ok(*args):
    """Run git and fail loudly on a nonzero exit. `_git` swallows errors,
    which is right for the tree scan and wrong everywhere a bad revision
    would otherwise read as "nothing to check" -- an empty scan is the same
    silent all-clear this gate exists to refuse."""
    r = subprocess.run(['git', '-C', str(ROOT), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"leak gate FAIL: `git {' '.join(args)}` failed "
                 f"({r.stderr.strip() or 'no message'}). A gate that cannot read what "
                 f"it is gating has not passed.")
    return r.stdout


def _lines(text):
    return [l for l in text.split('\n') if l.strip()]


# --- what gets scanned -------------------------------------------------------
#
# A unit is (display, relpath_or_None, text_or_None). The path rules run on
# relpath, the content and blocklist rules on text.
#
# WHY THIS IS NOT SIMPLY "THE FILES ON DISK". A push publishes every commit
# it sends, not the tree those commits happen to end at, and the working tree
# is not what git transmits. Three misses were found by testing exactly that,
# each of which reported a clean pass on a push that published a blocked term:
#
#   1. `--range` used `git diff A..B`, the NET diff. A file added in one
#      commit and deleted in a later one in the same push does not appear in
#      it at all -- and its blob is published regardless, readable forever at
#      the commit that added it.
#   2. Both `--range` and `--staged` then read the WORKING TREE copy of each
#      name. A file staged with a private term and cleaned up afterwards, or
#      committed and then reverted, scanned as clean.
#   3. Commit messages were never scanned. They are published verbatim, and
#      a message is exactly where a session narrates what it was working on.
#
# So range mode walks the range commit by commit and reads blobs out of git,
# and staged mode reads the staged blob (`:path`) rather than the file.


def units_to_scan(mode, rev_range):
    if mode == 'staged':
        units = []
        for rel in sorted(set(_lines(_git_ok('diff', '--cached', '--name-only',
                                             '--diff-filter=ACMR')))):
            units.append((rel, rel, _blob(f':{rel}') if is_texty(rel) else None))
        return units

    if mode == 'range':
        units, seen = [], set()
        commits = _lines(_git_ok('rev-list', *rev_range.split()))
        for sha in commits:
            short = sha[:9]
            # The message is published with the commit. Scan it as text; it
            # has no path, so the path rules do not apply to it.
            units.append((f'{short} (commit message)', None,
                          _git_ok('log', '-1', '--format=%B', sha)))
            names = _lines(_git_ok('diff-tree', '-r', '-m', '--no-commit-id',
                                   '--root', '--name-only', '--diff-filter=ACMR', sha))
            for rel in sorted(set(names)):
                if (sha, rel) in seen:
                    continue
                seen.add((sha, rel))
                units.append((f'{short}:{rel}', rel,
                              _blob(f'{sha}:{rel}') if is_texty(rel) else None))
        return units

    # Tracked files PLUS untracked, non-ignored ones. A file that is one
    # `git add` away from being published is exactly what someone running
    # this by hand wants to know about; reporting "clean" because it is
    # not staged yet is the wrong answer to the question being asked.
    # (Caught by testing the path rules with untracked fixtures and
    # watching them pass.)
    names = sorted({n for n in (_lines(_git('ls-files'))
                                + _lines(_git('ls-files', '--others',
                                              '--exclude-standard')))})
    units = []
    for rel in names:
        text = None
        full = ROOT / rel
        if is_texty(rel) and full.exists():
            try:
                text = full.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                text = None
        units.append((rel, rel, text))
    return units


def _blob(spec):
    """The content git holds at `spec` (`:path`, or `<sha>:path`), not the
    working tree's copy. Returns None for anything that is not decodable
    text -- a submodule entry, a binary, a path git cannot resolve."""
    r = subprocess.run(['git', '-C', str(ROOT), 'show', spec],
                       capture_output=True)
    if r.returncode != 0:
        return None
    try:
        return r.stdout.decode('utf-8')
    except UnicodeDecodeError:
        return None


# The default blocklist necessarily CONTAINS the words it bans, so scanning
# it would hard-fail the gate on its own list -- the same self-match trap the
# home-directory content rule above already carries a comment about, and the
# reason the profanity terms were briefly base64-encoded instead. One fixed,
# committed path, skipped by name.
#
# This is NOT the `!path` exemption _parse_blocklist refuses. That one is
# caller-supplied and arbitrary, and exempting an arbitrary path from a leak
# scan is how a leak gets out. This is the single file whose entire purpose
# is to hold these strings, it is reviewed like any other committed file,
# and it may hold only publishable terms by its own header -- a private term
# put here would be published by the commit itself, long before any scan.
SCAN_EXEMPT = {'tools/leak-blocklist.default.txt'}


def is_texty(rel):
    p = pathlib.Path(rel)
    if p.as_posix() in SCAN_EXEMPT:
        return False
    return p.suffix.lower() in TEXT_SUFFIXES and not any(d in p.parts for d in SKIP_DIRS)


# --------------------------------------------------------------------------
# Repo references: an ALLOWLIST, because a blocklist cannot block what nobody
# typed into it
# --------------------------------------------------------------------------
#
# The vocabulary layer is a list of literal strings, so it blocks exactly the
# names somebody remembered. That is the wrong default for repository names
# specifically, and it failed in both directions on one day, 2026-09-07: it
# missed a private repository nobody had listed, and it blocked two names
# that had since become public. Detection after the fact now exists
# (very_deep_check.py's visibility audit, which asks the GitHub API), but a
# push gate cannot ask the network -- it has to work offline and in CI.
#
# So for repository references the default is inverted. Declare an OWNER
# whose repositories are private unless stated otherwise, and every
# `owner/name` mention is refused unless it carries a reason:
#
#     # visibility-audit: private-owner <account> -- repos private by default
#     # visibility-audit: allow <account>/<repo> -- why this one may be named
#
# The example uses placeholders on purpose: this file is public, and writing
# a real account into it would be the rule leaking through its own manual.
#
# The set of names you may mention is small, stable and known to you. The set
# of repositories you might create is unbounded and grows without anyone
# thinking about the blocklist. Inverting the default puts the work where the
# knowledge is: naming a new private repo in a public tree now requires one
# line saying why, instead of requiring that somebody once predicted it.
#
# Both declarations live as COMMENTS in the private blocklist file, which is
# already the per-person place where "which names matter" is decided, and are
# read by very_deep_check.py's audit from the same file -- one declaration,
# two consumers, rather than a second file to keep in sync.
PRIVATE_OWNER_RE = re.compile(
    r'#\s*visibility-audit:\s*private-owner\s+([A-Za-z0-9][\w-]*)\s*--\s*(.+)$')
ALLOW_REF_RE = re.compile(
    r'#\s*visibility-audit:\s*allow\s+([A-Za-z0-9][\w-]*/[\w.-]+)\s*--\s*(.+)$')


def parse_repo_policy(path):
    """-> (private_owners, allowed_refs) from a blocklist file's comments."""
    owners, allowed = {}, {}
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        return owners, allowed
    for line in text.splitlines():
        line = line.strip()
        m = PRIVATE_OWNER_RE.match(line)
        if m:
            owners[m.group(1).lower()] = m.group(2).strip()
            continue
        m = ALLOW_REF_RE.match(line)
        if m:
            allowed[m.group(1).lower()] = m.group(2).strip()
    return owners, allowed


def repo_ref_hits(text, owners, allowed):
    """-> [(line_no, owner/name)] for references that are not allowed."""
    if not owners:
        return []
    alt = '|'.join(re.escape(o) for o in sorted(owners))
    # Two entry points, and missing the second made the rule nearly useless:
    # the lookbehind that keeps `a/acct/x` from matching ALSO rejected
    # `github.com/acct/x`, because the character before the owner is `/`
    # there too -- and a URL is the likeliest way a repository name ever
    # appears. Caught by the stated case for it, not by reading.
    pat = re.compile(r'(?:github\.com/|(?<![\w./-]))(' + alt + r')/([A-Za-z][\w.-]*?)'
                     r'(?=[\s)\]"\'`,;:]|\.git\b|/|$)', re.I)
    out = []
    for m in pat.finditer(text):
        ref = f'{m.group(1)}/{m.group(2)}'
        if ref.lower() in allowed:
            continue
        out.append((text.count('\n', 0, m.start()) + 1, ref))
    return out


def _parse_blocklist(path, allow_inside_repo=False):
    """Compile one blocklist file to patterns. Shared by both halves so the
    default list and a private one cannot drift in how they are read."""
    pats = []
    for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('!'):
            sys.exit(f"leak gate FAIL: {path}:{i} starts with '!'. Path "
                     f"exemptions are a practice_audit.py scrub feature and "
                     f"are deliberately NOT honoured here -- exempting a path "
                     f"from a leak scan is how a leak gets out. Remove the "
                     f"line, or keep the two files separate if the scrub "
                     f"genuinely needs the exemption.")
        try:
            pats.append(re.compile(line, re.I))
        except re.error as e:
            sys.exit(f"leak gate FAIL: {path}:{i} is not a valid regex ({e}): {line}")
    return pats


def load_default_blocklist():
    """The committed, publishable patterns -- always applied.

    A missing or empty default file is FATAL, not a silent downgrade. This
    file is the reason the vocabulary layer runs at all on an ordinary
    clone, so losing it would silently restore the exact state it was added
    to remove: a layer that never runs outside its own tests."""
    if not DEFAULT_BLOCKLIST.is_file():
        sys.exit(f"leak gate FAIL: the default blocklist {DEFAULT_BLOCKLIST} is "
                 f"missing. It is committed and always applied; without it the "
                 f"vocabulary layer silently stops running on every clone that "
                 f"has no private list.")
    pats = _parse_blocklist(DEFAULT_BLOCKLIST)
    if not pats:
        sys.exit(f"leak gate FAIL: the default blocklist {DEFAULT_BLOCKLIST} has no "
                 f"patterns. An empty list reports as a vocabulary-layer pass while "
                 f"checking nothing.")
    return pats


def load_blocklist():
    """-> (patterns, source_description, private_configured).

    Always includes the committed default patterns; adds the private list
    when PRECEDENT_LEAK_BLOCKLIST names one. The third value reports whether
    the PRIVATE half was configured, which is what --require-vocabulary and
    the reporting below key off -- the default half is never in question."""
    default_pats = load_default_blocklist()
    raw = os.environ.get(BLOCKLIST_ENV, '').strip()
    if not raw:
        return default_pats, f'{DEFAULT_BLOCKLIST.name} ({len(default_pats)} pattern(s))', False
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
                 f"exists to protect. Keep it in the private set "
                 f"(see practice: scrub-gate) and point {BLOCKLIST_ENV} at it there.")
    # practice_audit.py's scrub reads the same file format and honours a
    # leading `!` as a path exemption. This gate deliberately does NOT --
    # see _parse_blocklist, which refuses it for both halves.
    pats = _parse_blocklist(path)
    if not pats:
        sys.exit(f"leak gate FAIL: the blocklist at {path} contains no patterns. A "
                 f"configured-but-empty blocklist reports as a vocabulary-layer PASS "
                 f"while checking nothing, which is the one outcome this gate must "
                 f"never produce. Add at least one term, or unset {BLOCKLIST_ENV} "
                 f"deliberately and rely on the default list alone.")
    return (default_pats + pats,
            f'{DEFAULT_BLOCKLIST.name} ({len(default_pats)}) + {path} ({len(pats)})',
            True)


def scan(units, blocklist, repo_policy=(None, None)):
    owners, allowed = repo_policy
    hits = []
    for display, rel, text in units:
        if rel is not None and rel not in ALLOWED_PATHS:
            for pat, why in FORBIDDEN_PATHS:
                if pat.search(rel):
                    hits.append((display, 0, why, rel))
        if text is None:
            continue
        for pat, why in FORBIDDEN_CONTENT:
            for m in pat.finditer(text):
                line_no = text.count('\n', 0, m.start()) + 1
                hits.append((display, line_no, why, m.group(0).strip()[:70]))
        for pat in blocklist:
            for m in pat.finditer(text):
                line_no = text.count('\n', 0, m.start()) + 1
                hits.append((display, line_no, f'blocklist /{pat.pattern}/',
                             m.group(0).strip()[:70]))
        for line_no, ref in repo_ref_hits(text, owners or {}, allowed or {}):
            hits.append((display, line_no,
                         'undeclared repo reference (owner is private by '
                         'default; add a `# visibility-audit: allow ' + ref +
                         ' -- why` line to the blocklist if this may be named)',
                         ref))
    return hits


KNOWN_FLAGS = {'--explain', '--staged', '--range', '--require-vocabulary'}


def _require_vocabulary_configured():
    """Opt-in, per clone: `git config precedent.requireVocabulary true`.

    WHY THIS EXISTS. Without it the vocabulary layer fails OPEN. Someone who
    has a blocklist, and is relying on it, loses it the moment a shell starts
    without the variable set -- a new terminal, a cron job, a cloud session --
    and the gate prints PARTIAL and exits 0, so the push goes through. On a
    branch of a public repo, "the check silently did not run" and "the check
    passed" must not be the same exit code once you have said you have a list.
    The setting lives in git config rather than in a tracked file because
    whether a person HAS an individual set is itself a fact about that
    person, not about this repository."""
    v = _git('config', '--get', 'precedent.requireVocabulary').strip().lower()
    return v in ('1', 'true', 'yes', 'on')


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
        args = args[:i - 1] + args[i + 1:]
    # An unknown flag must not be ignored. `--stage` (a typo for --staged)
    # silently scanned the whole tree and exited 0, which answers a question
    # the caller did not ask with a confident all-clear.
    unknown = [a for a in args if a.startswith('--') and a not in KNOWN_FLAGS]
    if unknown:
        sys.exit(f"leak gate FAIL: unknown option(s) {', '.join(unknown)} -- known "
                 f"options are {', '.join(sorted(KNOWN_FLAGS))}.")

    require_vocab = '--require-vocabulary' in args or _require_vocabulary_configured()
    blocklist, source, configured = load_blocklist()
    units = units_to_scan(mode, rev_range)
    # The repo-reference allowlist is read from the SAME private file as the
    # vocabulary patterns, so a clone with no private blocklist configured
    # gets no owner policy either -- and says so through the existing
    # PARTIAL reporting, rather than silently enforcing nothing.
    _raw_bl = os.environ.get(BLOCKLIST_ENV, '').strip()
    _policy = (parse_repo_policy(pathlib.Path(_raw_bl).expanduser())
               if _raw_bl else ({}, {}))
    hits = scan(units, blocklist, _policy)

    for display, line, why, sample in hits:
        where = f"{display}:{line}" if line else display
        print(f"LEAK: {where}: {why} -- {sample!r}")

    scope = {'tree': 'the tracked tree', 'staged': 'the staged changes',
             'range': f'the range {rev_range}'}[mode]
    if hits:
        print(f"\nleak gate FAIL: {len(hits)} hit(s) in {scope}. Nothing is pushed. "
              f"Precedent is a branch of a PUBLIC repo -- a push is a publication, "
              f"and it cannot be taken back.")
        return 1

    # The vocabulary layer ALWAYS runs now -- the committed default list is
    # applied on every invocation, so "the layer did not run" is no longer a
    # reachable state and is no longer reported as one. What is still worth
    # saying is which HALVES ran: a clean scan against publishable terms is
    # not evidence that no PRIVATE word is present, and that sentence has to
    # survive the change or this is just the old silence with better wording.
    print(f"leak gate OK: {len(units)} unit(s) in {scope} clean against "
          f"{len(FORBIDDEN_PATHS)} path rule(s), {len(FORBIDDEN_CONTENT)} content "
          f"rule(s) and {len(blocklist)} blocklist pattern(s) from {source}.")
    if configured:
        return 0

    print(f"  Note: the private half of the vocabulary layer did not run "
          f"({BLOCKLIST_ENV} is unset), so publishable terms were checked and "
          f"private ones were not. Expected in CI, which has no access to a "
          f"private list. Said out loud rather than left to inference: a clean "
          f"scan against the default list is not evidence that no private word "
          f"is present.")
    if require_vocab:
        print(f"\nleak gate FAIL: this clone has declared that it HAS a private-term "
              f"blocklist (`git config precedent.requireVocabulary true`, or "
              f"--require-vocabulary), and {BLOCKLIST_ENV} is not set. Once you have "
              f"said you have a list, an unrun vocabulary layer is a failure, not a "
              f"partial pass -- set {BLOCKLIST_ENV} to your blocklist in your "
              f"individual set, or unset the git config deliberately.")
        return 1
    return 0


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/HOW_TO_USE_THIS_TECHNICAL.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
