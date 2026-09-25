---
title:         Three branch tiers -- pre-staging, staging, main
kind:          proposal
status:        accepted
opened:        2026-09-25
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Every repo gets three branches with three levels of checking: pre-staging (seconds -- markdown lint and the leak gate), staging (every local check), main (every local check plus one GitHub test on the pull request into it). Many windows push to pre-staging and never wait; a Promote moves pre-staging to staging and pays the full check once for the whole batch. precedent-beta-v01 becomes staging."
---

# Three branch tiers -- pre-staging, staging, main

**The problem.** Morgan works in the cloud version of Claude Code, often
with eight or more windows open at once, each editing a different part of
the same document. Since the local push check came back on 2026-09-25
([precedent_push_check.py](../tools/precedent_push_check.py), wired by
[push-check-gate.sh](../templates/harness/claude-code/hooks/push-check-gate.sh)),
every push runs the full list, on every branch, including a session's own
working branch. Saving went from about a second to many minutes. He wants to
keep every check -- *"I love the long detail checks. Prevent so many
problems"* -- and stop waiting on them: *"even just 5 minutes still kills
flow."*

**The shape.** Checking depends on which branch is pushed to. Most pushes go
to a branch that checks in seconds; the full list runs once per batch, when
the batch is promoted.

**Status: accepted, being built.** Steps 1 to 4 landed 2026-09-25 (pull
request #605); steps 5 to 7 are next, with `landing_branch` defaulting to
staging until Alex has heard, so only a person who sets it lands on
pre-staging meanwhile. Worked out in a brainstorm on 2026-09-25
and approved the same day. The decisions, with how firmly each was made
([decision-strength](../practices/decision-strength.md)):

| Decision | Morgan's words | Strength |
|---|---|---|
| Three tiers, checked by branch | *"to prestaging only the most minimal test; to staging/precedent-beta-v01 all local tests; and then to main, you get all those local tests AND the most important GitHub test"* | decided |
| No scheduled promotion | *"I think that it should not be on a cron"* | decided |
| The name | *"let's call it \"pre-staging\""* | decided |
| Every repo | *"I think all repos should use this."* | decided |
| Other branches get the basic check only, by default, for everyone | *"the default for everyone should be all branches other than the above never get tested beyond the basic markdown test when pushed to"* | decided |
| The staging branch is called `staging`, everywhere, and `precedent-beta-v01` is renamed | *"we should always call the staging one \"staging\" including renaming that branch to staging in precedent"* | decided |
| The leak gate joins the basic check | *"Good on nothing private going out."* | assented |
| The one GitHub test is the full check, on the pull request into main | *"Good on the one GitHub test."* | assented |
| The freshness guard syncs from pre-staging | *"the freshness guard at pre-staging is good"* | assented |
| Keep yesterday's CI settings as opt-ins rather than retiring them | raised as a question: *"would they still be useful in case someone turns in that they want CI on branches, or on prestaging"*, then the plan saying so approved | assented |
| Rename the GitHub settings to start with `github_ci_` | *"since those refer only to github's tests, maybe we rename them all to start with github_ci_ instead of ci_ to make that clear"* | decided |
| Build it | *"Otherwise, this looks great, let's do it, go ahead, go update"* | decided |
| The recommendations under "Settled at approval" below | approved with the plan as a whole, not one by one | assented |
| `Go update` lands on pre-staging by default | *"in go update" ruleset, the default place to push it to is "pre-staging"? Update the spec to reflect these"* | decided |
| Installs take their updates from main | *"Maybe vendored-in copies are now taken from \*main\*? [...] Update the spec to reflect these"* | decided -- with the 2026-09-24 reversal below in view |
| The primary branch is brought in line with the tiers | *"we now have a concept called \"primary branch\" - that should probably be updated in reference to this"* | decided |

## The rule

| Push to | Checks on our side | GitHub |
|---|---|---|
| any other branch (a session's own branch, a feature branch) | **basic** | none, unless the person opts in |
| **pre-staging** | **basic** | none, unless the person opts in |
| **staging** | **full** | none, unless the person opts in |
| **main** | **full** | **the full check, on the pull request into main** |

**Basic** is the markdown lint on the files the push touches and the leak
gate over the tree. Measured here on 2026-09-25: the lint under a second, the
leak gate about five. The commit-author check
([commit-identity-push-gate.sh](../templates/harness/claude-code/hooks/commit-identity-push-gate.sh))
is separate, instant, and unchanged. **The leak gate is in the basic check
because pushing any branch to a public repository publishes it**; it cannot
wait for promotion.

**Full** is everything [precedent_push_check.py](../tools/precedent_push_check.py)
runs today for the repo's kind. In this repo that includes the verification
harness, about four minutes by [AGENTS.md](../AGENTS.md)'s own measurement,
and it is most of the wait.

**The GitHub test on main** is the full check run in GitHub's clean
environment, on the pull request into main, so it blocks a bad merge rather
than reporting one afterwards. It is the one thing a local run cannot prove:
AGENTS.md already says local green is not CI green, because a session's
container resolves private sources that GitHub's does not. Main is merged
into rarely, so the cost stays small even in a private repository.

**One exception to "GitHub only on main":** a public repository keeps
[leak-gate.yml](../.github/workflows/leak-gate.yml) on every push. It is
free there, and it is the only thing that catches an edit made on github.com
without going through a session.

## What a working day looks like

1. Eight windows open. Each edits, commits, and pushes to **pre-staging** --
   basic check, seconds -- and is free again.
2. Before each push, a window pulls in what the others already pushed, so
   the windows see each other's edits almost live and conflicts stay small.
3. When Morgan wants the batch checked, he says **Promote** in any window and
   leaves it in the background. It merges pre-staging into staging, the push
   to staging runs the full check, and it reports what landed -- or what
   failed.
4. If the full check fails, staging does not move. The same window fixes it
   on pre-staging and promotes again. The other windows keep pushing to
   pre-staging the whole time.
5. Staging reaches main the way beta reaches main today: a pull request, the
   GitHub test, and the repo's own approval rule -- in this repository, Alex's
   named go-ahead for a major change
   ([merge-target-is-beta-branch](../local/practices/merge-target-is-beta-branch.md)).

## The branch names are the same everywhere

**`pre-staging`, `staging`, `main`, in every repository** -- this one, the
practice sources, and every repository that installs Precedent. A repo that
today has only `main` gains the other two; routine work that used to land on
its `main` lands on pre-staging, and main takes it by promotion.

**Names live in one place.** Today the literal `precedent-beta-v01` appears
in 249 files in this repository alone, 37 of them under `tools/` (measured
2026-09-25 at 1c37df3f), and in 30 to 64 files in each of the four practice
sources. Before anything is renamed, every tool reads the three names from
one module ([registry-source-of-truth](../practices/registry-source-of-truth.md)),
so the rename is a one-line change for code. Prose is different: a current
rule is rewritten to say `staging`; a `## Story` section or a closed item
keeps the name it had at the time, because it is history.

## Settings

**Our own checks** get one new setting:

- **`branch_push_checks`** -- `"basic"` (the default, for everyone) or
  `"full"`. It governs pushes to every branch other than staging and main,
  pre-staging included. Read from the person's `identity.json`; a repo's
  `precedent.json` may override it, the same pattern
  [CI_CADENCE_PLAN.md](CI_CADENCE_PLAN.md) uses. Nothing can lower the check
  on staging or main.

**GitHub's checks** keep the three existing settings, with the default
narrowed to main and each one becoming the way to widen it. **Each is
renamed to start with `github_ci_`**, because each governs GitHub's runs
only and never our own checks -- the bare `ci_` prefix let a reader think
`ci_on_branches: false` meant "no checks on branches". A reader accepts the
old name for as long as any file still carries it, and the new name wins
where both appear:

- **`github_ci_workflows`** (was `ci_workflows`) -- whether the installer writes a GitHub workflow into
  a repo at all. **The default becomes `"enabled"`**, installing a workflow
  that triggers only on pull requests into main, so every repository gets
  its main test. `"disabled"` still means no workflow, and then main has no
  GitHub test -- a choice, said out loud at install time. Morgan's own
  `identity.json` says `"disabled"` today and would change to `"enabled"`
  for his main test to exist.
- **`github_ci_on_branches`** (was `ci_on_branches`) -- `false` by default now. `true` adds GitHub runs
  on pushes to pre-staging, staging and other branches, for someone who wants
  them.
- **`github_ci_every_hours`** (was `ci_every_hours`) -- still caps how often those opted-in runs happen
  in a private repo. **It never skips the main test.**

## Three holes this has to close

**1. A merge through GitHub skips the local gate.** A session that merges a
pull request with GitHub's merge tool makes no local push, so the push gate
never runs. Today that is safe only because the branch was fully checked when
it was pushed; under this plan it got the basic check. **A second gate runs
before the merge tool** (`mcp__github__merge_pull_request`, and `gh pr merge`
where a harness has it): when the pull request targets staging or main, it
runs the full check on the pull request's head first and refuses the merge
on a failure.

**2. Pre-staging falls behind when someone pushes to staging directly.**
Alex, or anyone who does not use pre-staging, may push straight to staging
(fully checked). Windows syncing from pre-staging would not see that work.
**The freshness guard reports it at session start and names the command**,
`python3 tools/precedent_branches.py --sync-pre-staging`, which merges
staging into pre-staging -- a basic-tier push, seconds. The guard itself
never merges a base, the rule it has always kept, since a merge from a
hook is a merge nobody chose to make. `Go update` landing on pre-staging
and Promote both run the same sync first, and it stops and reports on a
conflict rather than guessing.

**3. A `[skip ci]` line could silence the main test.** GitHub skips
pull-request workflows when the head commit says `[skip ci]`
([CI_CADENCE_PLAN.md](CI_CADENCE_PLAN.md), "The branch switch"), and with
`github_ci_on_branches` off, commits on pre-staging carry that line. If staging were
fast-forwarded onto one of them, the pull request from staging into main
would get no run. So **Promote always makes a merge commit** (`--no-ff`),
which the cadence hook never tags, and **the hook never tags a commit on
staging**. The move from staging to main is a merge, never a squash -- a
squash message would carry the branch's `[skip ci]` lines with it.

## Who it binds

**Every repository has the three branches, and `Go update` lands on
pre-staging by default, for everyone.** Pushing straight to staging stays
allowed, and is fully checked, so someone who prefers to work that way --
Alex, perhaps -- loses nothing: a per-person setting, `landing_branch`,
set to `"staging"` in that person's own `identity.json`, sends their
`Go update` there instead. Alex hears about this before it ships (step 6),
since it changes where his sessions land their work.

## The primary branch is pre-staging

[primary-branch](../practices/primary-branch.md) defines the primary branch
as *"the one shared branch regular work pushes to and pull requests
target"*. Under this plan that is **pre-staging**, in every repository:
`Go update`, `Push directly` with no branch named, and a session's pull
request all land there. Staging and main are not the primary branch; they
are what the primary branch is promoted into.

Two things in that practice change with it:

- **The repository no longer chooses the name.** Today each repository
  declares its own primary branch (`base_branch` in `precedent.json`), and
  the practice says that choice never travels to the repositories that
  take updates from it. With the same three names everywhere, the tiers are
  one universal rule rather than one repository's rule, and they travel
  like any other practice.
- **`base_branch` means staging until the rename is done.** Every tool that
  reads it today reads it as "where finished work lands", which is what
  staging now is. It is read through the one branch-names module (step 1),
  never directly, so the rename changes one place.

## Installs take their updates from main

**Every install -- every repository that vendors Precedent, and every
practice source a session clones -- takes its updates from `main`**, all
of them at once, not some now and some later. That is the one branch whose
content has passed every local check *and* the GitHub test.

This has been tried once already: on 2026-09-24 installs were pointed at
main and moved back to `precedent-beta-v01` the same day, because that
approval had been *"more an assent, than a decision"*, and because the
move had left installs split across two branches. Morgan then: *"they
should all be consistent and following the same one. Maybe later we'll
move them all to follow main"*. This is that later move, and it keeps
both conditions: decided, and every install at once.

**What it costs:** a change reaches Morgan's other repositories only after
it reaches main -- in this repository, a merge that needs Alex's named
go-ahead when the change is major. Work that sits on staging waiting for
that merge is invisible to every install.

**What it simplifies:** the rename (step 9) no longer touches any install,
because no install follows staging. Only sessions working inside the
Precedent repositories themselves see the old and new names.

## Build steps

In order. Each step leaves every repository working.

1. **One module for the branch names**, and every tool reads from it.
   Nothing is renamed yet; the staging name still resolves to
   `precedent-beta-v01` wherever that is still the branch.
2. **Tier the push check.** Each entry in `PUSH_CHECKS` is tagged basic or
   full; `--tier basic|full` selects. The record of a passing tree names the
   tier, so a basic pass never satisfies a full gate.
3. **The push gate picks the tier by target branch**, per the table and
   `branch_push_checks`. Same change in the template copy under
   `templates/harness/claude-code/hooks/`.
4. **The merge gate** (hole 1), in the harness adapter, with a
   harness-neutral script behind it
   ([vendor-neutral-by-default](../local/practices/vendor-neutral-by-default.md)).
5. **Pre-staging exists.** Created from staging (today, `base_branch`) on first use in
   any repository; the freshness guard syncs from it and merges staging in
   (hole 2).
6. **`Go update` and `Push directly` land on pre-staging**, unless the
   person's `landing_branch` says staging; **a new `Promote` command** does
   the merge and push to staging, as a new practice file; and
   [primary-branch](../practices/primary-branch.md),
   [go-merge](../practices/go-merge.md) and
   [push-directly](../practices/push-directly.md) are rewritten to say so.
   Alex hears about it first.
7. **The Boildown's "not yet landed" line becomes a Promote reminder**:
   commits on pre-staging and not on staging are named, with the
   recommendation to Promote.
8. **GitHub workflow templates trigger on pull requests into main only**,
   plus the opt-ins; the three settings take their `github_ci_` names; the
   `github_ci_workflows` default flips; the cadence hook
   stops tagging staging (hole 3). This repo's own
   [deep-check.yml](../.github/workflows/deep-check.yml), paused on
   2026-09-25, comes back scoped to pull requests into main.
9. **Installs follow main.** `SOURCE_BRANCH` in
   [precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) and
   [precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
   becomes `main`, with every other pin that names a branch, in one change,
   and reaches each install through its next
   [Update Vendors](../practices/vendor-update-runbook.md). Nothing here
   waits on the rename, and the rename then waits on nothing here.
10. **The rename.** Create `staging` at `precedent-beta-v01`'s tip in each
   Precedent repository, and move every `base_branch` to it. **Keep
   `precedent-beta-v01` updated alongside `staging`** until no session
   still pushes to the old name. Then stop updating it and hand
   over the one-click delete link
   ([never-delete-a-remote-branch](../practices/never-delete-a-remote-branch.md)).
   Rewrite the current rules -- AGENTS.md's merge-target paragraph first --
   to say `staging`. **Waits on Alex hearing about it first** (below).

   **Other sessions keep working through the rename.** Nothing is deleted
   or renamed in place; `staging` is added beside the old branch. During
   the transition, a sync -- run by Promote, by the freshness guard, and by
   any push to either branch -- merges each branch into the other and pushes
   both, so a session in another repository that still pushes to
   `precedent-beta-v01`, or an install not yet moved to main (step 9), sees the
   same content it would have seen anyway. The one conflict it cannot settle
   by itself is two sessions changing the same lines on the two branches at
   once; it stops and reports that, exactly as a merge would today. A
   one-click GitHub rename is ruled out for this reason: it would leave every
   session that is mid-work pushing to a name that no longer means what it
   did.
11. **Tests** in [verify_harness.py](../tools/verify_harness.py): each tier
    by branch, the setting and its override, the merge gate, the
    staging-into-pre-staging merge, Promote's `--no-ff`, and the rename
    transition.

**This is high-risk work** under [go-merge](../practices/go-merge.md): it
changes gating code and a governance rule. Each step goes through a pull
request. It also changes content other repositories vendor, so it reaches
them only through Update Vendors
([vendor-rollout-disclosed](../practices/vendor-rollout-disclosed.md)).

## Settled at approval

1. **Where `Go update` lands** is pre-staging by default; the per-person
   `landing_branch` can send one person's to staging instead.
2. **The command word is `Promote`.**
3. **Alex hears about the rename before step 10 runs.** It renames the branch
   his own merge-target rule is named after and changes where he pushes. It
   is not a main merge, so the rule does not require his go-ahead; he should
   still hear about it before it happens rather than after. He also hears
   before step 6, which changes where his sessions land their work.

## What this gives up

- **A failed promotion does not say which window broke it.** The batch is
  checked together. Promoting often keeps batches small; the failure names
  the commits since the last green promotion.
- **A break on pre-staging spreads** until someone promotes and sees it --
  the other windows build on it in the meantime. Cheap for content; worse for
  code. A person working on tools or hooks can set `branch_push_checks` to
  `"full"`.
- **"Is my edit live?" gets a second answer**: on pre-staging, waiting for
  Promote.

## Acronyms

- **CI** -- continuous integration: here, GitHub Actions running checks on
  GitHub's machines.
