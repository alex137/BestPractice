<!-- Last updated: 2026-09-07 (Buenos Aires) by the session making this directory the permanent home; written here, not copied. -->

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
fails the build if a rule anywhere starts leaning on these essays for its
authority.

## This Is the Only Copy

**These documents live here and nowhere else.** They were written in a
separate working notebook, the project's own prior notes repository, which was retired on
2026-09-07 — this directory is not a mirror of it, and there is no
upstream to sync with. The provenance line at the top of each file records
which document it came from and the version it was taken at; that is a
**historical record of where the text originated**, not a pointer to
something still live.

Two consequences worth stating outright, because both are easy to get
wrong later:

- **Edit these files directly.** There is no "and also update the
  original", because there is no original any more.
- **Nothing did, or should, vendor these essays anywhere.** They are prose
  belonging to this repository, not a practice source. A consuming repo
  that vendors Precedent gets [../practices/](../practices/); it has no
  reason to carry this directory, and carrying it would just make a
  second copy of documents that exist to have exactly one.

One thing did not survive the retirement, deliberately: a recipe governing
that notebook's own root glossary, which was a rule about that repo's
tooling rather than about any document here.

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
the work itself. [`write-like-a-human`](../practices/write-like-a-human.md)
is the worked example: it began as two halves of an argument in these
essays and is now a universal practice.

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
- [ASSORTED_NOTES.md](ASSORTED_NOTES.md) — the brainstorm itself: one entry
  per idea, prompt, workflow, or observation, loosely grouped. Its closing
  **Open Questions** section holds the unfinished parts of the argument —
  what is still unsettled, and what was already tried and rejected.
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

**What used to be here.** `RANDOM_NOTES.md` was renamed
[ASSORTED_NOTES.md](ASSORTED_NOTES.md) on 2026-09-09, and `OPEN_QUESTIONS.md`
was folded into that document's closing **Open Questions** section on the
same day and deleted. The lineage is recorded here rather than in either
document ([index-remembers-past](../practices/index-remembers-past.md)).

## Citing Something Here

**Every durable item in these essays carries its own `<a id="slug"></a>`
anchor**, and is cited by that slug — a link whose target ends
`COMPANY_BUILDING_RULES.md#capital-asset`, labelled with the slug —
never as "rule 4". The lists get renumbered; the slugs do not. A citation
from outside this directory is a citation *of an argument*, and never
turns that argument into a rule the cited-from file has to follow.
