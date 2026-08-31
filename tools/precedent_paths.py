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
import fnmatch, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRACTICES_DIR = ROOT / 'practices'

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp


def _globs(fm_applies_to):
    # frontmatter value is a JSON-array literal, e.g. '["**/*.md"]'
    import json
    try:
        return json.loads(fm_applies_to)
    except (json.JSONDecodeError, TypeError):
        return []


def load_on_demand_practices():
    out = []
    for f in sorted(PRACTICES_DIR.glob('*.md')):
        fm, sections = sp._read_practice_file(f)
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
            if any(fnmatch.fnmatch(path, g) for g in globs):
                hits.append((slug, path))
                break
    return hits


def main():
    args = sys.argv[1:]
    matches_only = '--matches-only' in args
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
