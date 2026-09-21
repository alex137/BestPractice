---
title:         The per-job billing floor
kind:          record
status:        live
opened:        2026-09-21
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "GitHub Actions bills per JOB, rounded up to a whole minute. Measured 2026-09-21: 0.47 seconds of real work billed as three minutes. Every lever tried between 2026-09-15 and 2026-09-20 reduced how OFTEN that was paid and none reduced what one payment cost — including a debounce job that was arithmetically worse than no debounce at every setting. This is the finding, the numbers, what was tried and why each attempt missed."
---

# The per-job billing floor

**GitHub Actions bills per JOB, rounded up to the whole minute.** Not per
workflow, not per second of compute. A job that finishes in eight seconds
costs a minute. Three jobs that each finish in eight seconds cost three
minutes.

This document exists because that sentence was not written down anywhere in
this repository until 2026-09-21, and five days of cost work was spent
without it. **Everything here is measured**; where a number is an estimate
the text says so.

## The measurement that settles it

Timed 2026-09-21 in a clone of a real installed practice set, running the
checks its CI workflow exists to run:

| What the runner is there to do | Time |
|---|---:|
| [tools/precedent_check.py](../tools/precedent_check.py) | **0.35s** |
| [tools/build_views.py](../tools/build_views.py) `--check` | **0.12s** |
| **Total useful work** | **0.47 seconds** |
| **What it was billed** | **3 minutes** |

Three minutes, because the work sat in three jobs — a `debounce` job, a
`precedent-check` job and a `views-drift` job. Three runners, three
checkouts, three Python setups, to carry under half a second.

**The ratio is roughly 380 to 1.** The overhead is not a tax on the cost. It
very nearly *is* the cost.

A consuming repo reached the same conclusion independently the same day: its
light check is a **13-second job** at the same one-minute floor, running on
about **14 pull-request runs a day** — roughly **420 minutes a month from
one repository**, with nothing misconfigured.

## What the bill actually looked like

Account usage export, **2026-09-01 to 2026-09-20**, 22 repositories, 17
distinct workflows, **2,593 minutes**:

| Minutes | Share | Workflow |
|---:|---:|---|
| 761 | 29.3% | `bestpractice-docs.yml` |
| 609 | 23.5% | `light-check.yml` |
| 573 | 22.1% | `precedent-check.yml` |
| 328 | 12.6% | `views-drift.yml` |
| 117 | 4.5% | `commit-identity.yml` |

The morning that triggered the investigation: **134 minutes in the first
three hours of 2026-09-20** — about **$0.80** — of which **71 minutes came
from the four practice sets that were already carrying the complete previous
round of fixes.**

That last figure is the whole problem in one number. The repos with the fix
were the ones spending the money.

## What was tried, and why each attempt missed

Five distinct interventions between 2026-09-15 and 2026-09-20. Every one was
reasonable. Every one aimed at **frequency**.

| # | Date | Lever | What it changes | Why it missed |
|---|---|---|---|---|
| 1 | 09-15 | `ci_workflows` defaults to disabled | Whether a workflow is installed at all | Gates one filename, at install time only; nothing already installed moves |
| 2 | 09-16 | `concurrency: cancel-in-progress` | Overlapping runs on one branch | A 13-second job has usually finished before the next run starts — nothing to cancel |
| 3 | 09-16 | Debounce: skip if checked recently | How often the expensive part runs | **Negative savings — see below** |
| 4 | 09-19 | `push:` scoped to named branches | Which branches trigger anything | Real and useful; does not touch per-run cost |
| 5 | 09-19/20 | Debounce window tuned 360 → 30 → 720 | The skip interval | The quantity being tuned was never the one spending |

**Nobody had measured what one run costs.** That is the single sentence
this document exists to prevent being true again.

## The debounce job could not pay for itself at any setting

The reasoning behind it was sound as far as it went: a job whose `if:`
evaluates false is reported SKIPPED, never allocates a runner, and is not
billed. **True.** What it missed is that **the job that makes the decision
is billed like any other job.** Deciding not to spend a minute costs a
minute.

Write it out, with `S` the fraction of triggers the window skips and `N` the
number of check jobs behind the gate:

```
with a debounce job:     S·1 + (1−S)·(1+N)  =  1 + N − S·N
without one:                                       N
```

The difference is `1 − S·N`, which is positive — the debounce is **more
expensive** — whenever `S·N < 1`. For the shipped shapes:

| Workflow | With debounce | Without | Debounce wins when |
|---|---|---|---|
| `precedent-check.yml` (N=2) | `3 − 2S` | `1` | `S > 1` — **never** |
| `doc-lint.yml` (N=1) | `2 − S` | `1` | `S > 1` — **never** |

At a 100% skip rate the two merely tie, and a workflow that skips every
trigger is doing nothing at all. **There is no window setting that wins.**
The three days spent tuning `360 → 30 → 720` could not have succeeded.

It also cost coverage: the 720-minute window meant a base branch could sit
up to **12 hours unchecked** after a push, accepted explicitly at the time
as the price of the saving. There was no saving.

## What actually fixes it

**Count jobs.** That is the whole intervention.

| Change | Before | After |
|---|---:|---:|
| `precedent-check.yml.template` — debounce removed, `views-drift` folded in as steps | 3 jobs | **1** |
| `doc-lint.yml.template` — debounce removed | 2 jobs | **1** |
| Consuming repos — doc lint folded into the repo's own check | 2 workflows | **1** |

Cost per firing trigger: **3 minutes → 1** for a practice set, **2 → 1** for
a consuming repo. Removing the debounce also returns the 12-hour staleness
window, so this is cheaper *and* better covered — the rare change that is
not a trade.

**`paths:` filters are the one genuinely free lever**, and worth naming
separately: GitHub evaluates them **before allocating any runner**, so a
filtered-out event costs exactly zero rather than one minute. Nothing
inside a workflow can match that, because anything inside a workflow has
already started a job. A filter only helps where the excluded extensions are
what people actually touch, though — measured in the busiest consuming repo,
its pull requests are overwhelmingly Markdown and Markdown is inside the
filter, so the filter is correct and recovers little.

## The projection, and the honest correction to it

An earlier figure in this investigation claimed a **77%** cut. **That was
wrong.** It counted savings from deleting nine checks that turned out to be
live checks doing real work, all since restored
([spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md) item 14). Counting only the
job-count reduction:

| | per month | at 20× current usage |
|---|---:|---:|
| Before | 3,890 min | ~$467 |
| After | 1,797 min | ~$216 |

**A 54% cut**, and the difference from 77% is checks still running rather
than savings lost. The monthly figures normalise the measured 20-day window
to 30 days; the 20× figure is the stated growth target, not a forecast.

**There is a floor this cannot go below.** One check, one job, one minute,
every trigger. Past that the only levers are fewer triggers, a **public**
repository (unmetered on standard runners), or a **self-hosted runner**,
where GitHub meters nothing at all.

## The same arithmetic, still shipping: `leak-gate.yml.template`'s `scope` job

Named here because it is a live instance of this finding that has not been
fixed, not a historical one.

[templates/github-actions/leak-gate.yml.template](../templates/github-actions/leak-gate.yml.template)
carries a `scope` job whose only purpose is to decide whether the real
`leak-gate` job runs — skipping the scan on a **private** repo's push to a
non-base branch. It is the debounce shape exactly, and the same arithmetic
applies with `N = 1`:

```
scope job + conditional scan:   S·1 + (1−S)·2  =  2 − S
scan job alone, no scope:                            1
```

Worse for every `S` below 1. And the two cases pull in opposite directions
without either one paying:

- On a **public** repo, the scope job **always** decides "scan" — it cannot
  change the answer, so it is pure overhead. It costs nothing only because a
  public repo's standard-runner minutes are unmetered.
- On a **private** repo it can change the answer, and that is exactly where
  minutes are billed — so it spends a whole billed minute per push, on every
  branch, to decide.

**It has cost nothing so far because no repository has it installed** —
verified 2026-09-21 by two sessions independently across thirteen
repositories: the only copies on disk sit under `process/upstream/`, inside
vendored mirrors GitHub never executes, and the four practice sets have no
copy at all. That is the only reason this is a note rather than an incident.

**Consequence for installing it:** on a public repo it is free and the scan
is worth having, so install it. On a private repo, installing it as shipped
buys the branch-scoping behaviour at a cost that the scoping itself creates.
Restructure the job first — the decision belongs where it costs nothing, and
`on:` cannot read repo config, which is the constraint that produced this
shape in the first place. That tension is real and unresolved; it is not a
reason to keep paying for a decision.

## Why this was not found sooner

Worth stating plainly, because the mechanism generalises past Actions
billing.

**A usage report names workflows and minutes.** It is a *cost* signal, and
it is silent about *purpose* and about *structure*. Every investigation
before this one read it as though it said more than it does:

- Read as a purpose signal, it produced "these filenames are not in our
  template tree, therefore they are retired" — which deleted nine live
  checks across nine repositories (item 14).
- Read as a frequency signal, it produced five straight interventions
  against trigger volume, none of which asked what a single run costs.

**The structure was never in the report and was never asked for.** Job
count does not appear in a usage export. Nothing prompts you to count jobs.
It took timing the actual work — 0.47 seconds — for the three-minute bill to
look absurd rather than normal.

The check that would have caught it at any point in those five days: **take
the billed minutes for one workflow, divide by its run count, and compare
against how long the work takes.** If the quotient is a small integer number
of minutes and the work takes seconds, the cost is structural and no
frequency lever will touch it.

## Related

- [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md) — the running record: item 13
  (the measurement and the one-job fix), item 14 (the sweep that deleted live
  checks), item 15 (the consuming-repo numbers)
- [documentation/GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md) —
  "Controlling Actions Minutes", the operator-facing levers
- [gotchas/gotcha-2026-09-21-github-actions-rejects-yaml-anchors-python-accepts.md](../gotchas/gotcha-2026-09-21-github-actions-rejects-yaml-anchors-python-accepts.md)
  — a near-miss from the fold that would have silently disabled CI in nine
  repositories
