---
slug:        routing-audit
title:       The routing audit checks coverage, not content
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "checking whether the practices that should have fired for recent work actually fired"
gates:       []
index_clause: "run the mechanical coverage check now; roll the deep-read slice forward"
checked_by:  "tools/precedent_check.py"
defines:     ["routing audit"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "pending review"
---
## Rule
Ask a narrower question than "did we follow every practice": **did every
practice that should have fired, fire?** Two parts, run with
[tools/routing_audit.py](tools/routing_audit.py): a mechanical coverage
check (`coverage`) — every judgment-only on-demand practice (no
`checked_by`, no `gates`) whose `applies_to` glob matches the files in
question, reported as a routing-failure candidate — and a rotating deep
read (`slice`), a bounded number of that same judgment-only set, whichever
have gone longest unreviewed, handed to the invoking session to actually
judge against real work. Never sweep the whole judgment-only set in one
pass; that is a different, heavier mechanism —
[full-practice-audit](full-practice-audit.md) — kept deliberately separate.
What this produces is fixes to the *routing* (a narrower glob, a better
occasion, or, best, a promotion to `checked_by`), not just a list of misses
cleared and forgotten.

## Detail
A practice with a working `checked_by` or a `gates` entry needs no
human-style review here — the check either fired or it did not, or the
gate reaches it deterministically at its named moment. The coverage check
and the rotating slice both skip that set entirely and spend themselves on
the smaller set that can only be judged: the practices that depend on a
session noticing them unaided. `tools/routing_audit.py mark-reviewed SLUG`
records that a slice was actually read and judged, in
`tools/routing_audit_state.json`.

**What this tool cannot do, disclosed rather than assumed.** The design
this practice implements compares "practices that matched" against
"practices the session actually loaded" — this repo keeps no record of
what a past session actually loaded, so `coverage` reports only which
practices *should* have fired, not whether they did. A match with no
`checked_by`/`gates` is a candidate, not a proven miss. See
[spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md).

## Why
The loader's whole architecture accepts a real risk in exchange for not
loading every practice into every session: **a practice with a wrong or
missing trigger is worse than one buried in a wall of text, because nobody
notices its absence.** A periodic check on routing itself is the standing
mitigation — but it must not do this by reading every practice with the
whole diff in context, which is the load-everything failure moved to a
different moment. `spec/ATTENTION_CEILING.md`'s review-arm experiment
measured exactly that heavier shape and found it scored *worse* than doing
nothing (54% recall against an 84% no-review baseline) — the concrete
reason this mechanism stays a cheap mechanical pass plus a small rotating
slice, never a full sweep. And its own honest limit: this is a detective
control, not a preventive one. It finds misses after the fact; the
preventive controls are triggers and checks, and this mechanism's real
value is improving *those*.

## Story
Approved for phase 5 in the 2026-09-01 preflight review
(`PRACTICE_ENGINE_PLAN.md`, "v28... the unbuilt one is renamed *routing
audit*") and never built — not tracked in `TODO.md`, not carried forward in
`spec/PHASE5_BRIEF.md` or `spec/PHASE6_BRIEF.md`, found only because a
2026-09-03 session was asked to build a related, human-requested audit
mechanism and read the plan first rather than building from memory of the
conversation alone. See
[spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md) for the
investigation this gap itself opens: why an approved phase-5 deliverable
fell through, and what else the plan approved that the tree does not show.

## Install
[tools/routing_audit.py](tools/routing_audit.py) implements both parts;
`tools/precedent_check.py`'s `routing-audit` check verifies the tool exists
and that `tools/routing_audit_state.json`, if present, carries no rotation
entry for a practice that is no longer active — stale bookkeeping a
retired or renamed practice would otherwise leave behind silently.
`coverage()`'s glob-matching is itself a planted case in
`tools/verify_harness.py` (`check_routing_audit_coverage`, added
2026-09-04) rather than only asserted correct. The rotating slice's
judgment step shares its mechanism with
[full-practice-audit](full-practice-audit.md)'s whole sweep, and shares
that practice's first evaluation result — 6 of 6 (100%) on a small,
single-run test, 2026-09-04, see
[spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md), "The
audit-judgment result." On-demand only, invoked explicitly; not wired into
a commit, push, or merge gate until a session validates it is worth the
cost (see [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md)).
