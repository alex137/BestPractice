---
title:         "Generated Files: Generated Everywhere, Never Hand-Edited"
kind:          proposal
status:        accepted
opened:        2026-10-03
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       Every generated file is generated in every repository and never hand-edited; the views rebuild themselves as their sources change.
---
# Generated Files: Generated Everywhere, Never Hand-Edited

The decision and its history are in
[todo-2026-10-03-generated-files-are-never-hand-edited](../todo/todo-2026-10-03-generated-files-are-never-hand-edited.md).
This is the plan for building it (Morgan, 2026-10-03: "Act").

## Decisions

- **G1. Never hand-edited.** A generated file is never edited by hand, in
  any repository. A change goes into its sources, its generator, or the
  rules that make it (Morgan, 2026-10-03, strength: decided).
- **G2. What MAP.md is.** A map of the practice catalogue and the engine's
  own code, not of every file in the repository, kept current
  automatically as those change. Each precedent-* repository has its own
  (Morgan, 2026-10-03, strength: decided).
- **G3. WHERE_THINGS_ARE.md is generated too** (Morgan, 2026-10-03,
  strength: decided). The What's New log is not part of this plan.
- **G4. Repositories that use Precedent** get the same generated map and
  glossary of the practices and engine in force there. Their own sections
  and terms move into a small repo-owned source the views include, so
  nothing they wrote is lost (the session's pick; Morgan: "your pick, I
  agree with you", strength: assented).

- **G5. A copy cites its original or is generated from it.** Content that
  appears in two places either cites the original instead of repeating it,
  or both are generated from one source, so they stay in sync (Morgan,
  2026-10-03, on AGENTS.md's short table: "It should either cite the
  original instead of repeating it OR make sure they are kept in sync",
  strength: decided). Step 2 is the second kind.

## Steps

1. **Descriptions come from the file they describe.** Each tool's line in
   MAP.md is the first line of its own docstring. `TOOLS_DESCRIPTIONS`, a
   hand-typed second copy inside build_views.py, is retired. Its text moves
   into each tool as that first line, word for word, so the map does not
   change. A tool with no docstring still stops the build, naming the file
   to describe.
2. **WHERE_THINGS_ARE.md and AGENTS.md's quick index come from one
   source.** That source is `where_things_are.json`, one row per entry,
   `quick: true` on the rows AGENTS.md carries. Today the short table is a
   second hand copy, and several of its rows already read differently from
   the full one. build_views.py renders both, and checks that every link
   in a row resolves.
3. **The views rebuild themselves at commit.** The global commit backstop
   already runs fixers that correct a commit and never refuse it. An
   engine fixer joins them: for each entry in `tools/generated_files.json`
   whose inputs the commit touches, it runs the entry's `regenerate` and
   stages the result. A session no longer has to remember. Session start
   and the Debut already rebuild them as well.
4. **The list ships, and the check runs at the basic tier everywhere.**
   Each precedent-* repository gets its own `generated_files.json`, listing
   the views it generates. `generated-files-registered` then reaches it,
   and a stale or hand-edited view fails the push to pre-staging, not only
   the Debut.
5. **Repositories that use Precedent.** The view sync generates MAP.md and
   GLOSSARY.md from the practices and engine in force there, plus the
   repo-owned source. A one-time migration turns a hand-written map and
   glossary into that source with nothing lost. It is proven on a real
   consumer first, and each repository runs it at its next Update Vendors.
   Until it has, the sync leaves a hand-written view alone and says so
   (already true since 2026-10-03).
6. **The documents follow.** templates/MAP.md.template, INSTALL.md section
   0, and the orientation-map and acronyms-glossary practices say
   "generated, never hand-edited".

Steps 1 to 4 change BestPractice and the precedent-* repositories. Step 5
changes what every repository using Precedent receives: it reaches each one
at its next Update Vendors, and that repository's next check passes only
once its migration has run. The change says so where it lands.

## Built (2026-10-03)

All six steps, each with tests that a mutation of the change fails:
- **Step 1.** Each tool's description moved word for word into its
  tool's first docstring line; MAP.md came out byte-identical.
- **Step 2.** WHERE_THINGS_ARE.md and AGENTS.md's short table both render
  from `where_things_are.json`. Where they disagreed, the newer wording
  (AGENTS.md's) was kept.
- **Step 3.** `tools/precedent_regenerate.py`, run by the commit
  backstop, rebuilds and stages the generated files a commit's sources
  feed, and the generated blocks inside hand-written documents too
  (doc_sync.py's, which the list leaves to doc_sync on purpose). Its first
  real uses added its own MAP.md row and refreshed a stale count in
  spec/LOADER.md.
- **Step 4.** A practice set's view check runs at the basic tier. Each of
  the five sets has its own list of generated files, on a branch there,
  and two of them carried stale todo indexes nothing had checked.
- **Steps 5 and 6.** `MAP.source.md` / `GLOSSARY.source.md`,
  `tools/precedent_migrate_views.py`, the migration at Update Vendors, a
  fresh install that starts generated, and the documents.

Proven on a scratch copy of a real consumer, through a full Update
Vendors from this branch. Both of its hand-written views moved word for
word, and every line of each is in the generated view. Its sync, its view
check and its generated-files check pass.

**Found on the way, and fixed at the root:**
- **A full build rewrote AGENTS.md's loader block** in a repository using
  Precedent, where only the view sync may write it. `--views-only` is now
  what every consumer-side rebuild runs.
- **The tracked loader block depended on who regenerated it.** A set the
  person brings counted as a deferred source, so build_views.py and the
  sync disagreed. In every consumer, the full check failed after an engine
  update for anyone who brings a set. This was reproduced on staging's own
  engine, so it predates this work. Only declared sources count now.
- **A vendored copy of another repository's generated file** was listed
  as the consumer's own. `VENDORED_TREES` now names those trees once.

**Left for a person:**
- **One consumer's own map was overwritten.** Its last hand-written map
  (2026-09-08: top-level layout, document types, the books, the
  brainstorm) was replaced by the engine's map at a vendor update on
  2026-09-15, and has been missing since. `precedent_migrate_views.py
  --restore-map-from` brings it back into its source file from the commit
  the person names; whether to, and from which commit, is that
  repository's call.
