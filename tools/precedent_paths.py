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
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRACTICES_DIR = ROOT / 'practices'

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp


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


def normalize_path(path):
    """A glob is written relative to the repo root, so a path has to be too
    before it can be compared against one. A PreToolUse hook hands over
    absolute paths; a person types "./AGENTS.md" as often as "AGENTS.md".
    All three spellings of one file must give one answer."""
    p = str(path).replace('\\', '/')
    root = ROOT.as_posix().rstrip('/') + '/'
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


def path_matches(path, glob):
    return _glob_regex(glob).match(normalize_path(path)) is not None


def _globs(fm_applies_to):
    # frontmatter value is a JSON-array literal, e.g. '["**/*.md"]'
    try:
        return json.loads(fm_applies_to)
    except (json.JSONDecodeError, TypeError):
        return []


def load_on_demand_practices():
    out = []
    for f in sorted(PRACTICES_DIR.glob('*.md')):
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


def matches_for_paths(paths, practices=None):
    """-> list of (slug, path) for every (practice, path) pair where the
    path matches one of the practice's narrower-than-** applies_to globs."""
    practices = practices if practices is not None else load_on_demand_practices()
    hits = []
    for slug, globs, _rule in practices:
        for path in paths:
            if any(path_matches(path, g) for g in globs):
                hits.append((slug, path))
                break
    return hits


def main():
    args = sys.argv[1:]
    matches_only = '--matches-only' in args
    # An unrecognized "--flag" used to be silently dropped and the run
    # continued, so a typo produced a confident answer to a different
    # question. Same failure class precedent_show.py had.
    unknown = [a for a in args if a.startswith('--') and a != '--matches-only']
    if unknown:
        sys.exit(f"precedent paths FAIL: unknown option(s) {', '.join(unknown)} -- "
                 f"the only option is --matches-only.")
    paths = [a for a in args if not a.startswith('--')]
    if not paths:
        sys.exit(__doc__)

    practices = load_on_demand_practices()
    hits = matches_for_paths(paths, practices)
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

    rule_by_slug = {slug: rule for slug, _globs, rule in practices}
    out = [f"### {slug}\n{rule_by_slug[slug].strip()}" for slug in seen_slugs]
    print('\n\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
