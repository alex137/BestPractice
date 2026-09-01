---
date:        2026-09-01
question:    Should a session working on Precedent be allowed to also hold
             themorgan/precedent-individual and themorgan/precedent-team-maintainers
             (read and write), and may content from them be staged into
             Precedent's working tree, during active pre-Phase-5 development?
decision:    Yes, for now. The plan's blanket prohibition -- "a session cannot
             hold repositories from two owners with push access at once" /
             "nothing from an individual or team set may be staged on this
             branch at any point, even transiently" -- is relaxed for the
             duration of active development, at Morgan's explicit direction.
             It should be reinstated before Phase 6 migrates any consumer
             repo other than Morgan's own, and in any case no later than
             Phase 7 (merge-back to main / any wider audience) -- see "What
             this does not change" below.
alternatives: ["Keep the rule as an absolute and route every private-set
               question through a separate session opened against those
               repos, as phase 3's population already did", "A narrower
               relaxation: read-only access to the private repos from a
               Precedent session, but keep the no-staging rule absolute",
               "Leave the plan's prose alone and just note the gap in
               practice, undocumented"]
decided_by:  Morgan
---

## Why this was asked

The isolation rule -- stated three times in PRACTICE_ENGINE_PLAN.md (the
"Why the private sets could not be populated from here" section, the Risks
section, and a 2026-08-31 amendment) and echoed in spec/PHASE3_BRIEF.md,
spec/PRIVATE_ENFORCEMENT_BRIEF.md, spec/PRIVATE_SETS_BRIEF.md and
spec/SOURCES.md -- was slowing down active development of Precedent itself.
Morgan is designing and building the engine that will eventually resolve
these three sources together, and doing that work with zero visibility into
what the private sets actually contain, and no ability to edit them from the
same session, was creating real friction: verification gaps recorded
explicitly in this plan's own "What Phase 3 Built, and What It Could Not"
section ("the precedence contract was tested against fixture practices, not
against RepoPersonalPreferences' (RPP) real 46"), and now a second one in the immediately preceding
deep-check session's own findings (the cross-source resident-budget cap
"was tested only against synthetic fixtures, never the real private sets").

## What was actually offered, and what was chosen instead

A narrower middle ground was proposed first: read-only access to both
private repos from a Precedent session, while keeping the absolute rule
that nothing from them may be staged/committed into Precedent's tracked
files intact. Morgan explicitly declined this and asked for full read/write
across all three repos from any session, for two stated reasons:

1. **There is no actual secret content in the private sets.** Per Morgan
   directly: the individual and team sets hold process preferences (e.g.
   "bold key phrases"), not anything that reads as sensitive, and Morgan's
   own identifying information (name, email) is already public. The
   severity of the leak this rule exists to prevent -- for this specific
   content, right now -- is much lower than the rule's own language
   ("the exposure the whole arrangement exists to prevent") implies.
2. **The underlying platform restriction was never actually confirmed.**
   spec/PRIVATE_SETS_BRIEF.md already recorded this, independently, before
   this decision: *"Phase 3 also recorded a platform restriction -- that a
   session cannot hold repositories from two owners with push access at
   once. As of 2026-08-31 all four repositories above report as pushable at
   the account level, so that restriction is UNCONFIRMED and may not be
   what blocks it."* Separately, a session was asked directly (2026-09-01)
   whether the block it had been observing was an actual access failure or
   a policy choice -- it was a policy choice: sessions, this one included,
   had been declining to even try `add_repo` on the private repos because
   the plan's prose said not to, not because anything ever refused them.

## What this actually changes

- The plan's three statements of the isolation rule (Risks section; "Why
  the private sets could not be populated from here"; the routing/spec
  briefs that echo it) are marked as relaxed, with a pointer to this
  record, rather than rewritten as if they were never true -- they
  correctly describe why phase 3's population happened the way it did, and
  that history is not being edited.
- Future Precedent sessions may `add_repo` themorgan/precedent-individual
  and themorgan/precedent-team-maintainers alongside BestPractice, read and
  write across all three, and stage private-set content into Precedent's
  working tree if that is genuinely useful for the work at hand.
- The leak gate (tools/leak_gate.py) is UNCHANGED -- its structural layer
  still runs on every push, and still refuses individual/team-shaped paths,
  emails, and non-universal-source frontmatter by pattern, regardless of
  this decision. Nobody asked for that mechanism disabled, and it costs
  nothing to leave running even during this relaxed period.

## What this does NOT change, and when to undo it

This is scoped to **Morgan's own individual and team-maintainer sets**,
**during active development of Precedent itself**, by Morgan's own explicit
risk tolerance for Morgan's own content. It does not generalize:

- **Reinstate the isolation rule before Phase 6 migrates any consumer repo
  other than Morgan's own.** The moment someone else's team set or
  someone else's individual set could plausibly end up visible to a
  Precedent session, the original reasoning (a mistake here is a permanent
  publication into a public repo owned by someone else, with no
  "private initially" grace period) is back at full force, for content
  that is not Morgan's to make this call about.
- **No later than Phase 7** (merge-back to `main`, or any point Precedent
  reaches an audience beyond Morgan), regardless of whether Phase 6 has
  started, since a wider audience means the assumption "there is nothing
  sensitive here" needs re-confirming rather than carried forward.
- Whoever reinstates it should re-read this record rather than just delete
  it -- the two reasons above (no real secrets in this content, and the
  platform restriction being unconfirmed) may or may not still hold for
  whatever is in the private sets by then.
