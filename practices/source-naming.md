---
slug:        source-naming
title:       A practice-set source carries its identity in its own manifest; its name is chosen once, and its repository may be called anything
tier:        on-demand
severity:    default
applies_to:  ["precedent.json", "precedent-source.json"]
occasion:    "importing, creating, or declaring a repository that holds practices"
gates:       []
index_clause: "identity lives in the source's manifest; the name is chosen once, the repository is called anything"
checked_by:  "tools/precedent_check.py"
defines:     ["practice-set source", "source manifest"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       2026-09-06
approved_by: "Morgan F"
---
## Rule
A practice-set source says what it is in a file at its root,
`precedent-source.json`: its **name**, its **level** (`universal`,
`shared`, `individual` or `repo-local`), its **visibility**, one sentence
of **subject**, and the **code** directories it ships beside its practices.
The name is chosen once, by the author, when the set is created, and every
consumer declares it verbatim; the resolver checks that the clone at a
declared path answers to the name declared for it. **The repository may be
called anything.** Nothing in the engine keys on a repository's name: where
a set lives is declared, what it is is read off the set.

Two names are fixed, because they are not anyone's product: the universal
set is `precedent`, and a repo-local source is `local`, matching its fixed
`path`. Every other name is a slug — lowercase, digits, single hyphens —
because it becomes a clone directory, a manifest key and a path segment.
A person's own set defaults to `precedent-individual` when their config
names none; that is a default, not a rule.

**Say this the first time it can matter.** When importing, creating, or
attaching a repository that will hold practices comes up — before anyone
picks a name — say that the name is chosen once and written into the
manifest, that renaming it later breaks every consumer's attribution, and
that the repository's own name is free. Do not apply the convention
silently, and do not correct a name after the fact. The person naming the
set is the one participant no mechanical check can reach.

## Detail
Four different things get called "the name," and they are treated
differently:

| The name | If it varies | Answer |
|---|---|---|
| `name` in the source's own `precedent-source.json` | It is the identity: attribution in every consumer's materialized `MANIFEST.json` keys on it | Chosen once; never changed after a consumer exists |
| `name` in a consumer's `precedent.json` or user config | Must equal the source's own; a clone at that path that calls itself something else is the wrong repository there | **Refused** by [tools/precedent_resolve.py](../tools/precedent_resolve.py) when the clone carries a manifest; a slug that is not one is refused outright |
| The clone directory a source's `path` points at | The declared relative path is wrong on that machine | **Warned** about, never refused: continuous integration checkouts and git worktrees legitimately differ |
| The repository's own name | Nothing, so long as the consumer's declaration says where the set lives (`repo`, when it is not called what the set is) | Free. A rename is still **detected** afterwards by [tools/precedent_source_names.py](../tools/precedent_source_names.py), because a redirect is a 404 waiting to be dated |

`level` says how a set ranks and whether it is private by default;
`shared` is any set a repository declares beside the universal one and its
own `local/` — a team's house rules, a subject system with the code it
needs, a code style. It was called `team` until 2026-09-18, and a
declaration that still says `team` resolves as `shared`.

## Why
A name was doing a file's work. Until 2026-09-18 a shared set had to be
called `precedent-team-<slug>`, and four mechanisms keyed on that shape:
the level was inferred from it, the clone URL was built from it, the leak
gate recognised a vendored private set by it, and the attribution key was
it. The first set built for a subject rather than a team could not be
called what its author called it, and the gate refused a public planning
document for having a title that began the same way. Every one of those
four jobs is done better by a declared field: a level that is stated, a
repository that is named where it is declared, a manifest that says the
set is private, and an identity the resolver verifies instead of parses.

The disclosure half exists because the enforcement half structurally
cannot reach the moment that matters. A check runs against a declared
source; a person picks a name minutes earlier, in conversation, often from
a phone. Telling them then is the only intervention available.

## Story
The convention was first written down as a shape per level — the
universal set unprefixed, `precedent-individual` for every person,
`precedent-team-<slug>` per team — and left in a plan's checklist rather
than the loader or a check. Within days the one document a new adopter
follows was telling them to pick `<your-name>-individual` **or similar**,
while the engine had quietly begun depending on the shape it had never
stated. Fixing the name by level closed that gap on 2026-09-06, and it held
for twelve days.

Then the first subject set arrived: a body of practices and code for one
kind of work, used by whoever does that work, on any team. It was not a
team, and its author wanted it called what it was. The resolver refused
the name; the leak gate had already refused a proposal document for the
same prefix. Reading what the name actually carried showed four jobs, each
with a file that could carry it instead — and the same repository had
already made this move once, one layer down, when a repo-local `path` was
fixed to `local` rather than left as a choice. This is that move again, in
the other direction: the choice is given back to the author, and the
machinery reads a file. Morgan approved the change on 2026-09-18 (relayed
by Alex).

## Install
[tools/precedent_resolve.py](../tools/precedent_resolve.py) reads a
source's `precedent-source.json` in `load_source` and refuses a declared
name or level the clone does not answer to; `check_source_name` refuses a
name that is not a slug, and the two fixed names. Its `normalize_level`
reads `team` as `shared`. [tools/precedent_bootstrap_source.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_bootstrap_source.py)
writes the manifest into every set it creates.
[tools/precedent_source_bootstrap.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_source_bootstrap.py)
clones a declared set from its declared `repo` when the repository is not
called what the set is, else from the base URL and the name.
[tools/leak_gate.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/leak_gate.py) recognises a vendored private
set by a declared name or by the manifest it carries, never by a name
shape. [tools/checkin.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/checkin.py) `--source NAME` vendors the
code directories a shared set's manifest lists.
[tools/precedent_check.py](../tools/precedent_check.py) checks every
`precedent.json` in the tree, and every reachable source's manifest against
what is declared for it. The disclosure half is carried by the occasion
index, which is why this practice's occasion names importing and creating a
repository rather than only declaring one.
