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

  WRITE THE STEM, NOT THE WHOLE NAME. The two halves recognise different
  spellings: the allowlist matches `owner/name`, the patterns match the bare
  name. So a private repo whose pattern is its FULL name is guarded when
  written with a slash and naked when written short -- which is how a name
  leaked on 2026-09-07, as `<repo>-local`. Truncate each pattern to a
  distinctive head, and MEASURE the hit count against the tree before
  committing to the cut: a stem short enough to be an ordinary English word
  fires on innocent text, and a gate that cries wolf is a gate people
  switch off.

  To make the missing ones visible, a run with an owner declared also
  surveys the git clones on this disk and NOTES any repository under that
  owner whose bare name no pattern matches. It notes rather than refuses --
  a missing stem is latent risk, not a hit, and the content scan already
  covers what this tree says today. It is silent with no owner declared,
  which is also what keeps a private name out of a public CI log.
  very_deep_check.py answers the same question from the other side, for the
  repositories this tree already NAMES, by asking GitHub which are private.

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
import json, os, pathlib, re, subprocess, sys

# THE CONSUMING REPO, not this file's parent. Vendored at
# <repo>/process/upstream/tools/, `parents[1]` is process/upstream/ -- so in
# the repositories that actually hold private content this gate scanned
# BestPractice's own mirrored tree and reported it clean, while the consuming
# repo's tracked files were never opened. Found 2026-09-07 refreshing a real
# consumer: it reported "893 unit(s) ... clean", which is BestPractice's file
# count, in a repo tracking 1060.
#
# precedent_check.py hit exactly this and fixed it the same way, with the
# same comment, months earlier -- and nobody carried the fix across to the
# gate whose whole job is keeping private content out of a public push. A
# false clean here is the one this project can least afford.
#
# `git rev-parse --show-toplevel` walks up from wherever this file sits to
# the enclosing repository, which is right in both layouts without knowing
# which one it is in. The literal parents[1] stays as the no-git fallback
# only, matching doc_lint.py and practice_audit.py.
_toplevel = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                           cwd=pathlib.Path(__file__).resolve().parent,
                           capture_output=True, text=True).stdout.strip()
ROOT = pathlib.Path(_toplevel) if _toplevel else pathlib.Path(__file__).resolve().parents[1]
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


# --- Stem coverage: which private repos have no pattern at all ----------
#
# THE GAP THIS CLOSES. The allowlist above catches `owner/name`; the
# vocabulary patterns catch the BARE name. Only the first works for a
# repository nobody has written a pattern for -- so a private repo with no
# stem is guarded in its qualified form and naked in its short one, which is
# exactly how the 2026-09-07 leak got out: `<repo>-local`, no slash anywhere.
#
# WHY THE SCOPE IS "CLONES ON THIS DISK". Enumerating an account's
# repositories is not available -- `/user/repos` answers "sessions are bound
# to their configured repositories" -- and very_deep_check.py deliberately
# scopes its own audit to what the TREE names, on the ground that an unnamed
# repository is not a leak. Both are right and both miss the same case: a
# private repo you are working in right now, whose name has not reached this
# tree YET. A session working in one has it attached, and that is the moment
# its name is most likely to be typed into a document. So this takes the
# third scope, the only one that needs no network: the sibling checkouts.
#
# IT NOTES, IT DOES NOT REFUSE. A missing stem is latent risk, not a hit --
# the content scan already covers what this tree actually says, and failing
# a push over a directory sitting next to it would block work that leaks
# nothing. practice: fail-gracefully -- report what could not be guaranteed
# rather than either crying wolf or going quiet.
#
# IT CANNOT RUN IN CI, BY CONSTRUCTION, and that is deliberate: it needs the
# private blocklist's owner declaration, which CI never has. Printing a
# private repository's name into a public build log would be this rule
# leaking through its own mechanism.
_REMOTE_RE = re.compile(
    r'github\.com[:/]([A-Za-z0-9][\w-]*)/([A-Za-z][\w.-]*?)(?:\.git)?/?$')


def _remote_ref(repo_dir):
    """-> (owner, name) from a clone's origin URL, or None."""
    try:
        r = subprocess.run(['git', '-C', str(repo_dir), 'config', '--get',
                            'remote.origin.url'],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    m = _REMOTE_RE.search(r.stdout.strip())
    return (m.group(1), m.group(2)) if m else None


def local_clone_refs(root):
    """-> {(owner, name)} for this checkout and every sibling git clone.

    Siblings, because that is how a session holds more than one repository:
    `add_repo` puts each beside the others. A directory that is not a git
    checkout, or whose remote is not GitHub, is skipped silently -- this is
    a best-effort survey of what happens to be on disk, not an inventory.
    """
    root = pathlib.Path(root)
    candidates = [root]
    try:
        candidates += [d for d in sorted(root.parent.iterdir()) if d.is_dir()]
    except OSError:
        pass
    refs = set()
    for d in candidates:
        if not (d / '.git').exists():
            continue
        ref = _remote_ref(d)
        if ref:
            refs.add(ref)
    return refs


def uncovered_repo_stems(refs, owners, allowed, patterns):
    """-> [(owner, name)] whose BARE name no blocklist pattern matches.

    Only repositories under a declared private-by-default owner, and never
    one carrying an `allow` line: an allow line is somebody stating that the
    name may appear, so blocklisting its stem would refuse the exposure they
    just accepted.
    """
    out = []
    for owner, name in sorted(refs):
        if owner.lower() not in owners:
            continue
        if f'{owner}/{name}'.lower() in allowed:
            continue
        if any(p.search(name) for p in patterns):
            continue
        out.append((owner, name))
    return out


def declared_visibility(root):
    """-> ('public'|'private'|None, why) from the repo's own precedent.json.

    THE GATE'S ENTIRE PREMISE IS PUBLICATION -- its own refusal says so: "a
    push is a publication, and it cannot be taken back." That is true of the
    upstream repository and false of a private consumer, where nothing in the
    tree is published by pushing it.

    Found the moment the ROOT fix above started scanning consumers for real,
    2026-09-07: a private consuming repo lit up with 111 hits for naming the
    owner's own private repositories inside a repository that is itself
    private. Shipping the ROOT fix without this would have turned every
    private consumer's gate red for content that was never at risk -- and a
    gate that cries wolf in every install is a gate people switch off, which
    is how the real one stops being read.

    What still guards the export path from a private consumer is
    practice_audit.py's scrub over the vendored tree: that is the content
    which actually leaves, and it is gated where it leaves.

    An ABSENT field is not treated as private. Omitting it counts as public
    everywhere else in the engine (build_views.py's repo_is_public), for the
    reason that the failure is asymmetric: assuming public costs a few false
    hits, assuming private costs a permanent publication.
    """
    cfg = root / 'precedent.json'
    if not cfg.exists():
        return None, 'no precedent.json'
    try:
        data = json.loads(cfg.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        return None, f'precedent.json unreadable ({e})'
    v = (data.get('visibility') or '').strip().lower()
    if v in ('public', 'private'):
        return v, f'precedent.json declares visibility: {v}'
    return None, 'precedent.json declares no visibility'


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


KNOWN_FLAGS = {'--explain', '--staged', '--range', '--require-vocabulary',
               '--structural-only'}


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


def _private_sources_declared(root=None):
    """-> True when precedent.json declares a source whose practice text is
    private -- an individual or team set.

    THE HOLE THIS CLOSES, and it is in the docstring above. That one says the
    setting lives in git config because "whether a person HAS an individual
    set is a fact about that person, not about this repository." True, and
    incomplete: whether THIS REPOSITORY resolves private sources at all is a
    fact about the repository, it is declared in a tracked file, and it
    survives a fresh container -- which the git config does not.

    2026-09-08, the incident: a session in a fresh container could not attach
    either private source, so the vocabulary layer had no blocklist to load.
    No git config existed to make that fatal, so the gate printed PARTIAL,
    exited 0, and the push went through with only the structural rules
    applied -- into a public repository. The session reported it afterwards,
    accurately and too late. **"The check silently did not run" and "the
    check passed" were the same exit code**, which is the exact failure the
    requireVocabulary docstring says must not happen; the setting just was
    not reachable in the environment where it mattered.

    So the requirement is derived here as well as configured. A repository
    that declares no private source is unaffected -- it never had a
    vocabulary layer to lose.
    """
    import json as _json
    cfg = pathlib.Path(root or ROOT) / 'precedent.json'
    if not cfg.is_file():
        return False
    try:
        data = _json.loads(cfg.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        # A malformed precedent.json is somebody else's error to report, and
        # guessing "no private sources" here would fail open in exactly the
        # direction this function exists to close (practice: fail-gracefully).
        return True
    return any((s or {}).get('level') in ('individual', 'team')
               for s in data.get('sources', []))


def _private_sources_resolved(root=None):
    """-> (any_resolved, names_that_did_not) for the declared private sources.

    THE CORRECTION THIS MAKES, 90 minutes after the first version landed and
    on a real report from a session it blocked. Requiring the blocklist
    whenever precedent.json DECLARES a private source refuses every session
    that could not attach one -- and in this repository that is a live,
    unexplained, intermittent condition (see AGENTS.md on cross-owner adds).

    **The first version had the threat model backwards.** Private vocabulary
    reaches a session by the session READING the private sources' text. A
    session that could not attach them never read a word of it and has
    nothing from them to leak; the dangerous session is the one that DID
    attach them and is now writing to a public tree. So resolution, not
    declaration, is what should require the list.

    What the blanket refusal actually bought was not safety. It relocated the
    work: the blocked session's remedy was to hand a patch to another session,
    which is more error-prone than the push it replaced -- and its commit
    "dies with the container", which is repo-is-memory losing outright.

    The residual risk when the sources did not resolve is a private term that
    reached the session some other way, typically the person's own messages.
    That is real, small, unchanged from the behaviour before 2026-09-08, and
    named out loud in the notice rather than silently accepted.
    """
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_resolve as _pr
    except ImportError:
        # Vendored into a source set, where precedent_resolve is deliberately
        # absent. Fall back to declaration: such a repo has no multi-source
        # resolve to ask about (practice: fail-gracefully).
        return _private_sources_declared(root), []
    try:
        sources = _pr.load_config(str(root or ROOT))
        res = _pr.resolve(sources)
    except Exception:
        # A resolve that cannot run is not evidence that nothing resolved.
        # Fail toward the strict side: assume the private text IS in context.
        return True, []
    missing = {(m or {}).get('name') for m in res.get('missing', [])}
    private = [s for s in sources
               if (s or {}).get('level') in ('individual', 'team')]
    unresolved = [s.get('name') for s in private if s.get('name') in missing]
    resolved = [s.get('name') for s in private if s.get('name') not in missing]
    return bool(resolved), unresolved


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

    # --structural-only is the ONE way to ask for the structural half alone,
    # and it is deliberately explicit: continuous integration has no private
    # blocklist and never will, so it opts out BY NAME in a tracked workflow
    # file rather than every other caller failing open by default. The
    # workflow that uses it is already called "Leak gate (structural)".
    structural_only = '--structural-only' in args
    _priv_resolved, _priv_unresolved = _private_sources_resolved()
    require_vocab = (not structural_only
                     and ('--require-vocabulary' in args
                          or _require_vocabulary_configured()
                          or _priv_resolved))
    blocklist, source, configured = load_blocklist()
    units = units_to_scan(mode, rev_range)
    # The repo-reference allowlist is read from the SAME private file as the
    # vocabulary patterns, so a clone with no private blocklist configured
    # gets no owner policy either -- and says so through the existing
    # PARTIAL reporting, rather than silently enforcing nothing.
    _raw_bl = os.environ.get(BLOCKLIST_ENV, '').strip()
    _policy = (parse_repo_policy(pathlib.Path(_raw_bl).expanduser())
               if _raw_bl else ({}, {}))
    _vis, _why = declared_visibility(ROOT)
    if _vis == 'private':
        print(f'leak gate NOT APPLICABLE: {_why}, so pushing this tree '
              f'publishes nothing and there is no leak for this gate to '
              f'prevent. This is a stand-down, NOT a pass -- it inspected '
              f'nothing. What still guards content leaving here is '
              f'practice_audit.py\'s scrub over the vendored tree, which is '
              f'where the export actually happens.')
        return 0

    hits = scan(units, blocklist, _policy)
    # SAY WHEN THE ALLOWLIST IS OFF. It only does anything once somebody
    # declares an owner private-by-default, and a clone that never did would
    # otherwise get a clean "OK" covering a rule that inspected nothing --
    # the fail-open shape this gate's own vocabulary layer already learned to
    # announce. Printed on every run, pass or fail.
    if not (_policy[0] or {}):
        print('leak gate NOTE: no `# visibility-audit: private-owner <account>` '
              'is declared, so the repo-reference allowlist is INERT -- a '
              'private repository named in this tree would not be caught by '
              'it. Declare one in the private blocklist to switch it on.',
              file=sys.stderr)
    else:
        # The other half of the same question. The allowlist above is on, so
        # every `owner/name` mention is covered -- these are the repositories
        # whose BARE name nothing covers, which is the form that actually
        # leaked. Reported every run, because the moment to add a stem is
        # while the repository is in front of you.
        _gaps = uncovered_repo_stems(local_clone_refs(ROOT), _policy[0],
                                     _policy[1], blocklist)
        for _owner, _name in _gaps:
            print(f'leak gate NOTE: {_owner}/{_name} is a clone on this disk '
                  f'under a private-by-default owner, and NO blocklist pattern '
                  f'matches its bare name "{_name}". Its qualified form is '
                  f'refused by the allowlist; the short form somebody actually '
                  f'types is not. Add a stem for it -- truncate to a '
                  f'distinctive head and measure the hit count before '
                  f'committing to the cut. This is a note, not a hit: nothing '
                  f'in this tree says the name today.', file=sys.stderr)

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
    if _priv_unresolved and not _priv_resolved:
        # The declared-but-unresolved case: allowed, and never quietly. The
        # session could not read the private text, so it has nothing from
        # there to leak -- but a private term can still have reached it
        # another way, most plausibly the person's own messages, and that is
        # the residual risk somebody should carry knowingly.
        print(f"  AND: {', '.join(sorted(n for n in _priv_unresolved if n))} "
              f"did not resolve this session, so no blocklist was reachable "
              f"at all -- this is not a misconfiguration you can fix from "
              f"here.\n"
              f"  The push is allowed BECAUSE the private text was never in "
              f"context: a session that could not read those sources has "
              f"nothing from them to leak.\n"
              f"  What is NOT covered: a private term that reached this "
              f"session some other way, most plausibly your own messages. "
              f"Say so in the reply -- somebody should carry that knowingly "
              f"rather than find it later.")
    if require_vocab:
        # Name WHICH of the three triggers fired. The message used to assert
        # the git-config one unconditionally, so once the requirement could
        # also be derived from precedent.json it sent a reader to a setting
        # that was not set and could not be unset -- a guard misreporting its
        # own reason (practice: control-asserts-which-failure).
        if '--require-vocabulary' in args:
            why = ("--require-vocabulary was passed on this run")
            fix = ("drop the flag, or set " + BLOCKLIST_ENV)
        elif _require_vocabulary_configured():
            why = ("this clone has declared that it HAS a private-term "
                   "blocklist (`git config precedent.requireVocabulary true`)")
            fix = ("set " + BLOCKLIST_ENV + " to your blocklist in your "
                   "individual set, or unset the git config deliberately")
        else:
            why = ("a private practice source RESOLVED this session, so its "
                   "text is in context and a private term could reach this "
                   "tree through it")
            fix = ("set " + BLOCKLIST_ENV + " to the blocklist in that same "
                   "source -- you have the repository, so you have the file. "
                   "Continuous integration, which has no private list by "
                   "design, passes --structural-only instead")
        print(f"\nleak gate FAIL: {why}, and {BLOCKLIST_ENV} is not set. "
              f"An unrun vocabulary layer is a failure, not a partial pass: "
              f"'the check silently did not run' and 'the check passed' must "
              f"not be the same exit code on a tree that publishes. To fix it, "
              f"{fix}.")
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
