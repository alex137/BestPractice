<!-- Last updated: 2026-09-06 (Buenos Aires) by a session working from a
     brainstorm with Morgan. Proposed, not built — see "Status" below. -->

# Proposal: one naming convention for practice-set sources

**Status: proposed. Nothing here is built, and nothing here is enforced.**
This document asks for four decisions (["Decisions needed"](#decisions-needed)).
If they land, the work is one practice file, one resolver change, and three
documentation fixes — all listed under
["What this would change"](#what-this-would-change), none of it started.

## What is being proposed

That the shape of a practice-set source's name stops being advice in a plan
and becomes a rule the engine states, checks where it can, and warns about
where it cannot.

| Level | Name | Where it lives |
|---|---|---|
| Universal | `precedent` — no prefix; it is the product, not a set | [alex137/BestPractice](https://github.com/alex137/BestPractice) |
| Individual | `precedent-individual`, identical in every person's account | a **private** repository in that person's own account |
| Team | `precedent-team-<slug>`, slug lowercase and hyphenated, named for the team's *purpose* | a private repository owned by the team |
| Repo-local | `local` | the consuming repo's own `local/` directory |

Three of those four rows are already written down. The fourth (repo-local's
`name`) has never been stated anywhere, and this repository's own answer to
it — `bestpractice-local`, in [precedent.json](../precedent.json) — was
picked freehand.

## The convention already exists; that is the actual finding

The question a brainstorm naturally asks is *should we have a naming
convention*. The answer is that we do, and it is not working. Four pieces of
evidence, all current as of 2026-09-06:

1. **It is specified in a phase checklist, not a spec.**
   [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s
   "What Morgan Needs to Do" carries the table above and three reasons for it:
   sets cluster in a repository listing, the account already namespaces the
   name so the owner is not repeated in it, and a team is named for its
   purpose because a roster-shaped name goes stale the moment a third person
   joins. None of that is in [spec/SOURCES.md](SOURCES.md), which is where a
   session reads about sources, and none of it is in the loader.

2. **It has already drifted, in the one document an adopter follows.**
   [spec/BOOTSTRAP_NEW_SOURCES.md](BOOTSTRAP_NEW_SOURCES.md)'s procedure tells
   a new adopter to pick `<your-name>-individual` **or similar**. That drops
   the `precedent-` prefix, does the one thing the plan explicitly says not to
   do (repeat the owner, which the account already supplies), and the
   "or similar" hands the next adopter licence to invent a third form.

3. **The name is already load-bearing in code, while documented only as
   advice.** [tools/precedent_resolve.py](../tools/precedent_resolve.py)
   defaults an unnamed individual source to `precedent-individual`.
   [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
   writes its session hook to a fixed
   `.claude/hooks/precedent-individual-bootstrap.sh` no matter what the source
   is called, so a person who takes the bootstrap document's own advice and
   names their set `morgan-individual` gets a hook file naming a set that does
   not exist. [tools/precedent_materialize.py](../tools/precedent_materialize.py)
   records the `name` string in the committed `MANIFEST.json` as the
   attribution for every materialized check, and its orphan detection reads
   that attribution back — so a renamed source silently stops matching its own
   manifest entries.

4. **The plan's own trigger for the next structural step has fired
   unnoticed.** It says to move team sets into a GitHub organization *once
   there is a second team*. As of 2026-09-06 there are two —
   `precedent-team-maintainers` and `precedent-team-tms` — both in a personal
   account.

The shape of this is exactly the `path: "local"` story that
[tools/precedent_resolve.py](../tools/precedent_resolve.py)'s `load_config`
now records in its own docstring: two dependent repos picked two different
names for the same thing, prose did not stop it, and what closed the gap was
removing the degree of freedom. That refusal was earned by two reproduced
bugs, not by a style argument. This proposal is the same move made one layer
earlier, before there are external adopters to break.

## Four names, four different enforcement stories

The single biggest risk in "let's have a naming convention" is treating four
distinct things as one. They fail differently and deserve different answers:

| # | The name | Who reads it | If it varies | Proposed |
|---|---|---|---|---|
| 1 | The GitHub repository name (`themorgan/precedent-team-tms`) | people, browsing | nothing breaks immediately; a later rename breaks every vendored reference | **Recommend**, and warn |
| 2 | The local clone directory (`../precedent-team-maintainers`, the `path` in [precedent.json](../precedent.json)) | the resolver, per machine | the declared relative path is wrong on that machine | **Warn** on mismatch |
| 3 | The `name` field in [precedent.json](../precedent.json) or the user config | the resolver, `MANIFEST.json` attribution, every error message | attribution stops matching; messages name a set nobody recognizes | **Refuse** a malformed shape |
| 4 | The repo-local source's `name` | the same as row 3 | one repo says `bestpractice-local`, the next says something else | **Fix** it to `local` |

The engine cannot rename anyone's repository, so row 1 can never be more than
a recommendation plus a warning. Row 3 is a string in a tracked configuration
file that the engine already parses and validates for `level` and `path` —
refusing a malformed name there costs one branch in `load_config` and the
error message can teach the convention at the exact moment it is being
broken. That asymmetry, not a general principle, is why this proposal
recommends *and* enforces rather than choosing one.

## What this would change

Six edits, in dependency order. None is large; the third is the only one that
can refuse anyone's work.

1. **A universal practice, `source-naming`.** `tier: on-demand`,
   `occasion: "creating or declaring a practice-set source"`,
   `applies_to: ["precedent.json"]` so
   [tools/precedent_paths.py](../tools/precedent_paths.py) surfaces it without
   the occasion index. Draft Rule and Story are in the last section below, so
   the candidate is ready to raise rather than re-derived.
2. **[spec/SOURCES.md](SOURCES.md) gains a "Naming" section** carrying the
   table and the three reasons, and becomes the one place the convention is
   stated. The plan keeps its text as the historical record of the decision.
3. **[tools/precedent_resolve.py](../tools/precedent_resolve.py)'s
   `load_config` refuses a malformed `name`** for each level, with a message
   in the style of the existing repo-local `path` refusal: what was declared,
   what is required, and why it is fixed rather than a per-repo choice.
4. **The same function warns** — on standard error, never fatal — when a
   source's `name` and the basename of its `path` disagree. It cannot refuse:
   continuous integration checkouts and git worktrees legitimately differ.
5. **[spec/BOOTSTRAP_NEW_SOURCES.md](BOOTSTRAP_NEW_SOURCES.md) step 1 is
   corrected** to `precedent-individual`, and its "or similar" removed. This
   one is worth doing whatever else is decided — it is a straight
   contradiction of the plan today.
6. **[precedent.json](../precedent.json)'s repo-local source is renamed**
   `bestpractice-local` → `local`, if decision 3 lands. The string appears in
   exactly one tracked file, so the rename is a one-line change with no
   reference-repointing behind it.

The practice's `checked_by` would name
[tools/precedent_check.py](../tools/precedent_check.py), with the check
asserting that every source declared in this repository's own
[precedent.json](../precedent.json) matches the convention.
[checkable-gets-checked](../practices/checkable-gets-checked.md) requires
running a candidate check against the whole unplanted tree before wiring it
in: on today's tree it would pass on the universal and team rows and fail on
`bestpractice-local`, which is decision 3 and not a surprise.

## Decisions needed

**1. Recommend, or recommend and enforce?** *Recommendation: both, split by
layer* — refuse the `name` field's shape (row 3), warn on the clone directory
(row 2), recommend the repository name (row 1). Leaving all of it advisory is
the status quo, and the status quo has already drifted in the document
adopters read.

**2. Must a team slug describe purpose?** The plan says name a team for its
purpose, never its roster. That is a judgment no check can make —
`precedent-team-tms` and `precedent-team-morgan-alex` are indistinguishable to
a regular expression. *Recommendation: keep it as stated guidance in the
practice's Rule, with the "stale the moment a third person joins" reason
attached, and do not pretend it is checkable.*

**3. What is a repo-local source's `name`?** *Recommendation: the literal
string `local`*, matching its already-fixed `path` and carrying the same
argument — zero degrees of freedom, so the answer travels from one Precedent
repository to the next. The alternative, `<repo>-local`, reads better in a
message but reintroduces the per-repo choice this is meant to remove, and
`MANIFEST.json` attribution is read inside the repo it describes, where
`local` is unambiguous.

**4. Do names assume organization ownership?** The plan's own trigger has
fired (two teams, one personal account). *Recommendation: decide the
organization question before writing the convention down, not after.* If team
sets move to an organization, `<owner>` in the convention becomes the
organization for team sets and stays the person's account for individual
sets, and the convention should say so on the first pass — a rename after
adoption is the expensive case this whole proposal is trying to avoid. This
is a real question for Morgan, not a formality; the naming work can land
without it, but it will need a second pass if the answer arrives later.

## What this deliberately does not do

- **It does not touch practice slugs.** Slugs are identities the resolver
  resolves precedence by, and they already have a stated uniqueness rule.
  This is about source names only.
- **It does not propose renaming anything that exists**, other than the
  one-line `bestpractice-local` case. All three real sources already conform.
- **It does not decide the reader-vocabulary tension.** `precedent-` is this
  project's word, not a reader's. For the non-technical editorial use case in
  [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md),
  the prefix buys the clustering benefit and costs
  [readers-vocabulary](../practices/readers-vocabulary.md): an editor sees a
  repository named after a system they never use. Naming it here rather than
  discovering it at adoption is the point; resolving it is not this
  proposal's to do.

## Rolling it out to the attached sources

Per [cross-source-rollout](../practices/cross-source-rollout.md), a change to
how sources are declared has implications for the sources themselves. Nothing
in this proposal changes a practice file inside `precedent-individual`,
`precedent-team-maintainers`, or `precedent-team-tms` — all three already
match the convention, so the rollout is a verification, not an edit. If
decision 1 lands, the check should be run once against each of those three
repositories' own consuming configurations before the refusal ships, so a
teaching error message is never the way someone finds out.

## The practice text, if approved

Draft, so the candidate can be raised as written rather than re-derived. Per
[cite-the-incident](../practices/cite-the-incident.md) the Story carries the
failure the rule prevents.

**Rule.** A practice-set source's name is fixed by its level, not chosen:
`precedent` for the universal set, `precedent-individual` for every person's
own set, `precedent-team-<slug>` for a team's, `local` for a repo-local one.
The owning account already namespaces the repository, so the owner is never
repeated in the name. A team slug is lowercase, hyphenated, and names the
team's *purpose* — a roster-shaped name is stale the moment a third person
joins, and renaming a set breaks every vendored reference to it. The `name`
declared in a configuration file must match; the repository and clone
directory should.

**Story.** The convention was written into a plan's human checklist and never
into the spec, the loader, or a check. Within days, the one document a new
adopter actually follows told them to pick `<your-name>-individual` or
similar — dropping the prefix, repeating the owner the account already
supplies, and inviting a third variant — while the engine had meanwhile
hardcoded `precedent-individual` in a resolver default and a session-hook
filename, and begun recording the name as attribution in a committed
manifest. The same repository had already been through this once at the
directory layer, where two dependent repos picked two different names for
their repo-local practices and the fix was not clearer prose but removing the
choice.
