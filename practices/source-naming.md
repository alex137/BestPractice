---
slug:        source-naming
title:       A practice-set source's name is fixed by its level, and is disclosed before anyone picks one
tier:        on-demand
severity:    default
applies_to:  ["precedent.json"]
occasion:    "importing, creating, or declaring a repository that holds practices"
gates:       []
index_clause: "names are fixed by level; say the convention before anyone picks a name"
checked_by:  "tools/precedent_check.py"
defines:     ["practice-set source"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       2026-09-06
approved_by: "Morgan F"
---
## Rule
A practice-set source's name is fixed by its level, never chosen:
`precedent` for the universal set, `precedent-individual` for every person's
own set, `precedent-team-<slug>` for a team's, and `local` for a repo-local
one. The owning account already namespaces the repository, so the owner is
never repeated in the name. A team slug is lowercase, hyphenated, and names
the team's **purpose** — a roster-shaped name is stale the moment a third
person joins, and renaming a set breaks every vendored reference to it. The
`name` declared in a configuration file must match; the repository and its
clone directory should.

**Say the convention the first time it can matter.** When importing,
creating, or attaching a repository that will hold practices comes up —
before anyone picks a name, gives an instruction that names one, or creates
the repository — state the convention and the exact name it produces for the
case at hand. Do not apply it silently, and do not correct a name after the
fact. The person naming the repository is the one participant no mechanical
check can reach.

## Detail
Four different names are all called "the naming convention," and they fail
differently, so they are enforced differently:

| The name | If it varies | Answer |
|---|---|---|
| The `name` field in `precedent.json` or the user-level config | Attribution in a materialized `MANIFEST.json` stops matching; every error message names a set nobody recognizes | **Refused** by [tools/precedent_resolve.py](../tools/precedent_resolve.py) |
| The clone directory a source's `path` points at | The declared relative path is wrong on that machine | **Warned** about, never refused: continuous integration checkouts and git worktrees legitimately differ |
| The GitHub repository name | Nothing breaks today; a later rename breaks every vendored reference | **Recommended**, and disclosed per the Rule above |
| A team slug's meaning (purpose, not roster) | The name goes stale rather than wrong | Judgment. No check can tell `precedent-team-writing` from `precedent-team-morgan-alex` |

A repo-local source's `name` is the literal string `local`, matching its
already-fixed `path`, so the answer travels from one Precedent repository to
the next instead of being re-chosen per repo.

## Why
A convention that lives only in prose is a convention that drifts, and the
drift is invisible until an outside adopter has already built on it. Names
are the worst place for that, because the remedy — renaming — is exactly
what breaks vendored references, so the cost of a wrong name rises with
every day it goes unnoticed.

The disclosure half exists because the enforcement half structurally cannot
reach the moment that matters. A check runs against a declared source; a
person picks a repository name minutes earlier, in a conversation, often
from a phone. Telling them the convention at that moment is the only
intervention available.

## Story
The convention was written down early — the universal set unprefixed, one
`precedent-individual` per person, `precedent-team-<slug>` per team, with
the reasons attached — and then left in a plan's human checklist rather than
the sources spec, the loader, or a check. Within days the one document a new
adopter actually follows was telling them to pick `<your-name>-individual`
**or similar**: no prefix, the owner repeated where the account already
supplied it, and an explicit invitation to invent a third form. Meanwhile
the engine had quietly begun depending on the convention it had never
stated — a resolver default of `precedent-individual`, a session-hook
filename hardcoded to the same string whatever the source was actually
called, and the `name` recorded as attribution inside a committed manifest,
where a rename silently stops matching.

The same repository had already been through this one layer down. Two
dependent repos picked two different directory names for their repo-local
practices, and what closed that gap was not clearer prose but removing the
choice: a repo-local `path` must now be exactly `local`, refused otherwise.
This practice is that move made one layer earlier, before there are outside
adopters whose references a correction would break.

## Install
[tools/precedent_resolve.py](../tools/precedent_resolve.py)'s `load_config`
refuses a `name` that does not match its level's shape, and warns when a
source's `name` and the basename of its `path` disagree.
[tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
refuses a non-conforming `--name` before it creates anything, which is the
last moment a wrong name is still cheap.
[tools/precedent_check.py](../tools/precedent_check.py) checks every
`precedent.json` in the tree, so a shipped template cannot drift either.
Neither reaches the disclosure half of the Rule: that one is carried by the
occasion index, which is why this practice's occasion names importing and
creating a repository rather than only declaring one.
