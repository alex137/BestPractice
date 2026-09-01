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

## Cross-referenced only, not a behavior change

### Slug-link citation sweep — 2026-09-01

**What changed.** Every in-body `practice N` / `practices N and M` cross-reference
in `practices/*.md` is now a `[slug](slug.md)` markdown link. Nothing about any
Rule's substance changed, and no `checked_by` enforcement changed — this is
purely how one practice points at another. Numbers stop meaning one fixed thing
the moment practices can be reordered, split, or retired (which this catalogue
is now built to do), so a bare `practice 44` is a citation that silently rots;
a slug is permanent. `tools/verify_harness.py` gained
`check_no_bare_numeric_citations` (the numeric form must not come back) and
`check_slug_link_integrity` (every link must resolve to a real slug) as the
forward-looking guards, alongside the existing `check_citation_integrity`.

**Why this needs a CHANGES_TO_TELL_ALEX.md entry at all**, given it isn't a
mechanism or decision-rule change: converting a citation to a link adds words
(the slug name) that were not counted at that frequency in BestPractice's
original numbered prose, so the affected files fail
`check_no_invented_content` / `check_content_preserved_by_sentence` on the
citation text alone unless exempted. Registered in `verify_harness.py`'s
`AMENDED_POST_CONVERSION` (a real, disclosed edit, not a conversion bug) and
logged here, per that mechanism's own rule that the exemption must be both
declared *and* found in this file.

**Affected practices** (slug — original BestPractice number):
`acronyms-glossary` (17), `affordance-is-shared` (43), `build-buy-decompose`
(35), `capture-gate` (10), `check-source-architecture` (40),
`computed-numbers-in-scripts` (19), `convention-to-audit` (6),
`deliverables-look-like-output` (49), `docs-track-models` (33),
`engine-plus-host-shims` (50), `environment-gotchas` (4),
`frame-from-audience-question` (28), `generated-artifact-provenance` (8),
`index-remembers-past` (48), `merge-authorization-keyword` (45),
`merge-runbook` (9), `mistakes-become-rules` (20), `no-rewrite-for-warnings`
(31), `one-formatter-per-quantity` (51), `outward-summary-discipline` (25),
`parallel-artifact-ledger` (22), `permutation-frontier-column` (47),
`practice-export-loop` (14), `readers-vocabulary` (34),
`registry-source-of-truth` (7), `repo-is-memory` (1),
`scripts-assert-properties` (30), `scrub-gate` (15), `search-by-purpose` (41),
`second-pass-capture` (21), `session-bootstrap` (13),
`tabular-shared-renderer` (46), `two-check-levels` (44),
`variant-re-derives` (29), `verify-decomposition` (42),
`verify-postcondition` (32), `volatile-rules-carry-dates` (16).
`todo-is-a-handoff` (BestPractice-`main` 53) also had its three citations
converted, but needs no exemption here: it post-dates this branch's
`PRACTICES.md` snapshot (`POST_SNAPSHOT_PRACTICE_NUMBERS`), so it already has
no frozen ancestor for the fidelity checks to compare against.

**Four citations were simply wrong**, found by resolving each one against its
target's actual content rather than trusting the printed number — a defect
class BestPractice's own history already has one instance of (the practice-39
corruption `check_corruption_drop_is_a_duplicate` guards), not something this
sweep introduced:

- `engine-plus-host-shims`, `one-formatter-per-quantity`, and
  `permutation-frontier-column` each cited "practice 44" for the shared
  renderer / sortable render — practice 44 is *two named check levels*
  (`two-check-levels`); the shared renderer is practice 46,
  `tabular-shared-renderer`. Three independent citations landing on the same
  wrong number, never the topic they described, reads as an old renumbering
  that never got swept. All three now link to `tabular-shared-renderer`.
- `tabular-shared-renderer` itself cited "practice 12" for "conventions harden
  into audits" — practice 12 is `reply-links-files`; the audit-hardening rule
  is practice 6, `convention-to-audit`. Fixed.
- `second-pass-capture` cited "(practice 2)" for "decisions queued in the
  typed TODO" — practice 2 is `orientation-map`; the TODO is one of the three
  living documents named in practice 1, `repo-is-memory`. Fixed.
- `affordance-is-shared` cited "practice 42(b)" for "compute the term whose
  direction is the point" — `verify-decomposition` (42) is the right
  practice, but that description matches its **(a)** sub-point (assert on the
  decomposition, compute terms directly), not **(b)** (a negative result is a
  parameterisation). Changed to `(a)` — lower confidence than the other
  three, since it is a sub-point call rather than a wrong practice.

None of these were introduced by the phase-1 conversion: the converter's
"move only" rule carried the wrong numbers forward exactly as BestPractice had
them, and a numeric-only citation check can only confirm a cited number
*exists*, not that it is the *right* one. Worth a note upstream at the next
real check-in, alongside the existing practice-39 finding.

**A considered no: `tools/precedent_check.py`'s `cite-the-incident` flags 5 of
these files** (`mistakes-become-rules`, `permutation-frontier-column`,
`second-pass-capture`, `tabular-shared-renderer`, `volatile-rules-carry-dates`)
because the citation being converted happened to sit inside their `## Rule`
text, and the check's mechanical proxy for "a new or rewritten Rule" is "the
Rule's text differs from the base commit" — true here, but not what the
practice it enforces is actually about (`cite-the-incident`'s own `occasion`
is "writing a new convention or rule"; its `Why` is about *decisions* decaying
without a recorded origin). No new judgment was written into any of these five
Rules — only how each one links to another practice — so no Story was added
to satisfy the check mechanically; per `checkable-gets-checked`'s own
discipline, that is a considered no with its reason recorded, not an
unexamined one.

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
