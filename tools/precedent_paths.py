#!/usr/bin/env python3
"""precedent_paths.py — the path-triggered loading channel
(PRACTICE_ENGINE_PLAN.md, "How an Agent Knows Which Practices to Load":
"A PreToolUse hook matches the edited file against every practice's
applies_to globs and prints the matching ## Rule sections.").

Given one or more file paths (the files a tool is about to touch), prints
the ## Rule section of every on-demand practice whose applies_to glob
matches at least one of them. Resident practices are never printed here —
they are already in context via the generated AGENTS.md block — and a
practice matching only "**" is not printed either, since applies_to: ["**"]
means "no narrower-than-everything scope", not "route this on every touch"
(reachability for those practices comes from checked_by or occasion instead;
see spec/PRACTICE_FORMAT.md).

This is deliberately the same code path a PreToolUse hook shells out to and
that tools/behavioral_replay.py drives against historical commits, per the
plan's "one code path" principle for the loader (Loading a Practice Means
Loading Its Rule, Not Its File).

Run:
  python3 tools/precedent_paths.py FILE [FILE...]
  python3 tools/precedent_paths.py --matches-only FILE [FILE...]
      -- print only "slug: file" pairs, no Rule text (used by
         behavioral_replay.py, which only needs to know what matched)
  python3 tools/precedent_paths.py --repo DIR FILE [FILE...]
      -- match against DIR's practices/ instead of this repo's own
  python3 tools/precedent_paths.py --seen-file PATH FILE [FILE...]
      -- print a practice's full Rule the FIRST time this session matches
         it, and a one-line reminder every time after. PATH is a
         session-scoped scratch file this tool appends slugs to; a missing
         or unreadable one just means "nothing seen yet", never an error.

WHY --seen-file EXISTS. Measured on this repo, 2026-09-06: an edit to any
markdown file matches ten on-demand practices and prints ~1,000 words of
Rule text. A session that edits thirty markdown files was being handed the
same ~1,000 words thirty times -- around forty thousand tokens of exact
duplication, in a mechanism whose entire purpose is to spend context
carefully. The Rules do not change between the first edit and the
thirtieth; only the reminder that they apply is worth repeating, and a
slug plus its one-line clause is that reminder. The full text stays one
`precedent_show.py SLUG` away, and the reminder names the slug precisely
so that call is easy to make.
"""
import json, pathlib, re, sys

# _ENGINE_DIR (where this file itself lives) is only ever used for the
# sibling-module import below -- never for --repo. ROOT is which repo's
# CONTENT (practices/, and the root a given path is normalized against) to
# operate on; it defaults to the engine's own parent directory but is
# overridable with --repo in main() -- see precedent_show.py for the fuller
# rationale, and precedent_sync_views.py's own docstring for the trap this
# avoids (computing ROOT from `__file__` alone breaks the moment this script
# is relocated or vendored somewhere other than <repo>/tools/whatever.py).
_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = _ENGINE_DIR.parent  # unchanged default when --repo is omitted
PRACTICES_DIR = ROOT / 'practices'

sys.path.insert(0, str(_ENGINE_DIR))
import split_practices as sp
# TODO.md item 20 (was 19): this channel read practices/*.md directly,
# bypassing precedent_show.py's materialized-source reachability note
# (PR #114). Fixed by importing precedent_show.py's two helpers directly
# -- same discipline this file already uses for split_practices.py, not a
# subprocess call (would mean re-parsing precedent_show.py's own stdout
# format back into structured data here for no reason) and not a
# copy-pasted second implementation (engine-plus-host-shims).
import precedent_show as ps
import build_views as bv


# ---------------------------------------------------------------- matching
# `applies_to` globs are repo-root-relative and use the recursive-glob
# convention the plan's own examples assume ("**", "**/*.md",
# "book/CHAPTER1.md"): `**` crosses directory separators, a single `*` and
# `?` do not.
#
# This used to be a bare fnmatch.fnmatch(path, glob), which is WRONG for
# both halves of that, and wrong in the direction that loses practices
# silently. fnmatch has no `**`: it expands every `*` to ".*", so
# "**/*.md" becomes ".*.*/.*\.md" -- which REQUIRES a literal "/" and
# therefore never matches a top-level file. Editing AGENTS.md, README.md,
# TODO.md, PRACTICES.md or any other root document surfaced ZERO of the
# eight document practices scoped to "**/*.md". Worse, the same file
# spelled "./AGENTS.md" DID match, so the answer depended on how the path
# was typed. Measured over this repo's own history, that silently dropped
# 520 (practice, commit) instances across 65 of 86 commits -- and it is
# precisely the failure the plan names as this design's real weak point:
# "a practice with a wrong or missing trigger is worse than one buried in
# a wall of text, because nobody notices its absence."
_GLOB_CACHE = {}


def _glob_regex(glob):
    """Recursive-glob -> compiled regex. `**/` matches zero or more whole
    path segments; `*` and `?` never cross a "/"."""
    rx = _GLOB_CACHE.get(glob)
    if rx is not None:
        return rx
    out, i, n = [], 0, len(glob)
    while i < n:
        c = glob[i]
        if glob.startswith('**/', i):
            out.append('(?:[^/]+/)*'); i += 3
        elif glob.startswith('/**', i) and i + 3 == n:
            out.append('/.+'); i += 3          # "dir/**" = everything INSIDE dir
        elif glob.startswith('**', i):
            out.append('.*'); i += 2
        elif c == '*':
            out.append('[^/]*'); i += 1
        elif c == '?':
            out.append('[^/]'); i += 1
        elif c == '[':
            j = i + 1
            if j < n and glob[j] in '!^':
                j += 1
            if j < n and glob[j] == ']':
                j += 1
            while j < n and glob[j] != ']':
                j += 1
            if j >= n:                          # unterminated class: literal
                out.append(re.escape(c)); i += 1
            else:
                body = glob[i + 1:j]
                body = '^' + body[1:] if body[:1] in ('!',) else body
                out.append('[' + body + ']'); i = j + 1
        else:
            out.append(re.escape(c)); i += 1
    rx = re.compile('(?s:' + ''.join(out) + r')\Z')
    _GLOB_CACHE[glob] = rx
    return rx


def normalize_path(path, root_dir=None):
    """A glob is written relative to the repo root, so a path has to be too
    before it can be compared against one. A PreToolUse hook hands over
    absolute paths; a person types "./AGENTS.md" as often as "AGENTS.md".
    All three spellings of one file must give one answer.

    root_dir defaults to ROOT (this repo's own root) -- pass the --repo
    target explicitly when normalizing against a different repo's tree."""
    root_dir = root_dir if root_dir is not None else ROOT
    p = str(path).replace('\\', '/')
    root = root_dir.as_posix().rstrip('/') + '/'
    if p.startswith(root):
        p = p[len(root):]
    elif p.startswith('/'):
        # The fast path above only matches when the caller's absolute path
        # already shares ROOT's own fully-resolved spelling. A path reached
        # through a symlinked route to the repo (a symlinked workspace, a
        # bind mount) does not, and used to fall through untouched -- the
        # leading '/' got stripped anyway below, turning e.g.
        # "/tmp/bp-link/README.md" into "tmp/bp-link/README.md" with no
        # error. A broad "**/*.md" glob still matched by coincidence; an
        # exact-filename glob like "README.md" silently stopped matching,
        # with nothing reporting it. resolve() does not require the path to
        # exist, so this is safe for a path a git diff names for a file
        # that was since deleted.
        try:
            resolved = pathlib.Path(p).resolve().as_posix()
        except (OSError, RuntimeError):
            # A symlink LOOP (a -> b -> a) makes resolve() raise rather than
            # return -- uncaught, this took down every caller (the
            # PreToolUse hook, behavioral_replay.py) with a traceback for a
            # path that merely happens to contain a loop somewhere, rather
            # than degrading the way "resolve() does not require the path to
            # exist" already promises just above. Fall through on the
            # unresolved spelling, same as any other path this function
            # cannot map back under ROOT.
            resolved = None
        if resolved is not None and resolved.startswith(root):
            p = resolved[len(root):]
    while p.startswith('./'):
        p = p[2:]
    return p.lstrip('/')


def path_matches(path, glob, root_dir=None):
    return _glob_regex(glob).match(normalize_path(path, root_dir)) is not None


def _globs(fm_applies_to):
    # frontmatter value is a JSON-array literal, e.g. '["**/*.md"]'
    try:
        return json.loads(fm_applies_to)
    except (json.JSONDecodeError, TypeError):
        return []


def load_on_demand_practices(practices_dir=None):
    practices_dir = practices_dir if practices_dir is not None else PRACTICES_DIR
    out = []
    for f in sorted(practices_dir.glob('*.md')):
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError as e:
            sys.exit(f"precedent paths FAIL: {e}")
        if fm.get('tier') != 'on-demand':
            continue
        globs = _globs(fm.get('applies_to', '[]'))
        narrow_globs = [g for g in globs if g != '**']
        if not narrow_globs:
            continue
        out.append((fm['slug'], narrow_globs, sections.get('rule', '')))
    return out


def matches_for_paths(paths, practices=None, root_dir=None):
    """-> list of (slug, path) for every (practice, path) pair where the
    path matches one of the practice's narrower-than-** applies_to globs."""
    practices = practices if practices is not None else load_on_demand_practices()
    hits = []
    for slug, globs, _rule in practices:
        for path in paths:
            if any(path_matches(path, g, root_dir) for g in globs):
                hits.append((slug, path))
                break
    return hits


def _read_seen(seen_file):
    """Slugs already shown in full this session. A missing, unreadable or
    malformed file means "nothing yet" -- this is a context optimization,
    and failing a tool call over its scratch file would be a far worse
    outcome than showing a Rule twice."""
    if seen_file is None:
        return set()
    try:
        return {line.strip() for line in
                seen_file.read_text(encoding='utf-8').splitlines() if line.strip()}
    except OSError:
        return set()


def _append_seen(seen_file, slugs):
    if seen_file is None or not slugs:
        return
    try:
        seen_file.parent.mkdir(parents=True, exist_ok=True)
        with seen_file.open('a', encoding='utf-8') as fh:
            for slug in slugs:
                fh.write(slug + '\n')
    except OSError:
        pass        # same reasoning as _read_seen: never fail the tool call


def _clause_for(practices_dir, slug):
    """The practice's own one-line `index_clause` -- the same sentence the
    generated occasion index uses, so the brief reminder and the index
    agree by construction instead of by a second hand-written summary."""
    path = practices_dir / f'{slug}.md'
    try:
        fm, _sections = sp._read_practice_file(path)
    except Exception:
        return 'applies here'
    return bv._json_str(fm.get('index_clause', '')) or 'applies here'


def main():
    args = sys.argv[1:]
    repo = None
    if '--repo' in args:
        i = args.index('--repo')
        if i + 1 >= len(args):
            sys.exit("precedent paths FAIL: --repo needs a value.")
        repo = args[i + 1]
        args = args[:i] + args[i + 2:]
    root = pathlib.Path(repo).resolve() if repo else ROOT
    practices_dir = root / 'practices'

    seen_file = None
    if '--seen-file' in args:
        i = args.index('--seen-file')
        if i + 1 >= len(args):
            sys.exit("precedent paths FAIL: --seen-file needs a value.")
        seen_file = pathlib.Path(args[i + 1])
        args = args[:i] + args[i + 2:]

    matches_only = '--matches-only' in args
    # An unrecognized "--flag" used to be silently dropped and the run
    # continued, so a typo produced a confident answer to a different
    # question. Same failure class precedent_show.py had.
    unknown = [a for a in args if a.startswith('--') and a != '--matches-only']
    if unknown:
        sys.exit(f"precedent paths FAIL: unknown option(s) {', '.join(unknown)} -- "
                 f"the options are --matches-only, --repo and --seen-file.")
    paths = [a for a in args if not a.startswith('--')]
    if not paths:
        sys.exit(__doc__)

    practices = load_on_demand_practices(practices_dir)
    hits = matches_for_paths(paths, practices, root)
    if not hits:
        if matches_only:
            return 0
        print("(no on-demand practice's applies_to matches the given path(s))")
        return 0

    seen_slugs = []
    for slug, path in hits:
        if slug not in seen_slugs:
            seen_slugs.append(slug)

    if matches_only:
        for slug, path in hits:
            print(f"{slug}: {path}")
        return 0

    manifest = ps._materialize_manifest(root)
    rule_by_slug = {slug: rule for slug, _globs, rule in practices}
    already = _read_seen(seen_file)
    out, brief = [], []
    for slug in seen_slugs:
        if slug in already:
            brief.append(f"{slug} — {_clause_for(practices_dir, slug)}")
            continue
        block = f"### {slug}\n{rule_by_slug[slug].strip()}"
        if manifest is not None:
            note = ps._source_unreachable_note(manifest, slug)
            if note:
                block += f"\n{note}"
        out.append(block)
    if brief:
        out.append("### Already loaded this session — still apply\n"
                   + '\n'.join(f"- {b}" for b in brief)
                   + "\n\nRun `python3 tools/precedent_show.py SLUG` for the "
                     "full Rule of any of these.")
    _append_seen(seen_file, [s for s in seen_slugs if s not in already])
    print('\n\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
