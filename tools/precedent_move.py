#!/usr/bin/env python3
"""Moves an existing practice between levels in the one safe order: lands it at the destination with its text and approval carried, then deduplicates the source copy and regenerates both sets' views; refuses the unsafe states by name

precedent_move.py -- move an existing practice from one level to another.

  python3 tools/precedent_move.py --slug SLUG \\
      --from individual|team|universal --from-path PATH \\
      --to individual|team|universal --to-path PATH \\
      --approved-by NAME [--strength decided|assented] [--story TEXT] [--dry-run]
      [--dedupe-only [--accept-reach-loss]] [--mentions-only]
      [--withdraw-from-universal]

Run it from a Precedent checkout: the sets and the consuming repositories
do not vendor it (the rehearsal of 2026-09-14 spent its first minutes
looking for a copy in the set), and every --from-path / --to-path is a
path to the set, absolute or relative to where you run it.

The two-step move spec/MOVING_PRACTICES.md describes, done in the one order
that is safe and with nothing left to remember:

  1. LAND the practice at the destination, as its own file, carrying the
     Rule, Detail, Why and Story exactly as they are -- this is vetted text,
     not a new draft -- with the destination level's own approval recorded
     (`--approved-by`; a listed approver for a shared set).
     One thing about the text does change: a link to a SIBLING practice
     that is not at the destination is re-homed -- a universal practice's
     URL, else the slug in backticks, never a URL into another set (see
     _rehome_sibling_links for the 2026-09-23 incident). Each is printed.
  2. DEDUPLICATE the copy at the source: `status: deduplicated`,
     `in_force_at: <the slug>`, and one dated line appended to its ## Story
     saying where it went and who approved it. Never a delete: the resolver
     drops a non-active practice before materialization, and the record of
     where the rule now lives is what a consumer's `precedent_show` reports.

Both sets' generated views are regenerated afterwards, where each set
carries build_views.py. Nothing is committed; the two sets are yours to
commit and publish, and a consumer picks the move up on its next sync.

  3. FIX THE MENTIONS, in every repository in force, on the run that
     withdraws the source copy (see _fix_mentions). A link to the old file
     is re-pointed where the practice now lives (the rules step 1 uses); a
     path naming the old set's copy names the new one; and a present-tense
     line that says where the practice lives names the new set. A dated or
     past-tense paragraph, a ## Story, a code comment's prose, and
     generated, vendored or record files are history and stay as written. Each file changed is
     named, and so is each repository -- commit every one of them.
     Morgan, 2026-09-28 (strength: decided): "I don't need a detailed
     report but for those problems to be solved."
     `--mentions-only` runs this step alone, for a move already made --
     it refuses unless the source copy is deduplicated and the destination
     copy active, so it can never rewrite mentions of a practice that has
     not actually left.
     Scope: this Precedent clone and every source its precedent.json and
     your user config resolve, plus both sets. PRECEDENT_MOVE_MENTION_REPOS
     (paths joined with the OS path separator; empty for none) replaces the
     discovered list -- the harness sets it so a fixture never reads real
     repositories.

WHY A TOOL (practice: cite-the-incident). The procedure said to run the
creation pipeline with the existing practice's text as the candidate's
content -- and precedent_candidate.py takes one `--proposed-rule` string,
so an existing file's four sections had no way in, and every move was a
hand copy with the deduplication done from memory or forgotten. Morgan,
2026-09-14: he had "had bumps doing that". The document itself named a
`precedent_move.py` that "does both atomically, and enforces the ordering"
as the missing piece; this is it.

WHAT IT REFUSES, each with its own message: a source practice that is not
`status: active`; an empty ## Story at the source with no `--story` to fill
it (a move is the last moment the original context is in front of
somebody, and catalogue-carries-stories would hold the destination red);
a destination that already carries the slug; a team destination whose
approvers.json does not list `--approved-by`; a `checked_by` naming a check
script the destination does not have (the script and its test move by hand
first -- see spec/PRIVATE_ENFORCEMENT_BRIEF.md); a `ships:` file the
destination does not have (same: copy it first, and commit it with the
practice); `--from universal --to
universal` (nothing to move); `--dedupe-only` on a practice that moved
OUT of universal, without `--accept-reach-loss` also given (see below), or
while the universal clone's tools/ still cite it as `practice: <slug>`;
withdrawing a practice from a shared set without `--approved-by` naming one
of THAT set's approvers (a removal changes what the team is bound by).
A `--to universal` draft from a file with no ## Install gets an empty one,
and says so: every universal practice carries the section.

UNIVERSAL AS THE DESTINATION drafts only: the file is written into the
Precedent clone's practices/ and the source is left ACTIVE, because the
landing there is still the pull request merging -- a session may merge it
directly once its deep check passes, same as any other PR into
precedent-beta-v01 (spec/MOVING_PRACTICES.md, merge-target-is-beta-branch.md)
-- and a source deduplicated before that lands has a rule in force nowhere. The
clone's own generated surfaces are regenerated (build_views.py, doc_sync.py
--write) so its deep check is green on the draft. Run this tool again with
`--dedupe-only` once the PR has merged AND every repository consuming the
source set has taken the new universal catalogue -- a consumer still
vendoring the old one sees the rule in neither source, and its sync prints
IN FORCE NOWHERE and drops it (exit 0) until it is refreshed (INSTALL.md
\u00a72 step 0, "Update Vendors").

UNIVERSAL AS THE SOURCE duplicates, never deduplicates, on landing.
`--from universal --to shared|individual` writes the destination copy
exactly as any other landing, but the universal copy stays `status: active`
-- it is NOT marked deduplicated, and `in_force_at` is not touched. This is
structural, not caution: universal is the one level every Precedent
consumer resolves, and a shared or individual set is not, so a universal
practice deduplicated to point at one leaves the rule genuinely in force
nowhere for any consumer that never declared that destination -- most of
them. [tools/precedent_sync_views.py](precedent_sync_views.py) reports an unresolvable `in_force_at` on
every sync (IN FORCE NOWHERE; exit 0 -- `precedent_resolve.py --strict`
fails on it), so that state alarms every plain consumer, not just a
reader. Confirmed by
incident, 2026-09-23: done by hand instead of by a tool, this exact move
passed every fast check and was only caught by \u2018verify_harness.py
--as-ci\u2019's consumer-fixture check hours later, after both copies had
already been pushed.

Both copies are then genuinely in force at once -- a deliberate, disclosed
duplication, not a bug -- and a Story note in each says so and points at
the other. Withdraw the universal copy later, on purpose, once the audience
that matters has taken the destination: run this tool again with
`--dedupe-only --accept-reach-loss`. `--accept-reach-loss` is required on
that run and that run only, is refused without it, and is not needed for
any other direction -- a plain universal-only consumer (most Precedent
adopters) loses the rule entirely the moment that step runs, and the flag
is the human decision that the audience who still needs it has moved.

WITHDRAWING FROM UNIVERSAL FOR GOOD (2026-10-02). `--withdraw-from-universal`
is the step for a rule meant only for the people who bring or declare the
destination set (spec/LADDER_OPT_IN_PLAN.md). Run after the destination copy
is active: it deletes the universal copy rather than leaving a deduplicated
stub (a stub prints IN FORCE NOWHERE in every repository that does not load
the set, naming the rule), fixes the mentions as any withdrawal does, and
appends one line to record/WITHDRAWN_FROM_UNIVERSAL.md saying when, where
it went and who approved it. It implies --dedupe-only --accept-reach-loss,
keeps every refusal they carry (the destination must be active; the
universal tools/ must not cite the slug), and needs --approved-by.

Exit 0 on a completed move (or a completed draft); 1 on a refusal, with the
reason on stderr and nothing written.
"""

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp    # noqa: E402
import frontmatter_yaml         # noqa: E402  (FIELD_ORDER)
import precedent_time           # noqa: E402  (practice: timestamps-carry-offset)
import precedent_resolve as _pr  # noqa: E402  (the withdrawal record's one format)

LEVELS = ('individual', 'shared', 'universal')
LEVEL_ALIASES = {'team': 'shared'}   # the pre-2026-09-18 spelling still reads
STRENGTHS = ('decided', 'assented')


class MoveRefused(Exception):
    pass


def _practice_path(root, slug):
    return pathlib.Path(root).resolve() / 'practices' / f'{slug}.md'


def _read(path):
    try:
        fm, sections = sp._read_practice_file(path)
    except Exception as e:                                  # noqa: BLE001
        raise MoveRefused(f'{path} does not parse as a practice file: {e}')
    return fm, sections


def _field(fm, key):
    v = fm.get(key)
    if v is None:
        return ''
    return str(v).strip().strip('"')


def _check_team_approver(repo, name, removing=False):
    """A shared set's own approvers.json must list `name`. Landing in a team
    set needs one of them; so does REMOVING a practice from one, since that
    changes what the whole team is bound by (spec/MOVING_PRACTICES.md, step
    2, "Team"). Until 2026-09-28 only the landing was checked: a shared-set copy
    was deduplicated on the destination's approval alone, and `--dedupe-only`
    asked for no name at all."""
    f = pathlib.Path(repo) / 'approvers.json'
    what = ('removing a practice from a shared set' if removing
            else 'landing in a shared set')
    if not f.is_file():
        raise MoveRefused(f'{f} does not exist, so no approver can be verified '
                          f'-- {what} needs one of its listed approvers')
    approvers = json.loads(f.read_text(encoding='utf-8')).get('approvers', [])
    names = {a.get('name') for a in approvers} | {a.get('github') for a in approvers}
    if name not in names:
        raise MoveRefused(f'{name!r} is not in {f} ({sorted(n for n in names if n)}) '
                          f'-- {what} needs a listed approver')


def _universal_citations(clone, slug):
    """-> ['tools/<file>:<line>'] for each `practice: <slug>` citation in a
    universal clone's own tools/*.py -- the files code-cites-practice reads,
    by the same parser. Withdrawing the practice turns every one of them
    into a citation of a practice that is not active there, and that check
    red; found rehearsing a withdrawal, 2026-09-28."""
    import precedent_check as pc
    out = []
    for f in sorted((pathlib.Path(clone) / 'tools').glob('*.py')):
        if f.name in pc.CODE_CITE_SKIP_FILES:
            continue
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        lines = sorted({i for i, s in pc._iter_code_citations(text) if s == slug})
        out += [f'tools/{f.name}:{i}' for i in lines]
    return out


def _drop_routing_audit_entry(clone, slug, dry_run=False):
    """-> True when `<clone>/tools/routing_audit_state.json` carried a
    rotation entry for `slug` (and, unless dry_run, no longer does). The
    routing-audit check reports an entry for a practice that is not active
    as stale bookkeeping, so a withdrawal that leaves it is red on the
    universal clone's own next check. Written the way routing_audit.py
    writes it."""
    f = pathlib.Path(clone) / 'tools' / 'routing_audit_state.json'
    try:
        state = json.loads(f.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    if not isinstance(state, dict) or slug not in state:
        return False
    if not dry_run:
        del state[slug]
        f.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n',
                     encoding='utf-8')
    return True


def _check_checked_by(fm, to_level, to_path):
    checked_by = _field(fm, 'checked_by')
    if not checked_by or checked_by == 'null':
        return
    if to_level == 'universal':
        import precedent_land as pl
        # Re-raised as this tool's own refusal: escaping as LandRefused, it
        # reached the caller as a traceback (2026-10-05, moving
        # assorted-notes, whose check script universal does not register).
        try:
            pl._verify_checked_by_universal(checked_by, _field(fm, 'slug'))
        except pl.LandRefused as e:
            raise MoveRefused(str(e)) from e
        return
    name = pathlib.Path(checked_by).name
    script = pathlib.Path(to_path) / 'tools' / 'checks' / name
    stem = name[len('check_'):-3] if name.startswith('check_') and name.endswith('.py') else name
    test = pathlib.Path(to_path) / 'tools' / 'checks' / 'tests' / f'test_{stem}.sh'
    if not script.is_file() or not test.is_file():
        raise MoveRefused(
            f'the practice declares checked_by: {checked_by}, and the destination '
            f'has no {script.relative_to(to_path)} with a '
            f'{test.relative_to(to_path)} beside it. Move the check script and '
            f'its test first (spec/PRIVATE_ENFORCEMENT_BRIEF.md), then the practice; '
            f'a checked_by naming a check the set cannot run is a coverage claim '
            f'nobody tested')


def _check_ships(fm, to_path):
    """Every file the practice declares in `ships:` must already be at the
    destination, byte for byte where the source still has it.

    practice: practice-carries-its-files -- a practice moves with everything
    it owns, in one commit. Before `ships:` existed nothing declared a
    practice's other files, so a move could leave its script behind and
    nothing noticed until a consumer's test went red (2026-09-26,
    create-word-doc)."""
    import build_views as bv
    try:
        ships = bv.ships_paths(fm)
    except ValueError as e:
        raise MoveRefused(f'the practice\'s {e} -- fix the declaration before '
                          f'moving it')
    missing = [rel for rel in ships
               if not (pathlib.Path(to_path) / rel).is_file()]
    if missing:
        raise MoveRefused(
            f'the practice ships {", ".join(missing)}, and the destination '
            f'does not carry {"it" if len(missing) == 1 else "them"}. Copy '
            f'each file to the same path there first -- the practice, its '
            f'checked_by script, that script\'s test and every `ships:` file '
            f'land in one commit (spec/MOVING_PRACTICES.md)')


def _raw_field(text, key):
    """A frontmatter field's whole value as the file writes it: continuation
    lines joined, the outer quotes taken off, escapes left as they are.
    split_practices reads only a field's first line, which cut a long
    approval off mid-sentence when a move carried it along (2026-10-02)."""
    end = text.find('\n---\n', 4)
    out = None
    for line in text[4:end].split('\n'):
        if out is None:
            m = re.match(rf'^{re.escape(key)}:\s*(.*)$', line)
            if m:
                out = [m.group(1).strip()]
        elif line.startswith((' ', '\t')):
            out.append(line.strip())
        else:
            break
    if not out:
        return ''
    v = ' '.join(x for x in out if x).strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        v = v[1:-1]
    elif len(v) >= 2 and v[0] == v[-1] == "'":
        v = v[1:-1].replace("''", "'")
    return '' if v == 'null' else v


def _quoted(s):
    """`s` as a double-quoted frontmatter value. A quote already escaped in
    the file (an approval quoting somebody) stays as it is; a bare one is
    escaped."""
    return '"' + re.sub(r'(?<!\\)"', r'\\"', s) + '"'


def _rewrite_frontmatter(text, updates):
    """Rewrite named top-level frontmatter fields in place, byte-for-byte
    elsewhere. A field absent from the frontmatter is appended before the
    closing fence. `updates` values are the raw text to put after the colon.

    A field being replaced may itself have spanned multiple physical lines
    in the original -- a quoted scalar folded onto a continuation line,
    indented deeper than the key (`approved_by:` carries the longest ones
    in this catalogue). Those continuation lines belong to the OLD value
    and are dropped along with it: replacing only the first line and
    leaving the rest in place corrupts the file, since the new value on
    line one is already a complete, closed string and what follows reads
    as a second, indented top-level scalar -- invalid YAML. Found 2026-09-23:
    exactly this, landing dont-race-another-window's already multi-line
    approved_by."""
    end = text.find('\n---\n', 4)
    fm_text, body = text[4:end], text[end:]
    lines = fm_text.split('\n')
    seen = set()
    out = []
    skip_continuation = False
    for line in lines:
        m = re.match(r'^([A-Za-z_]+):(\s*)(.*)$', line)
        if m:
            skip_continuation = False
            if m.group(1) in updates:
                key = m.group(1)
                pad = m.group(2) or ' '
                out.append(f'{key}:{pad}{updates[key]}')
                seen.add(key)
                skip_continuation = True
            else:
                out.append(line)
        elif skip_continuation:
            continue
        else:
            out.append(line)
    # A field the file did not have goes where frontmatter_yaml.FIELD_ORDER
    # puts it, not at the end: appending it was one way the order drifted
    # (frontmatter-field-order, 2026-09-26). Before the first field the order
    # puts after it; at the end only when there is none.
    rank = {k: i for i, k in enumerate(frontmatter_yaml.FIELD_ORDER)}
    for key, value in updates.items():
        if key in seen:
            continue
        at = len(out)
        for i, line in enumerate(out):
            m = re.match(r'^([A-Za-z_]+):', line)
            if m and rank.get(m.group(1), len(rank)) > rank.get(key, len(rank)):
                at = i
                break
        out.insert(at, f'{key}: {value}')
    return '---\n' + '\n'.join(out) + body


_SIBLING_LINK_RE = re.compile(r'(?<!!)\[([^\]]*)\]\(([a-z0-9][a-z0-9-]*)\.md(#[^)\s]*)?\)')


def _universal_url_base():
    """'https://github.com/<owner>/<repo>/blob/<base_branch>/practices/' for
    this Precedent clone, or None when either half cannot be read. A link
    into the universal catalogue is the one cross-set link that is safe to
    publish from anywhere."""
    try:
        url = subprocess.run(['git', '-C', str(ROOT), 'remote', 'get-url', 'origin'],
                             capture_output=True, text=True).stdout.strip()
        branch = json.loads((ROOT / 'precedent.json').read_text(encoding='utf-8')).get('base_branch')
    except (OSError, ValueError):
        return None
    m = re.search(r'github\.com[:/]+([^/]+/[^/\s]+?)(?:\.git)?/*$', url)
    return f'https://github.com/{m.group(1)}/blob/{branch}/practices/' if m and branch else None


def _rehome_sibling_links(text, dest_dir):
    """-> (text, [what changed]). A practice's links to its SIBLINGS are
    relative (`other-slug.md`), and the siblings that stay behind turn them
    into dead links at the destination. The obvious hand repair -- a URL to
    where the sibling stayed -- is the disclosure private-repo-scrub forbids
    whenever that set is private, and it is exactly what happened on
    2026-09-23 (practice: practice-links-travel). So the move does the
    repair itself: a sibling that is also at the destination keeps its link,
    a universal practice gets its universal URL, and anything else becomes
    its slug in backticks. Link markup only; the words are untouched."""
    universal = _universal_url_base()
    changed = []

    def repl(m):
        label, slug, frag = m.group(1), m.group(2), m.group(3) or ''
        # Inside a code span (an odd number of backticks before it): a value
        # being documented, not a reference. The label's own backticks sit
        # inside the match, so they never count here.
        if m.string.count('`', 0, m.start()) % 2:
            return m.group(0)
        if (dest_dir / f'{slug}.md').is_file():
            return m.group(0)
        if universal and (ROOT / 'practices' / f'{slug}.md').is_file() \
                and dest_dir.resolve() != (ROOT / 'practices').resolve():
            new = f'[{label}]({universal}{slug}.md{frag})'
        elif label.strip('`') == slug:
            new = f'`{slug}`'
        else:
            new = f'{label} (`{slug}`)'
        changed.append(f'{m.group(0)} -> {new}')
        return new

    out, fence = [], False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith(('```', '~~~')):
            fence = not fence
        if fence or line.lstrip().startswith(('```', '~~~')):
            out.append(line)
            continue
        out.append(_SIBLING_LINK_RE.sub(repl, line))
    return ''.join(out), changed


# Files a mention fix never edits: generated views (regenerated after the
# move anyway), records of what happened, and material a repo received rather
# than wrote.
_MENTION_SKIP_NAMES = {'MAP.md', 'GLOSSARY.md', 'AGENTS.md', 'CLAUDE.md',
                       'GEMINI.md', 'MANIFEST.json', 'ENGINE_MANIFEST.json',
                       'CLOSED.md', 'CHANGELOG.md', 'stale_branches.md'}
_MENTION_SKIP_DIRS = ('.precedent/', 'process/upstream/', 'record/',
                      'decisions/', 'gotchas/', 'candidates/', 'node_modules/')
_MENTION_EXTS = {'.md', '.py', '.sh', '.json', '.yml', '.yaml', '.txt',
                 '.toml', '.template'}
# A line that tells history is left as written: rewriting "moved from A" to
# "moved from B" makes it false.
_HISTORY_RE = re.compile(
    r'\b20\d\d-\d\d-\d\d\b|\b(?:moved|migrated|formerly|previously|used to|'
    r'until|retired|deduplicated|was (?:in|at)|lived in|came from)\b', re.I)
# A list item starts a new unit of history: one dated item does not make its
# siblings history. Found 2026-09-28: a numbered list whose item 5 said
# "(verified 2026-08-28)" kept item 8's two current links to a withdrawn
# practice from being fixed, and nothing said so.
_LIST_ITEM_RE = re.compile(r'^\s*(?:\d+\.|[-*+])\s')
# A level named AS a place ("the shared set", "universal's", "individual
# practice") -- not the adjective inside a slug like tabular-shared-renderer,
# which on the first run of this report was most of what it named.
_LEVEL_WORD_RE = re.compile(
    r"(?<![\w-])(?:individual|team|shared|universal)"
    r"(?:'s\b|\s+(?:set|level|catalogue|practice|copy|source|rule)s?\b)", re.I)


def _mention_repos(from_path, to_path):
    """-> [repo root Path] a mention fix reads: both sets, this Precedent
    clone, and every source it resolves (user config included), deduplicated
    by git toplevel. PRECEDENT_MOVE_MENTION_REPOS replaces the discovered
    list (both sets are always kept)."""
    import os
    roots = []

    def add(path):
        try:
            top = subprocess.run(['git', '-C', str(path), 'rev-parse',
                                  '--show-toplevel'], capture_output=True,
                                 text=True).stdout.strip()
        except OSError:
            top = ''
        r = pathlib.Path(top or path).resolve()
        if r.is_dir() and r not in roots:
            roots.append(r)

    add(from_path)
    add(to_path)
    override = os.environ.get('PRECEDENT_MOVE_MENTION_REPOS')
    if override is not None:
        for part in override.split(os.pathsep):
            if part.strip():
                add(part.strip())
        return roots
    add(ROOT)
    try:
        import precedent_resolve as pr
        for src in pr.load_config(str(ROOT)):
            if src.get('path'):
                add(src['path'])
    except Exception:                                        # noqa: BLE001
        pass
    return roots


def _vendored(repo):
    """-> set of repo-relative paths this repo RECEIVED from upstream (its
    ENGINE_MANIFEST.json), which a mention fix leaves for upstream to fix."""
    f = repo / 'tools' / 'ENGINE_MANIFEST.json'
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return set()
    out = set()
    # Each list names files relative to the directory it vendors into.
    for key, prefix in (('files', 'tools/'), ('hook_files', '.claude/hooks/'),
                        ('ci_workflow_files', '.github/workflows/')):
        v = data.get(key)
        names = list(v) if isinstance(v, (dict, list)) else []
        out |= {prefix + x for x in names if isinstance(x, str) and x}
    return out


def _fix_mentions(slug, from_path, to_level, to_path, dry_run=False,
                  say=print):
    """-> {repo root: [relative paths changed]}. Step 3 of the module
    docstring: after a move withdraws the source copy, nothing else in the
    repos in force should go on saying the practice lives there.

    Three kinds of mention, each fixed in place:
      a link   -- a markdown link whose target is the old file, by relative
                  path or by URL. Re-pointed by the rules _rehome_sibling_links
                  uses: a relative path inside the destination repo, the
                  universal URL when the destination is universal, else the
                  slug in backticks (never a URL into another set).
      a path   -- `<old set>/practices/<slug>.md` outside a link: the set
                  name becomes the destination's; a URL form becomes the
                  universal URL or the backticked slug, as above.
      prose    -- in Markdown only, a phrasing that says where the practice
                  lives ("<set>'s `slug`", "`slug` (<set>)", "`slug` in
                  <set>", "`slug` is a <set> rule"): the set name is replaced
                  in that phrase and nowhere else on the line.
    Never touched: the practice's own two files, generated views, records
    and vendored files (_MENTION_SKIP_*, _vendored), a ## Story section,
    fenced code, and any paragraph that reads as history (_HISTORY_RE)."""
    from_root = pathlib.Path(from_path).resolve()
    to_root = pathlib.Path(to_path).resolve()
    from_name, to_name = from_root.name, to_root.name
    old_file = from_root / 'practices' / f'{slug}.md'
    new_file = to_root / 'practices' / f'{slug}.md'
    universal = _universal_url_base() if to_level == 'universal' else None
    slug_re = re.compile(r'(?<![\w-])' + re.escape(slug) + r'(?![\w-])')
    name_re = re.compile(r'(?<![\w-])' + re.escape(from_name) + r'(?![\w-])')
    url_re = re.compile(r'https?://github\.com/[^/\s)]+/' + re.escape(from_name)
                        + r'/(?:blob|tree)/[^/\s)]+/practices/' + re.escape(slug)
                        + r'\.md(#[^\s)]*)?')
    path_re = re.compile(r'(?<![\w.-])((?:[\w.~-]+/)*)' + re.escape(from_name)
                         + r'/practices/' + re.escape(slug) + r'\.md')
    link_re = re.compile(r'(?<!!)\[([^\]]*)\]\(([^)\s]+)\)')
    # Where-it-lives phrasings, the name in group 'n' and nothing else
    # rewritten: "<set>'s `slug`", "`slug` (<set>)", "`slug` in/from <set>",
    # "`slug` is a <set> rule/practice".
    q, sl, nm = '`?', re.escape(slug), re.escape(from_name)
    home_re = re.compile(
        r"(?P<a>(?<![\w-]))(?P<n>" + q + nm + q + r")(?P<b>'s " + q + sl + q + r"(?![\w-]))"
        r"|(?P<c>(?<![\w-])" + q + sl + q + r" \()(?P<n2>" + q + nm + q + r")(?P<d>\))"
        r"|(?P<e>(?<![\w-])" + q + sl + q + r" (?:in|from|lives in|is in) (?:the )?)"
        r"(?P<n3>" + q + nm + q + r")(?P<f>(?![\w-]))"
        r"|(?P<g>(?<![\w-])" + q + sl + q + r" is an? )(?P<n4>" + q + nm + q + r")"
        r"(?P<h> (?:rule|practice))")
    to_label = 'universal' if to_level == 'universal' else to_name
    here_re = re.compile(r"\b(?:this|our) (?:repo|repository|set)(?:'s)?\b"
                         r"|\bin here\b", re.I)
    review, unfixed = [], []

    def home_repl(m):
        def swap(n):
            return n.replace(from_name, to_label)
        if m.group('n'):
            if to_level == 'universal':
                return 'the universal' + m.group('b')[2:]
            return m.group('a') + swap(m.group('n')) + m.group('b')
        if m.group('n2'):
            return m.group('c') + swap(m.group('n2')) + m.group('d')
        if m.group('n3'):
            return m.group('e') + swap(m.group('n3')) + (m.group('f') or '')
        return m.group('g') + swap(m.group('n4')) + m.group('h')

    changed = {}

    def new_target(referrer, frag):
        import os
        if str(referrer).startswith(str(to_root) + os.sep):
            return os.path.relpath(new_file, referrer.parent) + frag
        if universal:
            return f'{universal}{slug}.md{frag}'
        return None

    for repo in _mention_repos(from_path, to_path):
        r = subprocess.run(['git', '-C', str(repo), 'ls-files'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            continue
        vendored = _vendored(repo) if repo != ROOT.resolve() else set()
        for rel in r.stdout.splitlines():
            f = repo / rel
            if (f.suffix not in _MENTION_EXTS or f.name in _MENTION_SKIP_NAMES
                    or rel.startswith(_MENTION_SKIP_DIRS) or rel in vendored
                    or f.resolve() in (old_file, new_file) or not f.is_file()):
                continue
            try:
                text = f.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            if slug not in text:
                continue
            lines = text.splitlines(keepends=True)
            # History is judged by the PARAGRAPH (the run of non-blank
            # lines a line sits in), not the line: a wrapped sentence keeps
            # its date on the next line as often as on its own. A list item
            # is its own paragraph (_LIST_ITEM_RE).
            historical, para = [False] * len(lines), []

            def settle(run):
                if any(_HISTORY_RE.search(lines[j]) for j in run):
                    for j in run:
                        historical[j] = True

            for i, line in enumerate(lines):
                if not line.strip():
                    settle(para)
                    para = []
                    continue
                if para and _LIST_ITEM_RE.match(line):
                    settle(para)
                    para = []
                para.append(i)
            settle(para)
            out, fence, story, dirty = [], False, False, False
            for i, line in enumerate(lines):
                stripped = line.lstrip()
                if stripped.startswith(('```', '~~~')):
                    fence = not fence
                    out.append(line)
                    continue
                if f.suffix == '.md' and stripped.startswith('## '):
                    story = stripped.strip().lower() == '## story'
                if fence or story or slug not in line or historical[i]:
                    out.append(line)
                    continue
                new = line

                def link_repl(m):
                    label, target = m.group(1), m.group(2)
                    base, _, frag = target.partition('#')
                    frag = '#' + frag if frag else ''
                    hits_old = bool(url_re.fullmatch(target))
                    if not hits_old and '://' not in base:
                        try:
                            hits_old = (f.parent / base).resolve() == old_file
                        except (OSError, ValueError):
                            hits_old = False
                    if not hits_old or m.string.count('`', 0, m.start()) % 2:
                        return m.group(0)
                    tgt = new_target(f, frag)
                    # A label that IS the old path would go on naming the
                    # stub: it becomes the slug.
                    if label.strip('`').endswith(f'{slug}.md'):
                        label = f'`{slug}`'
                    if tgt:
                        return f'[{label}]({tgt})'
                    return (f'`{slug}`' if label.strip('`') == slug
                            else f'{label} (`{slug}`)')

                new = link_re.sub(link_repl, new)
                new = url_re.sub(lambda m: (f'{universal}{slug}.md{m.group(1) or ""}'
                                            if universal else f'`{slug}`'), new)
                new = path_re.sub(lambda m: f'{m.group(1)}{to_name}/practices/{slug}.md',
                                  new)
                # Prose only in prose files (a code comment naming a set is
                # nearly always the story of why the code is shaped so), and
                # only the phrasings that SAY where the practice lives. A line
                # that names the set and the slug for any other reason --
                # "precedent-individual has this check vendored" -- is about
                # the set, and renaming it there makes it false.
                if f.suffix == '.md':
                    new = home_re.sub(lambda m: home_repl(m), new)
                if new != line:
                    dirty = True
                    # The link is right now; a sentence around it that says
                    # the practice is HERE is not, and no rewrite of a link
                    # can fix a sentence. Named for a person to reword.
                    if here_re.search(new):
                        review.append(f'{repo.name}/{rel}:{i + 1}')
                # A current line that still names the old set beside the
                # practice, or names a level beside it and was not touched,
                # is a mention none of the rewrites above recognized. Named,
                # never left silent: a fix that says nothing about what it
                # could not fix reads as having fixed everything.
                if slug_re.search(new) and (
                        name_re.search(new)
                        or (new == line and _LEVEL_WORD_RE.search(line))):
                    unfixed.append(f'{repo.name}/{rel}:{i + 1}')
                out.append(new)
            if dirty:
                changed.setdefault(repo, []).append(rel)
                if not dry_run:
                    f.write_text(''.join(out), encoding='utf-8')
    for repo, rels in changed.items():
        for rel in rels:
            say(f'{"would fix" if dry_run else "fixed"} a mention of `{slug}` '
                f'in {repo.name}/{rel}')
    for where in review:
        say(f'reword by hand: {where} -- its link now points where `{slug}` '
            f'lives, and the sentence still says it is in this repository')
    for where in unfixed:
        say(f'could not fix: {where} -- it mentions `{slug}` beside '
            f'{from_name} or a level, and no rewrite here recognized the '
            f'phrasing; read it and reword it by hand if it still places '
            f'the practice in {from_name}')
    if changed and not dry_run:
        say('mentions fixed in: ' + ', '.join(str(r) for r in changed)
            + ' -- commit each of these repositories')
    return changed


def _append_story(text, line):
    """Append one paragraph to the END OF the ## Story section, creating the
    section when the file has none.

    Not the end of the file: ## Install follows ## Story, and appending at
    the end put the line inside ## Install. Found 2026-09-28: both practices
    withdrawn from universal on 2026-09-23 carried their "Withdrawn from
    universal" and "Also landed" lines in ## Install, where nothing that
    reads a Story (precedent_resolve.withdrawn_from_universal among them)
    ever saw them."""
    m = re.search(r'^## Story[ \t]*$', text, re.M)
    if not m:
        return text.rstrip('\n') + '\n\n## Story\n' + line + '\n'
    nxt = re.search(r'^## \S', text[m.end():], re.M)
    if not nxt:
        return text.rstrip('\n') + '\n\n' + line + '\n'
    cut = m.end() + nxt.start()
    return text[:cut].rstrip('\n') + '\n\n' + line + '\n\n' + text[cut:]


def _regenerate_universal(clone):
    """-> str. A Precedent clone's own generated surfaces after a draft lands
    in its practices/: build_views.py (AGENTS.md, MAP.md, GLOSSARY.md) and
    doc_sync.py --write (spec/LOADER.md's catalogue and the other derived
    sections). Both, because the rehearsal of 2026-09-14 that drafted a
    practice by hand found the clone's own deep check red on exactly those
    two until they were run, and nothing had said so."""
    clone = pathlib.Path(clone)
    out = []
    for rel, args in (('tools/build_views.py', []), ('tools/doc_sync.py', ['--write'])):
        script = clone / rel
        if not script.is_file():
            out.append(f'{rel}: not in {clone}, so not run -- is that a Precedent clone?')
            continue
        r = subprocess.run([sys.executable, '-B', str(script), *args], cwd=str(clone),
                           capture_output=True, text=True)
        last = (r.stdout + r.stderr).strip().splitlines()
        out.append(f'{rel}{" " + " ".join(args) if args else ""}: '
                   + ('OK' if r.returncode == 0 else (last[-1] if last else f'exit {r.returncode}')))
    return '; '.join(out)


def _regenerate(set_root):
    bv = pathlib.Path(set_root) / 'tools' / 'build_views.py'
    if not bv.is_file():
        return f'{set_root}: carries no tools/build_views.py, so its views were not regenerated -- run its own generator'
    r = subprocess.run([sys.executable, '-B', str(bv)], cwd=str(set_root),
                       capture_output=True, text=True)
    last = (r.stdout + r.stderr).strip().splitlines()
    return f'{set_root}: ' + (last[-1] if last else f'build_views exit {r.returncode}')


# The one committed record of every rule withdrawn from universal on purpose
# (--withdraw-from-universal). Read by people and by mentions_only; the
# resolver never needs it, because a deleted file is simply not there.
WITHDRAWN_RECORD = 'record/WITHDRAWN_FROM_UNIVERSAL.md'
DECOMMISSION_REGISTRY = 'process/decommissioned_paths.json'
WITHDRAWN_RECORD_HEADER = (
    '---\n'
    'title:         Rules withdrawn from the universal set on purpose\n'
    'kind:          record\n'
    'status:        live\n'
    'opened:        2026-10-02\n'
    'closed:        null\n'
    'superseded_by: null\n'
    'supersedes:    []\n'
    'audience:      contributor\n'
    'summary:       "One line per practice deleted from universal by '
    'precedent_move.py --withdraw-from-universal: when, where it is in force '
    'now, and who approved it. The reach loss was the point, so no sync '
    'reports these rules missing."\n'
    '---\n\n'
    '# Rules withdrawn from the universal set on purpose\n\n'
    'Each rule below was moved into a set that only the people who bring or '
    'declare it load. Its full text and Story live there.\n\n')


def move(slug, from_level, from_path, to_level, to_path, approved_by,
         strength=None, story=None, dry_run=False, dedupe_only=False,
         accept_reach_loss=False, withdraw=False, say=print):
    from_level = LEVEL_ALIASES.get(from_level, from_level)
    to_level = LEVEL_ALIASES.get(to_level, to_level)
    # --withdraw-from-universal (spec/LADDER_OPT_IN_PLAN.md step 4): the
    # reach loss is the POINT -- the rule is meant for the people who bring
    # the destination set, and nobody else. A deduplicated stub would print
    # IN FORCE NOWHERE, naming the rule and the set, on every sync in every
    # repository that does not load it, and ship its text to every consumer.
    # So the universal copy is deleted (practice: decommission-deletes-files)
    # and one committed record line says it was deliberate.
    if withdraw:
        if from_level != 'universal' or to_level == 'universal':
            raise MoveRefused('--withdraw-from-universal moves a practice OUT of '
                              'universal: --from universal --to shared|individual')
        if not approved_by:
            raise MoveRefused('--approved-by NAME is required: withdrawing a rule '
                              'from everyone is a decision somebody made')
        dedupe_only, accept_reach_loss = True, True
    if from_level not in LEVELS or to_level not in LEVELS:
        raise MoveRefused(f'levels are one of {LEVELS}')
    if from_level == 'universal' and to_level == 'universal':
        raise MoveRefused('source and destination are both universal -- nothing to move')
    # See the module docstring, "UNIVERSAL AS THE SOURCE" -- this incident's
    # own remedy. A practice landed OUT of universal stays
    # duplicated -- both copies active -- until a session deliberately
    # withdraws the universal one. That withdrawal is real reach loss for
    # any consumer resolving only universal, which precedent_sync_views.py
    # cannot see and this tool cannot check, so a human says so explicitly
    # rather than the tool inferring it from --dedupe-only alone.
    duplicate_from_universal = from_level == 'universal' and to_level != 'universal'
    if duplicate_from_universal and dedupe_only and not accept_reach_loss:
        raise MoveRefused(
            f'withdrawing `{slug}` from universal needs --accept-reach-loss on this '
            f'--dedupe-only run. Universal is the one level every Precedent consumer '
            f'resolves; the {to_level} set is not, so this step leaves the rule in '
            f'force nowhere for any consumer that never declared it -- most of them, '
            f'not a smaller audience. That is not a guess: verify_harness.py --as-ci\'s '
            f'consumer-fixture check found exactly this shape of deduplication '
            f'resolving nowhere, 2026-09-23, after it was done by hand instead of by '
            f'this tool. Pass the flag once the audience that matters has taken the '
            f'destination set.')
    if from_level == to_level and pathlib.Path(from_path).resolve() == pathlib.Path(to_path).resolve():
        raise MoveRefused('source and destination are the same set')
    if strength is not None and strength not in STRENGTHS:
        raise MoveRefused(f'--strength is one of {STRENGTHS}')
    if not approved_by and not dedupe_only:
        raise MoveRefused('--approved-by NAME is required: the destination level\'s own '
                          'approval is what makes this a move rather than a copy')
    if not approved_by and from_level == 'shared':
        raise MoveRefused('--approved-by NAME is required: removing a practice from a '
                          'shared set changes what the whole team is bound by, so it needs '
                          'one of that set\'s own approvers (spec/MOVING_PRACTICES.md, '
                          'step 2)')
    # The source copy is withdrawn on this run -- the one moment its
    # mentions elsewhere stop being true (step 3, _fix_mentions), and the
    # moment a shared source's own approval is needed.
    source_withdrawn = dedupe_only or (to_level != 'universal'
                                       and not duplicate_from_universal)

    src = _practice_path(from_path, slug)
    if not src.is_file():
        raise MoveRefused(f'{src} does not exist')
    fm, sections = _read(src)
    today = precedent_time.today(ROOT)  # practice: timestamps-carry-offset
    dest = _practice_path(to_path, slug)
    # A retired name (a deduplicated stub forwarding to another rule) leaves
    # universal too, when the rule it forwards to does: the set keeps its
    # own stub as history. 2026-10-02: the ladder took four such names with
    # it, this tool refused them (their set copies are not active, by
    # design), so their record lines were written by hand in a shape the
    # record's reader did not know -- and the first consumer to update past
    # them was refused on two of them (2026-10-04).
    forwarded_to = None
    if withdraw and _field(fm, 'status') == 'deduplicated':
        forwarded_to = _field(fm, 'in_force_at') or None
        if not forwarded_to or forwarded_to in ('null', 'none', slug):
            raise MoveRefused(f'{src} is deduplicated but forwards nowhere '
                              f'(in_force_at: {forwarded_to or "absent"}) -- fix its '
                              f'in_force_at before withdrawing it')

    if dedupe_only:
        if not dest.is_file():
            raise MoveRefused(f'--dedupe-only, but {dest} does not exist: nothing is '
                              f'in force at the destination yet, so the source copy '
                              f'may not be withdrawn')
        dfm, _ = _read(dest)
        if forwarded_to:
            if _field(dfm, 'status') != 'deduplicated':
                raise MoveRefused(f'{src} is a retired name forwarding to '
                                  f'`{forwarded_to}`; {dest} is status: '
                                  f'{_field(dfm, "status") or "active"}, not the same '
                                  f'retired name kept as history there')
        elif _field(dfm, 'status') not in ('', 'active'):
            raise MoveRefused(f'{dest} is status: {_field(dfm, "status")}, not active -- '
                              f'the rule would be in force nowhere')
        if from_level == 'universal':
            cites = _universal_citations(from_path, slug)
            if cites:
                raise MoveRefused(
                    f'`{slug}` is cited as `practice: {slug}` in {", ".join(cites)}. '
                    f'Withdrawn from universal, each of those cites a practice that '
                    f'is not active there, and code-cites-practice goes red on the '
                    f'universal clone. Reword or remove each citation (say what the '
                    f'code does, or cite the practice the code now serves), then run '
                    f'this again')
    else:
        status = _field(fm, 'status') or 'active'
        if status != 'active':
            raise MoveRefused(f'{src} is status: {status} -- only an active practice '
                              f'moves; a withdrawn one already records where it went')
        if not (sections.get('story') or '').strip() and not story:
            raise MoveRefused(f'{src} has an empty ## Story and no --story was given. '
                              f'Fill it before landing, not after: a move is the last '
                              f'moment the original context is in front of somebody, '
                              f'and catalogue-carries-stories holds the destination '
                              f'red until it is filled anyway')
        if dest.is_file():
            raise MoveRefused(f'{dest} already exists -- refusing to overwrite. If it is '
                              f'the same rule, deduplicate the source with --dedupe-only')
        if to_level == 'shared':
            _check_team_approver(to_path, approved_by)
        _check_checked_by(fm, to_level, to_path)
        _check_ships(fm, to_path)
    if source_withdrawn and from_level == 'shared':
        _check_team_approver(from_path, approved_by, removing=True)

    from_name = pathlib.Path(from_path).resolve().name
    to_name = pathlib.Path(to_path).resolve().name
    plan = []
    rehomed = []
    install_added = False
    why_missing = False
    checked_by_rehomed = None

    if not dedupe_only:
        text = src.read_text(encoding='utf-8')
        if story and not (sections.get('story') or '').strip():
            text = _append_story(text, story)
        old_approved = _raw_field(text, 'approved_by')
        # The approval the rule carried where it came from is part of its
        # record: kept, in brackets, never replaced (2026-10-02: fourteen
        # rules duplicated into the ladder set lost theirs, and the line
        # that replaced it went on saying the universal copy "stays active"
        # after the withdrawal deleted it). json.dumps quotes it, so an
        # approval that itself quotes somebody stays valid YAML.
        there = f' (there: {old_approved})' if old_approved else ''
        if duplicate_from_universal:
            approval = _quoted(f'{approved_by}, {today}, duplicated from the universal '
                               f'set {from_name}, where a copy stays active{there}')
        else:
            approval = _quoted(f'{approved_by}, {today}, moved from the {from_level} '
                               f'set {from_name}{there}')
        updates = {'status': 'active', 'in_force_at': 'null',
                   'added': f'"{today}"', 'approved_by': approval}
        if to_level == 'universal':
            updates['approved_by'] = (f'"pending PR review -- drafted {today} by {approved_by}, '
                                      f'moved from the {from_level} set {from_name}"')
            # A set's check is a script under its own tools/checks/; in
            # universal the same slug is a registered check in
            # precedent_check.py, which _check_checked_by has just confirmed.
            # The script path would name a file universal does not have
            # (2026-10-05: five drafts from repo-maintenance each carried it).
            if _field(fm, 'checked_by').startswith('tools/checks/'):
                checked_by_rehomed = _field(fm, 'checked_by')
                updates['checked_by'] = '"tools/precedent_check.py"'
        if strength:
            updates['strength'] = strength
        new_text = _rewrite_frontmatter(text, updates)
        new_text, rehomed = _rehome_sibling_links(new_text, dest.parent)
        if to_level == 'universal' and 'install' not in sections:
            # Every universal practice carries ## Rule, ## Why, ## Story and
            # ## Install, and the harness (check_practice_sections_present)
            # fails a draft without the last while every fast check passes
            # it -- found 2026-09-28, drafting one. The heading goes in here
            # rather than a refusal: an empty section is legal, and what
            # belongs in it is the person's to write, which the disclosure
            # below says.
            new_text = new_text.rstrip('\n') + '\n\n## Install\n'
            install_added = True
        if to_level == 'universal':
            # Two more things universal's deep check holds a draft to that a
            # set does not (2026-10-05, five drafts from working-style): the
            # spec's field order, which a set's file may have drifted from
            # and the tool can restore without changing a value; and an
            # applies_to_why on an on-demand practice, which only a person
            # can write -- so it is named below, not invented.
            new_text = frontmatter_yaml.reorder_fields(new_text)
            why_missing = (_field(fm, 'tier') == 'on-demand'
                           and not (_field(fm, 'applies_to_why') or '').strip('" '))
        plan.append(('write', dest, new_text))

    if source_withdrawn:
        src_text = src.read_text(encoding='utf-8')
        line = f'Moved to the {to_level} set `{to_name}` on {today}'
        if from_level == 'shared':
            # Who approved the REMOVAL is recorded nowhere else
            # (spec/MOVING_PRACTICES.md, step 2, "Team").
            if not dedupe_only:
                line += f', approved there by {approved_by}'
            line += (f'; its removal from `{from_name}` approved by {approved_by}, '
                     f'one of that set\'s approvers')
        elif approved_by:
            line += f', approved there by {approved_by}'
        # The slug alone, never "in force there": lookup is by slug, and a
        # destination set can itself fold into another later, which left
        # every stub naming it false while nothing broke (very deep check,
        # 2026-10-05, pass 3). The dated "Moved to" clause above is history.
        line += f'. This copy is deduplicated; the rule stays in force under its slug, `{slug}`.'
        if duplicate_from_universal:
            # precedent_resolve.withdrawn_from_universal() reads this line
            # back to say where the rule went; keep "Withdrawn from
            # universal on <date>" and "from the <level> set `<name>`".
            line = (f'Withdrawn from universal on {today}, deliberately, with '
                    f'--accept-reach-loss'
                    + (f' (approved by {approved_by})' if approved_by else '')
                    + f': deduplicated here; the rule is in force only '
                    f'from the {to_level} set `{to_name}` now. A consumer resolving only '
                    f'universal no longer gets it.')
        src_new = _rewrite_frontmatter(src_text, {'status': 'deduplicated',
                                                  'in_force_at': slug})
        src_new = _append_story(src_new, line)
        if withdraw:
            record = pathlib.Path(from_path) / WITHDRAWN_RECORD
            entry = _pr.withdrawn_record_line(today, slug, to_level, to_name,
                                              approved_by, forwarded_to)
            plan.append(('delete', src, None))
            plan.append(('append', record, entry))
            # The set's copy was made by a duplicate move, whose approval
            # line says a universal copy stays active. After this, none
            # does: say so, keeping the approval the rule had in universal.
            if dest.is_file():
                old_approved = _raw_field(src_text, 'approved_by')
                there = f' (there: {old_approved})' if old_approved else ''
                plan.append(('write', dest, _rewrite_frontmatter(
                    dest.read_text(encoding='utf-8'),
                    {'approved_by': _quoted(
                        f'{approved_by}, {today}, withdrawn from the universal '
                        f'set {from_name}, which keeps no copy{there}')})))
            plan.append(('decommission', pathlib.Path(from_path) / DECOMMISSION_REGISTRY,
                         {'path': f'practices/{slug}.md',
                          'reason': (f'withdrawn from universal with precedent_move.py '
                                     f'--withdraw-from-universal; in force from the '
                                     f'{to_level} set {to_name} for the people who '
                                     f'bring or declare it; {WITHDRAWN_RECORD}'),
                          'decommissioned_at': today}))
        else:
            plan.append(('write', src, src_new))
    elif duplicate_from_universal:
        src_text = src.read_text(encoding='utf-8')
        line = (f'Also landed in the {to_level} set `{to_name}` on {today}'
                + (f', approved there by {approved_by}' if approved_by else '')
                + f'. Kept ACTIVE here, not deduplicated: universal is the one level '
                  f'every Precedent consumer resolves, and a plain universal-only '
                  f'consumer never resolves a pointer into `{to_name}` -- deduplicating '
                  f'this copy would leave the rule in force nowhere for them '
                  f'(the failure `verify_harness.py --as-ci`\'s consumer-fixture check '
                  f'exists to catch, and did, 2026-09-23). Both copies are genuinely in '
                  f'force; review both when editing either. Withdraw this copy later, '
                  f'deliberately, with `--dedupe-only --accept-reach-loss` once the '
                  f'audience that matters has taken `{to_name}`.')
        src_new = _append_story(src_text, line)
        plan.append(('write', src, src_new))

    for change in rehomed:
        say(f'{"would rewrite" if dry_run else "rewrote"} a sibling link that does not '
            f'travel to {to_name}: {change}')

    # A universal withdrawal also leaves the universal clone's own
    # routing-audit bookkeeping behind; see _drop_routing_audit_entry.
    withdraw_universal = source_withdrawn and from_level == 'universal'

    if dry_run:
        for op, path, _content in plan:
            say(f'would {op} {path}')
        if withdraw_universal and _drop_routing_audit_entry(from_path, slug, dry_run=True):
            say(f'would drop `{slug}` from {from_name}/tools/routing_audit_state.json')
        if source_withdrawn:
            _fix_mentions(slug, from_path, to_level, to_path, dry_run=True,
                          say=say)
        say('dry run: nothing written')
        return

    # LAND FIRST, then withdraw the source: if the second write fails, the
    # rule is in force at both ends -- a duplication, which the resolver
    # settles by precedence -- and never at neither.
    for op, path, content in plan:
        if op == 'delete':
            path.unlink()
            say(f'deleted {path}')
            continue
        if op == 'decommission':
            # The deletion is recorded where the checks look for deletions
            # made on purpose (practice-change-propagates,
            # rename-updates-links), with the withdrawal record exempt as the
            # file that names it.
            if not path.is_file():
                say(f'no {DECOMMISSION_REGISTRY} in {from_path}, so the deletion '
                    f'is recorded only in {WITHDRAWN_RECORD}')
                continue
            reg = json.loads(path.read_text(encoding='utf-8'))
            done = {e.get('path') for e in reg.get('decommissioned') or []}
            if content['path'] not in done:
                reg.setdefault('decommissioned', []).append(content)
            ex = reg.setdefault('exempt_files', [])
            if WITHDRAWN_RECORD not in ex:
                ex.append(WITHDRAWN_RECORD)
            path.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + '\n',
                            encoding='utf-8')
            say(f'recorded the deletion in {path}')
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if op == 'append':
            if not path.is_file():
                path.write_text(WITHDRAWN_RECORD_HEADER, encoding='utf-8')
            with path.open('a', encoding='utf-8') as f:
                f.write(content)
            say(f'recorded the withdrawal in {path}')
            continue
        path.write_text(content, encoding='utf-8')
        _read(path)      # the written file must parse, or say so now
        say(f'wrote {path}')
    if withdraw_universal and _drop_routing_audit_entry(from_path, slug):
        say(f'dropped `{slug}` from {from_name}/tools/routing_audit_state.json '
            f'-- a rotation entry for a practice not active there is stale')

    # Step 3: only once the source copy is actually withdrawn. Before that
    # (a universal draft, or the first landing out of universal) the old
    # copy is still in force and every mention of it is still true.
    if source_withdrawn:
        _fix_mentions(slug, from_path, to_level, to_path, dry_run=False, say=say)

    def _regen_for(level, path):
        if level == 'universal':
            return f'{path}: {_regenerate_universal(path)}'
        return _regenerate(str(pathlib.Path(path).resolve()))

    if to_level == 'universal' and not dedupe_only:
        say(f'  {_regen_for(to_level, to_path)}')
    elif to_level == 'universal' and dedupe_only:
        say(f'  {_regen_for(from_level, from_path)}')
    else:
        # to_level is shared/individual: the destination always changed.
        # The source did too -- either deduplicated (ordinary move, or the
        # deliberate --accept-reach-loss withdrawal) or kept active with a
        # new Story note (duplicate_from_universal's initial landing) --
        # and when it's universal, that regeneration needs doc_sync.py too.
        say(f'  {_regen_for(to_level, to_path)}')
        say(f'  {_regen_for(from_level, from_path)}')

    # practice: disclose-landing
    if to_level == 'universal' and not dedupe_only:
        say(f'DISCLOSE TO THE HUMAN: `{slug}` is DRAFTED into {dest} and not yet in force '
            f'anywhere new. Commit it on a branch of that Precedent clone and open a pull '
            f'request; the source copy in the {from_level} set {from_name} stays ACTIVE '
            f'until that merges. Run this tool again with --dedupe-only to withdraw the '
            f'source copy only once the pull request has merged AND every repository '
            f'consuming {from_name} has taken the new universal catalogue (INSTALL.md '
            f'\u00a72 step 0, or "Update Vendors"): a consumer that still vendors the '
            f'old catalogue sees the rule in neither source, and its next sync '
            f'prints IN FORCE NOWHERE and drops it.')
        if install_added:
            say(f'ADDED an empty ## Install to the draft: {src} had none, and every '
                f'universal practice carries one. Fill it in the pull request -- what a '
                f'repo adopting `{slug}` does to take it up -- or leave it empty if '
                f'there is nothing.')
        if checked_by_rehomed:
            say(f'REPOINTED checked_by from {checked_by_rehomed} to '
                f'tools/precedent_check.py, where `{slug}` is registered. Reword any '
                f'prose in the draft that still names {checked_by_rehomed}: it does '
                f'not exist in universal.')
        if why_missing:
            say(f'ADD an applies_to_why to the draft before pushing: `{slug}` is '
                f'on-demand, and universal\'s deep check (routing-reason) refuses an '
                f'on-demand practice that does not say why its applies_to is what it '
                f'is, and which channel reaches it.')
    elif withdraw and forwarded_to:
        say(f'DISCLOSE TO THE HUMAN: the retired name `{slug}` (forwarding to '
            f'`{forwarded_to}`) is now WITHDRAWN from universal and its file there '
            f'is deleted; the {to_level} set {to_name} keeps it as history. The '
            f'withdrawal is recorded in {WITHDRAWN_RECORD}. Commit both sets.')
    elif withdraw:
        say(f'DISCLOSE TO THE HUMAN: `{slug}` is now WITHDRAWN from universal and its '
            f'file there is deleted; it is in force only from the {to_level} set '
            f'{to_name}, for the people who bring or declare it. Nobody else sees '
            f'it, and no sync anywhere reports it missing. The withdrawal is '
            f'recorded in {WITHDRAWN_RECORD}. Commit both sets.')
    elif duplicate_from_universal and dedupe_only:
        say(f'DISCLOSE TO THE HUMAN: `{slug}` is now WITHDRAWN from universal -- '
            f'deduplicated in {from_name}, in force only from the {to_level} set '
            f'{to_name}. Any consumer that resolves only universal (most of them) no '
            f'longer gets this rule at all -- --accept-reach-loss was required for '
            f'this step for exactly that reason.')
    elif duplicate_from_universal:
        say(f'DISCLOSE TO THE HUMAN: `{slug}` now ALSO lives in the {to_level} set '
            f'{to_name}, approved by {approved_by}. The universal copy in {from_name} '
            f'stays ACTIVE and is NOT deduplicated -- withdrawing it would break every '
            f'consumer that does not declare {to_name}, which is most of them. Both '
            f'copies are genuinely in force; edit either and check the other. Run this '
            f'tool again with --dedupe-only --accept-reach-loss, deliberately, if and '
            f'when withdrawing the universal copy is the right call.')
    elif dedupe_only:
        say(f'DISCLOSE TO THE HUMAN: `{slug}` is now deduplicated in the {from_level} set '
            f'{from_name}; the rule is in force from the {to_level} set {to_name}.')
    else:
        say(f'DISCLOSE TO THE HUMAN: `{slug}` now lives in the {to_level} set {to_name}, '
            f'approved by {approved_by}, and is in force from there; its copy in the '
            f'{from_level} set {from_name} is deduplicated and points at it. Commit both '
            f'sets; a consumer takes the move on its next sync.')


def mentions_only(slug, from_level, from_path, to_level, to_path,
                  dry_run=False, say=print):
    """Step 3 alone, for a move made before the tool fixed mentions."""
    to_level = LEVEL_ALIASES.get(to_level, to_level)
    src, dest = _practice_path(from_path, slug), _practice_path(to_path, slug)
    withdrawn = (not src.is_file()
                 and slug in _pr.withdrawn_record(from_path))
    # A retired name withdrawn with the rule it forwarded to is kept as
    # history at the destination, never active there.
    checks = [(dest, 'deduplicated' if withdrawn
               and slug in _pr.withdrawn_history(from_path) else 'active')]
    if not withdrawn:
        # A rule deleted by --withdraw-from-universal has no stub to read;
        # its record line is the proof it left. Anything else must be a
        # deduplicated stub, as before.
        checks.insert(0, (src, 'deduplicated'))
    for path, want in checks:
        if not path.is_file():
            raise MoveRefused(f'{path} does not exist')
        got = _field(_read(path)[0], 'status') or 'active'
        if got != want:
            raise MoveRefused(f'{path} is status: {got}, not {want} -- '
                              f'--mentions-only fixes mentions of a practice '
                              f'that has already left {from_path}')
    changed = _fix_mentions(slug, from_path, to_level, to_path,
                            dry_run=dry_run, say=say)
    if not changed:
        say(f'nothing to fix: no current mention of `{slug}` still places it '
            f'in {pathlib.Path(from_path).resolve().name}')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0
    opts = {'--slug': None, '--from': None, '--from-path': None, '--to': None,
            '--to-path': None, '--approved-by': None, '--strength': None, '--story': None}
    flags = {'--dry-run': False, '--dedupe-only': False, '--accept-reach-loss': False,
             '--mentions-only': False, '--withdraw-from-universal': False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in flags:
            flags[a] = True
        elif a in opts:
            i += 1
            if i >= len(argv):
                print(f'precedent_move FAIL: {a} needs a value', file=sys.stderr)
                return 1
            opts[a] = argv[i]
        else:
            print(f'precedent_move FAIL: unknown argument {a!r}', file=sys.stderr)
            return 1
        i += 1
    missing = [k for k in ('--slug', '--from', '--from-path', '--to', '--to-path') if not opts[k]]
    if missing:
        print(f'precedent_move FAIL: missing {", ".join(missing)}', file=sys.stderr)
        return 1
    if flags['--mentions-only']:
        try:
            mentions_only(opts['--slug'], opts['--from'], opts['--from-path'],
                          opts['--to'], opts['--to-path'], dry_run=flags['--dry-run'])
        except MoveRefused as e:
            print(f'precedent_move FAIL: {e}', file=sys.stderr)
            return 1
        return 0
    try:
        move(opts['--slug'], opts['--from'], opts['--from-path'], opts['--to'],
             opts['--to-path'], opts['--approved-by'], strength=opts['--strength'],
             story=opts['--story'], dry_run=flags['--dry-run'],
             dedupe_only=flags['--dedupe-only'],
             accept_reach_loss=flags['--accept-reach-loss'],
             withdraw=flags['--withdraw-from-universal'])
    except MoveRefused as e:
        print(f'precedent_move FAIL: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
