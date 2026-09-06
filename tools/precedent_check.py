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
import difflib, functools, io, json, os, pathlib, re, subprocess, sys

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

# --------------------------------------------------------------------------
# The one code path: a failure message is the practice's own Rule.
# --------------------------------------------------------------------------

def rule_of(slug):
    path = _practice_file(slug)
    if path is None:
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
    # on WorkingWithAI's hand-copied root tools (three of which had drifted
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
}


# cite-the-incident, 2026-09-06: themorgan/WorkingWithAI followed
# spec/MIGRATING_EXISTING_INSTALLS.md step 7 exactly as written and ended up
# with a hard-crashing precedent_gate.py -- FileNotFoundError on
# routing_scope.json, which precedent_gate.py itself names via
# `_ENGINE_DIR / 'routing_scope.json'` -- discovered only when someone
# actually tried to run a gate, not before. This check statically scans every
# tools/*.py file for exactly that shape of hardcoded reference and flags any
# target that isn't actually there, so the same class of gap (a vendored
# engine file naming a companion that never got copied) surfaces mechanically
# on the next `precedent_check.py` run instead of via a downstream crash.
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
                    f"never copied over is exactly how themorgan/WorkingWithAI "
                    f"ended up with a hard-crashing precedent_gate.py "
                    f"(2026-09-06, missing routing_scope.json)"))
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


def _md_in_scope(ctx):
    return [f for f in ctx.changed if f.endswith('.md') and (ROOT / f).exists()]


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


@check('github-setup-disclosed', 'change',
       'a newly added GitHub Actions workflow file is named somewhere in '
       'GITHUB_ACTIONS.md, where this project\'s people read about '
       'GitHub-specific setup',
       'a workflow file that is EDITED rather than added (this only fires '
       'on new files, per no-version-suffix\'s ctx.added_files pattern), '
       'and disclosure written anywhere other than GITHUB_ACTIONS.md -- a '
       'README section would satisfy the practice\'s intent but not this '
       'check.')
def _github_setup_disclosed(ctx):
    added = [f for f in ctx.added_files()
             if re.match(r'^\.github/workflows/.+\.ya?ml$', f)]
    if not added:
        raise NotApplicable('no GitHub Actions workflow file was added by '
                            'this change')
    doc_path = ROOT / 'GITHUB_ACTIONS.md'
    if not doc_path.exists():
        return [Finding(f, 'adds a workflow file, but this repo has no '
                            'GITHUB_ACTIONS.md to disclose it in') for f in added]
    doc = doc_path.read_text(encoding='utf-8', errors='ignore')
    out = []
    for f in added:
        name = pathlib.PurePath(f).name
        if name not in doc:
            out.append(Finding(f, f'{name} is not mentioned in '
                                  f'GITHUB_ACTIONS.md'))
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
       'Also blind to any file listed in INLINE_LINEAGE_SKIP_FILES, whose '
       'stated purpose is a historical record rather than a current-state '
       'document -- currently just spec/LOADER.md, which keeps prior '
       'measurement runs as a deliberate, correct appendix.')
def _index_remembers_past(ctx):
    out = []
    for f in _md_in_scope(ctx):
        if f in INLINE_LINEAGE_SKIP_FILES:
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
    owned = [f for _d, _n, s in doc_sync.PAIRS for f in doc_sync.owned_figures(s)]
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
       "makes sure that fix never has to happen by hand again).")
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
    out = []
    for f in sorted((ROOT / 'tools').glob('*.py')):
        if f.name in CODE_CITE_SKIP_FILES:
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


@check('migration-scrubs-vocabulary', 'tree',
       "a repo that has declared process/retired_vocabulary.json carries "
       "none of its listed terms outside the declared exempt files/directories",
       "NotApplicable for any repo that hasn't declared the config -- this "
       "is opt-in per migrated repo, since the terms themselves (a specific "
       "old repo's name, a retired secret) are never something BestPractice "
       "could know in advance. process/upstream/ is always excluded, "
       "vendored content never being this repo's own migration to finish.")
def _migration_scrubs_vocabulary(ctx):
    cfg_path = ROOT / RETIRED_VOCAB_CONFIG
    if not cfg_path.is_file():
        raise NotApplicable(f'no {RETIRED_VOCAB_CONFIG} -- this repo has not '
                            f'declared any retired vocabulary to scrub for')
    try:
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        return [Finding(RETIRED_VOCAB_CONFIG, f'not valid JSON: {e}')]
    if not isinstance(cfg, dict):
        # Valid JSON, wrong shape (e.g. a bare `["OldName"]` array where a
        # `{"terms": [...]}` object belongs) used to reach `cfg.get(...)`
        # below and raise an uncaught AttributeError, taking down every
        # OTHER check in the same run with it (found in a 2026-09-03
        # deep-check audit) -- a malformed config is exactly the kind of
        # thing this check exists to catch, not crash on.
        return [Finding(RETIRED_VOCAB_CONFIG,
                        f'must be a JSON object with a "terms" list (e.g. '
                        f'{{"terms": [...], "exempt_files": [...]}}), not a '
                        f'{type(cfg).__name__}')]
    terms = cfg.get('terms') or []
    exempt_files = cfg.get('exempt_files') or []
    if not isinstance(terms, list) or not isinstance(exempt_files, list):
        bad = 'terms' if not isinstance(terms, list) else 'exempt_files'
        return [Finding(RETIRED_VOCAB_CONFIG,
                        f'{bad!r} must be a JSON array of strings, not a '
                        f'{type(cfg[bad]).__name__}')]
    if not terms:
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
    out = []
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


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

def run(slugs, ctx, scopes):
    results = []
    for slug in slugs:
        c = CHECKS[slug]
        if c['scope'] not in scopes:
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
    results = run(slugs, ctx, scopes)

    all_violated = [r for r in results if r[1] == 'VIOLATION']
    skipped = [r for r in results if r[1] == 'SKIPPED']
    errored = [r for r in results if r[1] == 'ERROR']
    passed = [r for r in results if r[1] == 'PASS']

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
    if ctx.scope_reason and any(CHECKS[s]['scope'] == 'change' for s in slugs):
        print(f'note: {ctx.scope_reason}')

    print(f'\nprecedent_check: {len(passed)} passed, {len(violated)} violated, '
          f'{len(advisory)} advisory, {len(errored)} errored, {len(skipped)} '
          f'skipped (a skip is not a pass; advisory findings do not fail the run).')
    if violated or errored:
        return 1
    if skipped and '--strict' in flags:
        print('--strict: a check that could not run is a failure here.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
