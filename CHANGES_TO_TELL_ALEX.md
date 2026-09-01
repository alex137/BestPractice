<!-- Last updated: 2026-09-01 (Buenos Aires) by a follow-up session -->

# Changes to tell Alex

This branch (`precedent-beta-v01`) merges back to `alex137/BestPractice`'s
own `main` (`PRACTICE_ENGINE_PLAN.md`, "Precedent is a branch of BestPractice,
not a fork"). Most of what happens on it is additive — new practices, new
tooling, new documents — and needs no separate call-out; `git log` already
says what was added.

**This file is only for the other kind: a change to what one of Alex's
*pre-fork* practices means or how it works.** Anything that rewrites a
Rule's substance, retires a mechanism the original practice depended on, or
changes what its `checked_by` actually enforces goes here, dated, with the
practice's slug and its original BestPractice number, kept current as this
branch diverges — so the phase-7 merge-back conversation starts from a list
instead of a diff. A practice that is only cross-referenced (a pointer added
to its Install section, nothing about its Rule or enforcement changed) is
noted here too, briefly, for completeness, but is not a behavior change.

Nothing here is unilateral: everything below is either a rewrite that keeps
the original decision rule intact (marking a superseded *mechanism*, not a
disagreement with the practice), or a fix based on the base-repo drift this
session found for [Alex's practice 53](#alexs-real-time-additions) below.
None of it changes what a plain BestPractice-vendoring consumer repo
(pre-migration) sees — the pre-migration path each affected practice
describes is kept working in every case.

## Changed mechanism, decision rule kept

### `layered-practice-packs` (BestPractice practice 23) — 2026-09-01

**What changed.** The practice's vendored-pack *implementation* — a separate
tree at `process/<pack>/` with its own manifest, blocklist, and harness
adapter — is marked superseded for any repo running Precedent's loader. A
domain rule is now just a Universal or Team practice scoped with
`applies_to` / `occasion` / `gates`, routed by the same occasion index and
path-triggered channel as everything else; the loader already does the job
the pack's harness adapter existed to do.

**What did not change.** The three-way decision rule the practice opens
with — generic (upstream) / domain (a pack, or now, a scoped practice) /
repo-local (never leaves) — is unchanged and still how a new rule's home is
decided. The pack mechanism itself is kept, described in the practice's
Install section, for a consumer repo that has not yet migrated to the
loader (phase 6).

**What's still open.** The loader does not yet give a domain's rules a home
independent of any one team's roster — the case where several different
teams would all want the same compliance- or lab-workflow bundle, which the
old pack mechanism solved and nothing in the new source model replaces yet.
Tracked as a Deferred item in `PRACTICE_ENGINE_PLAN.md`, merged with the
existing "a practice belonging to more than one team" entry.

See [practices/layered-practice-packs.md](practices/layered-practice-packs.md).

## Considered, not changed

### `practice-export-loop` (BestPractice practice 14) and `mistakes-become-rules` (BestPractice practice 20) — 2026-09-01

Both relate to the new architecture — 14 to Stage 5's promotion round-trip,
20 to Stages 1–4's creation pipeline — and a first pass added a
cross-reference paragraph to each practice's Install section. Reverted on
reflection: per this repo's own `deliverables-look-like-output` (BestPractice
practice 49), a practice file is the deliverable and holds what following it
needs, not commentary about a related mechanism elsewhere. That cross-reference
now lives in `PRACTICE_ENGINE_PLAN.md`'s "What phase 5 should carry forward"
instead. **Both files are byte-for-byte unchanged from BestPractice's
original text.**

## Alex's real-time additions

### Practice 53, "A TODO is a handoff, not a parking lot" — 2026-09-01

Not a change *to* an inherited practice — a practice Alex added to `main`
(pull request (PR) #61, 2026-08-31) after this branch's fork point
(`88ecf7f`). Converted
through the same phase-1 pipeline as the original 52, unmodified in
substance: [practices/todo-is-a-handoff.md](practices/todo-is-a-handoff.md).
Noted here because it's the kind of drift this file exists to catch — `main`
had moved 3 commits past the fork point (this practice plus two unrelated
tooling fixes) before a session checked.
