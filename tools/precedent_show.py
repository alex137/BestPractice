#!/usr/bin/env python3
"""precedent_show.py — the one code path every loading channel calls
(PRACTICE_ENGINE_PLAN.md, "Loading a Practice Means Loading Its Rule, Not
Its File"). An agent never reads a practices/*.md file directly: it calls
this, and only this command's output enters context. That is what makes the
Rule/Detail/Why/Story/Install split actually save tokens — reading the file directly would
front-load the whole thing, Story included, defeating the split.

  precedent show SLUG [SLUG...]           the ## Rule section of each
  precedent show SLUG [SLUG...] --detail   the ## Detail section of each --
                                            the operational specifics, loaded
                                            when actually doing the work
                                            rather than when deciding whether
                                            the practice applies
  precedent show SLUG [SLUG...] --why      the ## Why section of each
  precedent show SLUG [SLUG...] --story    the ## Story section of each
  precedent show SLUG [SLUG...] --install  the ## Install section of each
                                            (not in the plan's own original
                                            three-section spec -- see
                                            spec/PRACTICE_FORMAT.md for why
                                            this repo's practice files carry
                                            five body sections)
  precedent show SLUG [SLUG...] --repo DIR  read DIR's practices/ instead of
                                            this repo's own -- defaults to
                                            this script's own parent repo
                                            when omitted

Multiple slugs concatenate, each under its own "### slug" heading, so a
caller loading several practices for one occasion gets one block back.

Exit 1, with a clear message naming the missing slug, on any slug that
doesn't resolve to a practices/*.md file -- this is a degrade-gracefully
tool (personal pack fail-gracefully, generalized): a bad slug in an occasion
index entry should be loud, not a silent empty read.
"""
import pathlib, re, sys

# Two different notions of "root" that must never be conflated: _ENGINE_DIR
# is where THIS SCRIPT physically lives, and is the only thing sibling-module
# imports (split_practices, below) may ever depend on -- wherever this file
# is, split_practices.py is right there too. ROOT is which repo's CONTENT
# (practices/) to read, which defaults to the engine's own parent directory
# but is overridable with --repo (see main()) -- the fix for the exact trap
# precedent_sync_views.py's own docstring already warns about: computing
# ROOT from `__file__` breaks the moment this script is relocated or
# vendored somewhere other than <repo>/tools/whatever.py.
_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = _ENGINE_DIR.parent  # unchanged default when --repo is omitted
PRACTICES_DIR = ROOT / 'practices'

sys.path.insert(0, str(_ENGINE_DIR))
import split_practices as sp

SECTION_FLAGS = {'--detail': 'detail', '--why': 'why', '--story': 'story',
                 '--install': 'install'}

# The plan requires Detail to come from THIS command, not a second one
# (PRACTICE_ENGINE_PLAN.md, phase-3 row): "## Detail must be reachable from
# the same `precedent show` command". A separate `precedent detail` would be
# a second extractor to drift from this one, which is the failure the "one
# code path" rule exists to prevent.

# A slug is an identity, not a path. Without this, `precedent show
# ../PRACTICES` cheerfully opened practices/../PRACTICES.md -- the whole
# 200KB catalogue -- and died on a bare AssertionError with no message.
SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def main():
    args = sys.argv[1:]
    repo = None
    if '--repo' in args:
        i = args.index('--repo')
        if i + 1 >= len(args):
            sys.exit("precedent show FAIL: --repo needs a value.")
        repo = args[i + 1]
        args = args[:i] + args[i + 2:]
    root = pathlib.Path(repo).resolve() if repo else ROOT
    practices_dir = root / 'practices'

    section = 'rule'
    for flag, sec in SECTION_FLAGS.items():
        if flag in args:
            section = sec
            args = [a for a in args if a != flag]

    # Anything still starting with "--" is a flag this tool does not know.
    # Silently ignoring it meant `--wy` (a typo for --why) printed the Rule
    # and exited 0 -- the caller gets a confident answer to a question it
    # did not ask, which is exactly the silent failure this tool's whole
    # reason for existing is to avoid.
    unknown = [a for a in args if a.startswith('--')]
    if unknown:
        sys.exit(f"precedent show FAIL: unknown option(s) {', '.join(unknown)} -- "
                 f"known options are {', '.join(sorted(SECTION_FLAGS))}.")

    slugs = args
    if not slugs:
        sys.exit(__doc__)

    malformed = [s for s in slugs if not SLUG_RE.match(s)]
    if malformed:
        sys.exit(f"precedent show FAIL: not valid slug(s): {', '.join(malformed)} -- "
                 f"a slug is lowercase, hyphenated, and names a practice, not a path.")

    out = []
    missing = []
    for slug in slugs:
        path = practices_dir / f'{slug}.md'
        if not path.exists():
            missing.append(slug)
            continue
        try:
            _fm, sections = sp._read_practice_file(path)
        except sp.PracticeFileError as e:
            sys.exit(f"precedent show FAIL: {e}")
        body = sections.get(section, '').strip()
        out.append(f"### {slug}\n{body if body else '(no ' + section + ' recorded yet)'}")

    if missing:
        sys.exit(f"precedent show FAIL: unknown slug(s), no practices/*.md file for: "
                 f"{', '.join(missing)}")

    print('\n\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
