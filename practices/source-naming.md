---
slug:        source-naming
title:       A universal, individual or repo-local source's name is fixed by its level; a shared source's is not
tier:        on-demand
severity:    default
applies_to:  ["precedent.json"]
occasion:    "importing, creating, or declaring a repository that holds practices"
gates:       []
index_clause: "names are fixed by level, except shared; say the convention before picking one"
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
Three of a practice-set source's four levels fix the name, never chosen:
`precedent` for the universal set, `precedent-individual` for every person's
own set, and `local` for a repo-local one. The owning account already
namespaces the repository, so the owner is never repeated in the name.

**The fourth level, `shared`, does not fix a name.** It carries no required
prefix and no pattern check — a shared source is named whatever the team
that owns it calls its repository. This is a deliberate narrowing from the
level's earlier convention (`precedent-team-<slug>`, retired 2026-09-19 —
see Story): free naming was Morgan's own call, made explicit as "we aren't
going to accept only precedent-team-* names anymore," not an oversight this
practice failed to enforce. The `name` declared in a configuration file must
still match what the source itself declares (its own `precedent-source.json`
or equivalent); the repository and its clone directory should too.

**Say the convention the first time it can matter.** When importing,
creating, or attaching a repository that will hold practices comes up —
before anyone picks a name, gives an instruction that names one, or creates
the repository — state the convention and the exact name it produces for the
case at hand. Do not apply it silently, and do not correct a name after the
fact. The person naming the repository is the one participant no mechanical
check can reach.

## Detail
Different names are all called "the naming convention," and they fail
differently, so they are enforced differently:

| The name | If it varies | Answer |
|---|---|---|
| The `name` field in `precedent.json` or the user-level config, for `universal`, `individual` or `repo-local` | Attribution in a materialized `MANIFEST.json` stops matching; every error message names a set nobody recognizes | **Refused** by [tools/precedent_resolve.py](../tools/precedent_resolve.py) |
| The same field for `shared` | Only that it must match the source's own declared name (see below) | **Unconstrained** otherwise — no pattern is checked |
| The clone directory a source's `path` points at | The declared relative path is wrong on that machine | **Warned** about, never refused: continuous integration checkouts and git worktrees legitimately differ |
| The GitHub repository name, for `universal`, `individual` or `repo-local` | Nothing breaks today; a later rename breaks every vendored reference | **Recommended**, and disclosed per the Rule above |
| The GitHub repository name, for `shared` | Nothing checks it at all | Whatever the owning team calls it |

A repo-local source's `name` is the literal string `local`, matching its
already-fixed `path`, so the answer travels from one Precedent repository to
the next instead of being re-chosen per repo. A shared source still needs
*a* stable name — every consumer that declares it must use the same string,
and that string is attribution in a materialized `MANIFEST.json` — it is
just no longer required to look a particular way.

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

**2026-09-19: the level was renamed `team` to `shared`, and the fixed-name
requirement for it was dropped in the same pass.** Three private repos
(precedent-team-writing, precedent-team-repo-maintenance,
precedent-team-working-style) had all independently vendored an
individual-scoped practice (`buenos-aires-dates`) alongside a genuinely
generic one (`commit-author`) — a mistake traced back to conflating "this
check's mechanism is generic" with "this practice's prose is meant to
travel." Fixing it surfaced that the engine's `team` keyword and the
consuming repos' own `precedent.json` files already disagreed (`shared` in
every config, `team` in the code that validated it) — vocabulary drift
nobody had reconciled. Morgan's decision, put to him directly: adopt
`shared` as the real name rather than force the configs back to `team`, and
while renaming it, stop requiring the `precedent-team-<slug>` prefix at
all — "we aren't going to accept only precedent-team-* names anymore." The
three repos above were renamed on GitHub to match (precedent-shared-writing,
precedent-shared-repo-maintenance, precedent-shared-working-style) as part
of the same change.

## Install
[tools/precedent_resolve.py](../tools/precedent_resolve.py)'s `load_config`
refuses a `name` that does not match its level's shape (`SOURCE_NAME_SHAPE`
in `check_source_name` — `shared` deliberately has no entry there, so the
check is a silent no-op for it), and warns when a source's `name` and the
basename of its `path` disagree.
[tools/precedent_bootstrap_source.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_bootstrap_source.py)
refuses a non-conforming `--name` for `universal`, `individual` or
`repo-local` before it creates anything, which is the last moment a wrong
name is still cheap; a `shared` `--name` is accepted as given.
[tools/precedent_check.py](../tools/precedent_check.py) checks every
`precedent.json` in the tree, so a shipped template cannot drift either.
Neither reaches the disclosure half of the Rule: that one is carried by the
occasion index, which is why this practice's occasion names importing and
creating a repository rather than only declaring one.
