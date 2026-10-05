---
title:         Very Deep Check, 2026-10-05 — What It Found and What Was Done
kind:          record
status:        closed
opened:        2026-10-05
closed:        2026-10-05
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The full account of the most recent very deep check: every repo it read, what each pass found, what was fixed and where, and what is left for a person. The next run rewrites it; git history keeps this one."
---
# Very Deep Check, 2026-10-05 — What It Found and What Was Done

The full record of the latest run (the next run rewrites this file; git
history keeps each earlier one). The ledger of every run is
[VERY_DEEP_CHECK.md](VERY_DEEP_CHECK.md); this is the long form behind its
"Current run" row.

**Scope:** all four passes, across BestPractice, the individual set and
the writing and ladder sets. The repo-maintenance and working-style sets
were folded into universal the same day, so they were read only for what
their retirement still needs. **This session could push to BestPractice
alone:** the five private sets refused it at the git proxy, so findings
there go to a new session as a prompt rather than a commit.

**The run did not start well, and that is part of the record.** It ran
the tool, read part of its output, and stopped to ask about access,
without starting a pass; Morgan had to ask whether anything deep was left.
It also skipped the full harness at first. Both were then done: four
agents worked one pass each in their own clones, and `verify_harness.py
--all` ran in full.

## The Short Version

- **Five mechanism fixes in BestPractice**, each with a planted case
  checked to fail without it: the update tool's generated-view trap, a
  fresh install's false "reachable by no channel", and three of the very
  deep check's own sections (bootstrap drift, the fix sweep's copy,
  orphans). Plus wording across AGENTS.md, INSTALL.md, README.md, 18
  practices and four documentation pages.
- **Six open items closed** on their own conditions.
- **The set fold is half done, and the run found why it cannot simply be
  finished.** Dropping repo-maintenance turns off the commit-trailer and
  fresh-before-write checks; keeping it lets its old `default-branch` rule
  beat universal's new one. BestPractice stopped declaring working-style
  and keeps repo-maintenance until those two checks are ported.
- **Left for a person:** the decisions in the four pass items below, and
  the private sets' fixes, which this session could not push.

## Pass 1 — Can an Adopter Install and Update?

Rehearsed on `main` with no personal configuration: a loader install, an
update of a consumer installed with the 2026-09-24 installer, an update
that deletes an engine file, and an unreachable declared set. Two defects
fixed; five more in
[the pass 1 item](../todo/todo-2026-10-05-very-deep-check-pass-1-findings.md).
Not rehearsed: a migration, practice moves, a real consumer.

## Pass 2 — Do the Mechanisms Do What They Claim?

The seven items the tool raised, each reproduced on `main`. Three of the
check's own sections were wrong and are fixed. Bot-authored commits
reaching `main` through merged pull requests is the largest open finding;
it and five more are in
[the pass 2 item](../todo/todo-2026-10-05-very-deep-check-pass-2-findings.md).

## Pass 3 — Does the Writing Hold Together?

Fifteen findings, the fold seam swept first. The BestPractice ones are
fixed; the "two meanings of deep check" decision and the sets' stale
copies are in
[the pass 3 item](../todo/todo-2026-10-05-very-deep-check-pass-3-findings.md).
Most of the 174 universal practices were swept, not read line by line.

## Pass 4 — Catalogue, Backlog, Branches

Every branch, 46 overlapping pairs and all 152 open items' frontmatter.
Six items closed; the `default-branch` conflict, the fold's order and
three branch calls are in
[the pass 4 item](../todo/todo-2026-10-05-very-deep-check-pass-4-findings.md).
The overlap verdicts and recommended deletions went to the review page,
which is shown in the session and never committed.

## What Is Left

The four pass items above, and a prompt for a session that can push to
the private sets.
