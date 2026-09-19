---
title:         A self-hosted runner for this repo's own deep-check
kind:          proposal
status:        drafted
opened:        2026-09-18
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Whether moving deep-check.yml (verify_harness.py) onto a self-hosted runner would close the local-vs-CI speed gap, scoped narrowly to this repo's own workflow rather than repeating spec/CI_MINUTES_PLAN.md's item 6 -- research only, per Morgan's own instruction, nothing here changes a workflow."
---
# A self-hosted runner for this repo's own deep-check

**This is a different question from [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md)'s
item 6**, not a restatement of it. That plan's self-hosted-runner pilot is
about moving Morgan's other, PRIVATE, metered repos off billed
GitHub-hosted minutes. This document is about whether BestPractice's own
[deep-check.yml](../.github/workflows/deep-check.yml) — public, unmetered, and already flagged in that same plan
as a separate category — should move to a self-hosted runner for **speed**,
which is a distinct motivation with a different cost/risk shape. Item 6
itself is still open, held for
[todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md](../todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md)
(due 2026-09-19).

## Why this repo's own workflows are already on record as a separate case

[spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md) item 2b pushed back on folding
[docs.yml](../.github/workflows/docs.yml), [deep-check.yml](../.github/workflows/deep-check.yml), and [leak-gate.yml](../.github/workflows/leak-gate.yml) into that plan's general
sweep, for two reasons that both still hold here:

- **This repo is public, so these three workflows already run free** on
  GitHub-hosted standard runners, at any volume. The money motivation
  behind item 6 does not exist for this specific workflow — the only thing
  a self-hosted runner could buy here is wall-clock speed.
- Item 2b already asked for **Morgan's explicit sign-off before touching
  this repo's own workflows either way**, given the security rationale
  on record. That bar applies here too.

## The mechanics, briefly

A GitHub-hosted runner is a fresh virtual machine (VM) GitHub spins up per
job. A self-hosted
runner is a long-lived process installed on a machine already under your
control; it polls GitHub outbound (no inbound ports to open), and the
workflow change is small — `runs-on: [self-hosted, <label>]` in place of
`runs-on: ubuntu-latest`. What changes is the hardware doing the work: if
that machine is faster than GitHub's shared runner for this workload, wall
time drops.

**What "faster" is worth here, from what's already measured**: per
[spec/VERIFY_HARNESS_PERFORMANCE.md](VERIFY_HARNESS_PERFORMANCE.md), a full
[tools/verify_harness.py](../tools/verify_harness.py) run measured **250.7s**, then **192.9s** after the
2026-09-16 change-scoping fix — both figures from a session's own container,
not GitHub's runner. This conversation's starting point (another session's
report: ~7-9 minutes locally, ~22 minutes on GitHub's shared runner) turned
out to include a real bug, not just more checks landing: an unbounded
recursion in [`precedent_resolve.py`](../tools/precedent_resolve.py)'s self-heal path was intermittently
spawning thousands of processes and either crashing the run outright or
burning most of its wall-clock, depending on timing (fixed 2026-09-18, see
[the gotcha's Resolution section](../gotchas/gotcha-2026-09-18-verify-harnesss-stress-checks-can-oom-kill-the-bash-tools.md)).
**With that fixed, a full local run measures 149.9s**, with one check
(`check_precedent_check_fires`, 71.6s) accounting for the only cost left
worth splitting out — already done, in `deep-check.yml`'s new parallel-job
structure. Whether GitHub's own runner still shows anything like the
original ~22 minutes after both fixes land is not yet measured; if it
doesn't, most of the case for self-hosting this workflow evaporates along
with the number that motivated it. See
"What I'd actually recommend" below.

## Security: a harder case than item 6's, not the same one

Item 6's own text says the fork/`pull_request` risk it names is "not a live
risk" for Morgan's *private, single-author* repos. BestPractice is neither:

- **It's public.** [deep-check.yml](../.github/workflows/deep-check.yml)'s own header already flags the
  reversible assumption this all rests on: *"PUT `pull_request:` BACK IF A
  PR EVER ARRIVES FROM A FORK."* Today the trigger is deliberately
  `push:`-only, and every PR to date has come from a branch inside this
  repo (checked 2026-09-07, #83–#123) — so a fork's workflow YAML has never
  actually run here. That is a standing assumption the file's own comment
  says could flip. On a GitHub-hosted runner, flipping it back just doubles
  a check run (the [leak-gate.yml](../.github/workflows/leak-gate.yml) history that motivated the current
  push-only design). **On a self-hosted runner, flipping it back means a
  fork's arbitrary workflow code executes with whatever access that
  machine has** — a materially worse failure mode than the one the existing
  comment was written against.
- **Even push-only, this repo's real risk shifts to "who can push."**
  Anyone with push access to any branch here (the actual contribution path,
  per [AGENTS.md](../AGENTS.md)) can put arbitrary code in a workflow file, and on a
  self-hosted runner it runs on real hardware, not a disposable VM. Worth
  confirming who currently holds push access before treating this as
  low-risk — this document doesn't have that answer.
- This is exactly the combination (public repo + self-hosted runner)
  GitHub's own hardening guidance singles out as needing short-lived,
  narrowly-scoped runners rather than a long-lived box, precisely because a
  compromised or malicious job can otherwise persist on the host and reach
  whatever secrets are in scope from there.

## Hosting options, for thinking through if a pilot is ever approved

1. **Home or personal hardware.** Cheapest, and the worst fit here: uptime
   depends on your own power and internet, and it's the least isolated from
   anything else that machine or network touches.
2. **A small dedicated cloud VM.** Predictable uptime, isolated from your
   daily-driver devices, a modest recurring cost — the simplest way to get
   a box that is *only* the runner and nothing else.
3. **An ephemeral, container-based runner** (spun up fresh per job, torn
   down after). Best security posture — a compromised job can't persist
   into the next run or leave anything behind on a live host — and the
   most setup effort. This is the shape GitHub's own guidance points to for
   a public repo specifically.

If this is ever piloted: (2) or (3), never (1) for a repo that's public,
and never combined with restoring a `pull_request:` trigger without
re-deriving this analysis first — that combination is the one GitHub
explicitly warns against.

## What I'd actually recommend

The case for self-hosting [deep-check.yml](../.github/workflows/deep-check.yml) is weaker than item 6's case for
Morgan's other repos: no money is on the table (already free), and the
security posture here is worse (public repo, the fork-trigger caveat
already on record). I'd treat this as a harder, separate call from item 6 —
not something that rides along once that pilot is approved.

**Sequencing:** let idea #1 (matrix-splitting the heavy checks across
parallel GitHub-hosted jobs) land and get measured first. If the remaining
wall-clock is still the problem after that, an ephemeral or dedicated-VM
runner (option 2 or 3), registered at the repo level rather than org level
to limit blast radius, and scoped to [deep-check.yml](../.github/workflows/deep-check.yml) alone, is the shape
worth piloting — with the explicit sign-off item 2b already asked for.

## Status

Research only, per instruction — nothing here changes a workflow. Item 6
(the self-hosted pilot for Morgan's other repos) and item 7 (checking the
real billing ceiling) remain open, tracked in
[todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md](../todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md).
