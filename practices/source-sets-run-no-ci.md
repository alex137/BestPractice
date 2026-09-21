---
slug:        source-sets-run-no-ci
title:       A practice source runs no continuous integration
tier:        on-demand
severity:    default
scope:       null
applies_to:  ["tools/precedent_vendor_engine.py", "templates/github-actions/**"]
occasion:    "installing, refreshing or adding a continuous-integration workflow in a practice SOURCE -- an individual or shared set"
gates:       []
index_clause: "a practice source runs no CI -- its checks already ran before the push"
checked_by:  null
defines:     []
command:     null
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-21"
approved_by: "Morgan, 2026-09-21 (strength: decided): \"the sets don't need CI;
  maybe we define the default to be that the precedent-individual and
  precedent-shared-* do NOT get CI. That could be the default rule, for future
  individual and shared source repos.\""
---

## Rule
**A practice source — an individual set, a shared set, any repository whose
`kind` is `source` — installs no continuous-integration workflow.** Not the
check suite, not the leak gate, not a documentation lint. A consuming repo
is a different case and keeps its leak gate; this rule is about sources
only.

**It is the default for every future set, not a cleanup of four existing
ones.** A new set created tomorrow gets no workflows, because the engine's
shipping list for that kind is empty, and an existing set loses the ones it
has on its next refresh.

## Detail
**The checks already ran, seconds earlier, on the same tree.** Every change
to a set arrives through a session that runs the deep check before it
pushes ([two-check-levels](two-check-levels.md) — deep check gates a push),
and the commit gate has already run the Markdown lint. A workflow firing
after that push re-runs the same tools against a tree that was just
checked, using the same versions, on a machine that bills by the job-minute
rounded up.

**And most of what it runs does not apply there.** A set carries few of the
practices the check registry binds, so the suite SKIPs most of its
catalogue — which is how two real sets came to report `0 passed` on an
ordinary commit while the same trees had real passing coverage under a full
sweep. Paying per job for a run that is mostly skips is the shape this rule
removes.

**A CONSUMER IS NOT A SOURCE, and the difference is forks.** A consuming
repo can receive a contribution from a fork, and a fork's pushes never fire
`push` in the receiving repository — so without a workflow, a contributed
branch arrives unscanned. That case needs the pull-request event and the
runner. A source set is single-owner and takes no forks, so the argument
does not reach it.

**What a set gives up, said plainly.** A change pushed to a set by
something other than a session — a GitHub web edit, a local commit from a
machine with no hooks — is now unchecked until somebody looks. That is a
real gap and it is accepted, because this whole system's founding
assumption is that every edit arrives through a cloud session. A set that
starts taking edits another way needs this decision revisited, not worked
around.

## Why
**Measured, from one day's GitHub usage export.** 2026-09-21: 127 of 143
billed minutes — **89%** — came from four practice sets running two
workflows each. The twelve consuming repos, all on a single-job check,
cost **16 minutes between them**. The sets' share had gone from 2% to 89%
in eleven days while the absolute number stayed flat.

The driver is structural rather than accidental: every `Update Vendors`
pass pushes a branch to four repos, and each push fires both workflows in
each — eight jobs, every one paying a checkout, a Python setup, and a
whole-minute rounding, to check four trees that a session had just checked.

**The number that made the case was the leak gate's.** It totalled 45
minutes across the entire export, and every one of those 45 was the day it
was installed in the sets. A workflow went from nothing to the second
largest line item in hours, because its trigger is an unrestricted `push:`
— every push, every branch.

## Story
The CI-minutes work through 2026-09-19 to 09-21 retired two workflows and
consolidated a third, and it worked: `bestpractice-docs.yml`, the single
largest line item at 761 minutes, billed nothing after 2026-09-20;
`views-drift.yml`, 328 minutes, nothing after 2026-09-19; and the twelve
consuming repos fell from 63 minutes a day to 16.

**The problem moved rather than ending.** Each fix made the consuming
repos cheaper and left the sources untouched, so the sets became almost the
whole bill without anyone changing anything about them. Morgan read the
export and drew the conclusion the per-workflow work had been stepping
around: the question was never which workflows a set should run, it was
whether a set should run any.

## Install
`CI_WORKFLOW_TEMPLATES['source']` in
[tools/precedent_vendor_engine.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_vendor_engine.py)
is an empty tuple. **The emptiness is load-bearing and is read as a
decision**: `_remove_retired_ci_workflow_files` sweeps whatever a kind no
longer ships, but only for a kind it recognises — so `source` being present
and empty propagates the deletion to every set on its next refresh, while a
typo'd or future kind still triggers nothing. Removing the key instead of
emptying it would silently stop the sweep.
