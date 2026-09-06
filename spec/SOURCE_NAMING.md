<!-- Last updated: 2026-09-06 (Buenos Aires) by the session that landed the
     convention, from a brainstorm with Morgan. -->

# How a practice-set source is named

A source's name is fixed by its level, not chosen. This document carries the
reasoning: what the convention is, why four different names that all get
called "the naming convention" are enforced differently, and what was decided.
The rule itself is [practices/source-naming.md](../practices/source-naming.md);
the reference a session reads while working is
[spec/SOURCES.md](SOURCES.md)'s Naming section.

## The convention

| Level | Name | Where it lives |
|---|---|---|
| Universal | `precedent` — no prefix; it is the product, not a set | [alex137/BestPractice](https://github.com/alex137/BestPractice) |
| Individual | `precedent-individual`, identical in every person's account | a **private** repository in that person's own account |
| Team | `precedent-team-<slug>`, slug lowercase and hyphenated, named for the team's *purpose* | a private repository the team owns |
| Repo-local | `local` | the consuming repo's own `local/` directory |

## Why this needed writing down at all

The first three rows were already specified — in
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s "What Morgan Needs to
Do", with the three reasons attached. Being written in a phase checklist
rather than the spec, the loader, or a check was enough for it to come apart.
Four things were true when this work started, all of them on 2026-09-06:

1. **The one document a new adopter follows contradicted it.**
   [spec/BOOTSTRAP_NEW_SOURCES.md](BOOTSTRAP_NEW_SOURCES.md) told them to pick
   `<your-name>-individual` **or similar** — no prefix, the owner repeated
   where the account already supplies it, and an explicit invitation to invent
   a third form.

2. **The engine already depended on the convention it had never stated.**
   [tools/precedent_resolve.py](../tools/precedent_resolve.py) defaults an
   unnamed individual source to `precedent-individual`;
   [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
   writes its session hook to a fixed
   `.claude/hooks/precedent-individual-bootstrap.sh` whatever the source is
   called, so a person following the bootstrap document's own advice got a
   hook file naming a set that did not exist.

3. **A rename silently breaks attribution.**
   [tools/precedent_materialize.py](../tools/precedent_materialize.py) records
   the `name` string in the committed `MANIFEST.json` as the attribution for
   every materialized check, and its orphan detection reads that back.

4. **The repo-local row had never been stated**, and this repository's own
   answer to it was picked freehand.

The shape is the one [tools/precedent_resolve.py](../tools/precedent_resolve.py)'s
`load_config` already records for `path`: two dependent repos picked two
different directory names for the same thing, prose did not stop it, and what
closed the gap was removing the degree of freedom. That refusal was earned by
two reproduced bugs. This is the same move one layer earlier, taken before
there are outside adopters whose references a correction would break.

## Four names, four enforcement stories

The single biggest risk in "let's have a naming convention" is treating four
distinct things as one. They fail differently:

| # | The name | Who reads it | If it varies | Answer |
|---|---|---|---|---|
| 1 | The GitHub repository name (`themorgan/precedent-team-tms`) | people, browsing | nothing breaks immediately; a later rename breaks every vendored reference | **Recommended**, and disclosed before anyone picks one |
| 2 | The local clone directory (the `path` in [precedent.json](../precedent.json)) | the resolver, per machine | the declared relative path is wrong on that machine | **Warned** about, never refused |
| 3 | The `name` field in [precedent.json](../precedent.json) or the user config | the resolver, `MANIFEST.json` attribution, every error message | attribution stops matching; messages name a set nobody recognizes | **Refused** |
| 4 | A team slug's meaning — purpose, not roster | people, over years | the name goes stale rather than wrong | Judgment; no check can see it |

The engine cannot rename anyone's repository, so row 1 can never be more than
a recommendation. Row 3 is a string in a tracked configuration file the engine
already parses and validates for `level` and `path`, so refusing a malformed
name there costs one branch in `load_config` and the message can teach the
convention at the moment it is being broken. That asymmetry, not a general
principle, is why this is both recommended and enforced.

Row 2 is deliberately not a refusal. A continuous integration checkout, a git
worktree, and a vendored universal copy at `process/upstream` all legitimately
put a conforming source in a differently-named directory.

## What carries it

| Half of the rule | Carried by |
|---|---|
| The `name` field must match its level's shape | [tools/precedent_resolve.py](../tools/precedent_resolve.py)'s `check_source_name`, raising rather than warning |
| Name and clone directory should agree | the same module's `warn_name_matches_path`, on standard error |
| A new set is never created under a wrong name | [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py) refuses the `--name` before it writes anything |
| Every `precedent.json` in the tree conforms, shipped templates included | [tools/precedent_check.py](../tools/precedent_check.py)'s `source-naming` check, with a planted case in [tools/verify_harness.py](../tools/verify_harness.py) |
| Say the convention before a name is picked | the occasion index — this practice's occasion names *importing and creating* a repository, not only declaring one |
| The adopter-facing procedure states it | [spec/BOOTSTRAP_NEW_SOURCES.md](BOOTSTRAP_NEW_SOURCES.md) and [INSTALL.md](../INSTALL.md) |

The disclosure half exists because the enforcement half structurally cannot
reach the moment that matters. A check runs against a declared source; a
person picks a repository name minutes earlier, in conversation. Telling them
the convention then is the only intervention available — which is why it is a
clause of the Rule and not a footnote.

## What the first real consumer refresh showed

`themorgan/HavrutaBrainstorm` refreshed its vendored engine from
`precedent-beta-v01` on 2026-09-06 — the first time the refusal met a repo
nobody had prepared for it. Worth keeping, because it is the only evidence
that the split between the two halves behaves:

- Its repo-local source was named `havruta-local`. The refusal fired during
  `precedent_sync_views`, **before** anything was written, and its message
  carried the expected name — so the session fixed it without having this
  document in its tree.
- [tools/precedent_check.py](../tools/precedent_check.py) reported
  `source-naming` as SKIPPED, with the reason
  (*"this check belongs to a source this repo does not resolve"*), rather
  than passing. The enforcement travels with the engine and the explanation
  with the catalogue; a consumer sees the gap instead of a false all-clear.
- The same refresh produced one finding nobody predicted: a citation
  problem. `# practice: source-naming` comments inside the vendored
  [precedent_resolve.py](../tools/precedent_resolve.py) named a practice the
  consumer's catalogue did not
  carry yet, so `code-cites-practice` reported them as typos.
  [tools/precedent_check.py](../tools/precedent_check.py) now exempts files
  named in `tools/ENGINE_MANIFEST.json` — a vendored engine file's
  citations are upstream's, and unfixable from the consuming repo. The
  exemption is keyed on the manifest rather than a filename list precisely
  so it cannot weaken the check here, where BestPractice has no manifest
  and never will.

The instruction that sent that session in was also wrong, and the correction
is worth more than the finding: it named `status` and `refresh` against a
repo whose `tools/` was a pre-mechanism hand-copy, where neither verb can
run. [INSTALL.md](../INSTALL.md) §2 step 6 already covered that case, in its
last sentence; it now leads with it.

## Decisions taken

**Recommend, or recommend and enforce? Both, split by layer** — refuse the
`name` field's shape, warn on the clone directory, recommend the repository
name. Leaving all of it advisory was the status quo, and the status quo had
already drifted in the document adopters read.

**Must a team slug describe purpose? Yes, and it stays judgment.**
`precedent-team-tms` and `precedent-team-morgan-alex` are indistinguishable to
a regular expression. The Rule says it, with the reason attached; no check
pretends to see it.

**What is a repo-local source's name? The literal string `local`**, matching
its already-fixed `path` and carrying the same argument: zero degrees of
freedom, so the answer travels from one Precedent repository to the next. The
alternative, `<repo>-local`, reads better in a message but reintroduces the
per-repo choice this exists to remove, and `MANIFEST.json` attribution is read
inside the repository it describes, where `local` is unambiguous.

**Do names assume organization ownership? Open, and deliberately so.** The
plan's own trigger for moving team sets into a GitHub organization — *once
there is a second team* — has fired: as of 2026-09-06 there are two,
`precedent-team-maintainers` and `precedent-team-tms`, both in a personal
account. Nothing in this convention breaks either way, because `<owner>` is
supplied by whoever owns the set and never appears in the name. If team sets
move, the team row's `<owner>` becomes the organization and the individual
row's stays the person; no name changes. That is the reason it was safe to
land the convention without settling the organization question first, and the
question itself is still Morgan's to answer.

## What this does not do

- **It does not touch practice slugs.** Slugs are identities the resolver
  resolves precedence by, and they already have a stated uniqueness rule.
- **It does not rename anything that exists**, beyond this repository's own
  repo-local source, whose name appeared in exactly one tracked file.
- **It does not resolve the reader-vocabulary tension.** `precedent-` is this
  project's word, not a reader's. For the non-technical editorial use case in
  [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md),
  the prefix buys the clustering benefit and costs
  [readers-vocabulary](../practices/readers-vocabulary.md): an editor sees a
  repository named after a system they never use. Naming the tension rather
  than discovering it at adoption is the point; the disclosure clause is what
  makes it surface in conversation, where it can be discussed, instead of in a
  refusal.
