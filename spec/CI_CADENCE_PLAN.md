---
title:         Run CI at most once every X hours in private repos
kind:          proposal
status:        drafted
opened:        2026-09-24
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Let Morgan push as often as he likes to a private repo while GitHub Actions runs at most once every X hours, X set once in precedent-individual. The decision is made on the commit, before GitHub starts a runner, so it costs nothing -- unlike the 2026-09-16 debounce, which paid a minute to decide not to spend one."
---

# Run CI at most once every X hours in private repos

**The ask.** Morgan pushes many times a day. In a private repo every push
starts GitHub Actions, and every job is billed at least a minute. He wants
one number, set once in his individual source: **run CI at most once every X
hours.** `0` means every push, as today; `48` means once every two days.
Public repos are untouched.

**Status.** Morgan, 2026-09-24, after the brainstorm this came from: *"I
don't want to save it, I want to do it"* (`strength: decided`, to build
it). **The design below is a proposal awaiting his review**, not something
he has approved line by line.

## Why the obvious version loses money

The obvious build is a CI job that asks "did CI run in the last X hours?"
and skips the rest if so. **That was built on 2026-09-16 as
`ci_debounce_minutes` and retired on 2026-09-20**, because the job asking the
question is billed a minute like any other. Deciding not to spend a minute
cost a minute, and there was no window setting where it came out ahead.
[BILLING_FLOOR.md](BILLING_FLOOR.md) has the arithmetic.

**The decision has to happen before GitHub starts anything.** Two places
qualify: the workflow's trigger, which can't express "within the last X
hours", and **the commit message**. GitHub does not start push or
pull-request workflows when the pushed head commit says `[skip ci]` (GitHub
behavior as of 2026-09; check its docs before building). No runner starts,
so nothing is billed.

## How it works

**The hook already exists.** Every session installs a global
`prepare-commit-msg` hook (git's `core.hooksPath`, under
`~/.config/precedent/git-hooks/`). It is written by
[commit-identity.sh](../templates/harness/claude-code/hooks/commit-identity.sh),
which precedent-individual carries as an engine path and runs at session
start. It already fires in every repository in the container, including ones
attached mid-session, and already has Morgan's declared values baked in (his
timezone). **This plan adds one step to that hook**; no new delivery channel
is needed.

The step decides whether to add a `[skip ci]` line to the commit message.
**It adds the line only when every one of these holds**; anything else
leaves the message alone and CI runs as normal:

| # | Check | Why |
|---|---|---|
| 1 | **X is above 0.** The repo's own `precedent.json` `ci_every_hours` wins; otherwise the value in precedent-individual's `identity.json`; otherwise 0. | A repo can opt out for itself (see "Repos others read from" below). |
| 2 | **The repo is declared private**: its `precedent.json` says `"visibility": "private"`. | An undeclared repo counts as public, the same default [precedent.json](../precedent.json) uses. Public repos run CI free on standard runners, and a leak there can't wait. |
| 3 | **The commit is on the repo's primary branch** (`base_branch` in its `precedent.json`). | Feature branches become pull requests. Never skipping them means a PR always gets its check (see "Required status checks" below). |
| 4 | **CI isn't due yet**: the newest commit on `origin/<primary>` without `[skip ci]` is less than X hours old. | That commit is the last push that ran CI. |
| 5 | **No override for this commit**: `PRECEDENT_CI_NOW=1` is not set. | A way to force a run when a change is risky. |

**Check 4 measures `origin`, never local commits.** Suppose CI is due, and
commit A goes in without the tag. Then commit B is made before pushing. If B
measured against local history, it would see A (untagged, a minute old),
tag itself, and the push of A+B would skip CI. GitHub reads only the head
commit, B. Measured against `origin`, B sees what A saw, stays untagged, and
the push runs CI.

**Every failure leans toward running CI.** Commits get tagged only when the
answer is a definite "not due". Missing python3, an unreadable
`precedent.json`, no `origin/<primary>` ref, or `core.hooksPath` already
claimed by something else all leave the message untouched. So does a commit
made anywhere the hook isn't installed: another laptop, GitHub's web editor,
a merge button.

## The setting

**In precedent-individual's `identity.json`**, beside the timezone the same
hook already reads:

    "ci_every_hours": 48

(Example value only, not for pasting. Morgan picks it; see the questions
below.)

**Repos others read from set their own `0`.** precedent-individual and the
three shared practice sets are private, so the personal value would reach
them. But every session in every repo pulls their newest commit at session
start, so a broken commit there spreads before CI would ever see it. Each
declares `"ci_every_hours": 0` in its own `precedent.json`, and check 1 lets
that win.

**Nothing tracks per-repo state.** "When did CI last run" comes from each
repo's own history (check 4), so precedent-individual needs no log of other
repos. That matters, because writing to it on every push would break:
parallel sessions in different repos would collide on one file, the
session-start refresh resets the local clone and discards anything
unpushed, and a session rooted in another repo only reaches
precedent-individual with write access granted explicitly.

## What this gives up

- **Your local check becomes the gate, with CI as the backstop.** This
  repo's rules already require the local deep check before a push, so this
  states the arrangement rather than creating it.
- **Nothing goes unchecked forever, but checks can come late.** After a
  quiet stretch, the next push is always more than X hours past the last
  run, so it runs CI over the whole tree. The cost is that a late failure
  covers a bigger batch of commits.
- **The decision is made at commit time, not push time.** A commit made at
  hour 47 and pushed at hour 50 is skipped although CI was due by then. The
  next push catches it.
- **An untagged commit on `origin` that wasn't the head of its push looks
  like a CI run.** That only happens for commits made outside the hook, and
  it costs at most one window.

## Required status checks

A repository can be set so nothing reaches a branch until a named CI job has
passed: Settings, then Branches (branch protection) or Rules (rulesets). On
private repos this needs a paid GitHub plan (as of 2026-09). **A skipped
workflow never reports**, so GitHub waits for a result that never arrives:
the pull request sits at *"Expected — waiting for status to be reported"*
and can't be merged, and a direct push to that branch is refused.

Check 3 covers pull requests, since feature branches are never tagged. A
primary branch with required checks refuses a direct push of a commit that
hasn't passed them, unless an admin bypasses the rule, so direct pushes and
required checks rarely meet. **Still, look before switching a repo on**: if any
private repo lists required status checks, leave it at X=0 until someone
has read how that repo is used.

## Build steps

1. **Engine, in this repo.** Add the step to the `prepare-commit-msg` body
   that [commit-identity.sh](../templates/harness/claude-code/hooks/commit-identity.sh)
   writes: X baked in at session start like the timezone offset, with
   visibility, `base_branch` and the repo override read at commit time.
   Harness cases in [tools/verify_harness.py](../tools/verify_harness.py),
   each with a negative control: public repo, X=0, repo override 0, feature
   branch, CI due, CI not due, the A+B case above, missing python3, and
   `PRECEDENT_CI_NOW=1`.
2. **Make the setting visible.** One row in
   [tools/precedent_session_check.py](../tools/precedent_session_check.py)
   saying what this repo resolved: *"CI cadence: private, primary `main`,
   at most every 48h"*, or *"every push"* and which check decided it.
   `ci_debounce_minutes` taught this: a setting that looks live and does
   nothing is worse than no setting.
3. **precedent-individual.** Add `ci_every_hours` to `identity.json`, take
   the engine refresh (its `engine_paths` already carries
   `commit-identity.sh`), and add `"ci_every_hours": 0` to its own
   `precedent.json`.
4. **The three shared sets.** `"ci_every_hours": 0` in each
   `precedent.json`.
5. **Look at each private repo's required status checks** before it runs
   with X above 0.
6. **Measure on one repo for a week**, minutes before and after, from
   Settings, then Billing. That also answers
   [todo-2026-09-21-measure-the-billing-floor-fix-on-one-repo](../todo/todo-2026-09-21-measure-the-billing-floor-fix-on-one-repo.md)'s
   question of what one repo spends.

**How it reaches other repos:** `commit-identity.sh` is content this repo
ships. It reaches precedent-individual through that repo's `engine_paths`
at its next engine refresh, and every session that resolves
precedent-individual then installs the updated global hook at session start.
Consumer repos need no change of their own. The only per-repo edits are the
`0` overrides in steps 3 and 4.

## Questions for Morgan

1. **What X?** 24 or 48 both came up. The example above uses 48.
2. **Should a vendor update always run CI?** Recommended: yes. An
   `Update Vendors` run is the largest change a consumer gets, so the
   [vendor-update-runbook](../practices/vendor-update-runbook.md) would set
   `PRECEDENT_CI_NOW=1` for its commits.
3. **Weekly backstop run: dropped.** The brainstorm floated a scheduled
   weekly run to catch the tail end. Morgan argued it isn't needed, since
   the next push after a quiet stretch always runs CI and the local check
   covers the gap. The repos where a stale unchecked commit would matter are
   the ones others read from, and they get X=0 instead.
