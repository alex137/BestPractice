---
date:        2026-08-31
question:    Should Precedent be built as Precedent, a new fork of
             BestPractice (private initially, merged back to BestPractice's
             main at phase 7 if Alex agreed), or as precedent-beta-v01, a
             branch living inside BestPractice itself?
decision:    A branch, not a fork. The work is `precedent-beta-v01`, a
             branch of `alex137/BestPractice`, merging to that repo's own
             `main` — not a separate `Precedent` repository.
alternatives: ["Fork BestPractice into a new, initially-private Precedent
               repo, and propose a merge-back to Alex once the rewrite
               proved out", "Fork it and keep it permanently separate,
               never merging back"]
decided_by:  Morgan
---

## What this buys

The plan's top risk — divergence from upstream during a long-lived,
structurally-rewriting branch — is largely neutralised. A branch shares one
history with `main` and is merge-clean by construction; a fork needs a
re-sync treadmill and a content-reconciliation merge at the end. Building on
a branch rather than a fork is itself the strongest available mitigation for
that risk, not merely a naming choice.

## What this costs

**The "private initially" safety margin is gone.** The original plan bought
a grace period — *"Create `Precedent` as a fork of BestPractice. Private
initially."* — during which a leak could be caught and force-pushed away
before anyone outside could see it. BestPractice is public, so every push to
a branch of it is publication, into a repo owned by someone else, from the
first commit. Two consequences follow directly and bind from phase 2
onward rather than phase 3:

- The leak gate must run before every push, not before every merge — a
  merge-time gate is a gate on the wrong event once there is no private
  window.
- Nothing from an individual or team practice set may be staged on this
  branch at any point, even transiently (later relaxed for Morgan's own
  sets during active development — see
  [2026-09-01-relax-private-repo-isolation.md](2026-09-01-relax-private-repo-isolation.md)).

## What this closes

Two decisions the original (fork) plan left open are moot under a branch:
license and attribution (BestPractice's own license governs; only reopens
if the work is ever extracted into a standalone repo), and when Precedent
"goes public" (it already is — BestPractice is public and Precedent is a
branch of it). The phase-0 action "create `Precedent` as a fork" is
superseded outright.
