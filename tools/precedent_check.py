#!/usr/bin/env python3
"""precedent_check.py — the ENFORCED loading channel, made real (phase 4).

PRACTICE_ENGINE_PLAN.md, "How an Agent Knows Which Practices to Load", names
four channels. Three were built in phase 2 and 3; this is the fourth:

    **Enforced.** Practices with `checked_by` are never loaded at all. The
    check's failure message *is* the rule, delivered at the moment of
    violation.

Before this existed, `checked_by:` was a *claim*: a string naming a script
that existed. The harness verified the file was there and nothing else, so
eight practices reported enforcement that nobody had ever seen fire. Tested
one by one at the start of phase 4, the eight came apart:
`readers-vocabulary` named a linter with no vocabulary check in it at all;
`acronyms-glossary` named a check that only ever warns; the two practices
naming `doc_sync.py` and the two naming `practice_audit.py` named gates that
were RED on this repository, for reasons that had nothing to do with either
practice. A claim nobody tested is worth less than no claim, because it
reads as coverage.

So this module is deliberately not "a script that checks practices". It is a
registry with one entry per enforced practice, and every entry owes two
things:

  * **a failure message that IS the rule.** On a violation the practice's
    own `## Rule` is printed, read through the same code path every other
    channel uses (`split_practices._read_practice_file`, via
    `precedent_show`'s reader) — never a paraphrase that can drift from it.
  * **a test that proves it fires.** tools/verify_harness.py plants a real
    violation for every registered slug in a throwaway repository and
    asserts the exit status, then asserts the unplanted baseline is clean.
    A slug registered here without a case there fails the harness.

A CHECK THAT CANNOT RUN REPORTS THAT IT DID NOT RUN. Every graceful-failure
path here ends in SKIPPED with a reason, never in a pass. This repository
has been bitten four times by the opposite -- a scan with an empty input set
printing OK -- and the whole point of an enforced practice is that its check
is the only thing standing where the prose used to be.

A RULE THIS REPO HAS SAID DOES NOT BIND IT REPORTS **EXEMPT**, and reports
it by name with the recorded reason. `not_binding` in precedent.json is
where a consuming repo declares that a pair -- this repo, this rule -- has
no relationship (precedent_resolve.load_not_binding). Until 2026-09-10 that
declaration did nothing to this module's run: only the reachability check
read it, so an exempted practice was still checked, still violated, still
counted, and there was no way for a consuming repo to declare a practice
non-binding and get a clean check. `severity: blocking` still cannot be
exempted. See load_exemptions().

Scopes, because a practice is not always a property of a file:

  tree      a property of the repository as it stands (an index exists, the
            generated views are current). Always runs.
  change    a property of what a change adds or edits (a new practice
            carries its incident). Runs against the files in scope.
  turn-end  a property of the state you wanted AFTER an operation (nothing
            unpushed, no published history rewritten). Excluded from the
            default run -- mid-work it is not a violation -- and run by
            --turn-end, which is where a Stop hook calls it.

Run:
  python3 tools/precedent_check.py                  # tree + change scopes
  python3 tools/precedent_check.py --turn-end       # the end-of-turn scope
  python3 tools/precedent_check.py --only SLUG      # one practice
  python3 tools/precedent_check.py --paths A B      # explicit change scope
  python3 tools/precedent_check.py --all            # change scope = whole tree
  python3 tools/precedent_check.py --list           # what is registered
  python3 tools/precedent_check.py --explain        # what each check does NOT check
  python3 tools/precedent_check.py --strict         # a SKIP is a failure
"""
import ast, difflib, functools, io, json, os, pathlib, re, subprocess, sys

# `git rev-parse --show-toplevel`, not `Path(__file__).resolve().parents[1]`:
# this module runs two ways -- self-hosted at THIS repo's own tools/
# (parents[1] is correct there) and vendored into a dependent repo at
# process/upstream/tools/ (parents[1] resolves to process/upstream/ itself
# in that layout, not the dependent repo's real root). A tree-scope check
# meant to scan the CONSUMING repo -- migration-scrubs-vocabulary is the one
# that surfaced this, in a real dependent-repo migration, 2026-09-03 --
# silently scanned process/upstream/'s own tree instead and reported a
# false-clean SKIPPED, never seeing the dependent repo's real files, no
# matter how the check itself was invoked. `git rev-parse --show-toplevel`
# walks up from wherever this file actually sits to the enclosing git
# repository's root, which is correct in both layouts without needing to
# know which one it's in -- doc_lint.py and practice_audit.py already use
# this same resolution for the same reason (this module's own `_git` helper,
# defined below, isn't used here -- it returns the full CompletedProcess,
# not the string ROOT needs, and isn't defined yet at this point in the
# file). The literal `parents[N]` stays as a last-resort fallback for the
# no-git case only (matching those two tools' own pattern), never as the
# primary path.
_toplevel = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                           cwd=pathlib.Path(__file__).resolve().parent,
                           capture_output=True, text=True).stdout.strip()
ROOT = pathlib.Path(_toplevel) if _toplevel else pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
# Where this module physically sits. In the classic INSTALL.md section 1
# layout that is <repo>/process/upstream/tools/, NOT <repo>/tools/ -- ROOT
# is deliberately the consuming repo's own root (see the long comment
# above), so `ROOT / 'tools' / x` names a directory the vendored audit
# tools are not in. Every check that reaches for a sibling tool goes
# through _tool_path() rather than assuming one layout or the other.
_HERE_TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import split_practices as sp

# practice: one-formatter-per-quantity -- every moment in time this project
# writes down comes from ONE module, in the person's zone, carrying its
# offset. Never a bare datetime.date.today(): that is the container's UTC.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # noqa: E402


# Which trees this repo MIRRORS from somewhere else, and therefore may not
# edit. precedent_resolve.mirrored_prefixes() is the one place that question
# is answered -- its own docstring carries the reasoning and the incident.
# Several checks here need it, and each of them used to hardcode
# 'process/upstream/', which is INSTALL.md §1's layout and invisible to a §0
# install. Cached because it reads files and is asked once per check.
#
# It never raises, so the only thing guarded is the import: precedent_check.py
# ships into source sets, which vendor it without precedent_resolve.py.
_MIRRORED_CACHE = {}


def _mirrored(repo):
    """-> tuple of repo-relative prefixes this repo mirrors; () if none."""
    key = str(repo)
    if key not in _MIRRORED_CACHE:
        try:
            import precedent_resolve as pr
            _MIRRORED_CACHE[key] = tuple(pr.mirrored_prefixes(repo))
        except Exception:
            _MIRRORED_CACHE[key] = ('process/upstream/',)
    return _MIRRORED_CACHE[key]


# --------------------------------------------------------------------------
# The one code path: a failure message is the practice's own Rule.
# --------------------------------------------------------------------------

def rule_of(slug):
    path = _practice_file(slug)
    if path is None:
        # Two very different reasons a slug has no practice file, and saying
        # "no practice file" for both reads as a broken install for the one
        # that is working exactly as designed. A practice_backed=False check
        # enforces a property of the ENGINE and never had a catalogue
        # practice; a practice_backed one whose file is absent is either a
        # withheld private source or a genuine gap.
        reg = CHECKS.get(slug) or {}
        if not reg.get('practice_backed', True):
            return (f'({slug} enforces a property of the engine itself, not a '
                    f'catalogue practice -- there is no practices/{slug}.md by '
                    f'design. The check\'s own description above is the rule.)')
        return f'(no practice file for {slug})'
    try:
        _fm, sections = sp._read_practice_file(path)
    except sp.PracticeFileError as e:
        return f'({slug}: {e})'
    return sections.get('rule', '').strip() or f'(no Rule recorded for {slug})'


class NotApplicable(Exception):
    """Raised by a check that could not run. Reported as SKIPPED, never PASS."""


class Finding:
    def __init__(self, where, detail):
        self.where, self.detail = where, detail

    def __str__(self):
        return f'{self.where}: {self.detail}' if self.where else self.detail


CHECKS = {}


def check(slug, scope, what, blind_to, advisory=False, practice_backed=True):
    """Register a check. `blind_to` is what it does NOT catch, printed by
    --explain -- a check's limits belong beside it, not in a document that
    drifts from it.

    `practice_backed=False` marks a check that enforces a property of the
    engine itself rather than a catalogue practice, so it has no
    `practices/<slug>.md` to be in force. Every other check is gated on
    its practice actually resolving in THIS repo (see `run()`): this file
    is vendored into consuming repos, and a check for a practice a
    consumer does not have is a finding it can never act on.

    `advisory=True` is distinct from a practice's own frontmatter
    `severity:` field (precedent_resolve.py's `severity: blocking`, about
    which SOURCE wins when two levels disagree) -- this is about whether
    THIS enforced check's own findings fail the run. Not exposed as a CLI
    flag or a general mechanism: a check is advisory only when a specific,
    dated incident justifies it (see parallel-artifact-ledger's own
    comment, 2026-09-05), the same bar checkable-gets-checked sets for
    leaving a practice advisory-only in the first place."""
    def deco(fn):
        CHECKS[slug] = dict(slug=slug, scope=scope, fn=fn, what=what,
                            blind_to=blind_to, advisory=advisory,
                            practice_backed=practice_backed)
        return fn
    return deco


def register_materialized_checks():
    """Register one CHECKS entry per `tools/checks/check_*.py` script this
    repo's sources materialized into it (precedent_materialize.py writes
    them there from every declared source's own tools/checks/).

    WHY THIS EXISTS. Until this ran, nothing anywhere invoked those
    scripts. `precedent_materialize.py` copied them in, `precedent_land.py`
    refused to land a team or individual practice without one, and
    `spec/PRIVATE_ENFORCEMENT_BRIEF.md` told a private set how to write
    them -- and then a consuming repo held fourteen real, tested check
    scripts (nine in precedent-team-maintainers, five in
    precedent-individual, as of 2026-09-06) that no command ever ran. The
    enforced channel was live for the universal catalogue and hollow for
    exactly the sources an adopting team writes for itself.

    The contract every one of those scripts already keeps, and this
    depends on: no arguments; `ROOT` derived from its own location
    (`<repo>/tools/checks/check_x.py` -> `<repo>`), so it audits the repo
    it was materialized INTO, not its source; exit 0 and print nothing
    when clean; exit 1 and print the finding when violated; exit 2 for
    "could not run" (reported SKIPPED, never PASS, per this module's own
    rule). Any other exit status is the script's own bug and is reported
    as ERROR, which is neither a pass nor a violation.

    The slug is taken from whichever practice's `checked_by` names the
    script, so a finding names the practice and prints its Rule like
    every other check here -- falling back to the filename only when no
    practice claims it (a hand-dropped orphan, which the consuming repo's
    own materialized-tree check is the thing that catches)."""
    # Built a segment at a time, deliberately: the literal spelling
    # `ROOT / 'tools' / '<name>'` is exactly what the
    # vendored-engine-file-refs-resolve check scans for, and this
    # directory is one a source materializes rather than one the engine
    # ships — a hardcoded reference to it would be a false violation on
    # every repo that has no per-source check scripts at all.
    # Two directories, because a source's check script reaches this repo by
    # two different routes:
    #
    #   tools/checks/       -- what precedent_materialize.py WROTE here, from
    #                          every source this repo resolves. The normal
    #                          case, in any consuming repo.
    #   local/tools/checks/ -- a repo-local source's own scripts, read in
    #                          place. A repo that IS one of its own sources
    #                          (Precedent itself: `path: "."`) cannot
    #                          materialize into itself -- materialize()
    #                          refuses that by name, since its output
    #                          directory would be the source's only copy --
    #                          so nothing ever copies these to tools/checks/.
    #
    # Built a segment at a time, deliberately: the literal spelling
    # `ROOT / 'tools' / '<name>'` is exactly what the
    # vendored-engine-file-refs-resolve check scans for, and these are
    # directories a source supplies rather than ones the engine ships -- a
    # hardcoded reference would be a false violation on every repo with no
    # per-source check scripts at all.
    checks_dirs = [(ROOT / 'tools').joinpath('checks'),
                   (ROOT / 'local').joinpath('tools', 'checks')]
    checks_dirs = [d for d in checks_dirs if d.is_dir()]
    if not checks_dirs:
        return
    claimed = {}
    for d in ((ROOT / 'practices'), (ROOT / 'local' / 'practices')):
        for f in sorted(d.glob('*.md')):
            try:
                fm, _sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            cb = (fm.get('checked_by') or '').strip().strip('"').strip("'")
            if cb.endswith('.py') and '/checks/' in cb:
                claimed[pathlib.PurePath(cb).name] = fm.get('slug', f.stem)

    # One script per FILENAME, and the materialized copy wins. The two
    # locations require different `ROOT` depths from the same file --
    # `tools/checks/x.py` counts three parents up to the repo root,
    # `local/tools/checks/x.py` four -- and a script hardcodes whichever
    # one it was written for. A repo-local source that is ALSO materialized
    # therefore has two byte-identical copies of every check, exactly one
    # of which resolves ROOT correctly, and this used to run both and let
    # alphabetical order decide which finding you saw: `local/...` sorts
    # before `tools/...`, so the WRONG one won every time.
    #
    # 2026-09-06, in a real consuming repo: two of its own repo-local
    # checks reported `no book-*/ directory exists` and `README.md: file
    # does not exist` about files sitting in plain view. Both scripts were
    # correct; run from `local/tools/checks/` their ROOT resolved to
    # `<repo>/local`, where indeed neither exists. Preferring the
    # materialized copy is right in both directions -- a repo that cannot
    # materialize into itself (Precedent's own `path: "."` source) has no
    # `tools/checks/` at all, so its `local/` scripts still run in place,
    # which is what they are written for.
    by_name = {}
    for d in checks_dirs:
        for s in sorted(d.glob('check_*.py')):
            by_name.setdefault(s.name, s)   # checks_dirs is in preference order
    for script in sorted(by_name.values()):
        slug = claimed.get(script.name, script.stem)
        if slug in CHECKS:          # a built-in check already owns this slug
            continue
        rel = str(script.relative_to(ROOT)).replace('\\', '/')

        def _run_script(ctx, _script=script, _rel=rel):
            r = subprocess.run([sys.executable, str(_script)],
                               cwd=str(ROOT), capture_output=True, text=True)
            out = (r.stdout + r.stderr).strip()
            if r.returncode == 0:
                return []
            if r.returncode == 2:
                raise NotApplicable(out or f'{_rel} reported it could not run')
            if r.returncode != 1:
                raise RuntimeError(
                    f'{_rel} exited {r.returncode} (expected 0 clean, 1 '
                    f'violated, or 2 could-not-run): {out or "no output"}')
            # Keep the script's findings and drop its own header and its
            # own copy of the Rule: the runner prints the Rule for every
            # check here, through one code path, so letting the script's
            # copy through too would print it twice and let the two
            # spellings drift.
            lines = []
            for line in out.splitlines():
                if line.strip().rstrip(':').lower() == 'the rule':
                    break
                if line.strip().startswith('VIOLATION:'):
                    continue
                if line.strip():
                    lines.append(line.strip())
            return [Finding(_rel, '\n    '.join(lines) or 'reported a violation '
                                                          'with no detail')]

        CHECKS[slug] = dict(
            slug=slug, scope='tree', fn=_run_script,
            what=f'whatever {rel} checks — a check script supplied by one '
                 f'of this repo\'s own practice sources',
            blind_to=f"anything {rel} does not look at; its own limits are "
                     f"documented in its docstring, not here",
            advisory=False, practice_backed=True)


def _practice_file(slug):
    """Where `rule_of` would find this slug's practice file, or None.

    The three layouts a practice file can be in, in the order they are
    searched: the materialized `practices/` tree (what
    precedent_materialize.py writes from every resolved source), a
    repo-local source's own `local/practices/`, and
    `process/upstream/practices/` -- the classic pre-Precedent vendoring
    layout INSTALL.md §1 still installs, where the catalogue never lands
    at the repo root at all. rule_of() searched only the first two, so in
    a §1 dependent repo every violation printed "(no practice file for
    ...)" where the Rule belonged -- and the whole design of this module
    is that the failure message IS the rule."""
    for rel in (('practices', f'{slug}.md'),
                ('local', 'practices', f'{slug}.md'),
                ('process', 'upstream', 'practices', f'{slug}.md')):
        p = ROOT.joinpath(*rel)
        if p.exists():
            return p
    return None


# --------------------------------------------------------------------------
# Scope
# --------------------------------------------------------------------------

def _git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=str(cwd or ROOT),
                          capture_output=True, text=True)


def _instructions_file():
    """The file a session's harness actually loads. AGENTS.md is the
    convention here; CLAUDE.md @-includes it."""
    for name in ('AGENTS.md', 'CLAUDE.md'):
        p = ROOT / name
        if p.exists():
            return name, p.read_text(encoding='utf-8', errors='ignore')
    raise NotApplicable('this repo has no AGENTS.md or CLAUDE.md, so it has '
                        'no session instructions to check')


class Ctx:
    """What a check is asked about: the repository, and the change in scope."""

    def __init__(self, paths=None, rng=None, whole_tree=False):
        self.root = ROOT
        self.range = rng
        self.scope_reason = None
        if paths:
            self.changed = list(paths)
            self.added = [p for p in paths if not (ROOT / p).exists()
                          or not _git('cat-file', '-e', f'HEAD:{p}').returncode == 0]
            self.base = 'HEAD'
        elif whole_tree:
            self.changed = _git('ls-files').stdout.split()
            self.added = []
            self.base = 'HEAD'
        elif rng:
            left = rng.split('..')[0]
            self.base = left
            st = _git('diff', '--name-status', rng).stdout.splitlines()
            self.changed = [l.split('\t')[-1] for l in st if l.strip()]
            self.added = [l.split('\t')[-1] for l in st if l.startswith('A')]
        else:
            self.base = 'HEAD'
            st = _git('status', '--porcelain').stdout.splitlines()
            self.changed, self.added = [], []
            for line in st:
                if len(line) < 4:
                    continue
                code, name = line[:2], line[3:].strip()
                if ' -> ' in name:
                    name = name.split(' -> ')[-1]
                self.changed.append(name)
                if 'A' in code or '?' in code:
                    self.added.append(name)
            if not self.changed:
                self.scope_reason = ('the working tree is clean, so no change '
                                     'is in scope')

    def added_files(self):
        """`git status --porcelain` collapses an untracked DIRECTORY to one
        entry ending in "/". The practice is about naming a file, so expand
        those rather than judging the directory entry -- which is also what
        stopped this check reporting a directory path as a file name."""
        out = []
        for f in self.added:
            p = ROOT / f
            if p.is_dir():
                out.extend(str(q.relative_to(ROOT)) for q in sorted(p.rglob('*'))
                           if q.is_file())
            else:
                out.append(f)
        return out

    def read(self, rel):
        p = ROOT / rel
        try:
            return p.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            return ''

    def read_base(self, rel):
        """The file as it was before this change, or None if it is new."""
        r = _git('show', f'{self.base}:{rel}')
        return r.stdout if r.returncode == 0 else None

    def changed_matching(self, pattern):
        rx = re.compile(pattern)
        return [f for f in self.changed if rx.search(f) and (ROOT / f).exists()]


# --------------------------------------------------------------------------
# Native checks
# --------------------------------------------------------------------------

_MD_LINK_RE = re.compile(r'\[([^\]\n]*)\]\([^)\s]*\)')


# A Rule counts as REWRITTEN when the edit is big enough, in both absolute
# and relative terms, to be an act of authorship rather than an edit.
#
# Both thresholds are needed, and a plain similarity ratio is not enough:
# on a short Rule one swapped word is a large fraction of the text, and on
# a long one a genuine paragraph rewrite can be a small fraction. The
# character floor answers "is this more than a clause?" and the ratio
# answers "is this most of the rule?"; an authorship event clears both,
# and a rename, a typo fix or a repointed link clears neither.
_RULE_REWRITE_MIN_CHARS = 80
_RULE_REWRITE_MIN_SHARE = 0.15


def _rule_prose(sections):
    """A Rule's words, with link TARGETS dropped and the label kept."""
    return _MD_LINK_RE.sub(r'\1', sections.get('rule', '')).strip()


def _rule_was_rewritten(old_sections, new_sections):
    """Did this Rule actually get (re)written, or just edited?

    The check this serves demands a `## Story` from anyone who writes a
    rule, so what it needs to detect is authorship, not any difference at
    all. A plain string comparison detects any difference at all, and that
    was wrong twice in one day: a sweep repointing 67 broken relative
    links demanded a `## Story` from four inherited practices whose prose
    it had not touched a word of, and then a one-word product rename did
    the same. Both times the only ways to clear the demand were to invent
    an incident or to leave the defect unfixed -- and a demand nobody can
    honestly satisfy is worse than no demand, because it teaches people to
    route around the check.

    Link targets are normalized away outright (a target is not prose), and
    what remains is measured by how much actually changed -- see the two
    thresholds above for why both an absolute and a relative one are
    needed. Guessing wrong in the lenient direction costs a missing Story
    on a practice that already had one; guessing wrong in the strict
    direction costs the credibility of the check, which is worse."""
    before, after = _rule_prose(old_sections), _rule_prose(new_sections)
    if before == after:
        return False
    if not before or not after:
        return True          # added or emptied: authorship either way
    # autojunk=False is load-bearing, not a style choice. On sequences of
    # 200 elements or more, SequenceMatcher's default heuristic treats any
    # element appearing in more than 1% of the sequence as "popular junk"
    # and refuses to anchor on it -- which, for a character-level diff of
    # ordinary English, is every common letter. The alignment collapses:
    # swapping one word three times in a 582-character Rule measured as
    # 622 characters changed, a 107% share, where the true answer is 12
    # and 2%. That is the STRICT direction of being wrong, so it would
    # have re-created the false demand this function exists to remove,
    # only on long Rules where it is hardest to notice. Caught by the
    # harness case for exactly that scenario.
    changed = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in
                  difflib.SequenceMatcher(None, before, after,
                                          autojunk=False).get_opcodes()
                  if tag != 'equal')
    return (changed >= _RULE_REWRITE_MIN_CHARS
            and changed / len(before) >= _RULE_REWRITE_MIN_SHARE)


@check('cite-the-incident', 'change',
       'a practice file whose Rule is new or changed must carry a non-empty '
       '## Story',
       'a Story that is present but says nothing. It tests that the incident '
       'was recorded, not that it was the right incident.')
def _cite_the_incident(ctx):
    out = []
    for f in ctx.changed_matching(r'^practices/.*\.md$'):
        try:
            _fm, sections = sp._read_practice_file(ROOT / f)
        except sp.PracticeFileError:
            continue
        old = ctx.read_base(f)
        if old is not None:
            try:
                _ofm, old_sections = sp._parse_practice_text(old)
            except Exception:
                old_sections = None
            if old_sections is not None and \
                    not _rule_was_rewritten(old_sections, sections):
                continue        # an edit, not an authorship event
        if not sections.get('story', '').strip():
            out.append(Finding(f, 'a new or rewritten Rule with an empty '
                                  '## Story — the failure it prevents is not '
                                  'recorded anywhere'))
    return out


# The suffix must be TERMINAL. `findings-v2.md` is a version label stuck on
# the end of a name, which is what the practice is about; the label goes stale
# the moment the file is edited without a rename. A name that CONTINUES after
# the token -- `answers-v3-pre-enforcement` -- is a compound identity in which
# the token is part of what the thing is, not a version on an evolving file.
# Origin: the first version of this check fired on
# `evals/routing/answers-v3-pre-enforcement/`, this session's own preserved
# eval baseline, whose name is doing exactly what the practice asks.
VERSION_SUFFIX_RE = re.compile(
    r'(?:^|[-_.])(?:v\d+|version\d*|rev\d+|final|latest|old|new|copy|backup|bak|'
    r'draft|\d{4}[-_]\d{2}[-_]\d{2})$', re.I)


_FRONTMATTER_RE = re.compile(r'\A---\n(.*?)\n---\n', re.S)
_FM_STATUS_RE = re.compile(r'^status:\s*(\S+)', re.M)
_STORY_RE = re.compile(r'^## Story\n(.*?)(?=\n## |\Z)', re.S | re.M)


def _practice_status(text):
    """Read `status:` from the FRONTMATTER only.

    Anchored rather than searched: several practices discuss the status
    vocabulary in their own prose (`status: retired` appears inside
    sentences), and a loose search reads one of those and mis-scopes the
    check onto a practice it should have skipped.
    """
    fm = _FRONTMATTER_RE.match(text)
    if not fm:
        return ''
    m = _FM_STATUS_RE.search(fm.group(1))
    return m.group(1).strip() if m else ''


def _foreign_practice(rel):
    """True if a COMMITTED practices/MANIFEST.json says another source owns it.

    Attribution never comes from live source resolution: a bare CI checkout
    can reach neither a team sibling clone nor a private user-level config,
    so "did not resolve here" is not "owned here". Same mechanism, and the
    same reasoning, as the materialized-practice guards elsewhere.
    """
    manifest = ROOT / 'practices' / 'MANIFEST.json'
    if not manifest.is_file():
        return False
    try:
        entries = json.loads(manifest.read_text(encoding='utf-8')).get('practices', [])
    except (ValueError, OSError):
        return False
    slug = pathlib.Path(rel).stem
    for entry in entries:
        if entry.get('slug') == slug:
            return entry.get('level') != 'repo-local'
    return False


@check('catalogue-carries-stories', 'tree',
       'every status: active practice in this catalogue carries a non-empty '
       '## Story',
       'whether a Story records the RIGHT incident, or any incident at all -- '
       'an honest "no originating incident was recorded" passes, and should. '
       'It tests that the section says something, not that it says something '
       'dramatic.')
def _catalogue_carries_stories(ctx):
    out = []
    pdir = ROOT / 'practices'
    if not pdir.is_dir():
        return out
    for path in sorted(pdir.glob('*.md')):
        rel = str(path.relative_to(ROOT))
        if _foreign_practice(rel):
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        if _practice_status(text) != 'active':
            continue
        m = _STORY_RE.search(text)
        if m is None:
            out.append(Finding(rel, 'has no ## Story section at all'))
        elif not m.group(1).strip():
            out.append(Finding(rel, 'is status: active with an empty ## Story '
                                    '-- the failure this rule prevents is '
                                    'recorded nowhere'))
    return out



# ---- practice-links-travel -------------------------------------------------
# A practice file is copied into every repository that adopts the catalogue,
# so a relative link in one is only real if the target is copied too.
# practice: practice-links-travel
_MD_LINK_RE = re.compile(r'(?<!\!)\[[^\]]*\]\(([^)\s]+)\)')
_BLOB_URL_RE = re.compile(
    r'^https://github\.com/([^/]+/[^/]+)/blob/([^/]+)/(.+)$')
# What precedent_materialize.py actually copies out of a source's
# tools/checks/: `check_*.py` beside the practices, and `tests/test_*.sh`
# under them. Both shapes are spelled out rather than a loose `[^/]+` --
# the tests half was missed the first time, and a private set citing the
# test that proves its own check is a real cross-reference, not a stray.
_CHECK_SCRIPT_RE = re.compile(
    r'\.\./tools/checks/(?:check_[^/]+\.py|tests/test_[^/]+\.sh)')


def _markdown_links(text):
    """[(lineno, target)] for every markdown link OUTSIDE fences and code
    spans. A link written inside backticks is a value being documented, not
    a reference -- same reading doc_lint.py's own link check uses, and the
    reason it is duplicated here rather than imported is that this module
    must keep working in a tree where cmark-gfm is absent and doc_lint
    degrades."""
    out, fence = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(('```', '~~~')):
            fence = not fence
            continue
        if fence:
            continue
        clean = re.sub(r'`[^`]*`', lambda m: ' ' * len(m.group(0)), line)
        for target in _MD_LINK_RE.findall(clean):
            out.append((i, target))
    return out


def _travelling_engine_files():
    """{'tools/<name>'} -- the engine files every consumer receives.

    Asked of precedent_vendor_engine.py, which is the one place that answers
    it, rather than kept as a second list here: the two would drift the first
    time a file was added to the vendored set, and the drift would show up as
    a false violation on a correct link (practice: registry-source-of-truth).
    """
    sys.path.insert(0, str(ROOT / 'tools'))
    import precedent_vendor_engine as _pve
    return {'tools/' + n for n in _pve.CONSUMER_ENGINE_FILES}


def _origin_slug():
    """'owner/repo' for origin, or None. Used only to decide whether an
    absolute URL points at THIS repository -- a URL naming some other
    repository is somebody else's to keep working."""
    r = _git('remote', 'get-url', 'origin')
    if r.returncode != 0:
        return None
    m = re.search(r'github\.com[:/]+([^/]+/[^/\s]+?)(?:\.git)?/*$',
                  r.stdout.strip())
    return m.group(1) if m else None


@check('practice-links-travel', 'tree',
       'every link in a practice file THIS repo owns either travels with the '
       "file (a sibling practice, a vendored engine file, this source's own "
       'tools/checks/ check script or tests/ test, which must exist here) or '
       'is an absolute URL into this repository on '
       'its declared base_branch, naming a path that exists',
       'whether the target is the RIGHT file -- including the nastiest '
       'shape of this bug, a link like ../.claude/settings.json that '
       'RESOLVES in the consumer, to that consumer\'s own file rather than '
       'the one the sentence is about. It is caught here only because such '
       'a path does not travel; nothing would catch it if it did. Also a '
       'link that travels today '
       'and stops travelling when a file leaves CONSUMER_ENGINE_FILES -- that '
       'shows up as a violation on the next run, not at the moment of '
       'removal. It reads practices/ only: local/practices/ is read in place '
       'here and never materialized, so its links travel nowhere and break '
       'nothing. It also cannot see a repo-local source in a CONSUMING repo, '
       'where materialization moves a practice up a directory and changes '
       'what its relative paths mean.')
def _practice_links_travel(ctx):
    pdir = ROOT / 'practices'
    if not pdir.is_dir():
        raise NotApplicable('this repo has no practices/ directory')
    owned = [p for p in sorted(pdir.glob('*.md'))
             if not _foreign_practice(str(p.relative_to(ROOT)))]
    if not owned:
        raise NotApplicable(
            'every practice here is materialized from another source, so '
            'practices/ is generated output -- these links have to be right '
            'in the publishing source, and repairing them here would be '
            'overwritten by the next sync')
    try:
        travel = _travelling_engine_files()
    except Exception as e:                      # practice: fail-gracefully
        raise NotApplicable(f'the vendored-engine file list could not be read '
                            f'({e}), so what travels is unknown')
    branch = _declared_base_branch(ROOT)
    slug = _origin_slug()
    out = []
    for path in owned:
        rel = str(path.relative_to(ROOT))
        text = path.read_text(encoding='utf-8', errors='ignore')
        for lineno, target in _markdown_links(text):
            where = f'{rel}:{lineno}'
            if target.startswith(('mailto:', '#')):
                continue
            if target.startswith(('http://', 'https://')):
                m = _BLOB_URL_RE.match(target)
                if not m or slug is None or m.group(1).lower() != slug.lower():
                    continue                    # somebody else's repository
                url_branch, url_path = m.group(2), m.group(3).split('#')[0]
                if branch and url_branch != branch:
                    out.append(Finding(
                        where, f'links this repository at `{url_branch}`, but '
                               f'precedent.json declares `{branch}` -- an '
                               f'upstream link goes stale the moment it names '
                               f'a branch nobody is publishing from'))
                elif not (ROOT / url_path).exists():
                    out.append(Finding(
                        where, f'links `{url_path}` in this repository, and '
                               f'no such path exists here'))
                continue
            base = target.split('#')[0]
            if not base:
                continue
            if '/' not in base and (pdir / base).exists():
                continue                        # a sibling practice file -- it travels
            if base.startswith('../') and base[3:] in travel:
                continue                        # a vendored engine file
            # A source's own check scripts travel too: materialize writes
            # every declared source's tools/checks/** into the consuming
            # repo alongside practices/. Missing this was a false violation
            # on the single most common cross-reference a private-set
            # practice makes -- a practice citing the script that enforces
            # it. Found 2026-09-11 by reading the individual set's original,
            # which had named both shapes from the start. It must EXIST in the
            # tree being scanned -- the same test the sibling-practice case
            # above uses -- so one check stays right for a private set, whose
            # scripts sit beside its practices, and for this repository, where
            # tools/checks/ is materialize's output directory and a link into
            # it points at nothing.
            if (_CHECK_SCRIPT_RE.fullmatch(base)
                    and (ROOT / base[3:]).exists()):
                continue                        # this source's own check script
            fix = (f'https://github.com/{slug}/blob/{branch or "<branch>"}/'
                   f'{base.lstrip("./")}' if slug else 'an absolute URL')
            out.append(Finding(
                where, f'`{target}` does not travel with this file -- it is '
                       f'live here and dead in every repository that receives '
                       f'the catalogue. Link it as {fix}, or drop the link '
                       f'markup and keep the backticked path'))
    return out

@check('no-version-suffix', 'change',
       'a file added by this change must not carry a version, date or state '
       'suffix in its name',
       'a versioned name that was already committed, and a version token that '
       'is not at the END of the name. It gates what a change ADDS, one file '
       'at a time.')
def _no_version_suffix(ctx):
    out = []
    for f in ctx.added_files():
        path = pathlib.PurePath(f)
        stem = path.name
        ext = ''
        for suffix in ('.md', '.py', '.json', '.txt', '.sh', '.yml', '.yaml',
                       '.template', '.html'):
            if stem.endswith(suffix):
                ext = suffix
                stem = stem[:-len(suffix)]
                break
        m = VERSION_SUFFIX_RE.search(stem)
        if not m:
            continue
        # The Rule's own coexistence exception: a version suffix earns its
        # place when two versions must coexist and it is the NEW file that is
        # suffixed beside its unsuffixed predecessor. If a sibling with the
        # suffix stripped already exists in the same directory, this added
        # file is that legitimate case, not a redundant-with-VCS label.
        predecessor = path.with_name(stem[:m.start()] + ext)
        if (ctx.root / predecessor).exists():
            continue
        out.append(Finding(f, 'the file name carries its version or state '
                              '— name it for what it is'))
    return out


# Person-nouns that make a skill-level label legitimate: the label is
# describing somebody, which is the one place it belongs.
# practice: technical-describes-people
_PERSON_NOUNS = ('contributor', 'contributors', 'person', 'people', 'user',
                 'users', 'team', 'teams', 'member', 'members', 'author',
                 'authors', 'reader', 'readers', 'writer', 'writers',
                 'staff', 'colleague', 'colleagues', 'owner', 'owners')

_SKILL_LABEL_RE = re.compile(r'(?:^|[/_\-])(non[_\-]?technical|technical)[/_\-]?',
                             re.IGNORECASE)


@check('technical-describes-people', 'tree',
       'no tracked path labels a FILE or DIRECTORY with a skill level; '
       "'technical' and 'non-technical' describe people",
       'the same label inside prose, and a path where the label is followed '
       'by a person-noun (NONTECHNICAL_CONTRIBUTOR_ACCESS.md names a person '
       'and is correct). It reads names only -- it cannot see a per-person '
       'rule written into a shared file, which is the failure the name leads '
       'to.')
def _technical_describes_people(ctx):
    out = []
    # practices/ names files after their SLUG, and a rule about this label
    # must contain it; record/ is settled history nobody renames. The third
    # exclusion is every tree this repo MIRRORS, and it used to be the
    # literal 'process/upstream/' -- INSTALL.md §1's layout, and the wrong
    # one for a §0 install, whose vendored catalogue sits wherever
    # precedent.json's `universal` source points. In a §0 consumer the only
    # path this check ever flagged was Precedent's own
    # technical-describes-people.md, inside a mirror the consumer may not
    # edit and cannot rename. Ask the engine (practice: durable-fix).
    skip = ('practices/', 'record/') + _mirrored(ROOT)
    for f in ctx.changed:
        if f.startswith(skip):
            continue
        for part in pathlib.PurePath(f).parts:
            m = _SKILL_LABEL_RE.search(part)
            if not m:
                continue
            rest = part[m.end():].lower()
            token = re.split(r'[/_\-. ]', rest.lstrip('_-'))[0]
            if token in _PERSON_NOUNS:
                continue
            out.append(Finding(f, "the path labels a file or directory with a "
                                  "skill level ('%s') -- that describes a "
                                  "person, not a thing" % m.group(1)))
            break
    return out


# Trees whose filenames belong to whoever produced them, not to this repo
# (practice: filename-separator -- the rule is about names somebody HERE
# chose). Vendored upstream, materialized output, and instantiable skeletons
# whose names are copied verbatim into an adopter's tree.
_SEPARATOR_FOREIGN_FIXED = ('tools/checks/', 'practices/')


def _separator_foreign():
    # The mirrored trees are asked for, not listed: the literal
    # 'process/upstream/' that used to sit here is INSTALL.md §1's
    # layout, and a §0 install mirrors the catalogue somewhere else
    # entirely. Same root cause as _mirrored()'s own comment.
    return _SEPARATOR_FOREIGN_FIXED + _mirrored(ROOT)


@check('filename-separator', 'tree',
       'files of the same kind in one directory use one word separator, '
       'never both - and _',
       'names determined elsewhere -- a language import rule, a platform-'
       'required filename, a slug, or the file this one generates. Those are '
       'exempted by precedent.json\'s filename_separator_exempt, which '
       'requires a stated reason; this check cannot tell an inherited name '
       'from a chosen one on its own, and does not guess.')
def _filename_separator(ctx):
    import collections
    exempt = {}
    try:
        cfg = json.loads((ctx.root / 'precedent.json').read_text(encoding='utf-8'))
        for e in cfg.get('filename_separator_exempt') or []:
            if e.get('reason'):
                exempt[(e.get('path', ''), e.get('ext', ''))] = e['reason']
    except (OSError, ValueError):
        pass

    groups = collections.defaultdict(lambda: {'-': [], '_': []})
    # Tracked files PLUS untracked-but-not-ignored ones. This is a tree-scope
    # check, so the question is what the repository CONTAINS -- and a file
    # just added and not yet committed is exactly when the answer is most
    # useful, since renaming it later costs a link sweep
    # (rename-updates-links). `--exclude-standard` keeps .gitignore'd noise
    # out. Plain `ls-files` was tried first and could not see an uncommitted
    # file at all, which the harness's own planted case caught.
    for f in _git('ls-files', '--cached', '--others',
                  '--exclude-standard').stdout.split():
        if any(f.startswith(x) for x in _separator_foreign()):
            continue
        path = pathlib.PurePath(f)
        # The FIRST dot ends the stem: `a_b.md.template` is named after
        # `a_b.md`, so its separator was inherited from that name, not
        # chosen here.
        stem = path.name.split('.')[0]
        key = (str(path.parent), path.suffix)
        if '-' in stem:
            groups[key]['-'].append(path.name)
        if '_' in stem:
            groups[key]['_'].append(path.name)

    out = []
    for (dirname, ext), seen in sorted(groups.items()):
        if not (seen['-'] and seen['_']):
            continue
        if (dirname, ext) in exempt:
            continue
        kebab = ', '.join(sorted(seen['-'])[:3])
        snake = ', '.join(sorted(seen['_'])[:3])
        out.append(Finding(
            f'{dirname}/' if dirname != '.' else '.',
            f'{len(seen["-"])} file(s) use "-" ({kebab}) and '
            f'{len(seen["_"])} use "_" ({snake}) for the same kind '
            f'(*{ext}) in one directory -- pick one, or exempt the group in '
            f'precedent.json with the reason each name was determined '
            f'elsewhere'))
    return out


GENERATED_VIEWS = ('MAP.md', 'GLOSSARY.md')


@check('generated-artifact-provenance', 'tree',
       'every generated view names the script that builds it and says it is '
       'generated, and regenerating it changes nothing',
       "the practice's own Rule also requires a content-derived build code "
       "and an input-hash manifest for deck/** build artifacts -- this check "
       "verifies neither, because deck/build_deck.py implements no such "
       "mechanism (its own 'manifest' selects INPUT slides, an unrelated "
       "concept). It only covers the views tools/build_views.py owns: "
       "MAP.md and GLOSSARY.md by name here (whole generated files, checked "
       "by their own stamp); AGENTS.md's generated LOADER BLOCK is a "
       "different shape (a hand-authored file with one generated section, "
       "not a wholly generated file) and its byte-identical regeneration is "
       "covered by verify_harness.py's check_generated_views_regenerate "
       "instead, not by this check.")
def _generated_artifact_provenance(ctx):
    out = []
    builder = _tool_path('tools/build_views.py')
    if builder is None:
        raise NotApplicable('tools/build_views.py is absent, so nothing here '
                            'declares which artifacts are generated')
    # Which of the two this repo actually GENERATES, read off the files
    # themselves. build_views.py can write all three views, but a
    # consuming repo runs it as `--agents-only` on purpose: MAP.md and
    # GLOSSARY.md "assume THIS repo's layout" (build_views.py's own
    # docstring, and INSTALL.md section 0's caveat, which says so in
    # as many words), so a consumer hand-authors them from
    # templates/MAP.md.template. Before this distinction, that documented,
    # intended state was a VIOLATION in every consuming repo -- both files
    # reported "carries no stamp" and then `build_views.py --check`
    # reported them as drifted, for a repo that never generated them and
    # never should. A file with no stamp is not a stale generated file;
    # it is a hand-authored one, and orientation-map already requires
    # MAP.md to exist and say something.
    generated_here = []
    for name in GENERATED_VIEWS:
        p = ROOT / name
        head = p.read_text(encoding='utf-8', errors='ignore')[:1200] \
            if p.exists() else ''
        if 'build_views.py' not in head:
            continue
        generated_here.append(name)
        if not re.search(r'do not (hand-)?edit|never hand-edit|generated',
                         head, re.I):
            out.append(Finding(name, 'names build_views.py but does not say '
                                     'it is generated, so a reader cannot '
                                     'tell whether editing it is safe'))
    # --repo, always: build_views.py derives its own root from its file
    # location, which in the classic vendoring layout is
    # <repo>/process/upstream/, not the consuming repo. Without this it
    # went looking for process/upstream/AGENTS.md and reported the
    # FileNotFoundError as "a generated view is stale or hand-edited".
    argv = [sys.executable, str(builder), '--repo', str(ROOT), '--check']
    if not generated_here:
        # Nothing wholly generated here, so the only thing left to
        # regenerate is AGENTS.md's loader block -- and a repo on the
        # classic INSTALL.md section 1 model has no such block at all
        # (its instructions file is hand-authored end to end). Reporting
        # "a generated view is stale or hand-edited" for a file that
        # declares nothing generated is a finding nobody can act on.
        _n, instructions = _instructions_file()
        if '<!-- BEGIN GENERATED: precedent-loader -->' not in instructions:
            return out
        argv.append('--agents-only')
    r = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        out.append(Finding('', 'a generated view is stale or hand-edited: '
                               + (r.stdout + r.stderr).strip().splitlines()[-1]
                               if (r.stdout + r.stderr).strip() else
                               'build_views.py --check failed'))
    return out


@check('source-naming', 'tree',
       "every precedent.json in the tree names each source by the shape its "
       "level fixes -- `precedent`, `precedent-individual`, "
       "`precedent-team-<slug>`, `local`",
       'the GitHub repository names themselves, and whether a team slug names '
       'a purpose rather than a roster. It sees declared names in tracked '
       'configuration, which is the layer a check can reach; the rest of the '
       'practice is disclosure, carried by the occasion index.')
def _source_naming(ctx):
    out = []
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import precedent_resolve as pr
    except Exception as e:
        # Same reason as title_case above: precedent_resolve.py is in
        # CONSUMER_ENGINE_FILES but not ENGINE_FILES, because a source set
        # resolves no catalogue. The reachability check further down already
        # gave this import the same treatment; this one was still bare.
        raise NotApplicable(f'precedent_resolve.py did not import ({e}), so '
                            f'no declared source can be read here')
    for cfg in sorted(ROOT.rglob('precedent.json')):
        if '.git' in cfg.parts:
            continue
        rel = cfg.relative_to(ROOT).as_posix()
        try:
            data = json.loads(cfg.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            out.append(Finding(rel, f'is not valid JSON ({e})'))
            continue
        for entry in data.get('sources', []):
            level, name = entry.get('level'), entry.get('name')
            shape = pr.SOURCE_NAME_SHAPE.get(level)
            if shape is None:
                continue
            pattern, expected = shape
            # The one regular expression per level lives in the resolver, so
            # the gate and the engine cannot disagree about the convention.
            if not (isinstance(name, str) and pattern.match(name)):
                out.append(Finding(
                    rel, f'names its {level} source {name!r}; a {level} '
                         f'source is named {expected} -- fixed by its level, '
                         f'not chosen (spec/SOURCE_NAMING.md)'))
    return out


@check('orientation-map', 'tree',
       'MAP.md exists at the repository root, is not empty, and the session '
       'instructions point at it',
       'whether the map is any good. It checks that a session that reads the '
       'instructions is sent to a map that exists.')
def _orientation_map(ctx):
    out = []
    p = ROOT / 'MAP.md'
    if not p.exists():
        return [Finding('MAP.md', 'no top-level map: a session has nowhere to '
                                  'orient from')]
    body = p.read_text(encoding='utf-8', errors='ignore')
    if len(body.split()) < 50:
        out.append(Finding('MAP.md', 'is effectively empty'))
    name, text = _instructions_file()
    if 'MAP.md' not in text:
        out.append(Finding(name, 'never mentions MAP.md, so the map is not '
                                 'reached from what a session actually reads'))
    return out


QUICK_INDEX_HEADER_RE = re.compile(
    r'^\|[^|\n]*\b(looking for|want to find|where things are|need)\b[^|\n]*\|',
    re.I | re.M)


@check('layered-practice-packs', 'tree',
       'every practice in force in this repo is reachable by at least one '
       'loading channel here -- resident, occasion index, a path trigger, a '
       'gate, or a running check',
       'whether a reachable practice is actually FOLLOWED, and whether a '
       'practice that is unreachable here SHOULD bind this repo at all. It '
       'reports the gap; closing it is either wiring the practice in or '
       'saying out loud that it does not apply, and only a person can pick.',
       advisory=True)
def _practice_is_reachable(ctx):
    """A rule nothing can load is not in force; it is filed.

    `precedent.json` declaring a source is a claim that its practices bind
    work here. Four channels can make good on that claim -- the resident
    block, the occasion index, a path trigger, and an enforced check (plus
    gates, which fire at a moment). A practice that none of them reaches is
    a rule nobody will ever be shown, in a repo that says it is in force:
    the config and the loader disagree, and the config is the one that
    reads as authoritative.

    Measured here on 2026-09-06: 30 of 114 practices in force in Precedent's
    own repo were reachable by nothing at all -- 27 from the team source and
    3 from the individual one. Both are genuinely declared in
    `precedent.json` and in the user-level config; neither reaches
    `AGENTS.md`'s generated block, because `build_views.py` deliberately
    stays single-source here, and neither reaches the enforced channel,
    because `register_materialized_checks()` can only see scripts that were
    materialized -- and Precedent cannot materialize into itself.

    ADVISORY, deliberately, to the bar this module sets for that (see
    parallel-artifact-ledger's own note): the remedy is an architectural
    decision -- wire the sources into this repo's generated views, or state
    per practice that it does not bind here -- and running the same 15
    source checks against this tree showed the answer is not simply "turn
    them all on": five pass, four report real findings, and six report
    things this repo cannot act on because the practice is about a
    different kind of repository. Failing the gate would leave it red until
    somebody makes that call, and a permanently red gate is a gate nobody
    runs, which is this repo's own documented lesson.

    A source that does not RESOLVE in this environment is skipped, never
    reported -- a team source is a sibling clone and an individual source
    resolves through a private user-level config, so neither exists in a
    bare CI checkout, and their absence there is not evidence of anything.
    """
    try:
        import precedent_resolve as pr
    except Exception as e:
        raise NotApplicable(f'precedent_resolve.py did not import ({e}), so '
                            f'the set of practices in force cannot be read')
    try:
        sources = pr.load_config(ROOT)
    except Exception as e:
        raise NotApplicable(f'this repo declares no readable source set ({e})')

    name, instructions = _instructions_file()
    if not instructions:
        raise NotApplicable('this repo has no instructions file, so it has no '
                            'resident block or occasion index to be reachable '
                            'through')

    reachable_names = set()
    for d in ((ROOT / 'tools').joinpath('checks'),
              (ROOT / 'local').joinpath('tools', 'checks')):
        if d.is_dir():
            reachable_names |= {f.name for f in d.glob('check_*.py')}

    try:
        not_binding = pr.load_not_binding(ROOT)
    except Exception as e:
        # A malformed exemption list must be loud, never silently empty:
        # an exemption mechanism that ignores its own bad entries is a way
        # to opt out of a rule by typo.
        return [Finding(str(ROOT / 'precedent.json'),
                        f'`not_binding` is malformed and no exemption could be '
                        f'read from it: {e}')]

    in_force, unreachable, unresolved = {}, [], []
    for s in sources:
        d = pathlib.Path(s['path']) / 'practices'
        if not d.is_dir():
            unresolved.append(f"{s['level']}/{s['name']}")
            continue
        for f in sorted(d.glob('*.md')):
            try:
                fm, _sections = sp._read_practice_file(f)
            except Exception:
                continue
            # Not in force -- any non-active status, not the literal
            # 'active' test this used to do by hand. Routed through the one
            # shared predicate so `deduplicated` counts too (practice:
            # layered-practice-packs).
            try:
                import build_views as _bv
                if not _bv.is_in_force(fm):
                    continue
            except Exception:
                if (fm.get('status') or 'active').strip('" ') != 'active':
                    continue
            in_force.setdefault(fm.get('slug', f.stem), (fm, s))

    # Word-boundary, not substring: a slug like `install` or `doc-recipe`
    # matches ordinary prose everywhere as a substring, and every one of those
    # would have counted as "reachable" -- the check would then under-report
    # exactly the practices whose names are common words.
    # Slugs the loader ACTUALLY indexes, read from the two shapes the
    # generated block uses -- an occasion-index line ("  slug — clause") and
    # a resident entry ("**slug.** ..."). Matching bare words in prose
    # instead was wrong both ways: it required a hyphen, so a single-word
    # slug like `install` could never be found and was reported unreachable
    # forever; and loosening the pattern to allow single words would have
    # matched the ordinary English word "install" anywhere in the file and
    # called the practice reachable when nothing indexed it.
    named = set(re.findall(r'^\s+([a-z0-9][a-z0-9-]*) \u2014 ', instructions, re.M))
    named |= set(re.findall(r'^\*\*([a-z0-9][a-z0-9-]*)\.\*\*', instructions, re.M))

    # THE FIFTH CHANNEL, and why it is judged structurally rather than by
    # looking for the file. In a repo declaring `visibility: public`, the
    # tracked loader block deliberately omits the team and individual
    # levels -- their text may not be committed -- and
    # tools/precedent_session_practices.py renders exactly that complement
    # into .precedent/SESSION_PRACTICES.md at session start, which
    # AGENTS.md's standing instruction points at.
    #
    # Those practices ARE reachable, and this check said they were not,
    # because _instructions_file() reads AGENTS.md and nothing else. Found
    # 2026-09-06 by testing the claim rather than assuming it: a second
    # session was weighing publishing private practice text against leaving
    # 34 team rules unloaded, on the belief that the already-built untracked
    # channel would not satisfy this check.
    #
    # Keyed off the MECHANISM being wired, not off the file existing: the
    # file is untracked and regenerated per session, so it is absent in
    # continuous integration and in every fresh clone. Testing for it would
    # make this check report those practices unreachable in CI forever --
    # the permanently-red-gate failure this module already refuses
    # elsewhere. What is asserted is that the channel exists: the tool is
    # present, the session-start hook invokes it, and the repo is public, so
    # the tool carries exactly these levels.
    session_channel_levels = ()
    try:
        import build_views as _bv
        hook = ROOT / '.claude' / 'hooks' / 'session-start.sh'
        wired = ((ROOT / 'tools' / 'precedent_session_practices.py').is_file()
                 and hook.is_file()
                 and 'precedent_session_practices' in hook.read_text(
                     encoding='utf-8', errors='ignore'))
        if wired and _bv.repo_is_public(ROOT):
            session_channel_levels = _bv.PRIVATE_LEVELS
    except Exception:                                        # noqa: BLE001
        session_channel_levels = ()

    exempted, blocked_exemptions, via_session = [], [], []
    for slug, (fm, s) in sorted(in_force.items()):
        if slug in not_binding:
            # `severity: blocking` may not be exempted -- the same rule the
            # resolver already applies to precedence, for the same reason: a
            # blocking practice is exactly the one no downstream declaration
            # is allowed to switch off.
            if (fm.get('severity') or 'default').strip('" ') == 'blocking':
                blocked_exemptions.append((slug, s['level'], s['name']))
            else:
                exempted.append(slug)
            continue
        if slug in named:
            continue                       # resident block or occasion index
        if s['level'] in session_channel_levels:
            via_session.append(slug)       # .precedent/SESSION_PRACTICES.md
            continue
        if (fm.get('gates') or '[]').strip('" ') not in ('[]', ''):
            continue                       # fires at a named moment
        cb = (fm.get('checked_by') or 'null').strip('" ')
        if cb and cb != 'null':
            # A check only counts if something here can RUN it.
            if pathlib.Path(cb).name in reachable_names or (ROOT / cb).is_file():
                continue
        unreachable.append((slug, s['level'], s['name']))

    if not in_force:
        raise NotApplicable('no practice resolved from any declared source, '
                            'so there is nothing to judge reachability for')

    # A repo that declares `visibility: public` deliberately keeps
    # individual-level practices OUT of its tracked loader block, because
    # publishing that block would publish somebody's private set (see
    # build_views.loader_practices). Those are excluded BY DESIGN, so
    # reporting them as gaps every run is how an advisory becomes wallpaper:
    # nine permanent findings nobody can act on would bury the real ones.
    # Counted and named, never listed as findings.
    public = False
    try:
        public = json.loads((ROOT / 'precedent.json').read_text(
            encoding='utf-8')).get('visibility') == 'public'
    except (ValueError, OSError):
        pass
    by_design = [u for u in unreachable if public and u[1] == 'individual']
    unreachable = [u for u in unreachable if u not in by_design]
    if by_design:
        print(f'  ({len(by_design)} individual-level practice(s) are '
              f'deliberately absent from this public repo\'s tracked block, '
              f'so the block cannot publish them -- they still apply to the '
              f'person, and reach a session through their own private repos)')

    out = []
    # A stale exemption is a real defect, not advisory noise: it names a
    # rule nothing puts in force, so it is either a typo (and the rule it
    # meant to exempt is still unreachable and unexplained) or a leftover
    # from a practice that has since gone. Only reported when every source
    # resolved -- otherwise "not in force" may just mean "not fetched".
    if not unresolved:
        for slug, reason in sorted(not_binding.items()):
            if slug not in in_force:
                out.append(Finding(
                    'precedent.json',
                    f'`not_binding` exempts {slug!r}, but no declared source '
                    f'puts that slug in force. Either it is a typo, or the '
                    f'practice is gone and the exemption outlived it. '
                    f'(Recorded reason: {reason})'))
    for slug, level, src in blocked_exemptions:
        out.append(Finding(
            f'{level}/{src}',
            f'`not_binding` exempts {slug!r}, but it is `severity: blocking` '
            f'-- a blocking practice is exactly the one a downstream repo may '
            f'not switch off. Remove the exemption, or take the matter up '
            f'with the source that set the severity.'))
    if via_session:
        print(f'  ({len(via_session)} practice(s) reach this session through '
              f'.precedent/SESSION_PRACTICES.md, which carries the levels a '
              f'public repo\'s tracked loader block may not: '
              f'{", ".join(sorted(via_session))})')
    if exempted:
        print(f'  ({len(exempted)} practice(s) declared not-binding here, with '
              f'reasons, in precedent.json: {", ".join(sorted(exempted))})')
    for slug, level, src in unreachable:
        out.append(Finding(
            f'{level}/{src}',
            f'{slug} is in force here but reachable by no channel: not in '
            f'{name}, no gate, and no check this repo can run. Either wire '
            f'it in, or say in the source that it does not bind this repo'))
    if out:
        print(f'  ({len(unreachable)} of {len(in_force)} practices in force '
              f'are reachable by nothing here'
              + (f'; {", ".join(unresolved)} did not resolve and were not '
                 f'judged)' if unresolved else ')'))
    return out


@check('quick-index', 'tree',
       'the session instructions carry a "looking for X → go to Y" table '
       'with at least five rows',
       'whether the rows are the right rows, or still resolve. It checks the '
       'table is there and populated.')
def _quick_index(ctx):
    name, text = _instructions_file()
    m = QUICK_INDEX_HEADER_RE.search(text)
    if not m:
        return [Finding(name, 'carries no "looking for X -> go to Y" table, so '
                              'every session searches the repo from scratch')]
    # Count from the line AFTER the header line, not from the end of the
    # regex match -- the match ends mid-line, and counting from there saw the
    # header's own remaining cells as "not a table row" and stopped at zero.
    lines = text.splitlines()
    header_line = text[:m.start()].count('\n')
    rows = 0
    for line in lines[header_line + 1:]:
        if line.startswith('|'):
            if not re.match(r'^\|[\s:|-]+\|?\s*$', line):
                rows += 1
        elif line.strip():
            break
    if rows < 5:
        return [Finding(name, f'the quick index has {rows} row(s) — too few to '
                              f'be worth checking before searching')]
    return []


GOTCHA_HEADING_RE = re.compile(
    r'^#{2,4}\s*.*(do NOT rediscover|environment gotchas).*$', re.I | re.M)
# What separates "the fix" from "the fix with its story" is checked
# STRUCTURALLY, not by vocabulary. The first version of this check looked for
# failure words (failed, broke, silently, cost, ...) and fired on a genuine
# story that happened to be told in other words -- "a smoke test believed it
# was exercising a shallow clone for an hour and was not". A check that fires
# on correct work is a check that gets switched off, and then it is absent
# when an entry really is a bare command. So: an entry that is one short
# sentence is a bare fix; an entry that runs to two sentences and some
# substance took the trouble to say what happened.
STORY_MIN_WORDS = 25
STORY_MIN_SENTENCES = 2


@check('environment-gotchas', 'tree',
       'the session instructions carry a "do NOT rediscover these" section, '
       'and every entry in it carries what failed, not only the fix',
       'whether the story is a good story, whether it is true, or whether the '
       'section is complete. It tells a one-line command from an entry that '
       'took the trouble to say what happened, and no more — padding defeats '
       'it, and it says so rather than implying otherwise.')
def _environment_gotchas(ctx):
    name, text = _instructions_file()
    m = GOTCHA_HEADING_RE.search(text)
    if not m:
        return [Finding(name, 'has no "do NOT rediscover these" section, so '
                              'every expensive environment discovery is paid '
                              'for again by the next session')]
    rest = text[m.end():]
    end = re.search(r'^#{1,4}\s', rest, re.M)
    section = rest[:end.start()] if end else rest
    # Strip HTML comments before splitting into entries. The old code
    # dropped only an entry that STARTED with `<!--`, which is not the
    # same thing: a multi-line comment holding a bulleted list -- exactly
    # what templates/AGENTS.md.loader.template uses to park the
    # placeholders an adopter fills in as they hit them -- had each of its
    # bullets parsed as a real gotcha entry and failed for having no
    # story. A comment is guidance to the person editing the file, not
    # content the file asserts.
    section = re.sub(r'<!--.*?-->', '', section, flags=re.S)
    entries, cur = [], []
    for line in section.splitlines():
        if re.match(r'^\s*[-*]\s+', line):
            if cur:
                entries.append('\n'.join(cur))
            cur = [line]
        elif cur and line.strip():
            cur.append(line)
        elif cur:
            entries.append('\n'.join(cur))
            cur = []
    if cur:
        entries.append('\n'.join(cur))
    entries = [e for e in entries if not e.strip().startswith('<!--')]
    if not entries:
        return [Finding(name, 'the gotchas section has no entries')]
    out = []
    for e in entries:
        first = re.sub(r'^\s*[-*]\s+', '', e.strip()).splitlines()[0]
        words = len(e.split())
        sentences = len([s for s in re.split(r'(?<=[.!?])\s', e) if s.strip()])
        if words < STORY_MIN_WORDS or sentences < STORY_MIN_SENTENCES:
            out.append(Finding(name, f'gotcha entry is a bare fix '
                                     f'({words} words, {sentences} '
                                     f'{"sentence" if sentences == 1 else "sentences"}) '
                                     f'with no account of what failed: '
                                     f'{first[:70]!r}'))
    return out


SETUP_CMD_RE = re.compile(r'\b(pip3?|apt-get|apt|npm|brew|uv)\s+install\b')


@check('session-bootstrap', 'tree',
       'if the session instructions name a setup command, a session-start '
       'hook must run it',
       'whether the hook actually installs the right thing. It catches setup '
       'that lives only in prose a session has to remember to obey.')
def _session_bootstrap(ctx):
    name, text = _instructions_file()
    prose = re.sub(r'```.*?```', '', text, flags=re.S)
    # Quote the COMMAND and its line, not sixty characters of the line -- the
    # first version cut a markdown link in half and the message read as
    # gibberish to the session receiving it.
    hits = [(i, m.group(0)) for i, l in enumerate(prose.splitlines(), 1)
            for m in [SETUP_CMD_RE.search(l)] if m]
    if not hits:
        raise NotApplicable('the session instructions name no setup command, '
                            'so there is nothing a hook would have to run')
    hooks = list(ROOT.glob('.claude/hooks/session-start*')) + \
        list(ROOT.glob('.*/hooks/session-start*')) + \
        list(ROOT.glob('templates/harness/*/hooks/session-start*'))
    settings = ROOT / '.claude' / 'settings.json'
    declared = False
    if settings.exists():
        declared = 'SessionStart' in settings.read_text(errors='ignore')
    own_hook = [h for h in hooks if 'templates/' not in str(h.relative_to(ROOT))]
    if not own_hook or not declared:
        line, cmd = hits[0]
        return [Finding(f'{name}:{line}',
                        f'names a setup command (`{cmd}`) but this repo has '
                        + ('no session-start hook' if not own_hook else
                           'no SessionStart entry in .claude/settings.json')
                        + ' — setup that lives in memory is setup that '
                          'gets skipped')]
    return []


# A hook path that does not resolve is the single most expensive silent
# failure this project has measured, which is why this is an engine-property
# check rather than a catalogue practice — it holds in any repo the engine is
# vendored into, whether or not that repo resolves session-bootstrap.
_HOOK_TOKEN_RE = re.compile(r'\$\{?CLAUDE_PROJECT_DIR\}?/\S+')


def _declared_hook_targets(settings_path):
    """[(abs_path, raw_token, is_argv0)] for every hook command in a
    settings.json that names a file under $CLAUDE_PROJECT_DIR.

    `is_argv0` is tracked because it decides whether the file has to be
    executable: `$CLAUDE_PROJECT_DIR/.claude/hooks/x.sh` is exec'd directly
    and a missing +x makes it silently never run, while the same path as an
    argument to `python3` is read, not executed, and demanding +x there
    would be a finding nobody should act on."""
    try:
        payload = json.loads(settings_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        # A settings.json this file cannot parse is the harness's problem to
        # report, not this check's to guess at.
        return []
    hooks = payload.get('hooks')
    if not isinstance(hooks, dict):
        return []
    out = []
    for entries in hooks.values():
        for entry in entries if isinstance(entries, list) else []:
            for h in (entry.get('hooks') or []) if isinstance(entry, dict) else []:
                cmd = h.get('command') if isinstance(h, dict) else None
                if not isinstance(cmd, str):
                    continue
                for m in _HOOK_TOKEN_RE.finditer(cmd):
                    raw = m.group(0)
                    rel = raw.split('/', 1)[1] if '/' in raw else ''
                    if not rel:
                        continue
                    out.append((ROOT / rel, raw, cmd.strip().startswith(raw)))
    return out


@check('declared-hooks-exist', 'tree',
       'every hook file a .claude/settings.json declares exists on disk, and '
       'is executable where the harness execs it directly',
       'a hook declared by an absolute or bare relative path (only '
       '$CLAUDE_PROJECT_DIR tokens are resolvable from here); a hook that '
       'exists, runs, and does the wrong thing; and a repo with working '
       'hooks that declares none at all, which is a different question and '
       'belongs to session-bootstrap. It does NOT read '
       'templates/harness/*/settings.json: those declare paths for the repo '
       'they are installed INTO, so resolving them against this tree would '
       'report a template as broken for being a template.',
       practice_backed=False)
def _declared_hooks_exist(ctx):
    """A hook whose path does not exist is not an error anybody sees.

    WHY THIS EXISTS (practice: cite-the-incident). Twice, measurably. On
    2026-09-08 this repo's own hooks all pointed at
    $CLAUDE_PROJECT_DIR/.claude/hooks/... while the harness had rooted the
    session one directory above the repo, so every path resolved to nothing
    and the commit identity, the freshness guard, the path-trigger channel
    and .precedent/SESSION_PRACTICES.md were silently absent for a whole
    session. On 2026-09-09 the same class turned up from the other end: the
    individual practice source has a .claude/settings.json and no
    .claude/hooks/ directory at all, because it was bootstrapped before
    precedent_bootstrap_source.py installed hooks and nothing since has
    repaired it. Both cost real sessions, and in both the harness said
    nothing -- it treats an unresolvable hook command as a no-op.

    The check is deliberately narrow: it answers "does the file the config
    names actually exist here", which is the half a machine can settle."""
    settings = [p for p in (ROOT / '.claude').glob('settings*.json')
                if p.is_file()]
    if not settings:
        raise NotApplicable('this repo has no .claude/settings*.json, so it '
                            'declares no hooks that could fail to resolve')
    found = []
    for sp_ in settings:
        rel_settings = sp_.relative_to(ROOT)
        targets = _declared_hook_targets(sp_)
        for path, raw, is_argv0 in targets:
            if not path.exists():
                found.append(Finding(
                    str(rel_settings),
                    f'declares the hook `{raw}` but {path.relative_to(ROOT)} '
                    f'does not exist — the harness treats an unresolvable '
                    f'hook command as a no-op, so this guard is off and '
                    f'nothing says so'))
            elif is_argv0 and not os.access(path, os.X_OK):
                found.append(Finding(
                    str(rel_settings),
                    f'declares the hook `{raw}` and '
                    f'{path.relative_to(ROOT)} is not executable — it will '
                    f'silently never run'))
    return found


@check('engine-plus-host-shims', 'tree',
       'no file outside the vendored tree duplicates a run of lines from '
       'inside it — that is a fork, not a shim',
       'a fork that was reworded as it was copied. It catches the verbatim '
       'copy, which is the one that silently drifts -- except where '
       'tools/ENGINE_MANIFEST.json records the copy, in which case it '
       'cannot drift silently and is not this check\'s business.')
def _engine_plus_host_shims(ctx):
    vendored = ROOT / 'process' / 'upstream'
    if not vendored.is_dir():
        raise NotApplicable('this repo vendors no upstream tree at '
                            'process/upstream/, so there is no engine/shim '
                            'boundary to hold. This is the expected state in '
                            'the upstream repo itself')
    # A copy the ENGINE MANIFEST records is not a fork. This check's whole
    # concern is a duplicate that drifts unnoticed, and
    # precedent_vendor_engine.py exists to make exactly these copies
    # impossible to drift unnoticed: ENGINE_MANIFEST.json pins the source
    # commit and a sha256 per file, and `precedent_vendor_engine.py status`
    # reports the moment one differs. Prohibiting the copy outright made
    # the check permanently red in every correctly-installed consumer --
    # the engine's own tools resolve ROOT from their own location, so they
    # HAVE to sit at <repo>/tools/ to see the consuming repo at all, and
    # the sanctioned mechanism for putting them there is a vendored copy.
    #
    # Verified against the two real consumers, 2026-09-06: it keeps firing
    # on that repository's hand-copied root tools (three of which had drifted
    # to OLDER content than that repo's own vendored tree, which is the
    # failure this rule is about), and stops firing on a manifest-recorded
    # engine.
    vendored_engine = _vendored_engine_files()

    RUN = 8

    def runs(path):
        lines = [l.strip() for l in
                 path.read_text(encoding='utf-8', errors='ignore').splitlines()]
        lines = [l for l in lines if len(l) > 12 and not l.startswith('#')]
        return {tuple(lines[i:i + RUN]) for i in range(len(lines) - RUN + 1)}

    # templates/ is excluded from the corpus, not exempted from the finding:
    # a file under it is SUPPOSED to be copied into the host repo -- that is
    # what a template is, and INSTALL.md instructs it. Matching a template
    # therefore proves the host followed the install, and reporting it as a
    # fork tells a correctly-installed repo to undo its own installation.
    # 2026-09-06: a consuming repo's `.claude/hooks/stop-git-check.sh` was
    # flagged for matching `templates/harness/claude-code/hooks/stop-git-check.sh`,
    # which is the file it is required to be a copy of.
    # `.claude/` is excluded for the same reason one step removed: the
    # upstream repo's own harness config is its own INSTANTIATION of those
    # same templates -- it dogfoods them -- so a host that installed the
    # template correctly matches that copy too, and excluding only
    # templates/ just moves the false finding rather than removing it.
    # Neither directory holds engine mechanism a host could shim.
    not_engine = (vendored / 'templates', vendored / '.claude')
    upstream = {}
    for p in sorted(vendored.rglob('*')):
        if any(d in p.parents for d in not_engine):
            continue
        if p.is_file() and p.suffix in ('.py', '.sh'):
            for r in runs(p):
                upstream.setdefault(r, str(p.relative_to(ROOT)))
    out = []
    for rel in _git('ls-files').stdout.split():
        if rel.startswith('process/'):
            continue
        if rel in vendored_engine:
            continue
        p = ROOT / rel
        if not p.is_file() or p.suffix not in ('.py', '.sh'):
            continue
        for r in runs(p):
            if r in upstream:
                out.append(Finding(rel, f'duplicates {RUN}+ consecutive lines '
                                        f'of {upstream[r]} — one vendored '
                                        f'engine, thin host shims, never a fork'))
                break
    return out


# The captured group is restricted to filename-shaped characters
# ([\w.-]+, no "<", ">", or spaces) deliberately, not just to keep the regex
# tight: this check's OWN registration below documents the two path shapes
# it looks for using a `'<name>'` placeholder, in a plain string literal --
# an unrestricted capture matched that placeholder text against itself,
# reporting a false violation for a file named literally "<name>" on every
# run, planted or not. Restricting the capture to real-filename characters
# fixed it structurally (the placeholder can never match) rather than by
# excluding this file by path, which would leave the same trap for the next
# docstring that quotes the pattern it implements.
_ENGINE_REF_RE = re.compile(
    r"""_ENGINE_DIR\s*/\s*['"]([\w.-]+)['"]|ROOT\s*/\s*['"]tools['"]\s*/\s*['"]([\w.-]+)['"]"""
)

# Companions whose ABSENCE is a normal state, not a vendoring gap. Each
# entry carries the reason, because an exemption whose justification lives
# somewhere else is how a real gap gets waved through later. Keep this
# short: the default answer to "this file isn't here" is to vendor it.
_ENGINE_REF_ABSENT_OK = {
    # split_practices.py's `split` subcommand, and nothing else, reads it:
    # the one-time conversion of BestPractice's own PRACTICES.md into
    # per-practice files. No consuming repo ever runs that, and
    # load_metadata() is called on demand with a graceful failure, never at
    # import — see its own docstring, which exists because a missing copy
    # used to take precedent_show.py down at import time.
    'practice_metadata.json',
    # routing_audit.py WRITES this on its first run. Absent means "no
    # routing audit has been run in this repo yet", which is the correct
    # state of a fresh install, not a file somebody forgot to copy.
    'routing_audit_state.json',
    # precedent_vendor_engine.py WRITES this into a repo it vendors INTO.
    # BestPractice is the origin, never a vendoree, so its absence here is
    # the correct state and its presence would be the anomaly -- the exact
    # inverse of every other entry's reasoning, which is why it needs
    # saying. code-cites-practice reads it to tell a stale citation from
    # version skew in vendored code.
    'ENGINE_MANIFEST.json',
    # A PRESENCE PROBE, not a dependency. _practice_is_reachable() asks
    # whether the session-practices channel is wired here, and the answer
    # for a SOURCE set is correctly "no": precedent_session_practices.py is
    # in CONSUMER_ENGINE_FILES only, since rendering other sources'
    # practices into a session file is a consuming repo's job. The reference
    # is already `.is_file()`-guarded and `wired` simply becomes False.
    # Found the moment precedent_check.py entered ENGINE_FILES (2026-09-07)
    # and started running in source sets, where it was a false violation on
    # every one of them -- the first real finding that vendoring produced.
    'precedent_session_practices.py',
}


# cite-the-incident, 2026-09-06: the project's own prior notes repository followed
# spec/MIGRATING_EXISTING_INSTALLS.md step 7 exactly as written and ended up
# with a hard-crashing precedent_gate.py -- FileNotFoundError on
# routing_scope.json, which precedent_gate.py itself names via
# `_ENGINE_DIR / 'routing_scope.json'` -- discovered only when someone
# actually tried to run a gate, not before. This check statically scans every
# tools/*.py file for exactly that shape of hardcoded reference and flags any
# target that isn't actually there, so the same class of gap (a vendored
# engine file naming a companion that never got copied) surfaces mechanically
# on the next `precedent_check.py` run instead of via a downstream crash.
# cite-the-incident, 2026-09-07: promoting two practices to the universal
# catalogue did every part of the job except the job. `git commit -a` does
# not stage an untracked file, so `practices/fail-gracefully.md` and
# `practices/bold-key-phrases.md` were written, regenerated into every view,
# given routing entries, deleted from both team sets -- and never added.
#
# For one pushed commit the two rules were in force NOWHERE: gone from both
# team sets, absent from the repository they had been promoted into. EVERY
# GATE PASSED, in both directions, and neither is a bug: locally the files
# were on disk, so the loader and every check read them and were right; in
# the pushed tree they did not exist, and a practice that does not exist
# violates nothing. The catalogue can lose a rule without anything saying so.
#
# The cheap, decidable half of that is this check. It does not attempt the
# general problem (did the catalogue silently shrink -- that needs a baseline
# to compare against, and is filed as `consumers-need-refresh-after-promotion`
# for the consumer-side version of the same shape). It asserts only that what
# a session can SEE is what the repository actually HAS.
_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


@check('expires-is-honoured', 'tree',
       'no practice is past the date in its optional `expires:` field while '
       'still active -- an expiry forces a decision, it never withdraws a '
       'rule on its own',
       'a CONDITION expiry ("when X happens"), which is deliberately never '
       'auto-evaluated: no general predicate can read an arbitrary English '
       'sentence, and a check that guessed would either withdraw a live rule '
       'or lie about an expired one. Those are listed by very_deep_check.py '
       'every run so a person judges them instead.',
       practice_backed=False)
def _expires_is_honoured(ctx):
    """Enforce the optional `expires:` frontmatter field.

    THE DESIGN CONSTRAINT, and it is the whole reason this is a check rather
    than a status: **an expired practice must never silently stop binding.**
    A rule that quietly switches itself off is worse than a stale one -- the
    stale rule is at least still being followed. So `expires:` makes NOISE
    and changes nothing: the practice stays `active`, keeps binding, and the
    gate goes red until a person decides.
    """
    import datetime
    today = precedent_time.today()
    out = []
    for f in sorted((ctx.root / 'practices').glob('*.md')) + \
            sorted((ctx.root / 'local' / 'practices').glob('*.md')):
        # sp.parse_frontmatter_fields is THE reader (one copy, deliberately
        # -- see its own docstring). The first draft of this check called a
        # function that does not exist and wrapped it in `except Exception:
        # continue`, so it reported every practice as having no expiry and
        # PASSED. A swallowed error is how a check reports a confident wrong
        # answer, which is the failure this whole field exists to avoid.
        text = f.read_text(encoding='utf-8')
        if not text.startswith('---'):
            continue
        fm = sp.parse_frontmatter_fields(text.split('---', 2)[1], decode=True)
        raw = fm.get('expires')
        expires = raw.strip() if isinstance(raw, str) else ''
        if not expires or expires.lower() in ('null', 'none'):
            continue
        if not _DATE_RE.match(expires):
            continue  # a condition -- very_deep_check lists these, see above
        if expires > today:
            continue
        status = (fm.get('status') or 'active').strip()
        if status != 'active':
            continue  # already withdrawn; the expiry did its job
        rel = f.relative_to(ctx.root).as_posix()
        out.append(Finding(rel, f'expires: {expires} has passed and the '
                                f'practice is still `active` -- decide: '
                                f'retire it, deduplicate it into whatever '
                                f'replaced it, or move the date and say why. '
                                f'It is STILL BINDING until you do; an expiry '
                                f'never withdraws a rule on its own'))
    return out


@check('tracked-practice-files', 'tree',
       'every practice file, check script and routing record in the working '
       'tree is tracked by git -- what a session reads locally is what the '
       'repository actually carries',
       'the opposite direction: a practice that is tracked but should not be, '
       'and a practice DELETED from the tree, which leaves nothing behind to '
       'notice. It compares the working tree against the index, so it cannot '
       'see a rule that was never written or one removed in the same commit; '
       'catching a silently shrinking catalogue needs a baseline this check '
       'does not have.',
       practice_backed=False)
def _tracked_practice_files(ctx):
    watched = []
    for pat in ('practices/*.md', 'local/practices/*.md',
                'tools/checks/*.py', 'tools/routing_scope.json'):
        watched.extend(sorted(ROOT.glob(pat)))
    if not watched:
        raise NotApplicable('no practice files, check scripts or routing '
                            'record in this tree')
    rels = [str(f.relative_to(ROOT)) for f in watched]
    r = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '--error-unmatch',
                        '-z', '--'] + rels,
                       capture_output=True, text=True)
    tracked = {x for x in r.stdout.split('\0') if x}
    # NOTHING TRACKED AT ALL is a repository that has not committed yet, not
    # a lost rule -- a freshly bootstrapped source set, or a scratch fixture.
    # The first version of this check flagged every file in exactly that
    # state, and the harness caught it as "a check that fires on a correct
    # fresh install", which is the failure this whole registry exists to
    # avoid. The state worth reporting is MIXED: this kind of file is tracked
    # here, and one of them is not, which is the shape a forgotten `git add`
    # actually leaves.
    if not tracked:
        raise NotApplicable(
            'nothing of this kind is tracked yet -- an uncommitted or freshly '
            'bootstrapped repository, not a file left out of one')
    out = []
    for rel in rels:
        if rel not in tracked:
            out.append(Finding(rel,
                               'is in the working tree but NOT tracked by '
                               'git -- every local check reads it and passes, '
                               'and the pushed repository does not have it '
                               '(`git add` it, or delete it)'))
    return out


@check('timestamps-carry-offset', 'tree',
       'no tracked Python file stamps a moment with a bare `date.today()`, '
       '`utcnow()`, `utcfromtimestamp()` or a zero-argument `datetime.now()` '
       '-- every one of those resolves to whatever zone the machine is on, '
       'which in a container is UTC and in a record is unrecoverable. And '
       'the declared fallback zone is the SAME string in all three places '
       'that hold it: precedent.json, the time engine, and the commit hook',
       'a stamp that carries an offset but the WRONG one -- a zone declared '
       'incorrectly in somebody\'s identity.json is a true statement about a '
       'false fact, and nothing mechanical can tell where a person actually '
       'is. It is also blind to `datetime.now(tz)` with an explicit zone '
       'argument: that IS offset-carrying and orderable, so flagging it '
       'would fire on correct code, and routing it through the one module '
       'is a one-formatter-per-quantity matter this check leaves to review. '
       'Non-Python emitters (a shell `date` call, a template) are out of '
       'scope for the same reason: `date +%Y-%m-%d` is correct once the '
       'session zone is set, which is the hook\'s job, not this one\'s.')
def _timestamps_carry_offset(ctx):
    """Two properties, one practice: nothing writes a naive moment, and the
    fallback zone cannot drift between the three files that name it.

    AST, NOT GREP. The first draft grepped, and matched its own explanatory
    comments in all twelve files it had just migrated -- a check reporting
    the sentence that describes the rule as a violation of it. Parsing means
    a comment, a docstring or a string literal mentioning `date.today()`
    reads as prose, which is what it is.
    """
    import ast

    # (attribute name, requires zero args) -- the calls that produce a moment
    # with no zone attached. `now` is listed with args_must_be_empty because
    # `datetime.now(tz)` is aware and fine; `now()` is naive.
    NAIVE = {'today': True, 'utcnow': False, 'utcfromtimestamp': False,
             'now': True}
    ENGINE = 'tools/precedent_time.py'

    out = []
    files = [f for f in _git('ls-files', '--cached', '--others',
                             '--exclude-standard', '--', '*.py').stdout.split()
             if f and f != ENGINE]
    if not files:
        raise NotApplicable('no tracked Python files in this repository')

    for rel in files:
        path = ctx.root / rel
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except (OSError, SyntaxError):
            # A file that will not parse is somebody else's finding, not
            # this check's to invent -- and never a silent pass: say it.
            out.append(Finding(rel, 'could not be parsed, so it was NOT '
                                    'checked for naive timestamps'))
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not isinstance(fn, ast.Attribute) or fn.attr not in NAIVE:
                continue
            # Only the datetime family. `pathlib.Path.cwd()` has no `today`,
            # but a domain object with a `.now()` of its own would otherwise
            # be flagged for having a common method name.
            root_name = fn.value
            while isinstance(root_name, ast.Attribute):
                root_name = root_name.value
            if not (isinstance(root_name, ast.Name)
                    and root_name.id in ('datetime', 'date')):
                continue
            if NAIVE[fn.attr] and (node.args or node.keywords):
                continue        # datetime.now(tz) -- aware, and orderable
            out.append(Finding(
                f'{rel}:{node.lineno}',
                f'`{fn.attr}()` writes a moment with no offset -- it resolves '
                f'in whatever zone this machine is on, which in a container '
                f'is UTC. Use tools/precedent_time.py '
                f'({"today()" if fn.attr == "today" else "stamp(), utc_iso() or from_unix()"}), '
                f'which resolves the person\'s zone and always carries the offset'))

    # ---- the declared fallback, in the three files that hold it
    declared = {}
    cfg = ctx.root / 'precedent.json'
    if cfg.exists():
        try:
            v = json.loads(cfg.read_text(encoding='utf-8')).get('fallback_timezone')
            if isinstance(v, str) and v.strip():
                declared['precedent.json (fallback_timezone)'] = v.strip()
        except ValueError:
            out.append(Finding('precedent.json', 'is not valid JSON, so the '
                                                 'declared fallback zone could '
                                                 'NOT be compared'))
    for rel, pat in ((ENGINE, r"^FALLBACK_TZ\s*=\s*'([^']+)'"),
                     ('.claude/hooks/commit-identity.sh', r'^DEFAULT_TZ="([^"]+)"'),
                     ('templates/harness/claude-code/hooks/commit-identity.sh',
                      r'^DEFAULT_TZ="([^"]+)"')):
        f = ctx.root / rel
        if not f.exists():
            continue
        m = re.search(pat, f.read_text(encoding='utf-8'), re.M)
        if m:
            declared[rel] = m.group(1)
        else:
            out.append(Finding(rel, 'holds the declared fallback zone and no '
                                    'longer states it in the form this check '
                                    'reads -- it could NOT be compared'))
    if len(set(declared.values())) > 1:
        detail = '; '.join(f'{k} says {v}' for k, v in sorted(declared.items()))
        out.append(Finding('', f'the declared fallback zone disagrees across '
                               f'the files that hold it -- {detail}. One of '
                               f'them silently stamps a different offset than '
                               f'the others'))
    return out


@check('document-status-header', 'tree',
       "every document under spec/ and record/ that CARRIES a lifecycle "
       "frontmatter header declares a legal kind/status pair, a title "
       "matching its own first heading, a `closed:` date exactly when it is "
       "closed, a `superseded_by:` that resolves exactly when it is "
       "superseded, and no competing hand-maintained `Last updated:` comment",
       "whether a declared status is TRUE. That a brief marked `open` really "
       "is open, or that a reference marked `current` still describes the "
       "system, is a judgment no field can carry and no check can make -- "
       "this verifies the claim is well-formed and internally consistent, "
       "not that it is honest. It is also blind to a document OUTSIDE spec/ "
       "and record/: the standard is scoped to those two trees, so a status "
       "declared in prose at the repository root is not reached. A repo "
       "part-way through its own backfill wants "
       "`python3 tools/doc_lifecycle.py --warn-only`, which reports "
       "unstamped files without failing; that was this check's own mode "
       "until the 2026-09-07 backfill stamped all 24 documents.")
def _document_status_header(ctx):
    try:
        import doc_lifecycle as dl
    except Exception as e:
        raise NotApplicable(f'tools/doc_lifecycle.py did not import: {e}')
    if not any((ROOT / d).is_dir() for d in dl.SCAN_DIRS):
        raise NotApplicable('this repo has no spec/ or record/ tree to stamp')
    findings, unstamped, stamped = dl.scan(root=ROOT)
    if not stamped and unstamped:
        # NOTHING stamped is a repo that has not started the backfill, not a
        # repo doing it wrong -- the same distinction tracked-practice-files
        # had to learn. The MIXED state is what this check is for.
        raise NotApplicable(
            f'{len(unstamped)} document(s) and none stamped -- this tree has '
            f'not adopted the lifecycle header at all')
    out = []
    for f in findings:
        rel, _, msg = f.partition(': ')
        out.append(Finding(rel, msg))
    # Blocking since the phase-2 backfill: a document with no header at all
    # is the failure this standard exists to prevent, not a lesser state.
    # Before the backfill this was deliberately silent -- see blind_to.
    for rel in unstamped:
        out.append(Finding(
            rel, 'carries no lifecycle frontmatter -- a reader cannot tell '
                 'from the file whether it is a live reference or the record '
                 'of something finished (see spec/DOCUMENT_LIFECYCLE.md)'))
    return out


_SPEC_WORD_RE = re.compile(r'\b(speculative|speculation|brainstorm(?:ed|s)?)\b', re.I)
_SPEC_PREFIX = 'SPECULATIVE_'
_SPEC_STATUSES = ('drafted', 'abandoned')


def _spec_heading_and_lede(text):
    """Return (heading text, the first non-blank block under it). A document
    with no `# ` heading yields (None, '')."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith('# '):
            rest = lines[i + 1:]
            j = 0
            while j < len(rest) and not rest[j].strip():
                j += 1
            block = []
            while j < len(rest) and rest[j].strip():
                block.append(rest[j])
                j += 1
            return ln[2:].strip(), '\n'.join(block)
    return None, ''


@check('speculation-is-marked', 'tree',
       "a speculative document under spec/ or record/ carries all four of "
       "its markers or none of them: the SPECULATIVE_ filename prefix "
       "requires a matching title, `kind: proposal`, a drafted/abandoned "
       "status and a warning block directly under the heading -- and, in the "
       "other direction, a document whose title or opening paragraph calls "
       "itself speculative must carry the prefix",
       "the PULL REQUEST, which is the fourth marker the practice asks for "
       "and the one no tree-scoped check can see: a gate runs against files, "
       "and a pull-request body lives on a hosting platform it cannot read "
       "offline or in continuous integration. That marker is prose, loaded "
       "at the `merge` gate instead. It is equally blind to a speculative "
       "document that says so NOWHERE -- no mechanism can read the "
       "conversation an idea came from and tell an intention from a "
       "brainstorm, so this catches DRIFT between the markers, never a "
       "document that never made the claim. And it does not judge the "
       "register: prose written in the voice of a plan ('ships in March', "
       "an owner named) passes as long as the four markers are consistent.")
def _speculation_is_marked(ctx):
    try:
        import doc_lifecycle as dl
    except Exception as e:
        raise NotApplicable(f'tools/doc_lifecycle.py did not import: {e}')
    scan_dirs = [d for d in dl.SCAN_DIRS if (ROOT / d).is_dir()]
    if not scan_dirs:
        raise NotApplicable('this repo has no spec/ or record/ tree')

    findings = []
    for d in scan_dirs:
        for p in sorted((ROOT / d).rglob('*.md')):
            rel = p.relative_to(ROOT).as_posix()
            text = p.read_text(encoding='utf-8', errors='ignore')
            fm, _body = dl.parse_frontmatter(text)
            if not fm:
                continue                      # unstamped: document-status-header's finding, not this one
            title = (fm.get('title') or '').strip().strip('"\'')
            heading, lede = _spec_heading_and_lede(text)
            prefixed = p.name.startswith(_SPEC_PREFIX)
            claims = bool(_SPEC_WORD_RE.search(title)
                          or _SPEC_WORD_RE.search(lede))

            if prefixed:
                if not title.lower().startswith('speculative'):
                    findings.append(Finding(rel, (
                        'the filename says SPECULATIVE_ and the title does not '
                        'open with "Speculative" -- a search hit shows the title '
                        'and never the path')))
                if heading is not None and not heading.lower().startswith('speculative'):
                    findings.append(Finding(rel, (
                        'the `#` heading does not open with "Speculative", so the '
                        'rendered document does not say what the filename says')))
                kind = (fm.get('kind') or '').strip()
                status = (fm.get('status') or '').strip()
                if kind != 'proposal':
                    findings.append(Finding(rel, (
                        f'kind is `{kind or "unset"}`; a speculative document is '
                        f'`proposal` (see spec/DOCUMENT_LIFECYCLE.md)')))
                elif status not in _SPEC_STATUSES:
                    findings.append(Finding(rel, (
                        f'status is `{status or "unset"}`; a speculative document '
                        f'is `drafted` or `abandoned`. `{status}` means somebody '
                        f'decided to do it, at which point it is not speculative '
                        f'any more and the markers come off (a rename -- see '
                        f'practices/rename-updates-links.md)')))
                if not lede.lstrip().startswith('>'):
                    findings.append(Finding(rel, (
                        'no warning block directly under the heading -- a reader '
                        'who opens the file must be told before the content that '
                        'nobody has decided this')))
            elif claims:
                findings.append(Finding(rel, (
                    'calls itself speculative in its title or opening paragraph '
                    'but the filename does not -- rename it to '
                    f'{_SPEC_PREFIX}<name>.md, so a file listing says it too')))
    return findings


@check('vendored-engine-file-refs-resolve', 'tree',
       "every hardcoded `_ENGINE_DIR / '<name>'` or `ROOT / 'tools' / '<name>'` "
       "path inside a tools/*.py file names a file that actually exists under "
       "this repo's own tools/",
       "whether the referenced file's CONTENT is current or correct, and "
       "whether a file with no hardcoded reference to it at all (nothing in "
       "tools/*.py names its path this way) was itself supposed to be here -- "
       "only that a path this code already commits to finding is actually "
       "there. It scans the `_ENGINE_DIR / '<name>'` and "
       "`ROOT / 'tools' / '<name>'` spellings only, not an equivalent path "
       "built any other way (an f-string, a joined variable).",
       practice_backed=False)
def _vendored_engine_file_refs_resolve(ctx):
    tools_dir = ROOT / 'tools'
    findings = []
    for p in sorted(tools_dir.glob('*.py')):
        text = p.read_text(encoding='utf-8', errors='ignore')
        for m in _ENGINE_REF_RE.finditer(text):
            name = m.group(1) or m.group(2)
            if name in _ENGINE_REF_ABSENT_OK:
                continue
            if not (tools_dir / name).exists():
                findings.append(Finding(
                    f'tools/{p.name}',
                    f"references tools/{name}, which does not exist locally "
                    f"-- a vendored engine file naming a companion that was "
                    f"never copied over is exactly how the project's own prior notes repository "
                    f"ended up with a hard-crashing precedent_gate.py "
                    f"(2026-09-06, missing routing_scope.json)"))
    return findings


# Keys that name a DECLARED branch. Three distinct questions get answered by
# a declaration rather than by inference, and a file answering ANY of them is
# not the failure this check is about:
#   base_branch     -- what lineage THIS repo's own work belongs to
#   branch          -- which branch a VENDORED copy tracks (checkin.py reads
#                      it from process/manifest.json's `upstream`)
#   SOURCE_BRANCH   -- which branch the engine is seeded from
_DECLARED_BRANCH_KEYS = ('base_branch', 'branch')

# Exemptions, each with the reason it is not an inference. Kept as a table
# rather than a bare name list because an unexplained exemption is how a
# check quietly stops covering the thing it was written for.
_BASE_BRANCH_INFERENCE_OK = {
    'verify_harness.py':
        "does not INFER a base branch -- it CONSTRUCTS throwaway fixture "
        "repositories and sets refs/remotes/origin/HEAD on them on purpose, "
        "including the negative controls for this very family of bugs",
    'precedent_check.py':
        "this file, whose own scan for the pattern necessarily contains it",
}


def _unguarded_branch_inferences(text):
    """-> sorted names of the FUNCTIONS that infer a base branch from
    `refs/remotes/origin/HEAD` without a declared branch being read first.

    Function-level, not file-level, and that took three attempts to get
    right -- each earlier version passed its own negative control, which is
    the only reason the weakness showed at all.

    v1 asked whether the FILE contained the literal `get('base_branch')`.
    Deleting the helper from doc_lint.py and renaming it left that literal
    in the dead body, and the control came back green: a check a file
    passes by containing the right *words*.

    v2 asked whether the file made a real declared-branch CALL anywhere,
    via AST. Same control, same green -- the dead helper's call was still a
    call.

    v3, here, asks the actual question: the function doing the inferring
    must itself read a declaration, or be called by a function that does.
    The one-hop allowance is not slack; it is checkin.py's real shape,
    where `_tracked_branch()` reads the manifest's `upstream.branch` and
    delegates to `_default_branch(clone)` only as the fallback. Requiring
    the read inside the leaf would have flagged the one resolver in this
    tree that was already correct.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    docstrings = set()
    for node in ast.walk(tree):
        body = getattr(node, 'body', None) if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                   ast.AsyncFunctionDef)) else None
        if body and isinstance(body[0], ast.Expr) and \
                isinstance(body[0].value, ast.Constant) and \
                isinstance(body[0].value.value, str):
            docstrings.add(id(body[0].value))

    def infers(fn):
        # A mention in a comment or docstring is prose, not an inference.
        # precedent_vendor_engine.py's only occurrence is a docstring
        # explaining checkin.py's old behaviour; flagging a file for
        # DESCRIBING the bug it already fixed trains people to ignore the
        # check.
        return any(isinstance(n, ast.Constant) and isinstance(n.value, str)
                   and id(n) not in docstrings
                   and 'refs/remotes/origin/HEAD' in n.value
                   for n in ast.walk(fn))

    def reads_declaration(fn):
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Name) and f.id == '_declared_base_branch':
                    return True
                if isinstance(f, ast.Attribute) and f.attr == 'get' and n.args \
                        and isinstance(n.args[0], ast.Constant) \
                        and n.args[0].value in _DECLARED_BRANCH_KEYS:
                    return True
            if isinstance(n, ast.Name) and n.id == 'SOURCE_BRANCH' \
                    and isinstance(n.ctx, ast.Load):
                return True
        return False

    def calls(fn):
        return {n.func.id for n in ast.walk(fn)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}

    fns = [n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    guarded_callers = {name for fn in fns if reads_declaration(fn)
                       for name in calls(fn)}
    return sorted(fn.name for fn in fns if infers(fn)
                  and not reads_declaration(fn)
                  and fn.name not in guarded_callers)


@check('declared-base-branch', 'tree',
       "every tool that resolves the repo's branch reads precedent.json's "
       "declared `base_branch` before falling back to inferring one from "
       "`refs/remotes/origin/HEAD`",
       "whether the declared value is CORRECT, whether a tool that needs a "
       "base branch resolves one at all (a tool that hardcodes 'main' as a "
       "string and never touches origin/HEAD is invisible here), and every "
       "non-Python way of asking the same question -- a shell script or a "
       "workflow running `git symbolic-ref` itself is not scanned.",
       practice_backed=False)
def _declared_base_branch_is_read(ctx):
    """Asking `origin/HEAD` for the base branch is the wrong question, and
    it is wrong in a way that tests clean.

    `origin/HEAD` answers "what does GitHub show first". Callers mean "what
    lineage does this work belong to". Those are the same value in almost
    every repo, so the mistake is invisible until one pins its work to a
    branch that is not its default -- which is what this repo does while
    `precedent-beta-v01` is unmerged, and has done since 2026-09-03.

    Measured on 2026-09-06, on a real checkout of that branch: SIX separate
    tools carried their own copy of the inference, and two were actively
    wrong. `doc_lint.default_branch()` returned the literal string 'HEAD'
    (origin/HEAD unset, origin/main absent from a single-branch clone), so
    `changed_md()` diffed against a ref that does not resolve and returned
    ZERO files -- the markdown gate passing by scanning nothing.
    `doc_html._link_base()` emitted `/blob/main/` for content that exists
    only on the beta branch: every generated link dead.

    The duplication is deliberate and stays -- doc_lint.py and doc_html.py
    are meant to be droppable into a host repo alone, and doc_html.py's own
    docstring says so. So this does not demand a shared import. It demands
    that each copy ask the declared question first. Without a check the
    next tool copies the nearest existing resolver, inherits the bug, and
    tests clean again: that is precisely how this reached six copies.
    """
    findings = []
    for path in sorted((ROOT / 'tools').glob('*.py')):
        if path.name in _BASE_BRANCH_INFERENCE_OK:
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        for fn in _unguarded_branch_inferences(text):
            findings.append(Finding(
                f'tools/{path.name}',
                f"{fn}() resolves refs/remotes/origin/HEAD without a "
                "DECLARED branch being read first, so under this repo's "
                "branch pin it measures against a lineage the work never "
                "touched -- read precedent.json's `base_branch` (the "
                "`_declared_base_branch` helper the other resolvers carry), "
                "or the manifest's `upstream.branch` if the question is "
                "which branch a vendored copy tracks"))
    return findings


@check('verify-postcondition', 'turn-end',
       'the state you wanted after the operations this turn: nothing '
       'committed but unpushed on any local branch, and no tracked file '
       'left modified',
       'every other postcondition. It asserts the two this practice names '
       'as its own examples, for this repository; naming the postcondition '
       'for anything else is still yours.')
def _verify_postcondition(ctx):
    # The practice's own quoted example, verbatim, is "no unpushed commits on
    # ANY branch" -- and its Install section is explicit: "enumerate every
    # local branch against its remote and require the difference to be
    # empty... the postcondition is 'nothing unpublished anywhere'." This
    # used to check only the CURRENTLY CHECKED OUT branch against its own
    # configured upstream (`@{upstream}..HEAD`), which is a strictly weaker,
    # single-branch postcondition -- and misses exactly the practice's own
    # origin incident: work committed on a branch that was then left
    # un-checked-out and unpublished while a session moved on. Reproduced
    # directly: commit to a second local branch, leave the checked-out
    # branch clean and fully pushed, and the old check reported "0 violated"
    # with the stray commit sitting right there in `git branch -v`.
    #
    # Rather than per-branch `@{upstream}` tracking (absent for plenty of
    # real branches -- e.g. one whose remote counterpart exists under the
    # same name but was never explicitly set as its upstream), this asks the
    # more direct question the Rule actually names: is this commit
    # reachable from ANY remote-tracking ref at all? `--not --remotes`
    # answers that without depending on tracking configuration, and doubles
    # as the fallback for a branch that was never pushed under any name.
    branches = _git('for-each-ref', 'refs/heads', '--format=%(refname:short)')
    if branches.returncode != 0 or not branches.stdout.strip():
        raise NotApplicable('this repository has no local branches to check')
    if not _git('for-each-ref', 'refs/remotes').stdout.strip():
        raise NotApplicable('no remote-tracking refs exist, so "no unpushed '
                            'commits on any branch" is not a postcondition '
                            'that can be evaluated here')
    out = []
    for branch in branches.stdout.split():
        ahead = _git('rev-list', '--count', branch, '--not',
                     '--remotes').stdout.strip()
        if ahead and ahead != '0':
            out.append(Finding('', f'{ahead} commit(s) on {branch!r} are not '
                                   f'reachable from any remote — the command '
                                   f'that reported success is not the state '
                                   f'you wanted'))
    # `refs/heads` only lists named branches. A detached HEAD is committed
    # work reachable from neither a branch nor (if unpushed) a remote — one
    # level worse than the branch case this check was rewritten for: there
    # is not even a name to notice it by by via `git branch -v`. Caught
    # directly: `git symbolic-ref` fails exactly when HEAD is detached.
    if _git('symbolic-ref', '-q', 'HEAD').returncode != 0:
        ahead = _git('rev-list', '--count', 'HEAD', '--not',
                     '--remotes').stdout.strip()
        if ahead and ahead != '0':
            out.append(Finding('', f'{ahead} commit(s) on the detached HEAD '
                                   f'are not reachable from any remote and are '
                                   f'on no branch — the command that reported '
                                   f'success is not the state you wanted'))
    dirty = [l for l in _git('status', '--porcelain').stdout.splitlines()
             if l and not l.startswith('??')]
    if dirty:
        out.append(Finding('', f'{len(dirty)} tracked file(s) still modified '
                               f'in the working tree'))
    return out


@check('no-rewrite-for-warnings', 'turn-end',
       'the commit this branch was last published at is still an ancestor of '
       'its tip — published history has not been rewritten',
       'a rewrite that has already been force-pushed. It catches the rewrite '
       'before the push, which is the moment it is still free to undo.')
def _no_rewrite_for_warnings(ctx):
    up = _git('rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}')
    if up.returncode != 0:
        raise NotApplicable('this branch tracks no upstream, so there is no '
                            'published history to compare against')
    remote = up.stdout.strip()
    anc = _git('merge-base', '--is-ancestor', remote, 'HEAD')
    if anc.returncode != 0:
        return [Finding('', f'{remote} is no longer an ancestor of HEAD: '
                            f'history that was already published has been '
                            f'rewritten. Fix it forward; do not force-push')]
    return []


# --------------------------------------------------------------------------
# Delegating checks -- an existing gate owns the enforcement; this names which
# practice each of its findings belongs to, which is what the bare
# `checked_by: "tools/doc_lint.py"` never did.
# --------------------------------------------------------------------------

def _doc_lint():
    try:
        import doc_lint
    except Exception as e:
        raise NotApplicable(f'tools/doc_lint.py did not import: {e}')
    return doc_lint


# A consuming repo vendors this repo's whole tree at process/upstream/ and is
# forbidden to hand-edit it -- it must stay byte-identical to what the mirror
# last wrote, so a finding there is not actionable where it is reported. Every
# change-scope document check below runs on `ctx.changed`, and a re-vendor
# marks the entire vendored tree as changed: a consumer that pulled 167
# commits of upstream got acronyms-glossary, header-caps and no-stale-counts
# firing on UPSTREAM's own prose, none of which it may touch (2026-09-06).
# migration-scrubs-vocabulary already excluded this path for exactly this
# reason; centralizing it here so the same exemption reaches every check that
# walks changed markdown, rather than being re-derived per check.
# practice: scrub-gate (the vendored tree's own gate is practice_audit.py)
# The path is ASKED FOR, never written down here. The literal that used to
# sit at this line was 'process/upstream/' -- INSTALL.md §1's layout -- so
# every check routed through _is_vendored() below silently lost its exemption
# in a §0 install, where the vendored catalogue lives at whatever path
# precedent.json's `universal` source names. That is the broadest instance of
# the bug: this one exemption feeds acronyms-glossary, header-caps,
# no-stale-counts and migration-scrubs-vocabulary at once.
def _is_vendored(path):
    return path.startswith(_mirrored(ROOT))


def _md_in_scope(ctx):
    return [f for f in ctx.changed
            if f.endswith('.md') and not _is_vendored(f) and (ROOT / f).exists()]


@check('doc-references-are-links', 'change',
       'a changed document must not render an accidental strikethrough span '
       '— use the approximately sign, never a tilde',
       'the other half of this practice. Whether a file reference is a link '
       'is a WARNING in doc_lint, not a gate, and this check inherits that.')
def _doc_references_are_links(ctx):
    dl = _doc_lint()
    if not dl.HAVE_GFM:
        raise NotApplicable('cmark-gfm is not installed, so strikethrough '
                            'cannot be detected exactly and this check will '
                            'not guess (pip install cmarkgfm)')
    files = _md_in_scope(ctx)
    if not files:
        raise NotApplicable('no changed markdown file is in scope')
    out = []
    for f in files:
        strikes, _u, _g, _t, _n = dl.check_file(f, fix=False, known=None)
        for i, txt in strikes:
            out.append(Finding(f'{f}:{i}', f'renders <del> on GitHub: {txt}'))
    return out


@check('heading-outline', 'change',
       'a changed document never jumps a heading level -- no heading is more '
       'than one level deeper than the one before it',
       'whether a heading sits at the RIGHT level for its meaning; only '
       'whether the outline it makes is well-formed. A section demoted by '
       'accident to a level that happens not to skip reads as fine here.')
def _heading_outline(ctx):
    dl = _doc_lint()
    files = _md_in_scope(ctx)
    if not files:
        raise NotApplicable('no changed markdown file is in scope')
    out = []
    for f in files:
        # One detector, two callers -- doc_lint reports these in the light
        # check and this gate fails on them, from the same function.
        for line, frm, to, txt in dl.scan_heading_skips(f):
            out.append(Finding(f'{f}:{line}',
                               f'h{frm} -> h{to}, with no h{frm + 1} between '
                               f'them: {txt}'))
    return out


@check('headline-capitalization', 'change',
       'a changed outward-facing document has every heading in New York '
       'Times headline capitalization',
       'headings outside the practice\'s scope (practice files, specs, the '
       'repo\'s own working documents), which are deliberately sentence '
       'case; a phrase whose capitalization carries meaning, which only '
       'a person can add to title_case.KEEP_PHRASES; a heading that is a '
       'SENTENCE rather than a title -- a rule stated outright, a question, '
       'an example line -- which --write capitalizes word by word into '
       'something correct by the NYT rule and wrong to read, and which only '
       'a person can rewrite as a title or exclude; and, in a CONSUMING '
       'repo, the scope boundary itself, since title_case.INTERNAL_DIRS is '
       'this repo\'s own list of directory names and a consumer\'s working '
       'directory that nobody thought to name there reads as publishable.')
def _headline_capitalization(ctx):
    sys.path.insert(0, str(ROOT / 'tools'))
    try:
        import title_case
    except Exception as e:
        # This file is in ENGINE_FILES as of 2026-09-07, so it now runs
        # inside SOURCE sets, which carry no title_case.py (that is
        # CONSUMER_ENGINE_FILES only). An unguarded import turns a
        # legitimately absent dependency into an ERRORED check, which reads
        # as a broken tool rather than an absent one. A named skip says what
        # is missing; the runner already prints that a skip is not a pass.
        raise NotApplicable(f'tools/title_case.py did not import: {e}')
    # title_case.is_outward() is the one definition of "outward-facing"
    # -- everything except its INTERNAL_DIRS/INTERNAL_FILES plus whatever
    # this repo's own precedent.json adds under `internal_paths`. This gate
    # asks it rather than carrying a second copy of the boundary, and passes
    # ROOT so the repo-declared half is read from THIS repo's config rather
    # than the process's working directory.
    scope = [f for f in ctx.changed
             if f.endswith('.md') and title_case.is_outward(f, root=ROOT)
             and (ROOT / f).exists()]
    if not scope:
        raise NotApplicable('no changed outward-facing document is in scope')
    out = []
    for f in scope:
        for line, before, after in title_case.process(ROOT / f, write=False):
            out.append(Finding(f'{f}:{line}',
                               f'not headline case: {before!r} -> {after!r}'))
    return out


def _unglossed(text, known, path=None):
    """[(line, TOKEN)] via doc_lint's own acronym scan, so this check and the
    warning it replaces never drift apart -- one detector, two callers.

    This used to hold its own copy of doc_lint's scan loop, under this same
    docstring, and drifted from it exactly as the docstring said it must
    not: two filters added to doc_lint (an ALL-CAPS filename stem is not an
    acronym; a document naming itself in its own title is not either)
    fixed doc_lint's report while this gate went on failing on `LEDGER.md`.
    It now calls the shared function."""
    return _doc_lint().scan_unglossed(text, known, path)


@check('acronyms-glossary', 'change',
       'a changed document does not introduce a NEW unglossed acronym -- one '
       'not already in GLOSSARY.md and not expanded on first use',
       'the entire existing corpus. doc_lint reports every unglossed '
       'acronym in a file as a warning; most predate this practice and '
       'gating on all of them would fail forever and get switched off. This '
       'gates only what a change ADDS: an acronym unglossed in the base '
       'version and still unglossed here is pre-existing debt, not this '
       "change's doing -- same reasoning as doc_lint's own opt-in numbers "
       'gate, applied here without needing an opt-in marker because the '
       "diff itself is the scope.")
def _acronyms_glossary(ctx):
    dl = _doc_lint()
    known = dl.load_known_acronyms()
    if known is None:
        raise NotApplicable('no GLOSSARY.md in this repo, so the acronym '
                            'check has nothing to check unglossed terms '
                            'against')
    files = [f for f in _md_in_scope(ctx) if f not in dl.ACRONYM_SKIP_FILES]
    if not files:
        raise NotApplicable('no changed markdown file is in scope')
    out = []
    for f in files:
        cur = _unglossed(ctx.read(f), known, f)
        base_text = ctx.read_base(f)
        base_toks = {tok for _i, tok in _unglossed(base_text, known, f)} if base_text else set()
        for i, tok in cur:
            if tok not in base_toks:
                out.append(Finding(f'{f}:{i}',
                                    f'{tok} used without expansion on first '
                                    f'use or a GLOSSARY.md entry'))
    return out


@check('deliverables-look-like-output', 'change',
       'a reader-facing document in scope carries no process residue — no '
       'verify-later flag, claims-to-source apparatus or decision provenance',
       'apparatus written in words its pattern list does not know. It catches '
       'the recurring forms, not the idea.')
def _deliverables_look_like_output(ctx):
    dl = _doc_lint()
    files = _md_in_scope(ctx)
    if not files:
        raise NotApplicable('no changed markdown file is in scope')
    out = []
    for f in files:
        for i, why in dl.check_residue(f):
            out.append(Finding(f'{f}:{i}', why))
    return out


LABEL_RE = re.compile(
    r'^(#{1,6}\s+.*|\*\*[^*\n]+\*\*:?)\s*$', re.M)
# Deliberately narrow: a PARENTHETICAL claim ("(one line)"), or the whole
# label IS the claim ("TL;DR", "One-liner:"). A heading merely mentioning
# "one-line" while naming something else -- MOBILE.md's "how the one-line
# opener works" -- is not a claim about the section's own length, and an
# earlier, broader version of this regex fired on exactly that heading.
ONE_LINE_CLAIM_RE = re.compile(
    r'\(\s*(?:in\s+)?one[- ]lin(?:e|er)\s*\)'
    r'|^#{1,6}\s*TL;DR\s*:?\s*$'
    r'|^\*\*(?:TL;DR|One-liner)\*\*:?\s*$', re.I)
ONE_PARA_CLAIM_RE = re.compile(
    r'\(\s*one[- ]paragraph\s*\)|\(\s*one-pager\s*\)', re.I)


@check('label-describes-content', 'change',
       'a heading or bold lead-in that claims "one line" / "one-liner" / '
       '"TL;DR" / "one paragraph" / "one-pager" must match the length of '
       'what actually follows it',
       'a claim made in running prose rather than a heading or bold '
       'lead-in — the practice covers both, this check only the labelled '
       'form, because prose mentions of "one-line" are not a label on a '
       'section and free text has no reliable block boundary to measure.')
def _label_describes_content(ctx):
    out = []
    for f in _md_in_scope(ctx):
        text = ctx.read(f)
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if not LABEL_RE.match(line):
                continue
            claims_line = ONE_LINE_CLAIM_RE.search(line)
            claims_para = ONE_PARA_CLAIM_RE.search(line)
            if not (claims_line or claims_para):
                continue
            # the block that follows: non-blank lines up to the next blank
            # line that precedes a heading/label or end of file, skipping
            # one immediate blank line after the label itself.
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            first_para = []
            while j < len(lines) and lines[j].strip():
                first_para.append(lines[j])
                j += 1
            if not first_para:
                continue
            # is there a second paragraph before the next label/heading?
            k = j
            while k < len(lines) and not lines[k].strip():
                k += 1
            has_second_para = k < len(lines) and not LABEL_RE.match(lines[k])
            if claims_line and (len(first_para) > 1 or has_second_para):
                out.append(Finding(f'{f}:{i + 1}',
                                    'labelled "one line" but the content '
                                    'runs to more than one line'))
            elif claims_para and has_second_para:
                out.append(Finding(f'{f}:{i + 1}',
                                    'labelled "one paragraph" but the '
                                    'content spans more than one paragraph'))
    return out


# WHERE DISCLOSURE COUNTS, and the three-way contradiction this settled
# (2026-09-10). The practice's Rule names one destination -- "for a
# dependent repo, that document is templates/GETTING_STARTED.md's
# administrator section". This check read a root GITHUB_ACTIONS.md and
# nothing else. And INSTALL.md §1 step 6's root-hygiene list names
# GITHUB_ACTIONS.md among the files that exist ONLY under
# `process/upstream/` and must never be copied to the root. So a dependent
# repo that FOLLOWED the practice failed the check, and one that satisfied
# the check tripped root hygiene -- unless it wrote its own,
# differently-scoped GITHUB_ACTIONS.md, which nothing asked it to. The
# check's own "blind to" text half-admitted it ("a README section would
# satisfy the practice's intent but not this check").
#
# Settled in the Rule's favour, because the Rule is the one of the three
# that carries the reasoning: the destination is "the document that
# project's own people actually read", and in a dependent repo that is
# GETTING_STARTED.md, which root hygiene explicitly DOES place at the root.
#
# Both are read, rather than swapping one hard-coded filename for another.
# GITHUB_ACTIONS.md stays a valid home for a repo that has its own --
# BestPractice itself is exactly that repo, being the upstream, and its
# root copy is its own document rather than a vendored one. A repo that
# discloses in either has disclosed.
DISCLOSURE_DOCS = ('GETTING_STARTED.md', 'GITHUB_ACTIONS.md')


@check('github-setup-disclosed', 'change',
       'a newly added GitHub Actions workflow file is named in '
       "GETTING_STARTED.md's administrator section -- the document a "
       "dependent repo's own people read -- or in a repo's own root "
       'GITHUB_ACTIONS.md',
       'a workflow file that is EDITED rather than added (this only fires '
       "on new files, per no-version-suffix's ctx.added_files pattern); "
       'WHERE in the document the name appears, so a filename dropped '
       'anywhere in it passes; and whether the line says what the workflow '
       'does or what must be clicked to enable it, which is most of what '
       'the Rule actually asks for.')
def _github_setup_disclosed(ctx):
    added = [f for f in ctx.added_files()
             if re.match(r'^\.github/workflows/.+\.ya?ml$', f)]
    if not added:
        raise NotApplicable('no GitHub Actions workflow file was added by '
                            'this change')
    present = [(name, (ROOT / name).read_text(encoding='utf-8', errors='ignore'))
               for name in DISCLOSURE_DOCS if (ROOT / name).is_file()]
    if not present:
        return [Finding(f, f'adds a workflow file, but this repo has none of '
                           f'{" or ".join(DISCLOSURE_DOCS)} to disclose it '
                           f'in. A dependent repo instantiates '
                           f'GETTING_STARTED.md at its root '
                           f'(INSTALL.md §1 step 2); that is where its own '
                           f'people read about GitHub-specific setup')
                for f in added]
    out = []
    for f in added:
        name = pathlib.PurePath(f).name
        if not any(name in doc for _where, doc in present):
            out.append(Finding(
                f, f'{name} is not mentioned in '
                   f'{" or ".join(w for w, _ in present)} -- an install that '
                   f'turns a check on and records it only in the install log '
                   f'has informed nobody who will act on it'))
    return out


# WHAT COUNTS AS "THIS WORKFLOW COMMITS". Deliberately the shell verbs, not
# a YAML parse of every step: a workflow commits by running `git commit`,
# and that string is what a reader greps for too. A `uses:` action that
# commits on the caller's behalf is NOT caught -- named in the practice's
# own "blind to" rather than pretended away.
# Anchored at a WORD boundary, never at line start. The first version
# anchored at `^\s*[-|>]?\s*`, which reads a shell line as a commit only
# when `git` is the first word -- so `TZ="$ZONE" git commit -m ...`, the
# very shape a CORRECTLY-authored workflow uses, was classified as "this
# workflow does not commit" and skipped. A false negative, and the worse
# direction: it would equally have missed a bot-authored commit behind any
# env prefix. Caught by running the check against a correct fixture, which
# is the half checkable-gets-checked insists on.
CI_COMMIT_RE = re.compile(r'(?<![\w./-])git\s+commit\b')
# The bot account, in both spellings a workflow actually uses.
CI_BOT_RE = re.compile(r'github-actions\[bot\]|41898282\+github-actions')
# Configuring an identity at all.
CI_SETS_IDENTITY_RE = re.compile(r'git\s+config\s+(--\w+\s+)*user\.(name|email)', re.M)
# Reading a DECLARED one. identity.json is the declaration the practice
# names; PRECEDENT_COMMIT_* is the explicit override that outranks it.
CI_READS_DECLARED_RE = re.compile(r'identity\.json|PRECEDENT_COMMIT_')


@check('ci-commits-carry-identity', 'tree',
       'a .github/workflows/*.yml that runs `git commit` resolves the '
       'author from a declared identity (an identity.json, or an explicit '
       'PRECEDENT_COMMIT_*) rather than naming the github-actions bot or '
       'configuring a git identity from nothing',
       'whether the identity a workflow DOES read names the right person; a '
       '`uses:` action that commits on the workflow\'s behalf, which never '
       'shows a `git commit` line here at all; whether the workflow actually '
       'exits non-zero on a missing value, as opposed to reading one; and a '
       'commit made by anything other than a GitHub Actions workflow, which '
       'is the session-side commit-identity backstop\'s job and not this '
       'check\'s.')
def _ci_commits_carry_identity(ctx):
    wf_dir = ROOT / '.github' / 'workflows'
    if not wf_dir.is_dir():
        raise NotApplicable('this repo has no .github/workflows/ directory, '
                            'so it runs no workflow that could commit')
    workflows = sorted(list(wf_dir.glob('*.yml')) + list(wf_dir.glob('*.yaml')))
    if not workflows:
        raise NotApplicable('this repo declares no GitHub Actions workflow')

    committing, out = [], []
    for wf in workflows:
        try:
            text = wf.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        # COMMENTS ARE BLANKED, NOT DROPPED, AND EVERY TEST BELOW READS
        # `body` (corrected 2026-09-10, the same day this check landed).
        #
        # The first version stripped comments for the commit test and read
        # the RAW text for the bot test, four lines apart in this same
        # function. So a workflow explaining why it does NOT use the bot
        # was read as one that does -- and the workflow that hit it was the
        # one that had just been FIXED, carrying the incident note its own
        # fix is about. The check punished a repo for citing the incident,
        # which is the opposite of what cite-the-incident asks for, and the
        # only ways out were deleting the explanation or wording around it.
        # Found independently by two sessions within an hour, each against
        # a real workflow.
        #
        # Blanking rather than dropping keeps every line number equal to
        # the file's own, so a finding still points where a reader looks.
        body = '\n'.join('' if ln.lstrip().startswith('#') else ln
                          for ln in text.splitlines())
        if not CI_COMMIT_RE.search(body):
            continue                 # reads only -- nothing to author
        committing.append(wf)
        rel = wf.relative_to(ROOT).as_posix()
        bot = CI_BOT_RE.search(body)
        if bot:
            line = body.count('\n', 0, bot.start()) + 1
            out.append(Finding(
                f'{rel}:{line}',
                'commits as the github-actions bot. A workflow runs on a '
                'runner, where the session-side commit-identity hook never '
                'executes -- so this is the one commit nothing else will '
                'author correctly. Read name/email/timezone from the '
                'declared identity.json and exit non-zero if any is '
                'missing; falling back to the bot is the failure, not a '
                'lesser version of the fix'))
        elif CI_SETS_IDENTITY_RE.search(body) and not CI_READS_DECLARED_RE.search(body):
            m = CI_SETS_IDENTITY_RE.search(body)
            line = body.count('\n', 0, m.start()) + 1
            out.append(Finding(
                f'{rel}:{line}',
                'configures a git identity but reads no declared one (no '
                'identity.json, no PRECEDENT_COMMIT_*), so whatever it '
                'commits is authored by whatever that line happens to say'))
        elif not CI_READS_DECLARED_RE.search(body):
            out.append(Finding(
                rel,
                'runs `git commit` without resolving any declared identity, '
                'so the commit takes the runner\'s default author and its '
                'UTC clock -- both of which a repository\'s own author and '
                'timezone rules exist to refuse'))

    if not committing:
        raise NotApplicable(
            f'none of this repo\'s {len(workflows)} workflow(s) runs '
            f'`git commit`, so none of them authors anything')
    return out


REVISION_ANNOTATION_RE = re.compile(
    r'\((?:added|rewritten|updated|removed|revised)\s+\d{4}-\d{2}-\d{2}\)'
    r'|^#{1,6}.*\bRev(?:ision)?\.?\s*\d+\b', re.I | re.M)


@check('docs-are-current-state', 'change',
       'a changed document does not carry an in-document revision '
       'annotation -- an "(added <date>)" / "(rewritten <date>)" tag, or a '
       '"Rev N" heading ladder -- since version control already carries '
       'that losslessly',
       'the practice\'s real target: superseded text kept inline "for '
       'history" with no date tag at all, and the four narrow textual '
       'exemptions (dated decision records, volatile-fact freshness '
       'stamps, legally load-bearing markers, as-shipped artifacts), which '
       'this check does not try to distinguish -- it only catches the '
       'literal annotation forms named in the Rule.')
def _docs_are_current_state(ctx):
    out = []
    for f in _md_in_scope(ctx):
        text = ctx.read(f)
        for i, line in enumerate(text.splitlines(), 1):
            if REVISION_ANNOTATION_RE.search(line):
                out.append(Finding(f'{f}:{i}',
                                    'carries an in-document revision '
                                    'annotation -- state what is true now; '
                                    'version control holds the history'))
    return out


# Files whose stated purpose IS a historical record -- docs-are-current-state's
# own exemption (d), "as-shipped/as-filed artifacts whose purpose is
# historical". spec/LOADER.md keeps prior measurement runs (v2, v3, v4) as a
# deliberate appendix, each headed "superseded by vN above" -- exactly the
# phrase this check exists to catch everywhere else. An earlier version of
# this check had no exemption list and would have fired on that correct,
# intentional usage; add a file here only with the same kind of stated
# reason, never to silence a real finding.
INLINE_LINEAGE_SKIP_FILES = {'spec/LOADER.md'}


def _is_historical_record(f):
    """True when f's own stated purpose is a historical record.

    Two ways to qualify. The hardcoded set above is one file that declares
    it in prose and nowhere a script can read. The general way is
    doc_lint's own `is_record_doc()` -- a `<!--record-doc-->` marker, a
    record-shaped filename, or a records directory -- which any repo can
    use and this check should honour rather than making every record
    document earn its own line here.

    2026-09-07: CHANGES_TO_TELL_ALEX.md is the case that forced the
    generalization. It is a dated log of what changed in each inherited
    practice, kept for one future conversation, and it carries the
    `<!--record-doc-->` marker on line 2. Retiring a practice meant marking
    an earlier dated entry in that same log as superseded by a later one --
    structurally identical to spec/LOADER.md's superseded measurement runs,
    and flagged for the same phrase. Rewording to dodge the regex would
    have been gaming the check; hardcoding a second filename would have
    left the third one to rediscover this.
    """
    if f in INLINE_LINEAGE_SKIP_FILES:
        return True
    try:
        return _doc_lint().is_record_doc(f)
    except NotApplicable:
        # doc_lint did not import. Fail toward reporting, never toward a
        # silent pass -- a missed exemption is a false finding a human
        # reads, a missed finding is one nobody ever sees.
        return False
INLINE_LINEAGE_RE = re.compile(
    r'\bsuccessor to\b|\bsupersede[sd]?\s+by\b|\bsuperseded\s+by\b'
    r'|\breplaces?\s+the\s+(?:older|previous|prior)\b', re.I)


@check('index-remembers-past', 'change',
       "a changed document does not carry inline lineage language naming "
       "what it replaced or what replaced it, since provenance belongs in "
       "the repository index, not annotated into the documents themselves",
       'the other half of the practice entirely: whether the INDEX actually '
       'carries the lineage row this check pushes the language out of. It '
       'only prevents the wrong home, never confirms there is a right one. '
       'Also blind to any file whose stated purpose is a historical record '
       'rather than a current-state document: the INLINE_LINEAGE_SKIP_FILES '
       'set (spec/LOADER.md, which keeps prior measurement runs as a '
       'deliberate, correct appendix) plus anything doc_lint calls a record '
       'doc -- a <!--record-doc--> marker, a record-shaped filename, or a '
       'records directory. A document that wrongly claims to be a record '
       'buys itself silence here, and nothing checks that claim.')
def _index_remembers_past(ctx):
    out = []
    for f in _md_in_scope(ctx):
        if _is_historical_record(f):
            continue
        cur = {(i, m.group(0)) for i, line in enumerate(ctx.read(f).splitlines(), 1)
               for m in INLINE_LINEAGE_RE.finditer(line)}
        base_text = ctx.read_base(f)
        base = {m.group(0).lower() for line in (base_text or '').splitlines()
                for m in INLINE_LINEAGE_RE.finditer(line)} if base_text else set()
        for i, phrase in sorted(cur):
            if phrase.lower() not in base:
                out.append(Finding(f'{f}:{i}',
                                    f'carries inline lineage language '
                                    f'("{phrase}") -- provenance belongs in '
                                    f'the repository index, not in the '
                                    f'document'))
    return out


TWO_CHECK_LEVELS_RE = re.compile(
    r'\*\*light check\*\*.{0,400}?\*\*deep check\*\*', re.S | re.I)



def _declared_base_branch(root):
    """The branch this repo's work is measured against, as DECLARED in
    precedent.json's `base_branch` -- not inferred from `origin/HEAD`.

    Those are two different questions with usually the same answer, which is
    why asking the wrong one survives so long. `origin/HEAD` answers "what
    does GitHub show first"; callers here mean "what lineage does this work
    belong to". They diverge the moment a repo pins its work to a branch
    that is not the configured default -- BestPractice's own
    `precedent-beta-v01` -- and then every inference is quietly wrong with
    nothing failing. Returns None when undeclared or unreadable, so callers
    fall back to the old inference rather than breaking (fail-gracefully).
    Enforced by precedent_check.py's `declared-base-branch`.
    """
    try:
        import json as _json, pathlib as _pathlib
        v = _json.loads((_pathlib.Path(root) / 'precedent.json')
                        .read_text(encoding='utf-8')).get('base_branch')
        return v if isinstance(v, str) and v.strip() else None
    except Exception:
        return None

def _published_default_branch():
    """origin's default branch ref, or None when there is no usable one."""
    declared = _declared_base_branch(ROOT)
    if declared and _git('rev-parse', '--verify', '--quiet',
                         f'origin/{declared}').returncode == 0:
        return f'origin/{declared}'
    head = _git('symbolic-ref', 'refs/remotes/origin/HEAD')
    if head.returncode == 0 and head.stdout.strip():
        return head.stdout.strip().replace('refs/remotes/', '', 1)
    for cand in ('origin/main', 'origin/master'):
        if _git('rev-parse', '--verify', '--quiet', cand).returncode == 0:
            return cand
    return None


@check('rename-updates-links', 'tree',
       'no tracked file still references a path this branch renamed away '
       'or deleted',
       'a reference that was already dead before this branch started, and '
       'a rename whose old path is too generic to search for safely (a '
       'bare `README.md`, a single path segment) -- those are skipped '
       'rather than guessed at. It also cannot see a reference built by '
       'string concatenation at runtime, and it deliberately says nothing '
       'about a file the repo received rather than wrote: a vendored tree, '
       'a materialized practice or check, or the generated loader block, '
       'each of which is overwritten by its own next sync. It also says '
       'nothing about a file the decommissioning registry exempts -- the record OF a deletion naming what went is not a reference left behind '
       'by one.')
def _rename_updates_links(ctx):
    base = _published_default_branch()
    if base is None:
        raise NotApplicable(
            'no published default branch to compare against (no origin, or '
            'origin/HEAD unset), so there is no way to tell which paths '
            'THIS branch renamed from ones that moved long ago')
    r = _git('diff', '--name-status', '--find-renames', f'{base}...HEAD')
    if r.returncode != 0:
        raise NotApplicable(f'could not diff against {base}')
    # A practice a PUBLIC repo withholds is a third state this check had no
    # way to see. It was not renamed and it was not deleted: it is published
    # in a private source and deliberately kept out of this tree, so a
    # document that links to it is not a stale reference to repoint -- there
    # is nothing here to repoint it at. Found 2026-09-07: closing a public
    # consumer's disclosure produced 26 such findings in one repo, six of
    # them inside a vendored tree nobody can edit there, and every one of
    # them unactionable. MANIFEST.json's `withheld` list records exactly
    # this, written by precedent_materialize.py.
    # Files this repo received rather than wrote (see the skip below).
    _vendored_engine = set()
    try:
        _em = json.loads(
            (ROOT / 'tools' / 'ENGINE_MANIFEST.json').read_text(encoding='utf-8'))
        _vendored_engine = {f"tools/{f}" for f in (_em.get('files') or [])}
    except (ValueError, OSError):
        pass

    withheld = set()
    # Materialized output is the same third state one level further out.
    # precedent_materialize.py DELETES AND REWRITES practices/ and
    # tools/checks/ from every declared source on every sync, so a reference
    # inside one of those files cannot be repointed in the consuming repo at
    # all -- an edit survives until the next `precedent_sync_views.py` run and
    # no longer. The reference belongs to whichever source wrote it, and so
    # does the fix. Attribution is by MANIFEST.json's own committed record
    # (which source produced each file), never by live resolution: a bare CI
    # checkout can reach universal and repo-local but never team or
    # individual, and "this source did not resolve here" is not evidence of
    # anything. Found 2026-09-07, a consumer renaming its content directory:
    # of eight findings, seven sat in an individual source's own practice
    # text, its check script and that check's test -- all of which use the
    # old directory name as the canonical EXAMPLE of a convention, none of
    # which points at anything in the consuming repo, and not one of which
    # that repo could fix.
    received = set()
    try:
        _m = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
        withheld = {f"practices/{slug}.md" for slug in (_m.get('withheld') or [])}
        _local = {s.get('name') for s in (_m.get('sources') or [])
                  if isinstance(s, dict) and s.get('level') == 'repo-local'}
        for _e in (_m.get('practices') or []):
            if isinstance(_e, dict) and _e.get('slug') \
                    and _e.get('source') not in _local:
                received.add(f"practices/{_e['slug']}.md")
        for _e in (_m.get('checks') or []):
            if isinstance(_e, dict) and _e.get('path') \
                    and _e.get('source') not in _local:
                received.add(_e['path'])
    except (ValueError, OSError):
        pass

    _retired_exempt = _decommissioning_record_exemptions()

    old_paths = []
    for line in r.stdout.splitlines():
        parts = line.split('\t')
        if not parts or not parts[0]:
            continue
        status = parts[0]
        if status.startswith('R') and len(parts) >= 3:
            old_paths.append((parts[1], parts[2]))
        elif status.startswith('D') and len(parts) >= 2:
            old_paths.append((parts[1], None))
    if not old_paths:
        raise NotApplicable('this branch renames or deletes no file, so '
                            'there is no reference to repoint')
    # A path with one segment is too generic to search for: `README.md`
    # appears in prose everywhere and means a different file in every
    # directory. Skipping those is why this reports what it skipped.
    searchable = [(o, n) for o, n in old_paths if '/' in o]
    skipped = len(old_paths) - len(searchable)
    out = []
    tracked = _git('ls-files').stdout.split()
    for old, new_path in searchable:
        for rel in tracked:
            if rel == new_path or rel == old:
                continue
            if old in withheld:
                continue      # withheld, not deleted -- see the note above
            # A file the consuming repo RECEIVED cannot be repointed there:
            # a mirrored tree and the vendored engine are copied wholesale
            # from a published commit, and an edit is overwritten by the next
            # refresh. The reference is upstream's, and so is the fix.
            #
            # THE VENDORED CATALOGUE IS THE THIRD SUCH TREE and this check did
            # not know it. The engine and the materialized tree were already
            # attributed from the committed manifest; the catalogue was
            # excluded by the literal 'process/upstream/', which is
            # INSTALL.md §1's layout only. A §0 consumer deleting one of its
            # OWN files got two findings inside Precedent's practice prose,
            # where the path named is correct upstream and where the consumer
            # can repoint nothing. Ask the engine (practice: durable-fix).
            if rel.startswith(_mirrored(ROOT)) or rel in _vendored_engine \
                    or rel in received or rel == DECOMMISSIONED_PATHS_REGISTRY \
                    or any(_exempt_matches(rel, e) for e in _retired_exempt):
                # The decommissioning registry names every path this repo has
                # deleted, on purpose (practice: decommission-deletes-files) --
                # it is the record OF the deletion, not a reference left
                # behind by one, so reading it as a stranded link would make
                # every decommissioning fail the moment it was recorded.
                #
                # And so is everything the registry's own `exempt_files`
                # names, which is the half this check was missing: the
                # migration record explaining the deletion, and the dated
                # backlog entry it closed, are the same kind of document as
                # the registry and were being flagged for doing their job.
                # See _decommissioning_record_exemptions() for the incident.
                continue
            f = ROOT / rel
            if not f.is_file():
                continue
            try:
                text = f.read_text(encoding='utf-8', errors='ignore')
            except OSError:
                continue
            in_generated = False
            for i, line in enumerate(text.splitlines(), 1):
                # The loader block is rewritten wholesale by build_views.py
                # from the practice sources, so a reference inside it is the
                # sources' to fix, exactly like the materialized files it is
                # summarising. Skipped as a REGION, not as a file: the
                # hand-written half of the same document must still be
                # repointed, and usually is the thing that most needs to be.
                if '<!-- BEGIN GENERATED: precedent-loader -->' in line:
                    in_generated = True
                elif '<!-- END GENERATED -->' in line:
                    in_generated = False
                    continue
                if in_generated:
                    continue
                if old in line:
                    where = f'renamed to {new_path}' if new_path else 'deleted'
                    out.append(Finding(
                        f'{rel}:{i}',
                        f'still references {old!r}, which this branch '
                        f'{where} -- repoint it in the same change, or the '
                        f'repository is broken at every commit in between'))
                    break
    if not out and skipped:
        print(f'  (rename-updates-links: {skipped} single-segment path(s) '
              f'skipped as too generic to search)')
    return out


DECOMMISSIONED_PATHS_REGISTRY = 'process/decommissioned_paths.json'


@check('decommission-deletes-files', 'tree',
       'every path this repo declared decommissioned is still absent, and '
       'every decommissioning carries the reason it happened',
       'the whole positive direction -- a deprecated file nobody has '
       'declared. Nothing here can tell a dead file from a live one, so '
       'this catches a decommissioning coming UNDONE (a vendored tree mirrored '
       'back over a deletion, a materialized directory rewritten from its '
       'source), never one that was never made. The audit that decides a '
       'path is safe to delete is tools/precedent_decommission.py, run by a '
       'person at the moment of decommissioning; this check is only the record '
       'holding afterwards.')
def _decommission_deletes_files(ctx):
    cfg_path = ROOT / DECOMMISSIONED_PATHS_REGISTRY
    if not cfg_path.is_file():
        raise NotApplicable(f'no {DECOMMISSIONED_PATHS_REGISTRY} -- this repo has '
                            f'decommissioned nothing, which is the correct '
                            f'state for a repo that has never '
                            f'decommissioned a mechanism')
    try:
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        return [Finding(DECOMMISSIONED_PATHS_REGISTRY, f'not valid JSON: {e}')]
    # Same guard, and the same reason, as migration-scrubs-vocabulary's:
    # a valid-JSON-wrong-shape config reaching `.get` below raises an
    # uncaught AttributeError that takes down every OTHER check in the run.
    if not isinstance(cfg, dict):
        return [Finding(DECOMMISSIONED_PATHS_REGISTRY,
                        f'must be a JSON object with a "decommissioned" list (e.g. '
                        f'{{"decommissioned": [{{"path": ..., "reason": ...}}]}}), '
                        f'not a {type(cfg).__name__}')]
    entries = cfg.get('decommissioned') or []
    if not isinstance(entries, list):
        return [Finding(DECOMMISSIONED_PATHS_REGISTRY,
                        f"'decommissioned' must be a JSON array of objects, not a "
                        f'{type(entries).__name__}')]
    if not entries:
        raise NotApplicable(f'{DECOMMISSIONED_PATHS_REGISTRY} declares no '
                            f'decommissioning -- nothing to hold')
    tracked = set(_git('ls-files').stdout.split())
    out = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict) or not e.get('path'):
            out.append(Finding(f'{DECOMMISSIONED_PATHS_REGISTRY}[{i}]',
                               'every entry needs a "path"'))
            continue
        rel = str(e['path']).rstrip('/')
        if not str(e.get('reason') or '').strip():
            # The reason is the only part history does not already hold.
            out.append(Finding(f'{DECOMMISSIONED_PATHS_REGISTRY}[{i}]',
                               f'{rel!r} was decommissioned with no reason recorded '
                               f'-- git history holds what the file was; '
                               f'only this holds why it went'))
        back = sorted(f for f in tracked
                      if f == rel or f.startswith(rel + '/'))
        if back:
            out.append(Finding(
                DECOMMISSIONED_PATHS_REGISTRY,
                f'{rel!r} is declared decommissioned but is tracked again '
                f'({len(back)} file(s), e.g. {back[0]}) -- a mirror or a '
                f'materialization has undone the deletion, or the '
                f'decommissioning should be withdrawn from this file on purpose'))
    return out


@check('two-check-levels', 'tree',
       'the session instructions name two fixed, distinct check levels '
       '("light check" / "deep check") and say which gates a commit versus '
       'a push',
       'whether those are the RIGHT two tools per level, or whether a '
       'session actually runs the one it names -- only that a repo-chosen '
       'pair of names exists, so "run the light check" and "run the deep '
       'check" are unambiguous requests rather than needing re-description '
       'every time.')
def _two_check_levels(ctx):
    name, text = _instructions_file()
    if not TWO_CHECK_LEVELS_RE.search(text):
        return [Finding(name, 'does not name a fixed "light check" / "deep '
                              'check" pair, so a session asked to run '
                              '"the check" has to re-derive what that '
                              'means every time')]
    return []


@check('routing-audit', 'tree',
       'tools/routing_audit.py exists, and tools/routing_audit_state.json '
       '(if present) has no rotation entry for a practice that is not '
       'currently active',
       'whether the audit is actually being RUN or a slice actually READ -- '
       'only that the tool exists and its own bookkeeping stays honest.')
def _routing_audit(ctx):
    tool = _tool_path('tools/routing_audit.py')
    if tool is None:
        return [Finding('tools/routing_audit.py',
                        "does not exist -- routing-audit.md names it as "
                        "this practice's implementation")]
    state_path = tool.parent / 'routing_audit_state.json'
    if not state_path.exists():
        return []
    try:
        state = json.loads(state_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as e:
        return [Finding(str(state_path.relative_to(ROOT)),
                        f'is not valid JSON ({e})')]
    # The catalogue this repo actually has: the materialized/authored
    # practices/ at the root, or -- in the classic vendoring layout -- the
    # vendored tree this tool was copied alongside. Reading only the first
    # made `active` empty in every classic install, so every rotation entry
    # in the state file read as stale bookkeeping for a retired practice.
    practices_dir = ROOT / 'practices'
    if not practices_dir.is_dir():
        practices_dir = tool.parent.parent / 'practices'
    active = set()
    for f in sorted(practices_dir.glob('*.md')):
        try:
            fm, _sections = sp._read_practice_file(f)
        except sp.PracticeFileError:
            continue
        if (fm.get('status', 'active') or 'active').strip().strip('"') == 'active':
            active.add(fm.get('slug', f.stem))
    return [Finding(str(state_path.relative_to(ROOT)),
                    f'records a rotation entry for {slug!r}, which is not '
                    f'an active practice -- stale bookkeeping left behind '
                    f'by a retired or renamed practice')
            for slug in state if slug not in active]


_LEDGER_MEMBER_DIRS = ('templates/harness/claude-code',
                       'templates/harness/codex', 'templates/harness/gemini-cli')


def _shallow_boundary_commits():
    """Commits git's OWN `.git/shallow` file records as grafted boundaries --
    ground truth, unlike `git rev-list --max-parents=0` (used below to
    exempt the repository's real root commit) or `git log --format=%P`:
    this repo's own AGENTS.md documents both of those as unreliable at
    exactly a shallow boundary -- a commit that genuinely has two parents
    can be silently reported as having none, and the exact boundary a
    shallow fetch lands on is not something a caller of this function
    controls or can predict (it depends on the fetch depth requested, the
    target being a merge commit rather than a single ref, and apparently
    on the git version doing the negotiating -- confirmed 2026-09-05: a
    genuinely reproduced CI failure on a real PR whose LEDGER.md row for
    the flagged commit already existed and matched byte-for-byte, on a
    git version this session's own environment could not install to
    compare directly). `.git/shallow` is git's own bookkeeping for exactly
    this fact and isn't subject to either unreliability -- reading it
    directly, instead of inferring shallowness indirectly, sidesteps the
    whole class of version- and negotiation-dependent surprise rather than
    chasing one more instance of it."""
    git_dir = _git('rev-parse', '--git-dir').stdout.strip()
    if not git_dir:
        return set()
    git_dir_path = pathlib.Path(git_dir)
    if not git_dir_path.is_absolute():
        git_dir_path = ROOT / git_dir_path
    shallow_path = git_dir_path / 'shallow'
    if not shallow_path.is_file():
        return set()
    return set(shallow_path.read_text(encoding='utf-8', errors='ignore').split())


# cite-the-incident, 2026-09-05: this check was wired into CI the same day
# it was written (deep-check.yml) and immediately found a real, pre-existing
# gap -- templates/harness/LEDGER.md was missing a row for f2078d6, the
# commit that created the claude-code/codex/gemini-cli family in the first
# place, five weeks before the ledger file existed. That gap is fixed
# (backfilled in dfe504d). Two more, separately real fixes followed:
# b16b141 made the root/inception exemption above shallow-clone-safe (reads
# .git/shallow directly, since `git rev-list --max-parents=0` can't be
# trusted on a shallow checkout -- see this file's AGENTS.md for the
# general gotcha), and 2a0fbe0 added `fetch-depth: 0` to deep-check.yml's
# checkout (a real, repo-wide gap independent of this check).
#
# ROOT-CAUSED 2026-09-06 -- and it was never a false positive. The finding
# was true of the tree CI was actually standing on. verify_harness.py (step
# 5) invoked a vendored `precedent_vendor_engine.py refresh <ROOT> --force`,
# and refresh() then ran `git checkout precedent-beta-v01` + `git pull` in
# the clone it was handed -- which in CI is the job's own workspace. So step
# 5 moved the workspace onto the base branch, and precedent_check.py (step 6)
# ran the BASE branch's tree, where templates/harness/LEDGER.md genuinely has
# no row for f2078d6. The same substitution explains every other symptom:
# the summary line CI printed was the base branch's own pre-advisory format,
# and the diagnostic prints never appeared because by step 6 the file was no
# longer the file they had been added to. `git status` stays clean throughout
# -- a branch checkout leaves no dirty file to notice -- which is why four
# independent content verifications all came back correct while the workspace
# stood on a different commit. Reproduced deterministically: run
# verify_harness.py and then precedent_check.py in one checkout and the
# second reports this violation; run precedent_check.py alone on the same
# commit and it is clean. Fixed upstream in 25546bc (refresh() materializes
# blobs and never checks the clone out, with a regression case that fails
# against the pre-fix engine) and here by vendoring from a throwaway clone.
# Full account:
# https://github.com/alex137/BestPractice/pull/110#issuecomment-5556343855
#
# So this check is ENFORCING again, as originally written: there was no
# platform mystery, and nothing left to except it from. The lesson worth
# keeping is diagnostic -- when a check's finding contradicts the tree you
# believe you are on, confirm WHICH COMMIT is actually checked out before
# concluding the check is wrong. Four rounds of content verification cannot
# distinguish a wrong answer from a right answer about a different tree.
@check('parallel-artifact-ledger', 'tree',
       '`templates/harness/LEDGER.md` exists, and every commit that touched '
       'a harness-adapter member (claude-code/, codex/, or gemini-cli/) has '
       'its hash referenced somewhere in the ledger',
       'whether a referenced row is actually CORRECT -- the right verdict '
       'per member, not a rubber-stamped one -- only that a row exists for '
       'every commit that changed a member, the "any marked date without a '
       'complete ledger row fails" half of the practice, added 2026-09-05 '
       'after a routing-audit run found the ledger itself had no audit. '
       'Enforcing; the 2026-09-05 advisory downgrade was lifted 2026-09-06 '
       'once the CI substitution above was root-caused.')
def _parallel_artifact_ledger(ctx):
    # The practice is generic -- ANY family of parallel artifacts -- but
    # this check knows exactly one family: this repo's own harness
    # adapters. A repo without those directories has no family for this
    # check to walk, which is not the same fact as "a ledger is missing":
    # every consuming repo reported a VIOLATION demanding a ledger for a
    # directory it does not have and should not have. Finding that repo's
    # OWN parallel-artifact families is not something a static check can
    # do, so it says so rather than guessing.
    if not any((ROOT / d).is_dir() for d in _LEDGER_MEMBER_DIRS):
        raise NotApplicable(
            'this repo has none of the harness-adapter directories this '
            'check knows how to walk (' + ', '.join(_LEDGER_MEMBER_DIRS) +
            '), so there is no parallel-artifact family here for it to '
            'ledger. A family of its own still needs one -- that half is '
            'a review judgment, not something this check can find')
    ledger_path = ROOT / 'templates' / 'harness' / 'LEDGER.md'
    if not ledger_path.exists():
        return [Finding('templates/harness/LEDGER.md',
                        'does not exist -- parallel-artifact-ledger.md '
                        'names a ledger table as this practice\'s Install')]
    ledger_text = ledger_path.read_text(encoding='utf-8', errors='ignore')
    # A repo's (or a test scratch copy's) root commit -- the tree coming
    # into existence, zero parents -- is inception, not "a change to any
    # member" the practice's Rule is about; exclude it, or every squashed-
    # history scratch copy and this repo's own real "Initial import" commit
    # would need a ledger row for simply existing. Also exclude whatever
    # git's OWN `.git/shallow` bookkeeping records as a grafted boundary --
    # see _shallow_boundary_commits()'s own docstring: on a shallow clone (a
    # CI checkout, most obviously) `--max-parents=0` cannot be trusted to
    # find every commit this check should treat as "can't verify, don't
    # guess" the same way it already treats a genuine root.
    roots = set(_git('rev-list', '--max-parents=0', 'HEAD').stdout.split())
    roots |= _shallow_boundary_commits()
    findings = []
    for member_dir in _LEDGER_MEMBER_DIRS:
        # `git log` is newest-first, so the LAST entry is this member
        # directory's own first commit -- the one that created it. A family
        # coming into existence is inception, not "a change to a member"
        # the practice's Rule is about: there is nothing for the other
        # members to have transferred from, because none of them existed
        # either. Exempted for the same reason the repository's own root
        # commit already is, one level down. Before this, f2078d6 -- the
        # 2026-07-20 commit that created all three harness adapters from
        # scratch, five weeks before the ledger file existed -- went
        # unflagged by every backfill pass until CI on an unrelated pull
        # request caught it, and had to be written into the ledger by hand
        # as a row saying, in effect, "no transfer verdict applicable".
        # (TODO.md item 18.)
        out = _git('log', '--no-merges', '--format=%H', '--', member_dir).stdout.split()
        inception = {out[-1]} if out else set()
        for full_hash in out:
            if full_hash in roots or full_hash in inception:
                continue
            if full_hash[:7] not in ledger_text and full_hash not in ledger_text:
                findings.append(Finding(
                    'templates/harness/LEDGER.md',
                    f'no row references {full_hash[:7]} ({member_dir}), a '
                    f'commit that changed a member of the harness-adapter '
                    f'family -- add a dated row with a per-member verdict'))

    # A commit ledgered TWICE is the collision this check could not see,
    # because "a row exists" is satisfied by two of them. 2026-09-10: two
    # sessions working in parallel each noticed 82572e7 had no row and each
    # backfilled one, in different places in the file, so git merged both
    # cleanly and the audit stayed green on a ledger carrying two verdicts
    # for one change -- which is exactly the state the practice's "one dated
    # row per change" exists to prevent, since a later reader cannot tell
    # which verdict was the considered one. (practice: convention-to-audit)
    #
    # Counted per ROW rather than per occurrence: a single row names its
    # commit twice by design, in the link text and the URL.
    for full_hash in {h for d in _LEDGER_MEMBER_DIRS
                      for h in _git('log', '--no-merges', '--format=%H',
                                    '--', d).stdout.split()}:
        # Only the row's own COMMIT CELL counts, not the whole line. A row
        # citing an earlier commit in its prose -- "same reason as
        # [`810a1dc`]'s row" -- is the ledger's own convention working, and
        # counting it made three correct rows read as three duplicates of
        # one change. Found 2026-09-11, red on precedent-beta-v01 against a
        # tree nobody had edited: a check firing on correct work, which
        # checkable-gets-checked says is worse than no check at all.
        rows = []
        for ln in ledger_text.splitlines():
            if not ln.startswith('|'):
                continue
            cells = ln.split('|')
            cell = cells[2] if len(cells) > 2 else ''
            if full_hash[:7] in cell or full_hash in cell:
                rows.append(ln)
        if len(rows) > 1:
            findings.append(Finding(
                'templates/harness/LEDGER.md',
                f'{len(rows)} rows reference {full_hash[:7]} -- one change '
                f'gets one dated row, so a reader can tell which transfer '
                f'verdict was the considered one; merge them'))

    return findings


@check('search-by-purpose', 'change',
       'a document carrying generated numbers is reachable from an index a '
       'reader actually consults',
       'whether anyone searched both vocabularies before starting. It '
       'enforces the durable half: the thing they would find exists and is '
       'indexed.')
def _search_by_purpose(ctx):
    dl = _doc_lint()
    wired = dl.wired_docs()
    if not wired:
        raise NotApplicable('no document is registered as carrying generated '
                            'numbers (tools/doc_sync.py PAIRS is empty), so '
                            'there is nothing whose findability can be checked')
    scope = set(ctx.changed)
    return [Finding(d, n) for d, n in dl.check_findability(wired) if d in scope]


def _tool_path(rel):
    """Resolve a repo-relative `tools/<name>` against the layout this repo
    actually has, or None.

    Two layouts, both real: the Precedent loader install (INSTALL.md
    section 0) puts the engine at `<repo>/tools/`, and the classic
    vendoring install (section 1) puts it at
    `<repo>/process/upstream/tools/`. Checks that shell out to a sibling
    tool assumed the first, so in a classic install `practice_audit.py`,
    `model_audit.py` and `doc_sync.py` were all sitting right there in
    `process/upstream/tools/` and their checks reported nothing --
    silently PASSING before _run() learned to refuse a missing script, and
    honestly but wrongly SKIPPING after. Neither is the truth: the tool is
    present and the check should run."""
    rel = str(rel).replace('\\', '/')
    name = rel.split('/')[-1]
    for cand in (ROOT / rel, _HERE_TOOLS / name,
                 ROOT / 'process' / 'upstream' / 'tools' / name):
        if cand.exists():
            return cand
    return None


def _run(script, *args):
    """Run one of this repo's own audit scripts, refusing loudly if it is
    not here.

    A missing script is NOT a clean run. Python exits 2 with "can't open
    file" on stderr, which carries no `FAIL:`, no `SCRUB:` and no `NOT
    APPLICABLE` -- so every caller below filtered zero lines out of it and
    returned no findings, i.e. PASS. Three enforced practices
    (scrub-gate, practice-export-loop, scripts-assert-properties) reported
    a clean pass in every consuming repo, because the tools they run are
    not in the vendored engine and nothing noticed. That is precisely the
    "a scan with an empty input set printing OK" failure this module's own
    docstring says it exists to prevent, and this module was doing it."""
    path = _tool_path(script)
    if path is None:
        raise NotApplicable(
            f'{script} is in neither this repo\'s own tools/ nor a vendored '
            f'process/upstream/tools/, so this check has nothing to run. It '
            f'is not part of the vendored engine '
            f'(precedent_vendor_engine.py\'s CONSUMER_ENGINE_FILES) -- copy '
            f'it from Precedent if this repo needs the practice enforced')
    r = subprocess.run([sys.executable, str(path), *args],
                       cwd=str(ROOT), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def _doc_sync_findings():
    code, out = _run('tools/doc_sync.py')
    if 'NOT APPLICABLE' in out:
        raise NotApplicable(out.strip().splitlines()[-1])
    restated, other = [], []
    for line in out.splitlines():
        if 'FAIL' not in line and 'DRIFT' not in line:
            continue
        (restated if 'restates' in line else other).append(line.strip())
    return code, restated, other


@check('computed-numbers-in-scripts', 'tree',
       'every generated block in a document matches what its script emits, '
       'is registered, and its document names the scripts that feed it',
       'a computed number that was never wrapped in a block at all. It gates '
       'the blocks that exist; it cannot see a figure nobody declared.')
def _computed_numbers_in_scripts(ctx):
    try:
        import doc_sync
    except Exception as e:
        raise NotApplicable(f'tools/doc_sync.py did not import: {e}')
    if not doc_sync.PAIRS:
        raise NotApplicable('tools/doc_sync.py registers no (document, block, '
                            'script) pair, so no generated block is under a '
                            'gate here. This is a gap, not a pass')
    _code, _restated, other = _doc_sync_findings()
    return [Finding('', line) for line in other]


@check('docs-track-models', 'tree',
       'a figure a script declares it owns is not hand-typed into the prose '
       'around its generated block',
       'a restatement of a figure the script has not declared it owns. Its '
       'reach is exactly owned_figures().')
def _docs_track_models(ctx):
    try:
        import doc_sync
    except Exception as e:
        raise NotApplicable(f'tools/doc_sync.py did not import: {e}')
    try:
        owned = [f for _d, _n, s in doc_sync.PAIRS
                 for f in doc_sync.owned_figures(s)]
    except doc_sync.OwnedFiguresUnavailable as e:
        # A vendored copy carries UPSTREAM's PAIRS, naming scripts this repo
        # never vendored -- so the import genuinely cannot happen here, and
        # that is a not-configured-yet fact about the copy, not a defect in
        # this repo. Distinct from an import that fails where the script IS
        # present, which doc_sync itself fails the gate on.
        raise NotApplicable(
            f'{e} -- if this is a vendored copy, replace PAIRS in '
            f'tools/doc_sync.py with this repo\'s own pairs')
    if not owned:
        raise NotApplicable('no script declares an owned figure '
                            '(owned_figures()), so no restatement can be '
                            'detected. This is a gap, not a pass')
    _code, restated, _other = _doc_sync_findings()
    return [Finding('', line) for line in restated]


@check('scrub-gate', 'tree',
       'every text file in a vendored tree destined for another repo is clean '
       'against that tree\'s blocklist, at all times',
       'a private word nobody put on the blocklist. It is a word list, and a '
       'word list only sees the words somebody thought of.')
def _scrub_gate(ctx):
    code, out = _run('tools/practice_audit.py')
    if 'NOT APPLICABLE' in out:
        raise NotApplicable(out.strip().splitlines()[-1])
    if 'scrub' in out and 'skipped' in out:
        raise NotApplicable('practice_audit skipped the scrub: no blocklist')
    return [Finding('', l.strip()) for l in out.splitlines() if 'SCRUB:' in l]


@check('practice-export-loop', 'tree',
       'every manifest entry marked synced still matches its baseline — a '
       'local improvement to a vendored file has been exported, not absorbed',
       'an improvement to a practice that never touched a vendored file. The '
       'manifest can only see what it tracks.')
def _practice_export_loop(ctx):
    code, out = _run('tools/practice_audit.py')
    if 'NOT APPLICABLE' in out:
        raise NotApplicable(out.strip().splitlines()[-1])
    return [Finding('', l.strip()) for l in out.splitlines()
            if l.startswith('FAIL:') and 'SCRUB:' not in l]


@check('scripts-assert-properties', 'tree',
       'every instrumented script asserts its own properties, and every '
       'figure it recites from a source document still matches that document',
       'a script nobody added to INSTRUMENTED. Instrumentation is deliberate '
       'and per-script, so the check is exactly as wide as that list.')
def _scripts_assert_properties(ctx):
    code, out = _run('tools/model_audit.py')
    if 'NOT APPLICABLE' in out:
        raise NotApplicable(out.strip().splitlines()[-1])
    # model_audit.py itself treats "no self_check() or ANCHORS" as a WARN,
    # not a FAIL -- its own exit code is unaffected by warnings, by design,
    # since it is meant to run standalone without erroring on an
    # intentionally-uninstrumented script list. But that WARN line is
    # reporting exactly what this practice's Rule forbids: "every
    # instrumented script asserts its own properties." Filtering for only
    # `FAIL:` here silently passed a script explicitly listed in
    # INSTRUMENTED with zero assertions -- the practice's own Install
    # section calls this out by name ("keep the instrumented list explicit
    # so the audit can warn when a listed script has no assertions") and the
    # enforced gate must actually treat that warning as the violation it is,
    # not discard it.
    #
    # Matching is on the SPECIFIC warning text ("no self_check() or
    # ANCHORS"), not a bare `WARN:` prefix. model_audit.py currently emits
    # only this one kind of warning, so the two were equivalent -- but a
    # bare-prefix match would misclassify any future advisory WARN (e.g. "1
    # anchor instrumented, consider adding more") as a Rule violation just
    # because it happens to share the WARN: label. The Rule is about a
    # script asserting its own properties at all, which is exactly what
    # this one warning text reports; FAIL: stays a broad match, since every
    # kind of failure model_audit.py can emit already is a genuine assertion
    # or import failure by that script's own design, not an advisory note.
    return [Finding('', l.strip()) for l in out.splitlines()
            if l.startswith('FAIL:')
            or (l.startswith('WARN:') and 'no self_check() or ANCHORS' in l)]


_CODE_CITE_SLUG_RE = re.compile(r'\bpractice:\s*([a-z][a-z0-9-]*)')
_CODE_CITE_PAREN_SPAN_RE = re.compile(r'\(([^()]*)\)')
_CODE_CITE_HASH_COMMENT_RE = re.compile(r'#([^\n]*)')
# The parenthetical form matters: several existing citations are narrative,
# inside a module's own triple-quoted docstring ("the mechanism (practice:
# one-formatter-per-quantity) requires"), which is just as
# machine-checkable and just as much "right at the point of implementation"
# as a bare `#` comment. Requiring SOME anchor -- a `#` comment or a
# parenthetical -- is not cosmetic: an earlier, looser version of this
# pattern (bare "practice" + colon, no comment marker or parens) matched
# ordinary prose reading "Each PRACTICE_LABEL: the **rule**, **why**..."
# as a citation to a practice literally named "the"
# (tools/split_practices.py's own docstring, PRACTICE_LABEL standing in
# here for the actual word so THIS comment doesn't retrigger the very
# false positive it describes -- still unparenthesized prose today, which
# is why the anchor stays required rather than being dropped as "too
# strict").
#
# A 2026-09-03 deep-check audit found the FIRST version of this anchor
# requirement too strict in the other direction: requiring the slug to be
# immediately followed by `)` missed six real, live citations already in
# this codebase -- a trailing clause before the close-paren
# (`(practice: layered-practice-packs: "repo-local ... never leave")`,
# itself split across two physical lines by its own paragraph wrap), and
# more than one slug inside one parenthetical
# (`(practice: practice-export-loop; practice: scrub-gate; practice:
# layered-practice-packs)`), which a single `re.search()` per line could
# not have found either way -- only the first match on a line was ever
# checked. _iter_code_citations below scans the WHOLE FILE'S text (not
# line by line, so a citation split across a wrapped paragraph is not
# invisible) and every occurrence within a `#` comment or a parenthetical
# span (not just the first), while keeping the same anchor requirement
# that keeps ordinary prose from being read as a citation.


def _iter_code_citations(text):
    """Yield (line_no, slug) for every `practice: SLUG` citation in `text`,
    per the two forms this practice recognizes. A `#` comment never spans
    lines in Python, so that half is still naturally line-scoped; a
    parenthetical can (see above), so it is matched across the whole text
    with `re.finditer`, then the line number is recovered from the match's
    character offset. The same citation can never match twice (each
    character range belongs to exactly one comment, or to the innermost
    unnested parenthetical containing it), so no dedup is needed."""
    for m in _CODE_CITE_HASH_COMMENT_RE.finditer(text):
        line_no = text.count('\n', 0, m.start()) + 1
        for cm in _CODE_CITE_SLUG_RE.finditer(m.group(1)):
            yield line_no, cm.group(1)
    for m in _CODE_CITE_PAREN_SPAN_RE.finditer(text):
        for cm in _CODE_CITE_SLUG_RE.finditer(m.group(1)):
            line_no = text.count('\n', 0, m.start(1) + cm.start()) + 1
            yield line_no, cm.group(1)
CODE_PRACTICE_NUMBER_RE = re.compile(r'\bpractice\s+(\d+)\b')
# The exact anti-pattern this practice exists to end: citing by POSITION
# rather than by the slug that survives a renumbering. Flagged even with no
# slug anywhere nearby, so a citation can never quietly regress back to this
# form once fixed.
# tools/verify_harness.py plants both patterns as fixture text (to test this
# very check), so scanning it for real citations would fail on its own
# planted fixtures every time -- the one file excluded, and the reason is
# mechanical, not a carve-out for its content.
CODE_CITE_SKIP_FILES = {'verify_harness.py'}


@check('code-cites-practice', 'tree',
       'a `practice: SLUG` citation in tools/**/*.py names a real, active '
       'practice -- never a typo, a deleted file, one since retired, or a '
       'position number instead of a slug',
       'This only checks citations that EXIST -- it has no way to notice code '
       'that implements a practice but was never given a citation in the '
       'first place, since that requires knowing WHY a line of code exists, '
       'not just reading what it says. The forward direction (does this code '
       'need a citation?) stays a review judgment; this only keeps citations '
       'that already exist from silently going stale, which is exactly what '
       "happened to source_practice_number's old position-based citations "
       "(three tool comments cited a stale practice NUMBER after a "
       "renumbering -- fixed once by hand in 2026-08; this check is what "
       "makes sure that fix never has to happen by hand again). It is also "
       "blind to an UNANCHORED mention -- a bare `(some-slug)` or "
       "`# some-slug` with no `practice:` before it -- which this practice's "
       "own Rule already forbids as \"a bare mention of the practice's "
       "subject with no way to look it up\", and which no scanner can tell "
       "from ordinary hyphenated prose. That blindness is not theoretical: "
       "five citations of `fail-gracefully` sit in this repo's own tools/ in "
       "exactly that form, naming a slug that resolves nowhere here, and the "
       "anchored form would make this check FAIL rather than fix them, "
       "because the practice lives in a private team set. See TODO.md's "
       "`universal-code-cites-team-slug`.")
def _code_cites_practice(ctx):
    known = {}
    for d in ((ROOT / 'practices'), (ROOT / 'local' / 'practices')):
        for f in sorted(d.glob('*.md')):
            try:
                fm, _sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            known[fm['slug']] = fm.get('status')
            # A slug some IN-FORCE practice declares it overrides is
            # superseded, not missing. In a consuming repo a higher-precedence
            # source can replace a universal practice under a different name
            # -- precedent-team-maintainers' `rule-links` overrides the
            # universal `doc-references-are-links` -- and the overridden slug
            # then resolves to no file at all. The universal engine code that
            # cites it is still correct about why it exists; the rule simply
            # arrives under another name here. Reported as a typo or a
            # deletion (2026-09-06, in a real four-source consumer) it is
            # unfixable from the consuming repo: the citation is in vendored
            # code, and the "missing" practice is deliberately absent.
            ov = (fm.get('overrides') or 'null').strip().strip('"').strip("'")
            if ov and ov != 'null':
                known.setdefault(ov, fm.get('status'))
    # A VENDORED engine file's citations are upstream's, not this repo's.
    # In a consuming repo, tools/ IS the vendored engine, and its catalogue
    # under process/upstream/ tracks BestPractice's default branch -- so an
    # engine file refreshed from precedent-beta-v01 can legitimately cite a
    # practice the consumer's own catalogue does not carry yet. That is not
    # a typo and not a deletion; it is version skew, and it is unfixable
    # from the consuming repo: editing vendored code to silence it is the
    # one thing precedent_vendor_engine.py refuses outright. Reported for
    # real on 2026-09-06, in the first consumer refresh that pulled
    # precedent_resolve.py's `practice: source-naming` citations into a
    # repo whose catalogue predated the practice by hours.
    #
    # The exemption is deliberately keyed on ENGINE_MANIFEST.json rather
    # than on a filename list: BestPractice itself has no manifest -- it is
    # the origin, not a vendoree -- so the check keeps its full strength in
    # the one repo where these citations can actually be fixed. It is the
    # same accommodation the `overrides:` case above already makes, for the
    # same reason, in the other direction.
    vendored = set()
    manifest = ROOT / 'tools' / 'ENGINE_MANIFEST.json'
    if manifest.is_file():
        try:
            vendored = set(json.loads(manifest.read_text(encoding='utf-8'))
                           .get('files', []))
        except (json.JSONDecodeError, OSError):
            vendored = set()

    out = []
    for f in sorted((ROOT / 'tools').glob('*.py')):
        if f.name in CODE_CITE_SKIP_FILES or f.name in vendored:
            continue
        text = f.read_text(encoding='utf-8', errors='ignore')
        seen = set()
        for i, slug in _iter_code_citations(text):
            # A citation inside a `#` comment that itself sits inside a
            # multi-line parenthetical is found by both halves of
            # _iter_code_citations -- once per comment line, once as part
            # of the larger parenthetical span. Same (line, slug), reported
            # once.
            if (i, slug) in seen:
                continue
            seen.add((i, slug))
            status = known.get(slug)
            if status is None:
                out.append(Finding(f'tools/{f.name}:{i}',
                                    f'cites {slug!r}, which is not a real '
                                    f'practice slug (typo, or the file was '
                                    f'deleted instead of retired)'))
            elif status != 'active':
                out.append(Finding(f'tools/{f.name}:{i}',
                                    f'cites {slug!r}, which is status: '
                                    f'{status!r} -- this code implements a '
                                    f'practice that no longer is one; update '
                                    f'or remove it, or reconsider the '
                                    f'retirement'))
        for i, line in enumerate(text.splitlines(), 1):
            mn = CODE_PRACTICE_NUMBER_RE.search(line)
            if mn:
                out.append(Finding(f'tools/{f.name}:{i}',
                                    f'cites practice {mn.group(1)} by position '
                                    f'number, not by slug -- this is exactly '
                                    f'the citation form that already drifted '
                                    f'once after a renumbering; use `practice: '
                                    f'SLUG` instead'))
    return out


# A retired term is a NAME, so it matches at name boundaries -- not as a
# substring of a longer, current one. A plain `term in line` reported
# `voice_pack_sync.py` three times in a real consuming repo (2026-09-06) for
# carrying the retired term `pack_sync`: a live tool that syncs a voice pack,
# named years after and unrelated to the personal-pack sync that was retired.
# There is no way to satisfy that finding except by renaming a current file
# or exempting the document that mentions it, and both are worse than the
# collision. `_` and `-` count as name characters, so `pack_sync` no longer
# matches inside `voice_pack_sync` while `personal-pack-sync` still matches
# on its own.
@functools.lru_cache(maxsize=None)
def _vendored_engine_files():
    """Paths tools/ENGINE_MANIFEST.json records as vendored engine code.

    A consuming repo does not author these and cannot edit them: the next
    `precedent_vendor_engine.py refresh` overwrites whatever it changed.
    Reporting a finding inside one is unactionable -- 2026-09-06, seeding a
    real consumer's engine through the sanctioned tool immediately produced
    retired-vocabulary findings against the engine's own source code,
    including the comment in this very file explaining the voice_pack_sync
    collision.
    """
    manifest = (ROOT / 'tools').joinpath('ENGINE_MANIFEST.json')
    if not manifest.is_file():
        return frozenset()
    try:
        m = json.loads(manifest.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return frozenset()
    names = m.get('files') or []
    return frozenset([f'tools/{n}' for n in names] + ['tools/ENGINE_MANIFEST.json'])


@functools.lru_cache(maxsize=None)
def _retired_term_re(term):
    return re.compile(r'(?<![\w-])' + re.escape(term) + r'(?![\w-])')


RETIRED_VOCAB_CONFIG = 'process/retired_vocabulary.json'
# tools/verify_harness.py plants retired-term fixture text (to test this
# very check) inside its own source, so scanning it for real violations
# would fail on its own planted fixtures every time it runs against a copy
# of this repo -- the one file excluded, mechanically, not a content carve-out.
RETIRED_VOCAB_SKIP_FILES = {'tools/verify_harness.py'}


def _exempt_matches(rel, exempt_entry):
    """True if `rel` (a POSIX-relative path) is covered by one
    `exempt_files` entry. An entry ending in `/` is a DIRECTORY exemption --
    `rel` matches if it equals that directory or sits under it; anything
    else is an exact file match, unchanged from before this existed."""
    if exempt_entry.endswith('/'):
        return rel == exempt_entry.rstrip('/') or rel.startswith(exempt_entry)
    return rel == exempt_entry


def _decommissioning_record_exemptions():
    """-> the `exempt_files` list from the decommissioning registry, or [].

    THE SAME LIST, FOR THE SAME REASON, READ BY ONE MORE CHECK. A repo that
    retires a mechanism writes two things: the registry saying what went, and
    a record saying why. `decommission-deletes-files` and
    `migration-scrubs-vocabulary` both already read this list; that the
    registry FILE ITSELF was hard-coded into rename-updates-links, and
    nothing else was, is how the gap stayed invisible -- the one file the
    author happened to be looking at got covered and the category did not.

    2026-09-07, a real migration: retiring a vendored practice pack produced
    four findings, and three were the record OF the deletion being read as a
    reference left behind BY one -- a migration record's own "what was
    deleted" table, and a closed, dated backlog entry quoting the notice that
    prompted it. Neither can be repointed at anything: naming the dead path
    is the entire content. The fourth was a genuine stranded reference in a
    merge runbook, which is the finding this check exists for and which the
    three false ones were burying.

    Deliberately NOT a blanket exemption for any file mentioning a retired
    path. The list is written by a person at the moment of retirement,
    through tools/precedent_decommission.py, which refuses while any
    undeclared reference remains -- so an entry here is somebody's stated
    reason, reviewable in the same diff, not a wildcard.
    """
    try:
        cfg = json.loads(
            (ROOT / DECOMMISSIONED_PATHS_REGISTRY).read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return []
    ex = cfg.get('exempt_files')
    return ex if isinstance(ex, list) else []


# The old pack mechanism's own marker file. layered-practice-packs' Install
# section defines the pre-migration shape: the tree at `process/<pack>/`,
# declared by `process/manifest_<pack>.json`. That manifest name belongs to
# nothing else, which is what makes a leftover detectable without the repo
# having to declare anything.
OLD_PACK_MANIFEST_GLOB = 'manifest_*.json'


def _leftover_old_packs():
    """-> [(manifest_rel, tree_rel or None)] for a repo that MIGRATED and
    still carries the old pack mechanism.

    THE POINT IS THAT THIS NEEDS NO DECLARATION. Both existing retirement
    checks are opt-in: migration-scrubs-vocabulary fires only once a repo
    writes retired_vocabulary.json, and decommission-deletes-files only once
    it records a retirement in decommissioned_paths.json. A repo that migrated
    WITHOUT running spec/MIGRATING_EXISTING_INSTALLS.md's step 5 declares
    neither, so both stay silent and the leftover tree sits there
    indefinitely -- which is exactly the state Morgan asked about on
    2026-09-07 ("I already migrated a bunch, so even if it was migrated and
    that still exists, it should still be deleted"). Nothing was watching
    for it.

    Scoped to a repo that has ALREADY migrated (a precedent.json at the
    root). The pack mechanism is still supported for a repo that has not --
    that document's own "When this applies" section says so in as many
    words, and firing there would be telling a working install it is broken.
    """
    if not (ROOT / 'precedent.json').is_file():
        return []
    proc = ROOT / 'process'
    if not proc.is_dir():
        return []
    out = []
    for man in sorted(proc.glob(OLD_PACK_MANIFEST_GLOB)):
        # A pack manifest may name its tree; fall back to the conventional
        # `process/<pack>/` derived from the manifest's own suffix.
        tree = None
        try:
            data = json.loads(man.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                if data.get('kept_after_migration'):
                    continue          # a declared, reasoned keep -- see below
                tree = ((data.get('upstream') or {}).get('path')
                        if isinstance(data.get('upstream'), dict) else None)
        except (ValueError, OSError):
            pass
        if not tree:
            guess = proc / man.stem.replace('manifest_', '', 1)
            tree = guess.relative_to(ROOT).as_posix() if guess.is_dir() else None
        out.append((man.relative_to(ROOT).as_posix(), tree))
    return out


@check('migration-scrubs-vocabulary', 'tree',
       "a migrated repo carries no leftover pre-migration practice pack "
       "(process/manifest_*.json and its tree), and -- where the repo has "
       "declared process/retired_vocabulary.json -- none of its listed terms "
       "outside the declared exempt files/directories",
       "the SECOND half is opt-in: the terms themselves (a specific old "
       "repo's name, a retired secret) are never something BestPractice "
       "could know in advance, so a repo that has declared no config is not "
       "scanned for words at all. The pack half needs no declaration but is "
       "scoped to a repo that has already migrated (a precedent.json at the "
       "root) -- the old pack mechanism is still supported for one that has "
       "not, and firing there would call a working install broken. Neither "
       "half can tell whether the pack's CONTENT actually reached a "
       "Precedent source: it sees that the tree is still here, never "
       "whether deleting it would lose a rule. process/upstream/ is always "
       "excluded, vendored content never being this repo's own migration to "
       "finish.")
def _migration_scrubs_vocabulary(ctx):
    leftover = [
        Finding(man,
                f'is the pre-migration practice-pack mechanism, in a repo '
                f'that has already migrated to the Precedent loader'
                + (f' (its tree is still at {tree}/)' if tree else '')
                + '. A pack\'s rules live in a team or individual source '
                  'now, so the tree is a second, unsynced copy of rules '
                  'nobody reads. Retire it through the audit rather than by '
                  'hand: `python3 tools/precedent_decommission.py '
                  + (f'{tree} {man}' if tree else man)
                  + '` reports every file still referencing it and refuses '
                    'while any remain; then re-run with --reason "..." '
                    '--apply. If this pack is deliberately kept -- its '
                    'upstream never split into Precedent sources -- record '
                    'why with a "kept_after_migration" key in the manifest '
                    'and this stops asking.')
        for man, tree in _leftover_old_packs()]

    cfg_path = ROOT / RETIRED_VOCAB_CONFIG
    if not cfg_path.is_file():
        if leftover:
            return leftover
        raise NotApplicable(f'no {RETIRED_VOCAB_CONFIG} -- this repo has not '
                            f'declared any retired vocabulary to scrub for, '
                            f'and carries no leftover pre-migration pack')
    try:
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        return leftover + [Finding(RETIRED_VOCAB_CONFIG, f'not valid JSON: {e}')]
    if not isinstance(cfg, dict):
        # Valid JSON, wrong shape (e.g. a bare `["OldName"]` array where a
        # `{"terms": [...]}` object belongs) used to reach `cfg.get(...)`
        # below and raise an uncaught AttributeError, taking down every
        # OTHER check in the same run with it (found in a 2026-09-03
        # deep-check audit) -- a malformed config is exactly the kind of
        # thing this check exists to catch, not crash on.
        return leftover + [Finding(RETIRED_VOCAB_CONFIG,
                        f'must be a JSON object with a "terms" list (e.g. '
                        f'{{"terms": [...], "exempt_files": [...]}}), not a '
                        f'{type(cfg).__name__}')]
    terms = cfg.get('terms') or []
    exempt_files = cfg.get('exempt_files') or []
    if not isinstance(terms, list) or not isinstance(exempt_files, list):
        bad = 'terms' if not isinstance(terms, list) else 'exempt_files'
        return leftover + [Finding(RETIRED_VOCAB_CONFIG,
                        f'{bad!r} must be a JSON array of strings, not a '
                        f'{type(cfg[bad]).__name__}')]
    if not terms:
        if leftover:
            return leftover
        raise NotApplicable(f'{RETIRED_VOCAB_CONFIG} declares no terms -- '
                            f'nothing to scrub for')
    # A directory exemption (an exempt_files entry ending in `/`) exists for
    # exactly one reason: a MATERIALIZED, regenerated directory (this repo's
    # own practices/, filled in by precedent_materialize.py on every
    # precedent_sync_views.py run) can legitimately hold OTHER repos' own
    # content -- another source's own practice file citing ITS OWN
    # provenance, say -- that happens to share a literal substring with a
    # term this repo's migration is scrubbing for its own reasons. That
    # content isn't this repo's own migration to finish, the same reasoning
    # that already exempts process/upstream/ below, and a materialized
    # directory's file list changes on every sync, so hand-listing it
    # file-by-file in exempt_files would go stale the next time a slug is
    # added or dropped. Found for real, migrating a dependent repo
    # (2026-09-03): 'RepoPersonalPreferences' collided with a team-source
    # practice's own approved_by provenance, and 'PERSONAL_PACK_TOKEN'
    # collided with this file's own migration-scrubs-vocabulary.md Story
    # section, which uses that string as ITS illustrative example -- both
    # forced dropping otherwise-real retired terms rather than exempting the
    # one directory they were colliding in.
    exempt_files = [RETIRED_VOCAB_CONFIG] + exempt_files
    out = list(leftover)
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = pathlib.Path(dirpath).relative_to(ROOT).as_posix()
        rel_dir = '' if rel_dir == '.' else rel_dir
        # Prune .git and the vendored copy before descending -- .git is
        # never this repo's own content, and process/upstream/ is a
        # byte-identical mirror of a DIFFERENT repo, never hand-edited
        # regardless of what it happens to still say.
        dirnames[:] = [d for d in dirnames
                       if (f'{rel_dir}/{d}' if rel_dir else d)
                       not in ('.git', 'process/upstream')]
        for name in filenames:
            rel = f'{rel_dir}/{name}' if rel_dir else name
            if rel in RETIRED_VOCAB_SKIP_FILES:
                continue
            if any(_exempt_matches(rel, e) for e in exempt_files):
                continue
            if rel in _vendored_engine_files():
                continue
            try:
                text = (ROOT / rel).read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                for term in terms:
                    if _retired_term_re(term).search(line):
                        out.append(Finding(f'{rel}:{i}',
                                            f'still carries retired term '
                                            f'{term!r} -- scrub it, or add '
                                            f'this file (or its directory, '
                                            f'trailing "/") to exempt_files '
                                            f'if it is genuinely a historical '
                                            f'record or materialized '
                                            f'third-party content'))
    return sorted(out, key=lambda f: f.where)


# practice: open-item-disposition -- the grammar of the disposition line, so
# that "an item with no disposition is `wait`" can be relied on. A malformed
# line is the dangerous case, not a missing one: absence is a defined state
# (quiet), while `**Disposition:** parkd` reads as parked to a person
# skimming and as nothing at all to a session grepping for the word.
DISPOSITION_VALUES = ('parked', 'wait', 'ask')
DISPOSITION_RE = re.compile(
    r'^[ \t]*\*\*Disposition:\*\*[ \t]*'
    r'(?P<value>[^\s(]*)[ \t]*'
    r'(?:\((?P<stamp>[^)]*)\))?', re.M)
DISPOSITION_STAMP_RE = re.compile(r'^(?P<date>\d{4}-\d{2}-\d{2}),[ \t]*(?P<who>\S.*)$')
# Mirrors the practice's own applies_to. Kept as a literal rather than read
# out of the practice file: a check that derives its own scope from the
# document it is checking cannot report that the two disagree.
DISPOSITION_FILE_GLOBS = ('**/TODO.md', 'templates/TODO.md.template')


@check('open-item-disposition', 'tree',
       'every `**Disposition:` line in a TODO file names one of the three '
       'dispositions, and a `parked` or `ask` line records the date it was '
       'set and who set it',
       'whether a disposition is HONOURED -- nothing mechanical can see a '
       'session raising a parked item in chat, which is the behaviour the '
       'practice is actually about. It also cannot tell a correct `wait` '
       '(the default, written as nothing) from an item whose disposition '
       'nobody has ever considered: those are the same text by design, '
       'because the alternative was backfilling 52 items to say "quiet".')
def _open_item_disposition(ctx):
    # Resolved without precedent_paths: this module is copied ALONE into
    # fixtures that carry no sibling tools (the source-check harness builds
    # exactly that), so a module-level import of a neighbour takes those
    # fixtures down with a ModuleNotFoundError that reads as a broken check.
    # Both globs here are simple enough to resolve directly -- "**/x" is a
    # basename match, anything else is an exact path.
    files = []
    for glob in DISPOSITION_FILE_GLOBS:
        if glob.startswith('**/'):
            found = [p.relative_to(ROOT).as_posix()
                     for p in sorted(ROOT.rglob(glob[3:]))]
        else:
            found = [glob] if (ROOT / glob).is_file() else []
        for rel in found:
            # _mirrored() guards its own import, so the fixture-safety
            # note above still holds: copied alone, it falls back.
            if rel.split('/')[0] == '.git' or rel.startswith(_mirrored(ROOT)):
                continue
            if rel not in files:
                files.append(rel)
    if not files:
        raise NotApplicable('this repository has no TODO file to check')

    out = []
    for rel in sorted(files):
        try:
            text = (ROOT / rel).read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError) as e:
            out.append(Finding(rel, f'could not be read ({e})'))
            continue
        for m in DISPOSITION_RE.finditer(text):
            line_no = text.count('\n', 0, m.start()) + 1
            where = f'{rel}:{line_no}'
            value, stamp = m.group('value'), m.group('stamp')
            if value not in DISPOSITION_VALUES:
                out.append(Finding(where, f'disposition {value!r} is not one of '
                                          f'{", ".join(DISPOSITION_VALUES)}'))
                continue
            if value == 'wait':
                continue
            if stamp is None:
                out.append(Finding(where, f'{value!r} carries no "(YYYY-MM-DD, who)" '
                                          f'-- a disposition nobody owns is the '
                                          f'silence this practice replaces'))
                continue
            if not DISPOSITION_STAMP_RE.match(stamp.strip()):
                out.append(Finding(where, f'{value!r} stamp {stamp.strip()!r} is not '
                                          f'"YYYY-MM-DD, who"'))
    return out


# practice: decision-strength -- the grammar of the strength mark, so that
# "unmarked means unknown" stays a reliable reading. A malformed or invented
# value is the dangerous case: `strength: strong` reads as an endorsement to
# a person skimming and as nothing at all to a session looking for one of
# the two defined words. Absence is never a finding -- an unmarked approval
# is legal on purpose, in every source, forever, because the alternative was
# backfilling a catalogue of approvals by guessing at somebody's state of
# mind months after the fact.
STRENGTH_VALUES = ('decided', 'assented')
STRENGTH_FM_RE = re.compile(r'^strength:[ \t]*(?P<value>.*?)[ \t]*$', re.M)
STRENGTH_PROSE_RE = re.compile(
    r'^[ \t]*\*\*Strength:\*\*[ \t]*'
    r'(?P<value>[^\s(]*)[ \t]*'
    r'(?:\((?P<stamp>[^)]*)\))?', re.M)
# Mirrors the practice's own applies_to, as a literal for the same reason
# DISPOSITION_FILE_GLOBS is one.
STRENGTH_FILE_GLOBS = ('practices/*.md', 'local/practices/*.md', 'decisions/*.md')
# Who approved the thing. A strength with no approver names a firmness
# belonging to nobody, which is the silence this practice replaces.
STRENGTH_APPROVER_KEYS = ('approved_by', 'decided_by')


def _names_an_approver(block):
    """True if this frontmatter records a real person (or body) as having
    approved the thing, rather than an empty or null placeholder."""
    for key in STRENGTH_APPROVER_KEYS:
        m = re.search(r'^%s:[ \t]*(.*?)[ \t]*$' % key, block, re.M)
        if m and m.group(1).strip().strip('"\'') not in ('', 'null', '~'):
            return True
    return False


@check('decision-strength', 'tree',
       'every `strength:` in a practice file or a decision record holds one '
       'of the two defined words, and the file it sits in also records who '
       'approved the thing; and every `**Strength:` line in prose records '
       'the date it was set and who set it',
       'whether the word is the RIGHT one, which is the whole substance of '
       'the practice. Nothing mechanical can read the conversation an '
       'approval happened in, so a session that writes `decided` over a '
       'shrug passes this cleanly. It is also deliberately blind to '
       'ABSENCE: an unmarked approval is a defined state (unknown), so '
       'silence is never reported here -- which means this check cannot '
       'tell a catalogue that considered the question from one that has '
       'never heard of it.')
def _decision_strength(ctx):
    files = []
    for glob in STRENGTH_FILE_GLOBS:
        for path in sorted(ROOT.glob(glob)):
            rel = path.relative_to(ROOT).as_posix()
            if rel not in files and not _foreign_practice(rel):
                files.append(rel)
    if not files:
        raise NotApplicable('this repository has no practice files or '
                            'decision records to check')

    out = []
    for rel in sorted(files):
        try:
            text = (ROOT / rel).read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError) as e:
            out.append(Finding(rel, f'could not be read ({e})'))
            continue

        fm = _FRONTMATTER_RE.match(text)
        block = fm.group(1) if fm else ''
        marks = list(STRENGTH_FM_RE.finditer(block))
        if len(marks) > 1:
            out.append(Finding(rel, f'carries {len(marks)} `strength:` keys -- '
                                    f'an approval has one firmness'))
        for m in marks:
            value = m.group('value').strip().strip('"\'')
            where = f'{rel}:{block.count(chr(10), 0, m.start()) + 2}'
            if value in ('', 'null', '~'):
                # Written out as empty rather than omitted. That is the
                # unknown state said aloud, which is allowed and sometimes
                # clearer than absence -- but it carries no claim, so the
                # approver requirement below does not apply to it.
                continue
            if value not in STRENGTH_VALUES:
                out.append(Finding(where, f'strength {value!r} is not one of '
                                          f'{", ".join(STRENGTH_VALUES)}'))
                continue
            if not _names_an_approver(block):
                out.append(Finding(where,
                                   f'records strength {value!r} but names '
                                   f'nobody in '
                                   f'{" or ".join(STRENGTH_APPROVER_KEYS)} -- '
                                   f'a firmness belonging to no one'))

        body = text[fm.end():] if fm else text
        offset = fm.end() if fm else 0
        for m in STRENGTH_PROSE_RE.finditer(body):
            line_no = text.count('\n', 0, offset + m.start()) + 1
            where = f'{rel}:{line_no}'
            value, stamp = m.group('value'), m.group('stamp')
            if value not in STRENGTH_VALUES:
                out.append(Finding(where, f'strength {value!r} is not one of '
                                          f'{", ".join(STRENGTH_VALUES)}'))
                continue
            if stamp is None:
                out.append(Finding(where, f'{value!r} carries no '
                                          f'"(YYYY-MM-DD, who)"'))
                continue
            if not DISPOSITION_STAMP_RE.match(stamp.strip()):
                out.append(Finding(where, f'{value!r} stamp {stamp.strip()!r} '
                                          f'is not "YYYY-MM-DD, who"'))
    return sorted(out, key=lambda f: f.where)



# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

def load_exemptions():
    """{slug: reason} for the practices this repo declared `not_binding`
    and that may actually be exempted, plus the slugs whose exemption is
    REFUSED because the practice is `severity: blocking`.

    WHY THIS EXISTS, and what was broken without it (2026-09-10).
    precedent_resolve.load_not_binding()'s own docstring describes the
    mechanism exactly -- "whether a rule binds is a property of the PAIR,
    not of the rule: `commit-author` binds a repo one person authors alone
    and not one with many contributors" -- and this module read that list
    in exactly ONE place, `_unreachable_practices`, where it only ever
    suppressed a REACHABILITY finding. `main()` built its slug list from
    `sorted(CHECKS)` and never consulted it at all, so declaring
    `{"slug": "commit-author", "reason": "..."}` in a consuming repo's
    precedent.json changed nothing about the run: the practice was still
    checked, still violated, still counted, still exit 1. There was NO WAY
    for a consuming repo to declare a practice non-binding and get a clean
    check, and a real install ended on two permanent violations it had
    written reasoned exemptions for. The 17 entries in
    templates/document-project/precedent.json were, for check
    purposes, decorative.

    EXEMPTED IS ITS OWN STATUS, never silence. Dropping these slugs from
    the run would trade one problem for a worse one -- an exemption that
    leaves no trace in the output is how a rule gets switched off and
    forgotten. They are reported by name, with their recorded reasons, and
    counted in their own summary category.

    `severity: blocking` may not be exempted, the same rule
    _unreachable_practices already applies, for the same reason: a
    blocking practice is exactly the one no downstream declaration is
    allowed to switch off. A refused exemption runs normally here; the
    reachability check is what reports the refusal itself as a finding, so
    it is stated once rather than twice."""
    try:
        import precedent_resolve as pr
        not_binding = pr.load_not_binding(ROOT)
    except Exception as e:                                   # noqa: BLE001
        # A malformed list exempts NOTHING -- every check runs. Loud, not
        # silently permissive: an exemption mechanism that swallows its own
        # bad entries is a way to opt out of a rule by typo.
        # _unreachable_practices reports the malformed file itself.
        print(f'precedent_check note: `not_binding` could not be read '
              f'({e}), so no check is exempted this run.', file=sys.stderr)
        return {}, {}

    exempt, refused = {}, {}
    for slug, reason in sorted(not_binding.items()):
        path = _practice_file(slug)
        severity = 'default'
        if path is not None:
            try:
                fm, _sections = sp._read_practice_file(path)
                severity = (fm.get('severity') or 'default').strip('" ')
            except Exception:                                # noqa: BLE001
                severity = 'default'
        if severity == 'blocking':
            refused[slug] = reason
        else:
            exempt[slug] = reason
    return exempt, refused


def run(slugs, ctx, scopes, exempt=None):
    exempt = exempt or {}
    results = []
    for slug in slugs:
        c = CHECKS[slug]
        if c['scope'] not in scopes:
            continue
        # Declared non-binding in THIS repo, with a reason. Reported before
        # the check runs, because the point of the declaration is that the
        # pair (this repo, this rule) has no relationship -- running it and
        # then discarding the findings would still cost the run its time
        # and would still be reading a verdict this repo has said is not
        # about it. See load_exemptions() for the whole story.
        if slug in exempt:
            results.append((slug, 'EXEMPT', [], exempt[slug]))
            continue
        # A check whose practice is not in force here has nothing to
        # enforce. This file is vendored verbatim into consuming repos
        # (INSTALL.md §0 step 1), and it registers every check
        # BestPractice itself needs -- including ones for practices only
        # BestPractice has. Before this gate, a brand-new install's very
        # first `precedent_check.py` run reported a VIOLATION for
        # `merge-target-is-beta-branch`, this repo's own temporary
        # repo-local rule about ITS beta branch, which no consumer can
        # act on, satisfy, or even read the Rule of (`rule_of` prints
        # "(no practice file for ...)"). SKIPPED, never PASS: the check
        # did not run, and a skip is not a pass.
        if c['practice_backed'] and _practice_file(slug) is None:
            results.append((slug, 'SKIPPED', [],
                            f'no practices/{slug}.md in this repo, so the '
                            f'practice is not in force here -- this check '
                            f'belongs to a source this repo does not resolve'))
            continue
        try:
            findings = c['fn'](ctx) or []
            results.append((slug, 'VIOLATION' if findings else 'PASS',
                            findings, None))
        except NotApplicable as e:
            results.append((slug, 'SKIPPED', [], str(e)))
        except Exception as e:
            # A check's own bug (a malformed config it didn't validate, an
            # unhandled edge case) must not take the other checks down with
            # it -- a 2026-09-03 deep-check audit found a malformed
            # process/retired_vocabulary.json (a JSON array instead of an
            # object) raised AttributeError straight out of
            # migration-scrubs-vocabulary's check, uncaught here, aborting
            # the whole run before any of the other ~40 checks got a
            # chance to report anything at all -- loud, but a crash, not
            # the isolated refusal this repo's own "refuse loudly, never
            # silently" philosophy calls for. ERROR is its own status,
            # never folded into VIOLATION (a check that could not run
            # found no evidence either way) or SKIPPED (that means the
            # check legitimately does not apply here, not that it broke).
            results.append((slug, 'ERROR', [],
                            f'{type(e).__name__}: {e}'))
    return results


def main():
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith('--')}
    # Before --list/--explain/--only read CHECKS, so a source-supplied
    # check script is a first-class member of all three.
    register_materialized_checks()
    if '--list' in flags:
        for slug, c in sorted(CHECKS.items()):
            print(f"  {slug:32} [{c['scope']:8}] {c['what']}")
        print(f"\n{len(CHECKS)} practice(s) enforced.")
        return 0
    if '--explain' in flags:
        print(__doc__)
        print('What each check does NOT catch — its limits belong beside it:\n')
        for slug, c in sorted(CHECKS.items()):
            print(f"  {slug}  [{c['scope']}]")
            print(f"    checks:   {c['what']}")
            print(f"    blind to: {c['blind_to']}\n")
        return 0

    only = None
    if '--only' in args:
        only = args[args.index('--only') + 1]
        if only not in CHECKS:
            sys.exit(f'precedent_check FAIL: no check registered for {only!r} '
                     f'— run --list.')
    rng = args[args.index('--range') + 1] if '--range' in args else None
    paths = None
    if '--paths' in args:
        paths = [a for a in args[args.index('--paths') + 1:]
                 if not a.startswith('--')]
        missing = [p for p in paths if not (ROOT / p).exists()]
        if missing:
            sys.exit('precedent_check FAIL: path(s) not found under the repo '
                     f'root: {", ".join(missing)} — a path that resolves to '
                     'nothing is a silent no-op, not a pass.')

    scopes = {'turn-end'} if '--turn-end' in flags else {'tree', 'change'}
    if '--turn-end' in flags and '--all' in flags:
        scopes = {'tree', 'change', 'turn-end'}
    ctx = Ctx(paths=paths, rng=rng, whole_tree='--all' in flags)
    slugs = [only] if only else sorted(CHECKS)
    exempt, refused_exemptions = load_exemptions()
    results = run(slugs, ctx, scopes, exempt=exempt)

    all_violated = [r for r in results if r[1] == 'VIOLATION']
    skipped = [r for r in results if r[1] == 'SKIPPED']
    errored = [r for r in results if r[1] == 'ERROR']
    passed = [r for r in results if r[1] == 'PASS']
    exempted = [r for r in results if r[1] == 'EXEMPT']

    # advisory=True (see check()'s own docstring) is a per-check, incident-
    # justified exception, not a general severity dial -- as of 2026-09-05
    # the only member is parallel-artifact-ledger (see the dated comment
    # above _parallel_artifact_ledger()). Its findings still print in full;
    # they just don't fail the run.
    violated = [r for r in all_violated if not CHECKS[r[0]].get('advisory')]
    advisory = [r for r in all_violated if CHECKS[r[0]].get('advisory')]

    for slug, _st, findings, _why in violated:
        print(f'\nVIOLATION  {slug}')
        for f in findings:
            print(f'    {f}')
        print('  the rule:')
        for line in rule_of(slug).splitlines():
            print(f'    {line}')

    for slug, _st, findings, _why in advisory:
        print(f'\nADVISORY   {slug} — findings below do not fail this run '
              f'(see this check\'s own registration for why)')
        for f in findings:
            print(f'    {f}')
        print('  the rule:')
        for line in rule_of(slug).splitlines():
            print(f'    {line}')

    for slug, _st, _f, why in errored:
        print(f'\nERROR      {slug} — the check itself failed to run: {why}')

    for slug, _st, _f, why in skipped:
        print(f'SKIPPED    {slug} — {why}')

    # Named, with the recorded reason, every run. An exemption that leaves
    # no trace in the output is how a rule gets switched off and forgotten,
    # which is worse than the problem this fixed.
    for slug, _st, _f, why in exempted:
        print(f'EXEMPT     {slug} — declared not-binding in this repo\'s '
              f'precedent.json: {why}')
    for slug, why in sorted(refused_exemptions.items()):
        print(f'\nNOTE       {slug} is declared not-binding here, but it is '
              f'`severity: blocking` — a blocking practice is exactly the one '
              f'a downstream repo may not switch off, so the check ran '
              f'anyway. (Recorded reason: {why})')
    if ctx.scope_reason and any(CHECKS[s]['scope'] == 'change' for s in slugs):
        print(f'note: {ctx.scope_reason}')

    print(f'\nprecedent_check: {len(passed)} passed, {len(violated)} violated, '
          f'{len(advisory)} advisory, {len(errored)} errored, {len(skipped)} '
          f'skipped, {len(exempted)} exempted (a skip is not a pass; advisory '
          f'findings do not fail the run; an exemption is this repo declaring '
          f'the rule does not bind it, with a reason, in precedent.json).')
    if violated or errored:
        return 1
    if skipped and '--strict' in flags:
        print('--strict: a check that could not run is a failure here.')
        return 1
    return 0


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/HOW_TO_USE_THIS_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
