---
title:         Pre-staging retired for everyone
kind:          proposal
status:        accepted
opened:        2026-10-14
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The only person on the ladder retired pre-staging for everyone. Nothing lands on it or makes it any more, a leftover setting reads as staging, and every repository still carrying it moves off it at its next Update Vendors. The ladder becomes two tiers: Booked lands on staging, Debut runs the full tests there, Produce moves staging into main. Deleting the pre-staging code waits until every repository has moved."
---
# Pre-staging retired for everyone

**Decided:** Morgan, 2026-10-14 (strength: decided): *"Only me, go ahead
and plan it. Retire pre-staging."* He is the only person on the ladder, so
the three-tier route (`pre-staging` -> `staging` -> `main`) serves nobody,
and keeping it meant every ladder rule described two routes. That is how
the rules drifted: on 2026-10-13 a consumer's Update Vendors landed on
`staging` while the Booked text still said `pre-staging`.

Until now pre-staging was retired one person and one repository at a time
(`retire_pre_staging` in a person's identity.json, 2026-10-09; the
repository-by-repository move in the ladder set's
redesign plan). This plan finishes that move for everyone.

## The ladder after this

| Stage | What it moves | Command |
|---|---|---|
| 3 Booked | feature branch -> `staging`, quick checks | `python3 tools/precedent_branches.py --land BRANCH` |
| 4 Debut | nothing; the full suite runs on `staging` | `python3 tools/precedent_branches.py --run-tests` |
| 5 Produce | `staging` -> `main` | as the ladder set's `produce` says |

People off the ladder are untouched: their work lands on the repository's
main branch, as before.

## Pieces

**A. Engine (BestPractice `tools/`).**

1. **No route lands on pre-staging.** A `landing_branch` of `pre-staging`,
   in a person's identity.json or a repository's precedent.json, reads as
   `staging`, and says why. A repository with tiers and no value lands on
   `staging`. A new install, or a repository given its first
   `landing_branch`, gets `staging`.
2. **Nothing makes pre-staging.** `--ensure-tiers` makes only `staging`.
3. **Every repository still carrying pre-staging moves off it at its next
   Update Vendors**, by the step that already does it
   (`retire_pre_staging_step`, 2026-10-09): its waiting work merged into
   `staging` with the quick checks, the branch offered for deletion as a
   link, its precedent.json switched to `staging`, its own Markdown
   repointed. That step no longer waits on `retire_pre_staging` or on the
   person being the repository's only maintainer: only a person on the
   ladder ever landed on pre-staging, and that is one person.

**B. Rules.**

1. The ladder set (precedent-shared-ladder) describes two tiers. The
   add-on `ladder-in-a-repo-on-staging` becomes the rule itself and is
   retired. How pre-staging worked moves under each practice's `## Story`.
2. Morgan's individual set and the universal set lose their pre-staging
   instructions; examples name `staging`.

**C. Landing.** Booked, then Produce, in BestPractice,
precedent-shared-ladder and precedent-individual.

## Deliberately later

**Deleting the pre-staging code** (`--sync-pre-staging`, Promote's
pre-staging-into-staging path, the retirement step itself, and their
tests) waits until every repository has run Update Vendors with this
engine: the retirement step is what moves them, and it uses that code.
Filed as
[todo/todo-2026-10-14-delete-pre-staging-code.md](../todo/todo-2026-10-14-delete-pre-staging-code.md).
