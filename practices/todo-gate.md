---
slug:        todo-gate
title:       A backlog document gets reconciled before every push
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A push is a moment, not a file; the push gate and the occasion index reach it."
occasion:    "about to push after a thread of work"
gates:       ["push"]
index_clause: "add missed ideas, check off finished ones, before every push"
index_required: false
checked_by:  null
defines:     []
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "pending PR review -- drafted 2026-10-05 by Morgan F, moved from the shared set precedent-shared-repo-maintenance"
strength: decided
---
## Rule
Before pushing, check the thread's discussion against the repo's own backlog document (`TODO.md` or equivalent): add any idea that came up but never got a line, as a `todo/` item carrying its blocked-on or out-of-scope reason (universal [`todo-is-a-handoff`](https://github.com/alex137/BestPractice/blob/staging/practices/todo-is-a-handoff.md)), or do it now if this session can; close (`status: done`) any item this branch met the closing condition of.

## Detail
**How this differs from the second pass in universal [`capture-gate`](https://github.com/alex137/BestPractice/blob/staging/practices/capture-gate.md)** (a separate practice, `second-pass-capture`, until it was merged in on 2026-10-01), whose clause (d) also asks whether open decisions were queued in the TODO (stated 2026-09-07, after a redundancy audit across all four sources found the two overlapping and could not tell from either file whether that was deliberate):

- **It fires at a different moment.** The second pass runs once, after a substantial work-product, before the merge. This one runs before **every push**, including pushes that produced no work-product worth a second pass -- a one-line fix, a doc correction, a merge. That is where a backlog drifts.
- **It reconciles in both directions.** The second pass's clause (d) only asks whether things got *queued*. This one also requires removing or checking off what the branch just **implemented**. A backlog that only ever grows is the more common of the two failures and the one nobody notices, because nothing about it looks wrong.
- **It is scoped to one artifact.** The second pass sweeps five kinds of durable artifact; this asks about the backlog document specifically, which is what lets it be cheap enough to run on every push.

The overlap that remains -- "an idea came up and got no line" checked twice on a push that follows a substantial work-product -- is deliberate and costs one re-read. Merging the two would mean either giving up the every-push cadence or making the universal practice's five-item sweep run on every push in every adopting repo, and neither trade is worth it.

## Why
A backlog document drifting out of sync with what was actually decided is common enough in practice that it earns its own gate rather than staying an occasional "oh, I should update that" afterthought.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration. No single incident was recorded -- what was recorded is a
frequency judgment, which is its own kind of evidence.

The backlog document drifting out of sync with what was actually decided
happened often enough in practice to stop being an occasional "oh, I should
update that" afterthought and earn a fixed position in the merge runbook
instead. That is the whole argument: not that any one drift was costly, but
that the failure recurred reliably enough to be worth a gate.

Its placement is deliberate, immediately after the universal capture and
export gates, since all three ask the same kind of question -- did this
thread's work imply something that has to be written down before the branch
lands -- and answering them together is cheaper than remembering each one
separately.

## Install
No mechanical check: reconciling the backlog document against "the thread's discussion" requires comparing a file to a conversation this repo's tree never records -- a check could confirm a `TODO.md` exists and was touched in the same commit, but that's a weak proxy that would pass on an unrelated edit to the file and fail on a push that genuinely needed no reconciliation.

