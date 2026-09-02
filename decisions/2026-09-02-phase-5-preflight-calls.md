---
date:        2026-09-02
question:    Three calls needed before Stage 1 code could be written: (1)
             does retirement (Stage 6) need the same approval gate as
             creation (Stage 4), or can the evidence retire a practice on
             its own; (2) does the measured attention-ceiling ~54% (spec/
             ATTENTION_CEILING.md) transfer to Stage 1's gate judgment and
             Stage 3's promotion criteria, which the plan flagged as "not
             yet resolved either way"; (3) where does a universal-level
             candidate live, given Stage 2's "a dated file in candidates/"
             collides with tools/leak_gate.py's unconditional ban on that
             directory shape in Precedent.
decision:    (1) Retirement routes through the identical per-level gate as
             creation -- individual: the owner's own yes; team: an
             approver's review over approvers.json/CODEOWNERS; universal: a
             PR to Precedent. The report proposes; it never flips
             `status: retired` itself. (2) The ceiling is reasoned, not
             re-measured, not to transfer: Stage 1/3 judge one candidate
             with its own attached evidence, closed and narrow, not a whole
             diff swept against the full catalogue in one retrospective
             pass -- structurally closer to the oracle's framing than the
             review arm's. Recorded as an argument in spec/
             ATTENTION_CEILING.md, revisited later via Stage 6's own
             fire/citation data rather than a fourth eval arm now. (3)
             Universal candidates are GitHub Issues on alex137/BestPractice
             (label `precedent-candidate`, .github/ISSUE_TEMPLATE/
             practice-candidate.md), never a file -- individual and team
             candidates keep the file-in-a-private-repo design.
alternatives: ["(1) Let Stage 6's report auto-retire a practice past some
               dead threshold, with no human step -- rejected: retiring a
               rule changes the binding set exactly as much as adding one
               does, and the plan's own creation principle (system
               notices/enforces, human approves) draws no exception for
               removal.",
              "(2) Run a fourth pre-registered eval arm (a Stage-1/3-shaped
               task) before writing any Stage 1/3 code, to measure rather
               than argue -- rejected as spending a full measurement cycle
               to de-risk a task shape nothing has exercised even once;
               deferred to Stage 6's own data instead.",
              "(2 alt) Treat the unresolved flag as blocking and refuse to
               build Stage 1/3 until it is independently measured --
               rejected: the plan's own text asks for the reasoning to
               happen, not for a moratorium.",
              "(3) Carve a leak-gate exception for a candidates/ directory
               specifically marked source: universal -- rejected: the gate
               bans a shape, not a content claim, and a self-declared
               exception is exactly the shortcut the ban exists to close.",
              "(3 alt) Hold universal candidates in one of Morgan's own
               private repos instead of a public Issue -- rejected: needlessly
               conflates a universal-level artifact with Morgan's personal
               sets, and Issues are already Stage 4's own mechanism for
               universal approval, one stage earlier."]
decided_by:  Morgan
---

## Why these three, together

All three surfaced while drafting the phase-5 implementation plan, before
any Stage 1 code existed, and Morgan asked for the resolution to be
recorded and then built on rather than left as an open question re-derived
by whichever session picks this thread up next -- the same discipline
`spec/PRACTICE_FORMAT.md` and this directory's own README already ask for.
They are grouped in one record because they were decided in one sitting, by
the same person, as three inputs to the same next step (writing Stage
1-6), not because they are the same decision -- `decisions/README.md`'s
"one file per decision" is a default against letting reasoning sprawl
across the plan, not a rule against grouping tightly-coupled calls that
would otherwise be three near-duplicate headers with the same date and
decider.

## Where each one actually lives

Each decision's substantive reasoning was written into the artifact that
governs it, not duplicated here -- this record exists to be the thing
`PRACTICE_ENGINE_PLAN.md`'s "Amendments Since Approval" points at, per
`decisions/README.md`'s "one- or two-sentence pointer" rule, not to hold
the reasoning itself twice.

1. **Retirement approval routing** — spelled out in
   [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md#stage-6--the-loop-closes)'s
   Stage 6 section directly, since it is an architecture clarification the
   plan's own body should state, not a decision to keep separate from it.
2. **The attention-ceiling transfer argument** — the full case is in
   [spec/ATTENTION_CEILING.md](../spec/ATTENTION_CEILING.md#does-the-ceiling-reach-stage-1-and-stage-3-2026-09-02-reasoned-not-measured).
3. **Universal candidates as Issues** — the full reasoning, including the
   leak-gate collision it resolves, is in
   [spec/SOURCES.md](../spec/SOURCES.md#universal-candidates-are-github-issues-not-a-fourth-candidates),
   with the file format in
   [spec/CANDIDATE_FORMAT.md](../spec/CANDIDATE_FORMAT.md).

## What would change any of these

- **(1)** If a level is ever added with no human behind it at all (fully
  autonomous team operation), this would need revisiting -- not anticipated,
  not built for.
- **(2)** If Stage 6's later fire/citation data shows Stage 1/3 judgments
  disagreeing badly with what actually happened, that is the measured
  result this argument doesn't have, and it would override this reasoning
  on its own terms.
- **(3)** If Precedent ever gets its own GitHub App or bot identity capable
  of filing Issues on its own behalf, `tools/precedent_candidate.py`'s
  universal path stops being "draft only" -- the deferred-credentials gap
  this decision accepts, not a permanent design constraint.
