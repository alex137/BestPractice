---
title:         Run CI at most once every X hours in private repos
kind:          proposal
status:        accepted
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
don't want to save it, I want to do it"*, then, on reading this plan: *"The
plan is great, with one detail change: the default setting for this should
be 0 -- in other words, unless explicitly changed, the github ci/cd should
run every time. Go update."* (`strength: decided`, both.) **Built** in
BestPractice the same day; "Build steps" below says what is live and what
waits on other repos.

**Working branches have their own switch**, `ci_on_branches`, added later
the same day -- see "The branch switch" below.

**The default is 0.** Nobody's CI changes until they write a number above 0
into their own `identity.json` or a repo's `precedent.json`. An absent,
unreadable or invalid value is 0 too.

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
| 3 | **The commit is on the repo's primary branch** (`base_branch` in its `precedent.json`). | Any other branch is decided by `ci_on_branches` instead (see "The branch switch" below). |
| 4 | **CI isn't due yet**: the newest commit on `origin/<primary>` without `[skip ci]` is less than X hours old. | That commit is the last push that ran CI. |
| 5 | **No override for this commit**: `PRECEDENT_CI_NOW=1` is not set. | A way to force a run when a change is risky. |

**Check 4 measures `origin`, never local commits.** Suppose CI is due, and
commit A goes in without the tag. Then commit B is made before pushing. If B
measured against local history, it would see A (untagged, a minute old),
tag itself, and the push of A+B would skip CI. GitHub reads only the head
commit, B. Measured against `origin`, B sees what A saw, stays untagged, and
the push runs CI.

**Every failure leans toward running CI.** The step also sits above the
hook's author override, `PRECEDENT_ALLOW_ANY_AUTHOR=1`, which waives the
identity checks and nothing else -- the first build placed it below, and
the test harness, which sets that override for its whole run, caught every
cadence silently switched off. Commits get tagged only when the
answer is a definite "not due". Missing python3, an unreadable
`precedent.json`, no `origin/<primary>` ref, or `core.hooksPath` already
claimed by something else all leave the message untouched. So does a commit
made anywhere the hook isn't installed: another laptop, GitHub's web editor,
a merge button.

## The setting

**In precedent-individual's `identity.json`**, beside the timezone the same
hook already reads:

    "ci_every_hours": 48

(Example value only, not for pasting. The individual skeleton,
[identity.json.template](../templates/practice-set-individual/identity.json.template),
ships the key at `0`.)

**Repos others read from set their own `0`.** precedent-individual and the
three shared practice sets are private, so a personal value above 0 would
reach them. But every session in every repo pulls their newest commit at session
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

## The branch switch

**The first build left every working branch alone**, so a pull request
always got its check. Morgan, 2026-09-24, on learning that: *"that defeats
the purpose of saving minutes since we do tons of commits to clone local
branches ... I do NOT want the github ci/cd active in the clones and other
branch files"*, asked as a flag each person can change, with the day's bill
at 95 of 100 minutes. (`strength: decided`.)

**`ci_on_branches` in `identity.json`, default `true`.** Set to `false`, the
same hook tags **every** commit on any branch but a private repo's primary
one. It measures nothing: no window, no `origin` lookup, so the first commit
on a fresh branch is tagged too. Checks 2 and 5 above still apply, so a
public or undeclared repo and a `PRECEDENT_CI_NOW=1` commit run CI as normal.

**Which value wins, in order:** the repo's own `precedent.json`
`ci_on_branches`; then, if that repo sets `ci_every_hours` to 0, `true`,
because that 0 says every push there must be checked; then the person's
value; then `true`. Only the literal boolean `false` switches it off.

**What `false` costs:** GitHub skips pull-request workflows as well when the
head commit says `[skip ci]`, so **a pull request from a tagged branch gets
no CI run**. Where a repo requires a status check before merging, the pull
request stays blocked until a commit on it is made with `PRECEDENT_CI_NOW=1`.
A merge made with GitHub's button is a commit the hook never sees, so the
primary branch runs CI on it by its own rule -- except a squash merge, whose
message carries the branch's `[skip ci]` lines along with the rest.

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

Check 3 covers pull requests while `ci_on_branches` stays `true`; set to
`false`, it doesn't, as "The branch switch" says. A
primary branch with required checks refuses a direct push of a commit that
hasn't passed them, unless an admin bypasses the rule, so direct pushes and
required checks rarely meet. **Still, look before switching a repo on**: if any
private repo lists required status checks, leave it at X=0 until someone
has read how that repo is used.

## Build steps

**Live in BestPractice (2026-09-24):**

1. **The hook.** [commit-identity.sh](../templates/harness/claude-code/hooks/commit-identity.sh)
   resolves the personal value at session start and writes a
   `precedent-ci-cadence` script beside the commit hooks it already
   installs, per checkout and globally. The `prepare-commit-msg` body calls
   it. Thirteen cases in [tools/verify_harness.py](../tools/verify_harness.py)
   (`check_commit_identity_ci_cadence`), each skip paired with its no-skip
   case: the default, both override directions, public repo, feature
   branch, CI due, the A+B case above, an invalid value, no origin ref, and
   `PRECEDENT_CI_NOW=1`.
2. **The setting is visible.** [tools/precedent_session_check.py](../tools/precedent_session_check.py)
   has a row naming the cadence this repo resolves, where the value came
   from and why it does or does not apply, and fails only when a number
   above 0 (or `ci_on_branches: false`) is set and no cadence script is
   installed.
   `ci_debounce_minutes` taught this: a setting that looks live and does
   nothing is worse than no setting.
3. **The skeleton.** [identity.json.template](../templates/practice-set-individual/identity.json.template)
   carries `"ci_every_hours": 0` with a comment saying what a number does.

**Also live, later the same day: the branch switch.** The same hook and
script resolve `ci_on_branches`, the session-check row names it, the
skeleton ships it `true`, and [verify_harness.py](../tools/verify_harness.py) has eleven more cases,
24 in all.

**Waiting on other repos:**

4. **precedent-individual takes the engine refresh** (its `engine_paths`
   carries `commit-identity.sh`). Refreshes read BestPractice's `main`, so
   this waits for the next merge of `precedent-beta-v01` into `main`.
5. **precedent-individual and the three shared sets declare
   `"ci_every_hours": 0`** in their own `precedent.json`, so a personal
   value above 0 never reaches the repos everyone reads from. **Done
   2026-09-24**, all four on `main`; that 0 also keeps their working
   branches on CI whatever a person's `ci_on_branches` says.

**Before anyone sets a number above 0:**

6. **Look at each private repo's required status checks.**
7. **Measure on one repo for a week**, minutes before and after, from
   Settings, then Billing. That also answers
   [todo-2026-09-21-measure-the-billing-floor-fix-on-one-repo](../todo/todo-2026-09-21-measure-the-billing-floor-fix-on-one-repo.md)'s
   question of what one repo spends.

**How it reaches other repos:** `commit-identity.sh` is content this repo
ships. It reaches precedent-individual through that repo's `engine_paths`
at its next engine refresh, and every session that resolves
precedent-individual then installs the updated hook at session start.
Consumer repos need no change of their own. Until then they run the older
hook, which has no cadence step, so they behave exactly as the default does.

## Questions for Morgan

1. **What X? Settled: 0 by default** (Morgan, 2026-09-24, above). A
   number goes in only when someone chooses one.
2. **Should a vendor update always run CI? Open**, and moot until a number
   above 0 is set anywhere. Recommended: yes. An
   `Update Vendors` run is the largest change a consumer gets, so the
   [vendor-update-runbook](../practices/vendor-update-runbook.md) would set
   `PRECEDENT_CI_NOW=1` for its commits.
3. **Weekly backstop run: dropped**, with the rest of the plan (Morgan,
   2026-09-24: "The plan is great"). The brainstorm floated a scheduled
   weekly run to catch the tail end. Morgan argued it isn't needed, since
   the next push after a quiet stretch always runs CI and the local check
   covers the gap. The repos where a stale unchecked commit would matter are
   the ones others read from, and they get X=0 instead.
