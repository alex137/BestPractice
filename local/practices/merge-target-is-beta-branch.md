---
slug:        merge-target-is-beta-branch
title:       Pull requests target staging, never main; no merge needs Alex's sign-off
tier:        on-demand
severity:    blocking
applies_to:  ["**"]
occasion:    "opening or merging a pull request in this repository"
index_required: true
gates:       ["merge"]
index_clause: "PRs target staging, never main; main only when named"
checked_by:  "tools/checks/check_merge_target_is_beta_branch.py"
defines:     []
expires:     "when Morgan or Alex says work moves to main -- NOT when the branch is merged into main, which happened on 2026-09-14 (PR #367) and recurs on Morgan's regular merges"
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "Alex, 2026-09-03 (original rule); approval scope narrowed by Morgan, 2026-09-04; Alex's approval for main removed, Alex relayed by Morgan, 2026-09-26"
---
## Rule
**The branch was renamed from `precedent-beta-v01` to `staging` on 2026-09-25** ([spec/BRANCH_TIERS_PLAN.md](../../spec/BRANCH_TIERS_PLAN.md); Morgan, with Alex approving, relayed by Morgan). The old name is kept on origin and moved in step by every Promote while installs still pinned to it catch up; everything below means `staging`.

Every pull request (PR) opened in this repository targets
`staging`, never `main`. Alex merged `staging` into
`main` on 2026-09-14 ([PR #367](https://github.com/alex137/BestPractice/pull/367))
and Morgan merges it into `main` regularly from then on — **that does not
end this rule**: work keeps landing on `staging`, and `main`
receives it through those merges, never through a PR opened against it
(Morgan, 2026-09-14: *"work should still land to the precedent-beta-v01
branch; but I will regularly merge the precedent branch with main"* —
`strength: decided`). Before opening or merging a PR, confirm
the base branch is `staging` — do not assume `main` is the
default just because it is the repository's configured default branch.

**For a person whose landing branch is pre-staging, a PR targets
`pre-staging` instead**, and reaches `staging` by a Promote
([spec/BRANCH_TIERS_PLAN.md](../../spec/BRANCH_TIERS_PLAN.md)): Morgan, 2026-09-25: *"the \"high risk\" ones should still go to pre-staging but have a strong, bolded message for me, in the main text as a paragraph and also in The Boildown, that now I need to push pre-staging to staging"* (strength: decided).
Never `main`, either way.

**No merge needs Alex's sign-off, `main` included** (Morgan, 2026-09-26:
*"Alex said we no longer need his authorization to post to main so please
remove that"*, strength: decided; Alex's word relayed by Morgan). Once the
PR's own deep check (`two-check-levels`) passes, a session may merge a PR
into `staging` directly. A merge into `main` still needs the person running
the session to name `main` in that specific request, or a Promote that
chooses staging into main ([promote](../../practices/promote.md); Morgan,
2026-09-26, strength: decided); a general "PR and merge it" authorization,
with no branch named, defaults to `staging`.

**`staging` is staging and `main` is live.** A session working
here uses `staging` for everything unless the person running it
says otherwise, and `main` receives only what has been folded in from it.
**This rule is this repository's alone and is never vendored**: a repository
that takes updates from here works on its own primary branch, usually
`main` ([primary-branch](../../practices/primary-branch.md)). Morgan,
2026-09-24 (`strength: decided`): *"A session should default to using
precedent-beta-v01 for everything within that session; only the live
version with changes will be pushed to main at a later date, think of it
like a staging server; unless the manager of the session says otherwise;
but note that this rule doesn't get vendored in anywhere, the primary
branch of the vendored-in repo should be used, often main."* **Other repos
take their updates from `staging` too, for now**, all of them on
the same branch (Morgan, 2026-09-24, `strength: decided`: *"they should all
be consistent and following the same one. Maybe later we'll move them all
to follow main but, for now, they should all follow precedent-beta-v01"*).
That is `SOURCE_BRANCH` in `tools/precedent_vendor_engine.py` and
`tools/precedent_refresh_sources.py`. Earlier the same day it briefly read
`main`, on *"Yes, switch other repos to update from main"*, which Morgan
later recorded as `strength: assented`: *"That was more an assent, than a
decision. I didn't think about it."*

## Detail
This holds even when `main` and `staging` happen to be at the
same commit, which is exactly the condition under which the incident this
practice exists to prevent occurred — the two branches looked
interchangeable at that moment, and they were not.

## Why
`main` is this repository's public, shared default branch, and a change
landing there by accident, from a PR that merely had the wrong base, is
exactly the incident the Story below describes. `precedent-beta-v01` is the working
branch for the Precedent restructuring (`PRACTICE_ENGINE_PLAN.md`:
"Precedent is a branch of BestPractice, not a fork" — merging back to
`main` is `CHANGES_TO_TELL_ALEX.md`'s explicit, deferred phase-7 step, not
something any single PR does incidentally), so the day-to-day PRs building
toward it don't need to wait on Alex one at a time: this repo's own deep
check (`two-check-levels`) is what gates a push to `precedent-beta-v01`,
not a human. A branch based off `precedent-beta-v01`'s tip, opened with
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

## Install
`tools/precedent_check.py`'s `merge-target-is-beta-branch` check compares
`origin/main` against `origin/precedent-beta-v01`: if `precedent-beta-v01`
is an ancestor of `main` — meaning its work has landed there via a merge —
the check fails, unless this practice has already been retired (see
below). It reports `NotApplicable` when either ref is not fetched locally,
since it cannot compare branches it cannot see; run
`git fetch origin main precedent-beta-v01` first if it skips. It cannot
catch a PR opened with the wrong base *before* that PR is merged — only
that a merge already happened. `gates: ["merge"]` surfaces this practice's
Rule via `python3 tools/precedent_gate.py merge`, which is the check-before
step.

**A second, load-bearing gap, disclosed rather than assumed away**:
because this is a repo-local practice (declared in `precedent.json`,
`path: "local"`, per `PRACTICE_ENGINE_PLAN.md`'s "Source" section) and this
repository's own generated `AGENTS.md` loader block stays deliberately
single-source (`precedent.json`'s own `_comment`: "this repo's own
session-loading is the universal catalogue alone"), this Rule does **not**
reach a session through the normal resident/occasion-index channel the way
a universal practice would. `AGENTS.md`'s hand-authored "Working in this
repo" section carries the same rule directly, in prose, for exactly that
reason — belt and suspenders, not redundancy.

**Retirement.** When Morgan or Alex says work moves to `main` — a
decision, not an event: the merge into `main` already happened on
2026-09-14 and is repeated regularly, and this rule outlived it on purpose
— delete this file, delete
`local/tools/checks/check_merge_target_is_beta_branch.py`, remove the
pointer from `AGENTS.md`, flip `base_branch` in `precedent.json` and
rewrite the catalogue's absolute links, in that same PR, not left as later
cleanup.
