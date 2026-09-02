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
import io, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
sys.path.insert(0, str(TOOLS))
import split_practices as sp

# --------------------------------------------------------------------------
# The one code path: a failure message is the practice's own Rule.
# --------------------------------------------------------------------------

def rule_of(slug):
    path = ROOT / 'practices' / f'{slug}.md'
    if not path.exists():
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


def check(slug, scope, what, blind_to):
    """Register a check. `blind_to` is what it does NOT catch, printed by
    --explain -- a check's limits belong beside it, not in a document that
    drifts from it."""
    def deco(fn):
        CHECKS[slug] = dict(slug=slug, scope=scope, fn=fn, what=what,
                            blind_to=blind_to)
        return fn
    return deco


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
                    old_sections.get('rule', '').strip() == sections.get('rule', '').strip():
                continue        # frontmatter-only edit: not a new rule
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
    builder = ROOT / 'tools' / 'build_views.py'
    if not builder.exists():
        raise NotApplicable('tools/build_views.py is absent, so nothing here '
                            'declares which artifacts are generated')
    for name in GENERATED_VIEWS:
        p = ROOT / name
        if not p.exists():
            out.append(Finding(name, 'declared generated but missing'))
            continue
        head = p.read_text(encoding='utf-8', errors='ignore')[:1200]
        if 'build_views.py' not in head:
            out.append(Finding(name, 'carries no stamp naming the script that '
                                     'builds it, so a reader cannot tell it '
                                     'is generated'))
        if not re.search(r'do not (hand-)?edit|never hand-edit|generated',
                         head, re.I):
            out.append(Finding(name, 'does not say it is generated'))
    r = subprocess.run([sys.executable, str(builder), '--check'],
                       cwd=str(ROOT), capture_output=True, text=True)
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
       'copy, which is the one that silently drifts.')
def _engine_plus_host_shims(ctx):
    vendored = ROOT / 'process' / 'upstream'
    if not vendored.is_dir():
        raise NotApplicable('this repo vendors no upstream tree at '
                            'process/upstream/, so there is no engine/shim '
                            'boundary to hold. This is the expected state in '
                            'the upstream repo itself')
    RUN = 8

    def runs(path):
        lines = [l.strip() for l in
                 path.read_text(encoding='utf-8', errors='ignore').splitlines()]
        lines = [l for l in lines if len(l) > 12 and not l.startswith('#')]
        return {tuple(lines[i:i + RUN]) for i in range(len(lines) - RUN + 1)}

    upstream = {}
    for p in sorted(vendored.rglob('*')):
        if p.is_file() and p.suffix in ('.py', '.sh'):
            for r in runs(p):
                upstream.setdefault(r, str(p.relative_to(ROOT)))
    out = []
    for rel in _git('ls-files').stdout.split():
        if rel.startswith('process/'):
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


def _unglossed(text, known):
    """[(line, TOKEN)] via doc_lint's own acronym scan, so this check and the
    warning it replaces never drift apart -- one detector, two callers."""
    dl = _doc_lint()
    out, seen, incode = [], set(), False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith('```'):
            incode = not incode
            continue
        if incode:
            continue
        clean = dl._decontent(line)
        for m in dl.ACRONYM_RE.finditer(clean):
            tok = m.group(1)
            if tok not in known and tok not in seen and f'({tok})' not in clean:
                seen.add(tok)
                out.append((i, tok))
    return out


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
        cur = _unglossed(ctx.read(f), known)
        base_text = ctx.read_base(f)
        base_toks = {tok for _i, tok in _unglossed(base_text, known)} if base_text else set()
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


def _run(script, *args):
    r = subprocess.run([sys.executable, str(ROOT / script), *args],
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


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

def run(slugs, ctx, scopes):
    results = []
    for slug in slugs:
        c = CHECKS[slug]
        if c['scope'] not in scopes:
            continue
        try:
            findings = c['fn'](ctx) or []
            results.append((slug, 'VIOLATION' if findings else 'PASS',
                            findings, None))
        except NotApplicable as e:
            results.append((slug, 'SKIPPED', [], str(e)))
    return results


def main():
    args = sys.argv[1:]
    flags = {a for a in args if a.startswith('--')}
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

    violated = [r for r in results if r[1] == 'VIOLATION']
    skipped = [r for r in results if r[1] == 'SKIPPED']
    passed = [r for r in results if r[1] == 'PASS']

    for slug, _st, findings, _why in violated:
        print(f'\nVIOLATION  {slug}')
        for f in findings:
            print(f'    {f}')
        print('  the rule:')
        for line in rule_of(slug).splitlines():
            print(f'    {line}')

    for slug, _st, _f, why in skipped:
        print(f'SKIPPED    {slug} — {why}')
    if ctx.scope_reason and any(CHECKS[s]['scope'] == 'change' for s in slugs):
        print(f'note: {ctx.scope_reason}')

    print(f'\nprecedent_check: {len(passed)} passed, {len(violated)} violated, '
          f'{len(skipped)} skipped (a skip is not a pass).')
    if violated:
        return 1
    if skipped and '--strict' in flags:
        print('--strict: a check that could not run is a failure here.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
