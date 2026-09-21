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

## The same arithmetic, found in the one file left alone: `leak-gate.yml.template`

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

**Fixed the same day.** The `scope` job is gone; the decision is a step
inside the one `leak-gate` job. A step-level skip still bills that job's own
minute — the limit item 8 measured, which no in-workflow check can avoid —
but one minute is what the old shape's *cheapest* case cost and half its
scanning case. Verified against all eight real event/visibility/branch
combinations: only a private repo's push to a non-base branch skips, and a
`pull_request` or `workflow_dispatch` is never skipped whatever the
visibility.

**Paying nothing at all still needs `on: push: branches:`**, which GitHub
evaluates before allocating a runner. That is left to the adopter on
purpose: a hardcoded branch list is a list somebody has to keep correct, and
a stale one under-scans silently. The runtime check is the safe default; the
trigger filter is the cheap one, and choosing between them is a judgment
about that repo, not something a template should decide.

**A second bug surfaced at the same moment, and it is the worse one.**
`CI_WORKFLOW_TEMPLATES` listed `leak-gate.yml.template` for both kinds — but
[leak_gate.py](../tools/leak_gate.py), the script the workflow's only substantive step runs, was in
neither `ENGINE_FILES` nor `CONSUMER_ENGINE_FILES`, and no step fetched it.
**The workflow shipped without the thing it runs.** Any repo installing it
got a guaranteed red check and a billed minute per trigger, on precisely the
public repositories it existed to protect. Caught by a session told to
install it, which read both lists, found neither name, and refused — and
refused equally to hand-copy the script, a copy outside `ENGINE_MANIFEST.json`
being what the vendoring mechanism exists to prevent. Both refusals were
right. [leak_gate.py](../tools/leak_gate.py) and `leak-blocklist.default.txt` are now vendored to
both kinds.

**Three separate defects in one template in two days** — a self-declared
visibility field that was wrong on two live repos, a manifest read that
ignored one of two files, and a workflow shipped without its script — and
every one was found by a session verifying a claim rather than acting on it.
None was found by the session that wrote the template, including the two
written the same day the template was.

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

## What happened after the fix landed (2026-09-20 to 2026-09-21)

The one-job templates were merged on 2026-09-20. **Nobody's bill moved.**
That gap, and what was built to close it, is the second half of this
record.

### The templates reached nobody, and it was not a bug

Measured 2026-09-21, in all four practice sets on disk:

| Repo | `precedent-check.yml` jobs | Engine pinned at |
|---|---|---|
| `precedent-individual` | 3 (`debounce`, `precedent-check`, `views-drift`) | `de72bc56` |
| `precedent-shared-writing` | 3 | `de72bc56` |
| `precedent-shared-repo-maintenance` | 3 | `de72bc56` |
| `precedent-shared-working-style` | 3 | `de72bc56` |

The first hypothesis was that the vendor engine was failing to overwrite an
existing workflow file — its recorded hash matched the live one, which
reads exactly like a refresh that recorded without writing. **It is not
that.** `git merge-base --is-ancestor fc6e764a2 de72bc568` returns false:
the one-job template landed in `fc6e764a2`, the sets are pinned at
`de72bc568`, and the pin is *earlier*. `_refresh_ci_workflow_files()` works;
it has simply never been asked to run in these repos since the fix.

That is worth writing down precisely because it is the boring answer. The
interesting answer — a silent write failure in the vendoring engine — was
one command away from being reported as fact.

### The real gap: "a template changed" and "I am being billed for the old
one" were different facts

Nothing connected them. The freshness report, when it was built, would say
`templates/github-actions/precedent-check.yml.template` changed upstream and
stop. Reading that and knowing your own `.github/workflows/precedent-check.yml`
is the file it produces required carrying the mapping in your head.

[`precedent_engine_freshness.py`](../tools/precedent_engine_freshness.py)
now closes it. Run in a repo that is behind, `--files` prints:

```
-> YOU ARE RUNNING THE OLD ONE: .github/workflows/precedent-check.yml in
   this repo was installed from precedent-check.yml.template, which is
   among the changes above. Every run of it until the next "Update
   Vendors" is the superseded shape.
```

Verified against `precedent-shared-writing` on 2026-09-21 — a real stale
repo, not a fixture. The mapping comes from
`precedent_vendor_engine.CI_WORKFLOW_TEMPLATES`, the one place the
template-to-installed-path pairing is declared, and the whole thing is
best-effort: a repo whose vendored engine predates that module gets no
impact line and an otherwise unchanged report.

### `ci_debounce_minutes` was retired, and two runbooks kept applying it

The field was retired on 2026-09-20 — no Python reads it. But
[vendor-update-runbook](../practices/vendor-update-runbook.md) step 10 and
[MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md) step 6 both
still told a session to check the field was "set the way the person actually
wants". Both now say to **delete** it where found. A live-looking knob that
controls nothing is worse than no knob: somebody tunes it, sees no change,
and concludes the whole lever class does not work — which is close to what
five failed interventions already looked like from the outside.

## What was built so a change cannot silently fail to arrive

Morgan's framing, 2026-09-21: *an iron law that every change is tested for
whether it carries through to the vendored-in versions.* Four mechanisms
came out of it, and one deleted-checks incident paid for them.

**1. CI workflow deletions propagate by manifest diff.** Engine files always
did; CI workflows were tombstone-only, so a retired workflow kept running in
every repo that had ever installed it until somebody deleted it by hand.
`_remove_retired_ci_workflow_files()` now diffs the manifest's recorded
`ci_workflow_files` against what the kind actually ships. The tombstone list
stays for what a diff cannot express, such as a rename.

The `kind` comes from the **caller**, not from the manifest. During a
source-to-consumer conversion the manifest still names the old kind, so
reading it there removes the wrong set of files. The harness caught that:
`check_vendor_engine_consumer_case` stopped reporting `missing`.

**2. The outward check.** Everything else in the suite checks a repo against
itself, so a consumer could sit months behind with every gate green.
[precedent_engine_freshness.py](../tools/precedent_engine_freshness.py)
reads the manifest's `source_commit`,
`ls-remote`s the pinned branch tip, and says how far behind the repo is. It
never refreshes anything and **exits 0 in every failure mode**, including no
network — a freshness notice that can fail a build is a notice people turn
off. Wired into the session-start hook and into
[precedent_gate.py](../tools/precedent_gate.py)'s push and merge moments,
both `--quiet`.

**3. `shipped-template-carries-its-script`.** A shipped workflow template
that invokes a script out of `tools/` must be shipping that script too. Registered with `practice_backed=False`: it enforces an engine
property, not a catalogue practice.

**4. The provenance gate was made readable again.** See below — it is the
one that matters most, and it is not really about billing.

## The finding that outlived the billing question

**`generated-artifact-provenance` was failing on `precedent-beta-v01` through
eight merges**, and every deep check in that window needed a human to decide
which failures were new.

Root cause, reduced to one line in a scratch install with `HOME` emptied and
every `PRECEDENT_*` unset:

```
precedent_sync_views.py writes:  [My options](practices/my-options.md)
build_views.py --check wants:    [My options](precedent/universal/practices/my-options.md)
```

The installer runs the first; the check runs the second. A freshly installed
project failed its own provenance check from the moment it was created.
Both were already calling the same renderer — they disagreed on **one
argument**, the file path passed per practice, which is what decides how a
sibling citation is rewritten. Both paths exist on disk in a consuming repo,
so neither was reported unplaceable. They just wrote the same link two ways.
`build_views.placed_practice_file()` is now the only thing that answers it.

Three layers hid it: the check is rotation-gated, so a first reproduction
came back clean; an undeclared individual source contaminated the
regeneration with 18 individual-level practices (17 net, since one shadows
a universal slug), masking the one-line cause; and the trigger was one day
old.

**Why it belongs in a document about billing.** Cost is not only minutes.
That red gate cost two near-misses in a single session — a planted test case
silently disarmed by an unrelated change, and a `--structural-only` fix
over-corrected to drop both blocklist halves instead of one. Both were
caught only because somebody read output they had already been told to
expect. Three of this session's own defects were caught by a harness or a
sibling session verifying rather than executing; **none was found by the
session that wrote the code.**

Two rules earned that week:

- **A check that never reads clean is a check nobody reads.**
- **A detector verified only against a clean tree is indistinguishable from
  a broken one.** Test both directions or you have tested nothing.

## The largest line on the bill: `light-check.yml`, and what it says about us

Measured from the 2026-09-01..19 usage export, not inferred:

| Repo | `light-check.yml` minutes | Share | Active days | Per day |
|---|---:|---:|---:|---:|
| the busiest repo on the account | 277 | 45.5% | 19 | 14.6 |
| second | 101 | 16.6% | 14 | 7.2 |
| third — a repo whose own name marks it for deletion | 67 | 11.0% | 7 | 9.6 |
| fourth | 49 | 8.0% | 8 | 6.1 |
| fifth | 36 | 5.9% | 11 | 3.3 |
| sixth | 33 | 5.4% | 7 | 4.7 |
| seventh | 29 | 4.8% | 5 | 5.8 |
| five others | 17 | 2.8% | — | — |
| **total** | **609** | **23.5% of the account** | | |

(Repository names are deliberately absent: this repository is public, and
they are not. The leak gate caught the first draft of this table, which is
the gate doing exactly its job on exactly its author.)

**A head and a long tail, not one offender.** The working hypothesis before
this table was "almost certainly one or two repos" — reasoning from 609
across 12 against ~14 pull-request events a day in the busiest repo. The
top three are 73%; the top one is 45%. The hypothesis was directionally
right and quantitatively wrong, which is the usual outcome of arithmetic
done on two numbers instead of the data that was sitting in the export the
whole time.

**67 of those minutes belong to a repository whose own name marks it as
deprecated and awaiting deletion.** Free money, if it goes.

### Why it is ours, although no template shipped it

`two-check-levels` tells every adopter to name a fast check and a full
check. **This repository shipped the rule and never shipped a shape.** So
twelve repositories each invented a `light-check.yml`, uncoordinated, and
not one of them got the one-job or `paths:` discipline the other templates
here now have. Nothing propagated, because there was nothing to propagate
from.

That is a general failure mode worth naming: **a rule published without a
shape is a rule everybody implements differently, and expensively.** The
rule was right. The gap was that it named an outcome and left every adopter
to invent the mechanism, twelve times, in private.

[templates/github-actions/light-check.yml.template](../templates/github-actions/light-check.yml.template)
is the shape, added 2026-09-21. It is deliberately **not** auto-installed
and `ci_workflows` does not reach it: what a light check runs is a
per-repository decision, those twelve repos run twelve different things,
and at least one is a live required check. The command is a marked
`CUSTOMIZE` line whose instruction is to carry across whatever the existing
file ran rather than decide afresh — the discipline the 2026-09-20 sweep
skipped when it deleted nine live checks on the strength of a filename.

### The busiest repo, where the money actually is

| Workflow | Minutes | Share of repo | Per active day |
|---|---:|---:|---:|
| `bestpractice-docs.yml` | 350 | 55.3% | 18.4 |
| `light-check.yml` | 277 | 43.8% | 14.6 |
| `bestpractice-upstream-sync.yml` | 4 | 0.6% | 2.0 |
| `personal-pack-sync.yml` | 2 | 0.3% | 2.0 |
| **total** | **633** | **24.4% of the whole account** | |

**The bigger half is ours, and an ordinary "Update Vendors" is the fix.**
`bestpractice-docs.yml` is `doc-lint.yml.template`'s install. The current
template is one job (it was two) and carries `paths:` filters; a copy
predating both pays twice per trigger and pays on triggers that touch no
Markdown at all. Nothing bespoke is required — the repo is simply behind.

**So the single highest-value action available on this account is a vendor
update in one repository.** Not a fleet sweep, not a new mechanism: the
work was already done upstream and had not arrived. That is the same
sentence as this document's other half, which is why both halves are here.

## The number nobody looked for: Precedent's own sets are 39.6% of the bill

The investigation spent a day on a consuming repository's workflows. Then
somebody read the export by repository instead of by workflow:

| Repository | Minutes | Share of account |
|---|---:|---:|
| the busiest consuming repo | 633 | 24.4% |
| `precedent-individual` | 468 | 18.0% |
| `precedent-shared-writing` | 223 | 8.6% |
| `precedent-shared-repo-maintenance` | 194 | 7.5% |
| `precedent-shared-working-style` | 143 | 5.5% |
| **the four practice sets together** | **1028** | **39.6%** |

**The rule-keeping infrastructure costs more than the work it governs.**
Four repositories that hold practice text, and nothing else, out-spend the
single busiest project by 60%.

That is not an argument against the sets. It is an argument that the
cheapest thing in this system to get wrong is the thing that runs on every
pull request in every repository, and that the people best placed to notice
are the ones who never look at their own tooling's bill because it is
tooling.

### `precedent-individual`, broken out

| Workflow | Minutes | Per active day | Status |
|---|---:|---:|---|
| `precedent-check.yml` | 218 | 27.2 | **three jobs until 2026-09-21**; now one |
| `views-drift.yml` | 130 | 14.4 | retired; last billed 2026-09-19, file already gone |
| `commit-identity.yml` | 117 | 11.7 | live, one job, trigger narrowed 2026-09-21 |
| `engine-refresh.yml` | 3 | 1.0 | `workflow_dispatch` only; nothing to do |

**27.2 minutes a day for a three-job workflow whose work takes under half a
second** is the billing floor stated as plainly as it can be: roughly nine
triggers a day, three billed minutes each. One job makes the same nine
triggers cost nine.

`views-drift.yml` is worth its own line as the shape of the whole problem.
It was folded into `precedent-check.yml.template` upstream on 2026-09-19,
and it went on billing in this set until somebody deleted the file. A
retirement upstream is not a deletion downstream — which is exactly the
asymmetry the CI-workflow manifest diff now closes, and this is the case
that would have exercised it.

**What is left there is `commit-identity.yml`'s 117 minutes**, and the
session that audited it measured the shape: 118 runs, median run 12
seconds, against a 60-second floor. `fetch-depth: 0` is not the problem and
is load-bearing (both checks are tree-scope and exit non-zero on a shallow
clone). The remaining lever is folding its checks into
`precedent-check.yml`'s now-single job, which takes 117 minutes to zero
incremental, because a job already being billed absorbs another twelve
seconds for free.

## What is still not done

- **The carry itself.** All four practice sets still run the three-job
  workflow. It needs an `Update Vendors` in each, run from a session whose
  GitHub access reaches them; this repository's sessions are scoped to
  `alex137/bestpractice`, the git proxy returns 403, and `add_repo` refuses
  cross-owner adds. Tracked in
  [todo-2026-09-20-carry-one-job-ci-templates-into-installed-repos.md](../todo/todo-2026-09-20-carry-one-job-ci-templates-into-installed-repos.md).
- **`light-check.yml`**, 609 billed minutes month-to-date across 12 repos —
  23.5% of the account's whole spend, and it has no template in this tree,
  so nothing here governs it. Still the single largest line.
- **`commit-identity.yml`** in `precedent-individual`: every `pull_request`
  event, `fetch-depth: 0`, 117 minutes month-to-date. Also not ours.
- **The staleness roll-up** — "which of my repos are behind, and by how
  much" — still needs cross-repo read access this repository deliberately
  does not have. Whether it belongs here at all is undecided.

## Related

- [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md) — the running record: item 13
  (the measurement and the one-job fix), item 14 (the sweep that deleted live
  checks), item 15 (the consuming-repo numbers)
- [documentation/GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md) —
  "Controlling Actions Minutes", the operator-facing levers
- [gotchas/gotcha-2026-09-21-github-actions-rejects-yaml-anchors-python-accepts.md](../gotchas/gotcha-2026-09-21-github-actions-rejects-yaml-anchors-python-accepts.md)
  — a near-miss from the fold that would have silently disabled CI in nine
  repositories
- [todo-2026-09-21-nothing-checks-a-consumer-against-upstream.md](../todo/todo-2026-09-21-nothing-checks-a-consumer-against-upstream.md)
  — the carry-through item: two of its three pieces are built, the roll-up
  is not
