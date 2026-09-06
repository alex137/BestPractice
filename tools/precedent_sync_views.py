#!/usr/bin/env python3
"""precedent_sync_views.py — one command for a CONSUMING repo to refresh its
own generated AGENTS.md loader block from every source it resolves
(universal + team + individual + repo-local), instead of remembering to run
tools/precedent_materialize.py and then tools/build_views.py --agents-only
separately, with matching --repo/--out arguments each time.

This is glue over two already-existing, independently tested tools, not a
new mechanism:

  1. tools/precedent_materialize.py — resolve() every declared source
     (precedent_resolve.py) and write the merged practices/ + tools/checks/
     into the target repo, refusing an over-budget resident set or a
     tools/checks/ filename collision across sources.
  2. tools/build_views.py's build_loader_block() (the SAME renderer this
     repo uses on its own single-source catalogue) — fed the resolved
     practices directly from step 1's in-memory result, not re-read from
     disk, so this never risks parsing something materialize() just wrote
     differently than materialize() itself understood it.

What this tool does NOT do: generate MAP.md or GLOSSARY.md (those assume
this repo's own structure — see build_views.py's --agents-only, which this
tool always uses the equivalent of), or vendor the engine scripts
themselves (precedent_resolve.py, precedent_materialize.py, build_views.py,
precedent_show.py, precedent_paths.py, precedent_gate.py, split_practices.py
all need to already be sitting together in the consuming repo's own tools/
— INSTALL.md's existing vendoring model, or cloning/copying this repo's
tools/, same as precedent_materialize.py's own docstring already says).

Run:
  python3 tools/precedent_sync_views.py [--repo DIR] [--user-config PATH] [--check]

  --repo defaults to this script's own directory's parent — correct only
  when this script is vendored at the consuming repo's own tools/, sitting
  beside precedent_resolve.py/precedent_materialize.py/build_views.py, the
  documented convention. It is NOT this script's current working directory
  and NOT necessarily correct if this script is nested somewhere else (a
  fresh `process/upstream/tools/` mirror of BestPractice's OWN tree is the
  wrong place for it — that copy exists for the audit/sync tools, not this
  one). Override with --repo when testing against a fixture.

Exit: 0 on a clean sync, 1 on anything precedent_materialize.py or the
resident-budget check would themselves exit 1 on (a resolve conflict, a
tools/checks/ filename collision, an over-budget resident set), or on
--check finding drift.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_resolve as pr  # noqa: E402
import precedent_materialize as pm  # noqa: E402
import build_views as bv  # noqa: E402


def sync(repo, user_config=None, check=False):
    """-> (written, checks_written, rstats, agents_md_path, changed: bool,
    tree_drift: [str]).  tree_drift is always empty unless check=True.
    Raises pr.ResolveError or pm.MaterializeError on failure, exactly as
    the two tools this wraps would -- this function is thin on purpose,
    the two tools underneath carry all the real logic and all the real
    test coverage."""
    sources = pr.load_config(repo, user_config)
    if not sources:
        raise pr.ResolveError(
            f"no practice sources are declared for {repo}. A consuming repo "
            f"declares universal, team and repo-local sources in a tracked "
            f"precedent.json; a person declares their own individual set in "
            f"their user-level config ({pr.DEFAULT_USER_CONFIG}, or "
            f"{pr.USER_CONFIG_ENV}).")
    res = pr.resolve(sources)
    for m in res['missing']:
        print(f"precedent_sync_views: the {m['level']} source {m['name']!r} "
              f"is not available ({m['reason']}). Syncing WITHOUT it.",
              file=sys.stderr)

    # --check writes nothing at all -- not the materialized tree either.
    # It used to write it: --check guarded only the AGENTS.md write below
    # while materialize() ran unconditionally, so the documented read-only
    # drift check rewrote practices/, tools/checks/ and MANIFEST.json on
    # every run, and deleted a whole source's files whenever that source
    # happened to be unreachable. See precedent_materialize.drift().
    # A source that RESOLVED but contributed nothing. `missing` above covers
    # a source that could not be found; this is the other shape -- the path
    # exists, the resolver is happy, and the source is simply empty, so the
    # repo syncs with that whole catalogue silently gone. Verified 2026-09-06:
    # emptying a universal source's practices/ left both
    # `precedent_resolve.py` and this tool reporting success, with only a
    # "0 universal" in a count line that nothing reads.
    #
    # Retired practices count as contributed: a source that deliberately
    # retired everything is a decision, not an accident.
    contributed = {}
    for group in ('practices', 'retired', 'shadowed', 'blocked'):
        for entry in (res.get(group) or {}).values() if isinstance(
                res.get(group), dict) else (res.get(group) or []):
            name = entry.get('source') if isinstance(entry, dict) else None
            if name:
                contributed[name] = contributed.get(name, 0) + 1
    empty = [s['name'] for s in sources
             if s['name'] not in {m['name'] for m in res['missing']}
             and not contributed.get(s['name'])]
    if empty:
        raise pm.MaterializeError(
            f"these declared source(s) resolved but contributed no practices "
            f"at all: {', '.join(sorted(empty))}. That is not the same as a "
            f"missing source (reported separately, and degraded past): the "
            f"path exists and is simply empty, so a sync would quietly drop "
            f"that whole catalogue. Check the path in precedent.json, or that "
            f"the clone is not empty. Retired practices count as contributed, "
            f"so a source that deliberately retired everything does not trip "
            f"this.")

    written, checks_written, rstats = pm.materialize(
        sources, res, pathlib.Path(repo), dry_run=check)
    tree_drift = pm.drift(sources, res, pathlib.Path(repo)) if check else []

    # Render the loader block from the SAME resolved practices materialize()
    # just wrote, not by re-reading practices/ off disk -- res['practices']
    # already carries the parsed frontmatter+sections build_loader_block()
    # needs, and reusing it means this can never drift from what actually
    # got materialized.
    triples = [(p['fm'], p['sections'], pathlib.Path(p['file']))
               for p in res['practices'].values()]
    levels = {slug: p['level'] for slug, p in res['practices'].items()}
    block, _tokens, _n = bv.build_loader_block(triples, source_levels=levels)

    agents_md = pathlib.Path(repo) / 'AGENTS.md'
    if not agents_md.exists():
        raise pm.MaterializeError(
            f"{agents_md} does not exist. A consuming repo needs an "
            f"AGENTS.md with {bv.BEGIN_MARKER} / {bv.END_MARKER} markers "
            f"already in it before this tool can regenerate the loader "
            f"block inside them -- create the file first (see this repo's "
            f"own AGENTS.md for the surrounding structure to copy).")
    original = agents_md.read_text(encoding='utf-8')
    if bv.BEGIN_MARKER not in original or bv.END_MARKER not in original:
        raise pm.MaterializeError(
            f"{agents_md} has no {bv.BEGIN_MARKER} / {bv.END_MARKER} "
            f"markers to regenerate between.")
    pre = original[:original.index(bv.BEGIN_MARKER)]
    post = original[original.index(bv.END_MARKER) + len(bv.END_MARKER):]
    new_text = pre + block + post

    if check:
        return (written, checks_written, rstats, agents_md,
                (new_text != original), tree_drift)

    agents_md.write_text(new_text, encoding='utf-8')
    return (written, checks_written, rstats, agents_md,
            (new_text != original), tree_drift)


def main():
    args = sys.argv[1:]
    check = '--check' in args
    args = [a for a in args if a != '--check']
    repo, user_config = str(ROOT), None
    known = {'--repo', '--user-config'}
    i = 0
    while i < len(args):
        tok = args[i]
        if tok not in known:
            sys.exit(f"precedent_sync_views FAIL: unknown option {tok!r} -- "
                     f"known options are {', '.join(sorted(known | {'--check'}))}.")
        if i + 1 >= len(args):
            sys.exit(f"precedent_sync_views FAIL: {tok} needs a value.")
        if tok == '--repo':
            repo = args[i + 1]
        else:
            user_config = args[i + 1]
        i += 2

    try:
        written, checks_written, rstats, agents_md, changed, tree_drift = sync(
            repo, user_config, check=check)
    except (pr.ResolveError, pm.MaterializeError) as e:
        sys.exit(f"precedent_sync_views FAIL: {e}")

    if check:
        problems = list(tree_drift)
        if changed:
            problems.insert(0, f"{agents_md} is stale or hand-edited, "
                                f"drifted from a fresh sync")
        if problems:
            for line in problems:
                print(f"  {line}", file=sys.stderr)
            sys.exit(f"precedent_sync_views --check FAIL: "
                     f"{len(problems)} difference(s) from a fresh sync. "
                     f"Nothing was written -- re-run without --check to "
                     f"take the sync, then review the diff.")
        print(f"precedent_sync_views --check OK: {agents_md} and the "
              f"materialized tree are byte-identical to a fresh sync "
              f"({len(written)} practice(s), {len(checks_written)} check "
              f"file(s), {len(rstats['practices'])} resident, "
              f"~{rstats['tokens']} of {rstats['budget']} token budget)")
        return 0

    print(f"precedent_sync_views OK: materialized {len(written)} practice(s) "
          f"and {len(checks_written)} check script(s)/test(s), wrote "
          f"{agents_md} (resident ~{rstats['tokens']} of {rstats['budget']} "
          f"token budget)")
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
