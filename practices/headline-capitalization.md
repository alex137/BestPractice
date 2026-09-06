---
slug:        headline-capitalization
title:       "Outward-facing headings use one headline capitalization, defined once"
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing or editing a heading in an outward-facing document"
gates:       []
index_clause: "outward-facing headings are New York Times headline case, applied by tool"
checked_by:  "tools/precedent_check.py"
defines:     ["headline capitalization"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-06"
approved_by: "Morgan"
source_practice_number: null
---
## Rule
**This rule governs content published for people outside the project, and
nothing else.** Headings in internal working files — practice files,
specs, briefs, `AGENTS.md`, `TODO.md`, this file — are out of scope on
purpose, not by oversight: how a heading is *styled* matters where
strangers read it and matters nowhere else, so sentence case in a spec is
correct and is never to be "fixed". Stated by Morgan, 2026-09-06, settling
it; `applies_to` and the check are scoped to match, and the counterpart
rule for internal files is [heading-outline](heading-outline.md), which is
about whether an outline is *broken* rather than how it looks.

Every heading in an outward-facing document is written in **New York Times
headline capitalization**, and the rule is applied by
[tools/title_case.py](../tools/title_case.py) rather than by whoever is
drafting. The specifics live in that one file so no adopting repository,
document or person restates them:

- The first and last word of a heading are capitalized.
- A word immediately after a colon or a dash is capitalized — it opens a
  new phrase.
- Articles, coordinating conjunctions and short prepositions — the standard
  list `a an and as at but by en for if in of on or the to v via vs` — are
  lowercased anywhere else.
- Every other word gets its first letter capitalized and the **rest of the
  word untouched**, which is what keeps `AI`, `GitHub`, `PR` and `TODO`
  intact without a dictionary of proper nouns.
- Both halves of a hyphenated compound are capitalized: *Lock-In*,
  *Multi-Person*.
- A phrase whose own capitalization carries meaning is exempt by name, in
  the tool's `KEEP_PHRASES`. *The Why* is a noun phrase — the reasoning
  behind a decision — not an article plus a word.

**Scope is stated as an exclusion, not a list of directories.** Every
document is in scope unless it is named internal in
[tools/title_case.py](../tools/title_case.py)'s `INTERNAL_DIRS` /
`INTERNAL_FILES` — the project managing itself: practice files, the engine,
specs, briefs, decision records, evaluation fixtures, uninstantiated
templates, and the instructions, index and catalogue documents a session
reads to work here.

Written the other way round it decays. This practice shipped covering
`documentation/` alone; `content/` and `book*/` had to be added the same
day, and the next outward directory somebody creates would have been missed
in the same silence. An exclusion fails the safe way round: an unclassified
directory is treated as published, and the worst case is a heading
capitalized that did not need to be.

A repository's root holds both kinds, so directories alone cannot settle
it — `README.md` and `SETUP.md` are the first things an outsider reads,
while `PRACTICES.md` and `PRACTICE_ENGINE_PLAN.md` sit beside them and are
pure internal machinery. The internal root documents are therefore named
individually, and three of them (`AGENTS.md`, `MAP.md`, `GLOSSARY.md`) are
generated as well, so a rewritten heading there would be undone by the next
build and fail its byte-identical check in between.

## Why
Headline capitalization is the kind of rule everyone agrees with and nobody
applies consistently, because it is a dozen small decisions per heading and
the small words are exactly the ones a drafter stops seeing. Left to
judgment it produces a document that is *mostly* title case, which reads
worse than either convention applied whole — the reader notices the
exceptions without being able to say why.

It is also the kind of rule that gets restated. Written as prose in a style
guide, every repository that adopts it re-derives which prepositions are
short enough and what happens after a colon, and they diverge. Written as
one script, the answer is the same everywhere and an adopter gets it by
running the tool, not by reading about it.

## Story
2026-09-06: Morgan asked why `documentation/` was not following this rule,
believing a practice for it already existed. It did not — not in the
universal catalogue, not in this repo's own repo-local set. Four documents had
drifted into a mix: 25 of their headings were sentence case, some were
title case, and two headings added earlier in that same session were title
case only because they had been dictated that way.

The reason no practice fired is worth recording with the practice, because
it is not "nobody wrote one." The rule may well exist in
`precedent-team-maintainers` or in the individual set. Neither can load in
a BestPractice session: [tools/build_views.py](../tools/build_views.py)
builds this repo's own loader from the universal catalogue alone, so a team
or individual practice never reaches the occasion index a session actually
reads. The individual set could not resolve at all — no user-level config,
and the self-heal in
[tools/precedent_resolve.py](../tools/precedent_resolve.py) returns early
because BestPractice never instantiated the
`.claude/hooks/precedent-individual-bootstrap.sh` it ships to every other
adopter. Landing the rule at the universal level is what makes it load
here at all.

## Install
[tools/title_case.py](../tools/title_case.py) is both the definition and
the fix: bare, it checks and exits non-zero listing every heading that is
wrong; `--write` rewrites them in place; `--json` reports for another tool.
It skips fenced code blocks, so a `#` comment inside an example is never
rewritten.

`tools/precedent_check.py`'s `headline-capitalization` check runs it over
the changed documents in scope, so a heading cannot land wrong. Run
`python3 tools/title_case.py --write` after drafting and read the diff —
the tool is right about the mechanical rules and cannot know that a new
phrase belongs in `KEEP_PHRASES`.
