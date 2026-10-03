---
slug:              todo-2026-10-03-generated-files-are-never-hand-edited
kind:              decision
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "MAP.md and GLOSSARY.md are wholly generated in every repository, and so is every other generated file; none is ever edited by hand -- a change goes into its source files, the generator, or the rules that make it"
decision_strength: decided
waiting_on:        null
noted:             2026-10-03
closed:            null
---
## What

- <a id="generated-files-are-never-hand-edited"></a>**Every generated
  file, in every repository, is generated and never hand-edited.** Morgan,
  2026-10-03 (strength: decided), confirming a decision a session relayed:
  MAP.md and GLOSSARY.md must always be generated, in every repository --
  -- BestPractice (BP), now Precedent: "that is essential to the philosophy of BP/Precedent" -- and the same
  goes for the What's New file and every other auto-generated file. "Those
  should NEVER be touched manually directly, and when you want a change to
  them, we change the source files or the generation engine or rules to
  make them." Asked whether the two views should be wholly generated or
  carry generated sections inside hand-written files: "Let's keep them
  wholly generated."

  Today a repository that uses Precedent hand-writes MAP.md and
  GLOSSARY.md from [templates/MAP.md.template](../templates/MAP.md.template);
  [tools/precedent_sync_views.py](../tools/precedent_sync_views.py) builds
  only the generated block in AGENTS.md, and the generated-artifact-provenance
  check in [tools/precedent_check.py](../tools/precedent_check.py) skips an
  unstamped MAP.md or GLOSSARY.md. A consumer session reported the trap that
  follows: run bare, [build_views.py](../tools/build_views.py) overwrote a hand-written map and
  glossary with a list of practice rules, and their own terms and sections
  were nearly lost. That trap is closed on pre-staging (the view sync's
  `is_generated_view` guard, 2026-10-03): a hand-written view is left alone
  and said so. What is left is the decision itself.

  The work, to be planned before it is built:
  1. Both views built from the practice catalogue plus repo-owned source
     files holding everything repository-specific (where things live,
     deliverables, known consumers, the repository's own terms). Reuse a
     format the engine already reads where one fits (`our_language.json`
     for a repository's own terms) before inventing one.
  2. One registry of which files are generated, read by every check, so a
     hand edit to any of them fails, in every repository.
  3. A one-time migration that turns a repository's hand-written views into
     those sources with nothing lost, proven on a consumer before it ships,
     and a rollout said plainly: each repository runs it at its next Update
     Vendors before its next check passes.
  4. The templates, INSTALL.md section 0 and the orientation-map and
     acronyms-glossary practices say "generated, never hand-edited".

  **Why it was not already so** (traced through the history 2026-10-03):
  it was never built for a repository that uses Precedent, and the
  decision not to build it was a session's, never Morgan's or Alex's.
  - The plan of record ([spec/PRACTICE_ENGINE_PLAN.md](../spec/PRACTICE_ENGINE_PLAN.md),
    `02faee49`, 2026-08-31) says to make AGENTS.md, MAP.md and GLOSSARY.md
    generated, answering "navigation documents hand-maintained and
    drifting" -- but its links are to this repository's own files, phase 2
    (`903af45e`) generated only these, and left consumers to phase 6, whose
    row says nothing about views.
  - `b8089c57`, 2026-09-03, added `--agents-only` under "Judgment calls
    made": "Scoped --agents-only to skip MAP.md/GLOSSARY.md entirely rather
    than attempting a repo-agnostic version of render_map_md()".
    `53bcbb85` the same day reused it for consumers, and `779af18e` wrote it
    into INSTALL.md section 0 as "deliberately does not cover, by design and
    not oversight". An unratified call became the stated design that day.
  - `7d4988da`, 2026-09-06, made the provenance check skip a hand-written
    view so a fresh install came back clean -- enforcing that design, not
    deciding it.
  - `ccc85763`, 2026-09-14, dropped a document project's MAP.md and
    GLOSSARY.md from its owned generated views as "content", under Morgan's
    approval of a write-up as a whole (`assented`), not of that choice by
    name ([todo-2026-09-14-generated-views-are-owned-paths](todo-2026-09-14-generated-views-are-owned-paths.md)).
  - Practice sets are the exception: they have generated full views since
    2026-09-06 (`53a6b3b9`), which is likely the generation Morgan
    remembered.

## How It Closes

When a repository using Precedent generates MAP.md and GLOSSARY.md from its
sources, every generated file is named in one registry, and a hand edit to
any of them fails the check, here and in a migrated consumer.
