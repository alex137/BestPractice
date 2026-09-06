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

WHEN practices/ IS A tools/precedent_materialize.py-PRODUCED SNAPSHOT (a
consumer repo resolving universal/team/individual/repo-local together,
signalled by that directory's own MANIFEST.json -- never true for a source
repo's own hand-authored practices/): a slug whose declared source is not
reachable THIS session gets a trailing note naming that, on the READ side
of the gap practices/session-bootstrap.md's Story records on the write
side -- a materialized file is whatever was on disk at the last successful
materialize() run, and reading it proves nothing about whether that run's
source is still there today. See _source_unreachable_note's own docstring
for what this checks (a cheap directory probe) and deliberately does not
(a full precedent_resolve.py re-resolve, or a content-drift check against
the live source -- precedent_sync_views.py --check already owns that, at
the whole-tree granularity where it belongs).
"""
import json, pathlib, re, sys

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
import build_views as bv

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


def _not_in_force_banner(fm, slug):
    """A banner for a practice whose rule does NOT apply here, or None.

    WHY THIS MARKS RATHER THAN REFUSES. Naming a slug explicitly is usually
    a session asking "what happened to this?", and once `in_force_at:`
    exists the answer is more useful than a refusal -- a refusal sends the
    reader hunting through git history for a forwarding address the
    frontmatter is already holding. The other three channels
    (build_views.py, precedent_resolve.py, precedent_paths.py,
    precedent_gate.py) enumerate practices and must DROP these; this one is
    addressed by name and shows them, marked.

    WHY THE BANNER GOES ABOVE THE RULE, not below it (2026-09-06). Every
    consumer of this output is a session that reads top-down and may stop
    early. A footnote under a 200-word Rule is read after the rule has
    already been taken as current, which is the failure this whole status
    vocabulary exists to prevent, reproduced one layer down."""
    if bv.is_in_force(fm):
        return None
    status = bv.practice_status(fm)
    target = bv._json_str(fm.get('in_force_at', '')) or ''
    if status == bv.DEDUPLICATED_STATUS:
        if target and target != 'none':
            where = (f"the engine itself enforces it -- there is no practice to load"
                     if target == 'engine'
                     else f"the rule is in force at `{target}`; load that instead")
        else:
            # Declared redundant with no forwarding address. The check in
            # verify_harness.py refuses this, so reaching it means the file
            # was hand-edited past the check -- say so rather than implying
            # a successor exists.
            where = ("no `in_force_at:` recorded, so where the rule survives is "
                     "NOT known from this file -- treat it as unresolved")
        return (f"> NOT IN FORCE HERE (status: {status}) -- this copy is "
                f"redundant, {where}.")
    if status == bv.RETIRED_STATUS:
        if target == bv.IN_FORCE_AT_NOWHERE:
            return (f"> NOT IN FORCE ANYWHERE (status: {status}, "
                    f"in_force_at: none) -- this rule was withdrawn, not "
                    f"moved. See its ## Story for why "
                    f"(precedent_show.py {slug} --story).")
        # A LEGACY RECORD, and the one case where saying less is the whole
        # point. Before `in_force_at:` existed, `retired` covered BOTH a
        # withdrawn rule and a redundant copy of one still fully in force
        # elsewhere -- that ambiguity is the defect this vocabulary exists
        # to remove, and every real use of the old status turned out to be
        # the second kind. So this must NOT be reported as a withdrawal:
        # asserting "withdrawn, not moved" from a record that says no such
        # thing states the confusion as fact instead of merely inheriting
        # it, which is worse than the silence it replaced.
        return (f"> NOT IN FORCE HERE (status: {status}) -- and this record "
                f"PREDATES `in_force_at:`, so it does not say whether the "
                f"rule survives elsewhere. Do not read it as withdrawn: "
                f"under the older vocabulary `retired` covered both a "
                f"withdrawn rule and a redundant copy of a live one. Run "
                f"`precedent_migrate_status.py` to classify it.")
    return (f"> NOT IN FORCE (status: {status}) -- a status this engine does "
            f"not recognize, so the practice is treated as not current. "
            f"Known statuses: {', '.join(bv.KNOWN_STATUSES)}.")


def _materialize_manifest(root):
    """`root`'s MANIFEST.json if practices/ there is a
    tools/precedent_materialize.py-produced snapshot (a consumer/installing
    repo resolving universal/team/individual/repo-local together) -- None
    for a source repo's own hand-authored practices/, which never has one.
    Same detection this codebase already uses elsewhere for the identical
    question (HavrutaBrainstorm's tools/checks/check_light_check.py's
    _practices_are_materialized): keyed off MANIFEST.json's own
    `generated_by`, not a path guess -- so this never fires, and never has
    to be told not to, for BestPractice checking itself or for an
    individual/team set's own repo."""
    manifest_path = root / 'MANIFEST.json'
    if not manifest_path.is_file():
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get('generated_by') != 'tools/precedent_materialize.py':
        return None
    return data


def _source_unreachable_note(manifest, slug):
    """Reading a materialized practices/<slug>.md (practice: verify-postcondition)
    tells a caller what was on disk at the last
    successful `precedent_materialize.py` run, never whether the source
    that produced it is reachable THIS session. Both incidents
    practices/session-bootstrap.md's Story records were exactly this
    shape one level up (a hook silently not having run); this is the same
    gap at the read side -- a session can get a clean, confident-looking
    Rule printout while the individual (or team) source that produced it
    dropped off hours or days ago, with nothing to tell the two apart.

    Deliberately a CHEAP, TARGETED probe, not a full precedent_resolve.py
    re-resolve: reachability here is a local filesystem property (does the
    source's own declared directory still exist), never a network round
    trip, so a full resolve -- which would re-parse every OTHER practice
    file in that source too, just to answer this one yes/no question --
    buys no accuracy a directory check doesn't already give, for real,
    avoidable cost on every single `precedent show` call. It also does not
    check whether the slug's CONTENT has since changed at the source
    (a reachable-but-newer-upstream case) -- that is what
    `precedent_sync_views.py --check` already exists to catch, at the
    whole-tree level where re-parsing every source is the actual job, not
    a cost to avoid; duplicating it here at single-slug granularity would
    overlap that tool rather than complement it.

    -> a note string when this slug's declared source is not currently
    reachable; None on the ordinary, working path (nothing is printed
    there -- this is additive only to the failure case, not noise on
    every call)."""
    practice = next((p for p in manifest.get('practices', [])
                     if p.get('slug') == slug), None)
    if practice is None:
        return None  # not a slug this manifest's materialize run produced
    source = next((s for s in manifest.get('sources', [])
                  if s.get('name') == practice.get('source')
                  and s.get('level') == practice.get('level')), None)
    if source is None or not source.get('path'):
        return None  # the manifest doesn't name a path for this slug's own source -- nothing to check against
    if (pathlib.Path(source['path']) / 'practices').is_dir():
        return None  # reachable right now
    when = manifest.get('generated_at_utc', 'an unknown time')
    return (f"(source: {practice.get('level')}, materialized {when} -- "
            f"NOT reachable this session; treat this content as possibly stale)")


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

    manifest = _materialize_manifest(root)

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
        block = f"### {slug}\n{body if body else '(no ' + section + ' recorded yet)'}"
        banner = _not_in_force_banner(_fm, slug)
        if banner:
            block = f"### {slug}\n{banner}\n\n{body}" if body else f"### {slug}\n{banner}"
        if manifest is not None:
            note = _source_unreachable_note(manifest, slug)
            if note:
                block += f"\n{note}"
        out.append(block)

    if missing:
        sys.exit(f"precedent show FAIL: unknown slug(s), no practices/*.md file for: "
                 f"{', '.join(missing)}")

    print('\n\n'.join(out))
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
