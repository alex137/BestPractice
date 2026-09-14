---
name: Precedent practice candidate (universal)
about: Propose a universal-level practice for Precedent -- Stage 2 of PRACTICE_ENGINE_PLAN.md's creation pipeline
title: "Candidate: "
labels: precedent-candidate
---

<!--
This is Stage 2 of PRACTICE_ENGINE_PLAN.md's creation pipeline
(https://github.com/alex137/BestPractice/blob/precedent-beta-v01/PRACTICE_ENGINE_PLAN.md#stage-2--the-candidate),
for the UNIVERSAL level specifically. Individual and team candidates are
files in their own private repos' candidates/ directories -- see
spec/CANDIDATE_FORMAT.md
(https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/CANDIDATE_FORMAT.md)
for why universal candidates are Issues instead, and for what every field
below means. Filling this in costs nothing and commits to nothing --
Stage 3's promotion criteria run against what you write here before
anything becomes a binding practice, and closing this Issue without
promoting it costs nothing either.

Fields mirror spec/CANDIDATE_FORMAT.md's candidate schema exactly, so a
promotion tool can read either shape the same way.
-->

**Proposed slug** (kebab-case): 

**Working title**: 

**Signal** (pick one -- spec/CANDIDATE_FORMAT.md#signals):
- [ ] session-judgment-at-a-gate
- [ ] explicit-instruction
- [ ] reverted-or-corrected
- [ ] repeated-instruction
- [ ] repeated-check-failure
- [ ] review-found-defect
- [ ] restated-in-second-scope

**Recurrence**: how many times has this been observed? If once, why is it
worth promoting anyway (Stage 3's "recurrence or real cost" criterion)?

## Observed

What happened -- the incident, not the rule. A commit, a quote, a failing
check, a review comment. Specific enough that promotion doesn't have to
re-derive the story from a summary.

## Proposed Rule

One or two sentences -- draft quality, refined at promotion.

## Proposed channel

How would this be reached once it's a practice (Stage 3's "reachability"
criterion -- at least one of these needs a real answer, or it cannot become
an on-demand practice)?

- **`checked_by`**: a script that could check this, if one exists or is
  planned. A claim with no test proving it fires is refused at promotion --
  don't fill this in unless the check is real.
- **`applies_to`**: a path glob that scopes where this applies.
- **`occasion`**: a prose trigger naming the moment this applies.
- Resident tier (rare -- competes for the 2,000-token budget every session
  carries): 

**Proposed level**, with a reason (Stage 4 asks for a guess, not an open
question):
