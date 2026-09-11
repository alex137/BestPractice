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
  python3 tools/precedent_sync_views.py --repo DIR [--user-config PATH] [--check]

  --repo is REQUIRED and names the consuming repo's root; from that root it
  is `--repo .`. It used to default to this script's own directory's parent,
  which is right only when the script is vendored at the consuming repo's own
  tools/ beside precedent_resolve.py, and wrong wherever else it is nested —
  a `process/upstream/tools/` mirror most of all, since that copy exists for
  the audit tools rather than this one.

  The default was documented as a trap right here and went on catching
  people anyway: 2026-09-09, a careful session ran it bare from a consuming
  repo, --repo resolved to `process/upstream/`, the team sources' `../` paths
  then resolved against `process/`, every one of them missed, and the run
  hard-failed claiming the universal source's path collided with its own
  output directory. Nothing was wrong with that repo. A documented trap that
  still catches a reader is an argument for a refusal, not for a better
  paragraph (practice: checkable-gets-checked), so there is no default now.

Exit: 0 on a clean sync, 1 on anything precedent_materialize.py or the
resident-budget check would themselves exit 1 on (a resolve conflict, a
tools/checks/ filename collision, an over-budget resident set), or on
--check finding drift.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_resolve as pr  # noqa: E402
import precedent_materialize as pm  # noqa: E402
import build_views as bv  # noqa: E402



def _lost_practices(repo, res, sources, withheld):
    """-> {'blocking': [(slug, source)], 'source_dropped': [(slug, source)]}.

    Which practices the COMMITTED MANIFEST.json records that this sync would
    not write back. Reads the manifest from git HEAD rather than from disk on
    purpose: the on-disk copy is this tool's own output from the last run, so
    comparing against it asks "does the tree match the plan?" -- true
    constantly, and the question whose answer had to be reverted earlier that
    day. The committed copy asks "did this repository publish a catalogue
    that is about to lose a rule?", which is answerable and worth stopping
    for.

    Returns empty for anything it cannot establish -- not a git repo, no
    committed manifest, malformed JSON. A repository with no published
    catalogue has nothing to lose, and a guard that guessed here would fire
    on every fresh install.
    """
    empty = {'blocking': [], 'source_dropped': []}
    try:
        r = subprocess.run(['git', '-C', str(repo), 'show', 'HEAD:MANIFEST.json'],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return empty
    if r.returncode != 0 or not r.stdout.strip():
        return empty
    try:
        recorded = json.loads(r.stdout).get('practices') or []
    except ValueError:
        return empty

    # res['practices'] is a DICT KEYED BY SLUG. The first version of this
    # iterated it as a list of records and so iterated its KEYS as if they
    # were objects, producing an empty set -- and the "cannot establish it,
    # return empty" path below then swallowed that, leaving the guard
    # silently inert while reporting nothing. It shipped past its own
    # positive control that way. Reading a structure wrong is the third such
    # defect in this run; what made this one worse than the other two is that
    # a fallback meant to fail safe is what hid it.
    pracs = res.get('practices')
    now = set(pracs) if isinstance(pracs, dict) else {
        (p.get('slug') if isinstance(p, dict) else getattr(p, 'slug', None))
        for p in (pracs or [])}
    now.discard(None)
    if not now:
        # Could not read the new set at all. NOT the same as "nothing is
        # being lost" (practice: fail-gracefully) -- say so rather than
        # returning a clean answer nobody can distinguish from a real one.
        print("precedent_sync_views: could not read the resolved practice "
              "set, so the lost-practice guard did NOT run. This is not a "
              "clean result.", file=sys.stderr)
        return empty
    withheld = set(withheld or ())
    declared = {s.get('name') for s in sources}

    out = {'blocking': [], 'source_dropped': []}
    for entry in recorded:
        if not isinstance(entry, dict):
            continue
        slug, src = entry.get('slug'), entry.get('source')
        if not slug or slug in now or slug in withheld:
            continue
        (out['source_dropped'] if src not in declared
         else out['blocking']).append((slug, src))
    return out


def sync(repo, user_config=None, check=False, allow_missing=False,
         allow_removals=False):
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
              f"is not available ({m['reason']}).",
              file=sys.stderr)

    # REFUSE TO WRITE from an incomplete source set. materialize() rebuilds
    # practices/ by delete-and-rewrite, so a source that merely failed to
    # resolve does not just go unrendered -- every practice it contributed
    # is DELETED from the tracked tree, and AGENTS.md and MANIFEST.json are
    # rewritten to match. Exit 0, one warning line, a committable diff that
    # looks like a deliberate removal.
    #
    # This is the CI state by definition: a private team or individual
    # source is unreachable in every continuous-integration checkout, which
    # is exactly where an automated sync would run unattended.
    #
    # build_views.py already refuses this, in these words -- "refusing to
    # WRITE a loader block from an incomplete source set". This tool is the
    # one the install and migration documents actually tell an adopter to
    # run, and it did the opposite. The half of this bug that hit --check
    # was found and fixed on 2026-09-06 (see the note below); the writing
    # half was left, and it is the half that deletes.
    #
    # Reproduced before fixing: a consuming repo with one reachable team
    # source, synced and committed, then re-synced with the sibling clone
    # simply absent -- practices/widget-rule.md deleted, AGENTS.md and
    # MANIFEST.json rewritten, exit 0.
    if res['missing'] and not check and not allow_missing:
        names = ', '.join(f"{m['level']}/{m['name']}" for m in res['missing'])
        raise pm.MaterializeError(
            f"refusing to WRITE from an incomplete source set: {names} did "
            f"not resolve. Syncing anyway would DELETE every practice those "
            f"sources contribute from this repo's tracked tree and rewrite "
            f"AGENTS.md to match -- a silent removal that reads as a "
            f"deliberate one. Make them resolvable and re-run; use --check "
            f"to inspect without writing, or --allow-missing-sources if the "
            f"removal is genuinely what you intend.")

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

    # A PUBLIC repo's materialized practices/ tree is a TRACKED, published
    # artifact, so a private source's practice TEXT may not go into it.
    # build_views.py already refuses to render a private source into a
    # public repo's loader block for exactly this reason, and
    # precedent_materialize.py already refuses to mint a private repo's URL
    # into the same tree -- but the whole file was copied in regardless,
    # which is a larger disclosure than the link that was so carefully
    # withheld. Reproduced against a real fresh install: 13 individual-level
    # practices, one of them carrying a person's name and email address,
    # materialized into a `visibility: public` consumer's tracked tree.
    #
    # The private practices still BIND the session -- they reach it through
    # .precedent/SESSION_PRACTICES.md, untracked and regenerated per
    # session, which is the channel that exists for precisely this case.
    public = bv.repo_is_public(pathlib.Path(repo))
    omitted = []
    if public:
        omitted = sorted({p['level'] for p in res['practices'].values()
                          if p['level'] in bv.PRIVATE_LEVELS})
        if omitted:
            # RE-RESOLVE without the private sources rather than filtering
            # them out of the finished result. A private practice can WIN a
            # slug a publishable source also declares, and deleting the
            # winner from a resolved set does not promote the runner-up --
            # it drops the slug entirely. Caught here: filtering lost
            # `merge-authorization-keyword` (universal) because an
            # individual practice overrode it, so a public consumer would
            # have silently shipped one practice fewer than its own
            # universal source defines.
            withheld_slugs = sorted(
                slug for slug, pr_ in res['practices'].items()
                if pr_['level'] in bv.PRIVATE_LEVELS)
            sources = [s for s in sources
                       if s['level'] not in bv.PRIVATE_LEVELS]
            res = pr.resolve(sources)
            # A slug that a publishable source ALSO defines is not withheld --
            # the re-resolve above brings it back, from text this repo may
            # carry. Only what is genuinely absent here gets recorded.
            withheld_slugs = [x for x in withheld_slugs
                              if x not in res['practices']]

            # REFUSE when the exclusion is ASSUMED rather than declared AND
            # it would delete practice files that are already here. The
            # undeclared default is public, which fails safe against
            # publication -- but it fails UNSAFE in the other direction: an
            # existing private consumer that never declared `visibility`
            # loses every private practice from its tracked tree on its next
            # sync, silently, as a committable diff that reads as deliberate.
            #
            # Reported 2026-09-07 from a real private repo updating to this
            # engine: 15 individual- and team-level practices would have gone,
            # and the session caught it only by checking the repo's actual
            # visibility by hand. This is the same silent-deletion failure
            # this tool already refuses for an unreachable source, arriving
            # by a different door -- and it was introduced by the fix for the
            # opposite hazard, hours earlier, in this same run.
            #
            # A DECLARED public repo is choosing this and proceeds.
            if not bv.visibility_is_declared(pathlib.Path(repo)):
                existing = {f.stem for f in
                            (pathlib.Path(repo) / 'practices').glob('*.md')}
                would_delete = sorted(
                    slug for slug in withheld_slugs if slug in existing)
                if would_delete:
                    shown = ', '.join(would_delete[:5])
                    more = (f" (+{len(would_delete) - 5} more)"
                            if len(would_delete) > 5 else "")
                    raise pm.MaterializeError(
                        f"refusing to remove {len(would_delete)} practice "
                        f"file(s) on an ASSUMED visibility: {shown}{more}. "
                        f"{repo}/precedent.json declares no `visibility`, so "
                        f"this run assumed PUBLIC and would withhold every "
                        f"team- and individual-level practice -- deleting "
                        f"those files from a tree that already carries them. "
                        f"That assumption is right for a public repo and "
                        f"wrong for a private one, and only you know which "
                        f"this is. Declare it: \"visibility\": \"private\" "
                        f"to keep them, \"public\" to withhold them "
                        f"deliberately.")
            print(f"precedent_sync_views: {', '.join(omitted)}-level "
                  f"practice text is NOT materialized here -- this repo "
                  f"declares visibility: public and practices/ is tracked. "
                  f"Those practices still bind: they reach a session through "
                  f".precedent/SESSION_PRACTICES.md, which is untracked.",
                  file=sys.stderr)

    # REFUSE TO LOSE A RULE THIS REPOSITORY HAS ALREADY RECORDED.
    #
    # materialize() rmtree's practices/ and rewrites it, so a slug no
    # declared source produces any more simply stops existing. `--check`
    # names each one; a real sync says nothing, and the loss shows up only
    # as deletions in `git status` afterwards, to whoever reads the diff.
    #
    # THE BASELINE IS THE COMMITTED MANIFEST, and that choice is the whole
    # design. An earlier attempt compared the working tree against the plan
    # and had to be reverted: it fired on three legitimate flows -- a public
    # repo withholding private text by design, a sync already carrying
    # --allow-missing-sources, and a fixture re-syncing after its own sources
    # changed. "The tree differs from the plan" is true constantly and means
    # nothing on its own. "This repository committed a catalogue containing
    # rule X, and X is about to be gone" is a much narrower claim, and it is
    # the one worth refusing on.
    #
    # Four things fall out of using that baseline, each closing one of the
    # false positives that killed the first attempt:
    #   * No committed MANIFEST.json -- a scratch fixture, a fresh install,
    #     an uncommitted experiment -- and there is no baseline, so this does
    #     not apply. It cannot fire on a repo that has never published a
    #     catalogue.
    #   * A WITHHELD slug is excluded: a public repo keeps private-level text
    #     out of its tracked tree deliberately, and those practices still
    #     bind through .precedent/SESSION_PRACTICES.md.
    #   * A slug whose recorded SOURCE IS NO LONGER DECLARED is reported but
    #     not refused: dropping a source from precedent.json is a decision
    #     somebody just made on purpose, and the practices it contributed are
    #     supposed to go with it.
    #   * A slug whose recorded source IS STILL DECLARED, and which that
    #     source no longer produces, is the real case: the rule moved or the
    #     vendored copy went stale, and syncing now loses it. That is the
    #     2026-09-07 incident -- promoting two practices out of a team set
    #     left every consumer pinned before the promotion with them in
    #     neither source.
    if not check:
        _lost = _lost_practices(repo, res, sources,
                                locals().get('withheld_slugs'))
        if _lost['blocking'] and not (allow_removals or allow_missing):
            raise pm.MaterializeError(
                "refusing to WRITE: this sync would remove "
                + str(len(_lost['blocking'])) + " practice(s) this "
                "repository's committed MANIFEST.json records, whose source "
                "is still declared -- "
                + '; '.join(f"{s} (from {src})"
                            for s, src in sorted(_lost['blocking']))
                + ". The usual cause is a stale vendored copy: the rule moved "
                "between levels upstream, so a copy pinned before the move "
                "has it in neither source. Refresh and re-run "
                "(`process/upstream/tools/checkin.py update <clone>`). If the "
                "removal is intended -- retired upstream, or you meant to "
                "drop it -- re-run with --allow-removals.")
        if _lost['source_dropped']:
            print("precedent_sync_views: removing "
                  f"{len(_lost['source_dropped'])} practice(s) whose source "
                  "is no longer declared in precedent.json, which is what "
                  "dropping a source means: "
                  + ', '.join(f"{s} ({src})"
                              for s, src in sorted(_lost['source_dropped'])),
                  file=sys.stderr)

    written, checks_written, rstats = pm.materialize(
        sources, res, pathlib.Path(repo), dry_run=check,
        withheld=locals().get('withheld_slugs'))
    tree_drift = (pm.drift(sources, res, pathlib.Path(repo),
                          withheld=locals().get('withheld_slugs'))
                  if check else [])

    # Render the loader block from the SAME resolved practices materialize()
    # just wrote, not by re-reading practices/ off disk -- res['practices']
    # already carries the parsed frontmatter+sections build_loader_block()
    # needs, and reusing it means this can never drift from what actually
    # got materialized.
    triples = [(p['fm'], p['sections'], pathlib.Path(p['file']))
               for p in res['practices'].values()]
    levels = {slug: p['level'] for slug, p in res['practices'].items()}
    # omits_private must match what this run actually left out, or the
    # standing instruction disagrees with build_views.py's own render of the
    # same repo -- and `generated-artifact-provenance` then reports the file
    # the documented install step just wrote as hand-edited, with no state of
    # the repo able to satisfy it. Found exactly that way.
    block, _tokens, _n = bv.build_loader_block(
        triples, source_levels=levels, omits_private=bool(omitted))

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
    allow_removals = '--allow-removals' in args
    check = '--check' in args
    allow_missing = '--allow-missing-sources' in args
    args = [a for a in args if a not in ('--check', '--allow-missing-sources',
                                         '--allow-removals')]
    repo, user_config = None, None
    known = {'--repo', '--user-config'}
    i = 0
    while i < len(args):
        tok = args[i]
        if tok not in known:
            sys.exit(f"precedent_sync_views FAIL: unknown option {tok!r} -- "
                     f"known options are {', '.join(sorted(known | {'--check', '--allow-removals'}))}.")
        if i + 1 >= len(args):
            sys.exit(f"precedent_sync_views FAIL: {tok} needs a value.")
        if tok == '--repo':
            repo = args[i + 1]
        else:
            user_config = args[i + 1]
        i += 2

    if repo is None:
        sys.exit("precedent_sync_views FAIL: --repo is required and names the "
                 "consuming repo's root -- from that root, `--repo .`. There "
                 "is deliberately no default: the old one resolved to this "
                 "script's own parent, which is correct only where the script "
                 "is vendored at the consuming repo's tools/, and produced a "
                 "confident, wrong, hard failure everywhere else.")

    try:
        written, checks_written, rstats, agents_md, changed, tree_drift = sync(
            repo, user_config, check=check, allow_missing=allow_missing,
            allow_removals=allow_removals)
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
    # documentation/HOW_TO_USE_THIS_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())
