---
slug:        merge-target-is-beta-branch
title:       Pull requests target the landing branch, never main; main moves only by a Promote
tier:        on-demand
severity:    blocking
applies_to:  ["**"]
occasion:    "opening or merging a pull request in this repository"
index_required: true
gates:       ["merge"]
index_clause: "PRs target pre-staging or staging; main moves only by a Promote or when the person names main"
checked_by:  null
defines:     []
expires:     null
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "Alex, 2026-09-03 (original rule); approval scope narrowed by Morgan, 2026-09-04; Alex's approval for main removed, Alex relayed by Morgan, 2026-09-26"
---
## Rule
**Every pull request (PR) in this repository targets the person's landing
branch, never `main`**: `pre-staging` for a person whose landing branch is
`pre-staging`, `staging` otherwise
(`python3 tools/precedent_branches.py --landing` says which). Work moves on
from there only by a Promote: `pre-staging` into `staging`, then `staging`
into `main` ([promote](../../practices/promote.md);
[spec/BRANCH_TIERS_PLAN.md](../../spec/BRANCH_TIERS_PLAN.md)). **Check the
base branch explicitly before opening or merging** — never assume `main`
because it is the repository's configured default branch.

**Merging into `main` needs the person running the session to name `main`
in that specific request, or a Promote that chooses `staging` into `main`**
(Morgan, 2026-09-26, strength: decided). A general "PR and merge it", with
no branch named, means the landing branch. **No merge needs Alex's
sign-off, `main` included** (Morgan, 2026-09-26: *"Alex said we no longer
need his authorization to post to main so please remove that"*, strength:
decided; Alex's word relayed by Morgan). Once a PR's own deep check
(`two-check-levels`) passes, a session may merge it into the landing branch.

**This rule is this repository's alone and is never vendored**: a
repository that takes updates from here works on its own primary branch,
usually `main` ([primary-branch](../../practices/primary-branch.md)).
Consuming repositories vendor from `main` (`SOURCE_BRANCH` in
`tools/precedent_vendor_engine.py`, since 2026-09-25).

## Detail
This holds even when `main` and `staging` happen to be at the
same commit, which is exactly the condition under which the incident this
practice exists to prevent occurred — the two branches looked
interchangeable at that moment, and they were not.

## Why
`main` is this repository's public, shared default branch, and a change
landing there by accident, from a PR that merely had the wrong base, is
exactly the incident the Story below describes. `staging` (named
`precedent-beta-v01` until 2026-09-25) is where fully checked work collects
before a Promote moves it into `main`, and `pre-staging` sits below it for
anyone who lands there, so day-to-day PRs don't wait on a person one at a
time: this repo's own deep check (`two-check-levels`) is what gates a push
to the landing branch, not a human. A branch based off the landing branch's
tip, opened with
`base: main`, merges cleanly with no conflict and no warning — git has no
concept of "the wrong branch," only of mergeable or not — so nothing in
the mechanics of opening or merging the PR signals the mistake. The only
thing that catches it is checking the base explicitly, every time, before
acting.

## Story
2026-09-03: a session built two new practices on a branch created from
`precedent-beta-v01`'s tip, then opened and merged the PR with `base: main`
— main and precedent-beta-v01 happened to be at the identical commit at
that moment, so the merge produced no conflict and reported success
cleanly. Because the working branch's own history included all of
`precedent-beta-v01`'s unmerged restructuring work (phases 1 through 6,
roughly 600 files), the merge silently carried that entire body of work
onto `main` — work `CHANGES_TO_TELL_ALEX.md` already named as deliberately
staying off `main` until a real phase-7 review. Caught only because Alex
happened to ask "did that merge to main?" afterward. Fixed with a
`git revert -m 1` PR against `main` (verified byte-identical to `main`'s
real pre-incident tree) and a second PR re-targeting `precedent-beta-v01`
correctly. This practice is the fix that stops a session from needing to
be asked.

**Update, 2026-09-04 — approval scope narrowed, at Morgan's direction.**
The rule above had left "reviewed by Alex, not self-merged" as this
repo's assumed default for every PR, `precedent-beta-v01` included — PR
#93 was opened correctly against `precedent-beta-v01` and still held for
Alex, on that assumption, before this update. Restated explicitly: Alex's
approval gate is for `main`, and only for merges carrying major changes;
`precedent-beta-v01` merges need no sign-off from him at all, and a
session may merge its own PR there once the deep check passes. This
narrowing is Morgan's call, not Alex's — the original targeting rule above
carries his 2026-09-03 approval, this narrowing does not yet.

**Update, 2026-09-26 — Alex's approval for `main` removed.** Morgan:
*"Alex said we no longer need his authorization to post to main so please
remove that"* (strength: decided). The targeting rule stays: PRs still go to
`staging` (or `pre-staging`), and `main` still takes work only by a
deliberate, named merge. What went is the named go-ahead from Alex that a
major change reaching `main` used to need.

**Update, 2026-09-27 — the check retired, the rule rewritten for three
tiers.** After a named Promote of `staging` into `main`, the full check
reported this practice's violation, as it would after every Promote into
`main` from then on. Morgan: *"the merge target is no longer beta branch ---
shouldn't this be deprecated with our new system of pre-staging then staging
then main?"*, then *"please fix or remove etc and go update that"*
(strength: decided). The targeting rule is still right and stays; the
branch-graph check that assumed `main` never contains `staging` is gone, and
the Rule now names the landing branch and the Promote instead of one beta
branch. Its old Rule text, and the `precedent-beta-v01` history, are in this
file's git history.

## Install
**No mechanical check, since 2026-09-27.** The rule is carried by the tools
that pick a branch: [promote](../../practices/promote.md) and
[go-update](../../practices/go-update.md) land work on the branch
`python3 tools/precedent_branches.py --landing` names, and only a Promote
moves `staging` into `main`. `gates: ["merge"]` surfaces this Rule through
`python3 tools/precedent_gate.py merge`, which is the check-before step.

**The check this practice used to carry was retired, not lost.** Its
branch-graph check failed whenever
`main` contained all of `staging`. Before the branch tiers that meant a PR
had merged into `main` by mistake. Under the pre-staging, staging, main
pipeline it is what every Promote into `main` does on purpose, so the check
fired after each one until the next commit reached `staging`, and blocked the
deep check for a state nobody had got wrong. Its record is in
`process/decommissioned_paths.json`.

It is in AGENTS.md's occasion index (`index_required: true`), and
[AGENTS.md](../../AGENTS.md)'s opening paragraph carries the rule in prose so
it is read before any PR.
