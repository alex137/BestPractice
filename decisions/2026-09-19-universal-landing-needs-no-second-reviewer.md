---
date: '2026-09-19'
question: |
  Several documents -- spec/MOVING_PRACTICES.md, tools/precedent_land.py,
  tools/precedent_move.py, practices/disclose-landing.md,
  documentation/FOR_DEVELOPERS.md, documentation/ADOPTING.md -- state that
  landing a universal practice needs "a pull request (PR) to Precedent,
  reviewed and merged by someone other than whoever proposed it." That
  never got reconciled with local/practices/merge-target-is-beta-branch.md's
  2026-09-04 narrowing: a session may merge any PR into
  `precedent-beta-v01` directly once its own deep check passes, no
  sign-off from Alex or anyone else. Does the second-reviewer requirement
  still bind a universal-practice PR specifically, or was it superseded
  and just never updated?
decision: |
  Superseded, and the wording is struck everywhere it appeared as an
  operative rule. A universal-practice PR lands the same way as any other
  PR into `precedent-beta-v01`: merged once its own deep check passes, no
  second sign-off required. Edited: spec/MOVING_PRACTICES.md,
  tools/precedent_land.py, tools/precedent_move.py,
  practices/disclose-landing.md, documentation/FOR_DEVELOPERS.md,
  documentation/ADOPTING.md. decisions/2026-09-06-precedent-binds-itself.md
  is left as written -- it is a historical record, not rewritten -- and
  this entry is the pointer forward from it.
alternatives: |
  ["Keep the second-reviewer requirement as a stricter, content-specific
  overlay for universal practice CREATION specifically, distinct from
  ordinary precedent-beta-v01 engine or doc changes -- rejected on the
  evidence: a sample of the 30 most recent PRs merged into
  precedent-beta-v01 includes several landing new universal practices
  (#451 'Add vendor-rollout-disclosed', #456 'Add \"Archive?\" as a
  standing command', among others), and none carries a recorded review
  (checked via the PR review API, zero reviews on #451). The rule was
  never actually followed for exactly the case it was written to gate, so
  leaving it in the docs as a live requirement was misleading rather than
  protective."]
decided_by: Morgan
strength: decided
---

## How this was missed

[decisions/2026-09-06-precedent-binds-itself.md](2026-09-06-precedent-binds-itself.md)
postdates the 2026-09-04 narrowing by two days, cites it directly in its
own §1 ("the documented rule that a session may merge into
`precedent-beta-v01` without Alex"), and in the same breath restates the
older framing -- "the universal set['s] approval route the plan defines
as *a pull request to Precedent, reviewed and merged by someone other
than whoever proposed it* -- which is repository-level review, i.e.
GitHub permissions, exactly what is in place." That reads as though the
two were compatible: "GitHub permissions" as a review gate distinct from
"no sign-off from Alex." They weren't checked against each other, and no
branch-protection rule on `precedent-beta-v01` requires an approving
review before merge -- "GitHub permissions" turned out to mean write
access to the repository, nothing more. The PR-history check above is
what settled it, not a re-reading of either document in isolation.

## Why this one wasn't just "remove wording nobody could explain"

Before editing, this session read
[practices/disclose-landing.md](../practices/disclose-landing.md) (an
active practice, not a stray sentence) and the 2026-09-06 record itself,
because "someone other than whoever proposed it" is exactly the kind of
guardrail that deserves a real check before it's dropped -- a two-key
control against one session unilaterally publishing a bad rule to every
Precedent consumer is a reasonable thing to want. What settled it was
empirical: the last 30 PRs merged into `precedent-beta-v01`, new
universal practices among them, carry no recorded review at all. The
rule as written was never the actual mechanism doing that protection --
`precedent-beta-v01`'s own deep check (`two-check-levels`) was, the whole
time, same as for everything else on that branch. Removing stale wording
that contradicts working practice is a correction; the paragraph above is
what makes that a checked claim rather than a guess.
