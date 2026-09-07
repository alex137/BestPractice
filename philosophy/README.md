<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying WorkingWithAI's content/ into philosophy/; written here, not copied. -->

# The Philosophy Behind Precedent

**This directory holds the theory Precedent is built on** — why a team
should capture its rules as it works, why AI belongs between the work and
the people doing it, and what a group of people is actually good at that
is worth protecting. It is **argument and observation, not rules that bind
anything**. The catalogue in [../practices/](../practices/) is where this
repository's rules live; nothing in this directory tells a session what to
do outside it.

That boundary is deliberate and enforced, not merely stated:
[../local/practices/philosophy-is-not-repo-policy.md](../local/practices/philosophy-is-not-repo-policy.md)
is a repo-local practice scoped to `philosophy/**`, and
[../local/tools/checks/check_philosophy_is_not_repo_policy.py](../local/tools/checks/check_philosophy_is_not_repo_policy.py)
fails the build if a document here starts issuing repo-wide instructions.

## Where This Came From

These documents were written in
[themorgan/WorkingWithAI](https://github.com/themorgan/WorkingWithAI), a
private-to-public working notebook for figuring out how to work well with
AI assistants, and copied here on 2026-09-07 because the theory belongs
beside the platform that tries to embody it. **The copy is a copy, not a
move**: WorkingWithAI still holds the originals under `content/`, and its
three-stage pipeline still runs there. Each file's first line records the
source document and the version it was taken at, so a later session can
tell whether this copy has fallen behind.

Two things deliberately did **not** come across:

- **WorkingWithAI's [GLOSSARY.recipe.md](https://github.com/themorgan/WorkingWithAI/blob/main/content/doc-recipes/GLOSSARY.recipe.md).** It is a rule about that
  repository's root glossary and the vendored tooling underneath it, not
  about any document here.
- **The team- and individual-level practices that govern this writing** —
  `doc-recipe`, `durable-list-anchors`, `trim-prose`, `llm-neutral` and
  the rest. They live in private practice sources, and this repository is
  public, so their text may not be committed here. They are not missing:
  this repository already declares `precedent-team-maintainers` as a team
  source in [../precedent.json](../precedent.json), so those practices are
  already in force, and reach a session through the untracked
  `.precedent/SESSION_PRACTICES.md`.

## How an Idea Here Becomes Policy

An idea does not go from a brainstorm entry to something a company runs
on. It passes through three stages, each earning its way to the next:

1. **Work it out as theory** — [OUR_PHILOSOPHY.md](OUR_PHILOSOPHY.md),
   [COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md),
   [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md),
   [REASONS_WHY.md](REASONS_WHY.md).
2. **Try it for real** — [RULES_NOW_TESTING.md](RULES_NOW_TESTING.md),
   each rule tagged *Trial*, *Ready to promote*, or *Promoted*.
3. **Roll it out** — into a practice source, where it becomes a real
   practice file that binds real work.

**Stage 3 does not happen by editing a document in this directory.** A
rule that has proven itself gets written as a practice file in the source
it belongs to — [../practices/](../practices/) for a genuinely generic
rule, a team or individual source for one specific to a group or a person.
Marking something *Promoted* here is a pointer to work done elsewhere, not
the work itself.

## What's Here

- [OUR_PHILOSOPHY.md](OUR_PHILOSOPHY.md) — the underlying theoretical
  ideas everything else here assumes, named and explained on their own
  terms. **Start here.**
- [REASONS_WHY.md](REASONS_WHY.md) — its companion: the less obvious
  benefits those ideas produce in practice.
- [CORE_PILLARS.md](CORE_PILLARS.md) — the one-page pitch for what this
  approach argues is unique, specifically taken together.
- [HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md) — the one full list of
  what humans are good at, gathered from the shorter versions scattered
  through the other documents.
- [RANDOM_NOTES.md](RANDOM_NOTES.md) — the brainstorm itself: one entry
  per idea, prompt, workflow, or observation, loosely grouped.
- [COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md) — a full essay
  promoted out of the brainstorm: rules for building a company around AI.
- [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md) — a full
  essay promoted out of the brainstorm: how AI systems themselves should
  be configured so the healthy pattern is the default.
- [RULES_NOW_TESTING.md](RULES_NOW_TESTING.md) — the practical rules
  actually being tried in real work right now, and candidates for
  promotion.
- [doc-recipes/](doc-recipes/) — standing constraints on individual
  documents here, one `.recipe.md` file per document it governs.

## Citing Something Here

**Every durable item in these essays carries its own `<a id="slug"></a>`
anchor**, and is cited by that slug — a link whose target ends
`COMPANY_BUILDING_RULES.md#capital-asset`, labelled with the slug —
never as "rule 4". The lists get renumbered; the slugs do not. A citation
from outside this directory is a citation *of an argument*, and never
turns that argument into a rule the cited-from file has to follow.
