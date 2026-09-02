<!-- Last updated: 2026-09-02 (Buenos Aires) by the phase-5 build session -->

# The Candidate File Format (Phase 5, Stage 2)

What [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s
[Stage 2 — The Candidate](../PRACTICE_ENGINE_PLAN.md#stage-2--the-candidate)
builds to. Read that section first; this is the implementation note, in the
same relationship [spec/PRACTICE_FORMAT.md](PRACTICE_FORMAT.md) has to the
plan's "The Practice File" section.

## Where a candidate lives

**A candidate's level decides where the file is, exactly like a practice's
level decides which repository it lives in** — [spec/SOURCES.md](SOURCES.md)'s
"levels are repositories, not directories" applies unchanged:

| Level | Where |
|---|---|
| Individual | `candidates/*.md` in that person's own individual-set repo |
| Team | `candidates/*.md` in that team's own private repo |
| Universal | **A GitHub Issue** on `alex137/BestPractice`, labeled `precedent-candidate`, using [.github/ISSUE_TEMPLATE/practice-candidate.md](../.github/ISSUE_TEMPLATE/practice-candidate.md) — never a file. See [spec/SOURCES.md](SOURCES.md#universal-candidates-are-github-issues-not-a-fourth-candidates) for why: `tools/leak_gate.py` already forbids a `candidates/` directory in Precedent, unconditionally, by shape rather than content. |

A `candidates/` directory is exactly as private-shaped as `practices/` and
carries the identical leak-gate consequence in the individual/team repos it
lives in — nothing here weakens that; it only says where the universal case
goes instead.

## The shape

One file per candidate, at `candidates/<slug>-<date>.md` (the date suffix
because a candidate is explicitly allowed to be raised more than once before
recurrence promotes it — two files, not one file mutated in place, so the
recurrence count in [Stage 3](../PRACTICE_ENGINE_PLAN.md#stage-3--promotion-criteria)
is a count of files, not a field a session has to remember to increment):

```
---
slug:              proposed-kebab-case-slug
title:             Human-readable working title
date:              2026-09-02          # the day this was raised, the raiser's own local calendar date
status:            open                # open | promoted | expired | declined
signal:            session-judgment-at-a-gate   # see "Signals" below
raised_by:         "a name or a session URL"
recurrence_count:  1                   # how many candidate files (this one plus any earlier ones) name this same slug
cost_if_once:      null                # a one-line reason this is worth promoting even at recurrence_count 1, or null
tier_requested:    on-demand           # resident | on-demand -- feeds Stage 3's budget criterion
proposed_checked_by:   null            # a script path, ONLY once it exists and has a passing test -- see "What phase 5 should carry forward" in the plan; a claim without a case is refused at promotion, same as a real practice
proposed_applies_to:   ["**"]
proposed_occasion:     null
proposed_gates:        []
---

## Observed
What happened, in plain prose -- the incident, not the rule. This is the
evidence [Stage 3](../PRACTICE_ENGINE_PLAN.md#stage-3--promotion-criteria)'s
recurrence-or-cost criterion checks: a commit, a quote, a failing check, a
review comment. Specific enough that a promotion decision doesn't have to
re-derive the story from a one-line summary -- the same failure mode
[spec/ATTENTION_CEILING.md](ATTENTION_CEILING.md)'s review-arm result
diagnosed for an 80-character clause.

## Proposed Rule
One or two sentences -- draft quality. Refined, not necessarily rewritten,
at promotion; this is what `tools/precedent_promote.py` copies into the
drafted practice file's `## Rule` if all four criteria pass.
```

## Signals

The value `signal:` takes, one per [Stage 1](../PRACTICE_ENGINE_PLAN.md#stage-1--detection)
source:

- `session-judgment-at-a-gate` — the existing capture/export/review gates.
- `explicit-instruction` — the user said "from now on," "always," "never,"
  "going forward."
- `reverted-or-corrected` — the user reverted, rewrote, or corrected work a
  session produced.
- `repeated-instruction` — the same instruction has now appeared in a
  second session.
- `repeated-check-failure` — the same check has failed repeatedly.
- `review-found-defect` — a review found a defect (BestPractice's own
  `mistakes-become-rules`, detected instead of remembered).
- `restated-in-second-scope` — a practice has been restated in a second
  scope, the promotion signal.

`tools/precedent_candidate.py --list` and `tools/precedent_promote.py` both
validate against this closed set, the same discipline
`tools/precedent_gate.py` already applies to its own `gates:` vocabulary —
an unknown signal fails loudly rather than being silently accepted as prose.

## Never loaded into context

Per the plan's own text: creating a candidate costs nothing, ignoring one
costs nothing. Nothing in the loader (`tools/build_views.py`,
`tools/precedent_paths.py`, `tools/precedent_resolve.py`) reads
`candidates/`. Only `tools/precedent_candidate.py` and
`tools/precedent_promote.py` do, on demand.

## Expiry

A candidate nobody acts on should not accumulate forever. `status: expired`
is a real, honest value here for the same reason `status: retired` is a real
value on a practice — Stage 6's report can propose it, but per this phase's
own retirement-approval rule, expiring a *candidate* is not the same
decision as retiring a *practice* and needs no approval gate: nothing is
in force yet, so there is nothing to un-approve. `tools/precedent_candidate.py --expire`
sets the field; it does not delete the file, so the record of what was
proposed and dropped survives (`repo-is-memory`).
