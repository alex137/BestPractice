<!-- Last updated: 2026-09-04 (Buenos Aires) by the session merging pull request (PR) #86, folding in a cleanup session's and the phase-6 pre-fork audit session's own entries -->

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

### `layered-practice-packs` (BestPractice practice 23) — 2026-09-03, repo-local formalized

**What changed.** The practice's third tier — repo-local, "rules that live
in that repo's instructions files and never leave" — is now a real fourth
`precedent.json` source the loader itself understands, not just prose a
repo-local rule happened to sit in: a `practices/` directory (declared
with `path: "."` or, per the recommended convention, a subdirectory),
ranked in `PRECEDENCE` between individual and team by default, and subject
to the same `overrides:` and `severity: blocking` mechanics every other
level gets. Found while designing this, and worth naming here even though
it does not touch the three-way decision rule itself: a 2026-09-03
deep-check audit found materializing a self-referential repo-local
source (`path` equal to the sync target) could silently destroy or
corrupt its own hand-authored content across runs — `precedent_materialize.py`
now refuses that combination outright rather than attempting to make it
safe.

**What did not change.** The three-way decision rule itself (generic /
domain / repo-local) is untouched by this — this is the *same* mechanism
upgrade the entry above already logs for the middle (domain) tier,
now landing for the third. A repo-local rule described only in prose
(pre-migration, phase 6 not yet run) still works exactly as before.

**What's still open.** Same gap the entry above names for the domain
tier, now also true of repo-local formalized: nothing yet gives a rule a
home independent of the one repo it was declared for, which was never
repo-local's job to begin with (its whole point is staying scoped to one
repo) — no new gap here, noted only so this entry doesn't read as if it
closed something the one above left open.

See [practices/layered-practice-packs.md](practices/layered-practice-packs.md)
and [spec/SOURCES.md](spec/SOURCES.md).

### `layered-practice-packs` (BestPractice practice 23) — 2026-09-04, repo-local's `path` is now a fixed rule, not a recommendation

**What changed.** The entry above formalized repo-local as a real source
but left its subdirectory placement as a *recommendation*: `path: "."` or a
subdirectory both resolved, with a subdirectory only ever "the better
choice." Raised by a dependent-repo comparison (`WorkingWithAI` has no
repo-local practices at all and so no `local/`; `TodoMorgan` does, at
`local/practices/`, following the recommendation) — the two repos are not
actually inconsistent with each other, but the convention itself was only
ever advisory, so a third repo was always free to pick a different
subdirectory name, or the bare root, and nothing would have refused it.
`tools/precedent_resolve.py`'s `load_config` now requires a repo-local
source's `path` to be exactly `"local"` — refused outright otherwise, with
the reproduced silent-overwrite bug named in the refusal message. This is
the `checkable-gets-checked` treatment: what was prose-only advice is now
a mechanical check, with a firing test in `tools/verify_harness.py`
(`check_source_precedence`'s bare-root and other-subdirectory-name cases).

**What did not change.** `tools/precedent_materialize.py`'s own
level-agnostic `_self_referential_sources` guard (any source, not just
repo-local, whose `path` equals the materialize target) is untouched and
still the backstop for the levels this new rule doesn't reach — universal
self-hosted at `path: "."` (this repo's own `precedent.json`, unaffected)
remains legal. Every existing repo-local declaration already in the wild
(this repo's own `local/`, `TodoMorgan`'s) already used `"local"`, so
nothing that already followed the recommendation needed to change.

See [practices/layered-practice-packs.md](practices/layered-practice-packs.md),
[spec/SOURCES.md](spec/SOURCES.md), and
[PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s "Source" section.

### The phase-4 enforcement rollout — 24 inherited practices gained a real `checked_by` — 2026-09-03, found doing the pre-fork audit

**What changed.** This branch's own scope statement, above, says plainly:
"changes what its `checked_by` actually enforces goes here." Phase 4
(`spec/ENFORCEMENT.md`) converted 24 of your 53 inherited practices from
`checked_by: null` — advisory prose only, compliance depended on a session
noticing and following it — to a real script in `tools/precedent_check.py`.
That never got logged here as its own event: 16 of the 24 are mentioned in
this file only for the unrelated citation-link sweep above, whose own text
("no `checked_by` enforcement changed") is true of *that specific commit*
but left the separate, earlier enforcement commits undisclosed; 8 are
absent from this file entirely. Found auditing the full pre-fork catalogue
against this plan's architecture
([spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md)), not from any one commit's
own review.

**Affected practices (24), full list and verdict:**
[spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md)'s table — every row marked
"gained a real `checked_by`" or an enforcement re-point (that table is the
source of truth for this; not re-listed here). One re-point worth naming
inline since it is the sharpest example of this file's own scope
statement: `doc-references-are-links` (11) already had a `checked_by`
naming `tools/doc_lint.py`; phase 4 moved it to `tools/precedent_check.py`,
which is exactly "changes what its `checked_by` actually enforces."

**What did not change.** Every affected practice's `## Rule` — what it
actually asks a session to do — is unchanged; [spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md)
confirms this practice-by-practice, not just asserted. This is purely
*how* compliance is checked, never *what* is being asked.

### The phase-2 resident-tier promotion — 6 inherited practices are now always loaded — 2026-09-03, found doing the pre-fork audit

**What changed.** BestPractice pre-fork had no `tier` concept at all — every
practice was equally prose, consulted the same way. Phase 2 introduced
`tier: resident` (always loaded into every session, via `AGENTS.md`'s
generated block) versus `tier: on-demand` (reached only through the
occasion index, a path glob, or a check). Six of your inherited practices
are now resident — the same six [spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md)'s
table marks "Promoted resident." This is the architecture's own headline move
([PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md), "The Resident
Budget") and none of these six practices' own files log it — the same gap
the entry above names for enforcement, for a different mechanism.

**What did not change.** Same as above — the Rule text of all six is
untouched; only where and how often a session sees it changed.

## Cross-referenced only, not a behavior change

**A scope note on the entry below, added 2026-09-03**: "no `checked_by`
enforcement changed" in the Slug-link citation sweep entry is accurate for
that specific commit, not a claim that none of the affected practices ever
gained enforcement — several did, in separate, earlier commits, logged
above once this branch's own pre-fork audit actually found the gap.

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
not counted at that frequency in BestPractice's original numbered prose, so
the affected files needed a disclosed exemption — `verify_harness.py`'s
`AMENDED_POST_CONVERSION` — whose own rule is that the exemption must be
both declared *and* found in this file.

**Affected practices** (slug — original BestPractice number), each also
carrying the same exemption in `verify_harness.py`'s `AMENDED_POST_CONVERSION`
registry — this list and that registry must agree, and this is the copy a
human reads: `acronyms-glossary` (17), `affordance-is-shared` (43),
`build-buy-decompose` (35), `capture-gate` (10), `check-source-architecture`
(40), `computed-numbers-in-scripts` (19), `convention-to-audit` (6),
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
`verify-postcondition` (32), `volatile-rules-carry-dates` (16), and
`todo-is-a-handoff` (53, exempted 2026-09-02 once a phase-5 pre-flight
`git merge origin/main` gave it a frozen ancestor in `PRACTICES.md` for the
fidelity checks to compare against for the first time).

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

### `engine-plus-host-shims` (BestPractice practice 50) — 2026-09-03

The new `templates/harness/claude-code/hooks/precedent-paths.sh`
(a `PreToolUse` hook wiring the path-triggered loading channel into a
fresh install — see `spec/LOADER.md`) is a real, new *application* of this
practice's engine-plus-shim split: the vendored engine
(`tools/precedent_paths.py`) stays the single implementation, the new file
is a thin host shim that shells out and reshapes its output for Claude
Code's own hook contract. Considered logging it here as a mechanism
change and decided against it: this practice's own Rule, Why, and Story
are untouched, byte-for-byte — a new instance of an existing pattern is
not a change to what the pattern means or how it works, any more than a
new practice file citing `code-cites-practice` would be. This is purely
Precedent-native engine work (phase 6, consumer-repo integration for a
channel that did not exist pre-fork), so it needs no separate call-out by
this file's own stated scope; `git log` and `spec/LOADER.md`'s own status
table already say what was added.

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
