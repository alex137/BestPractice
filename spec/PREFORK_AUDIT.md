<!-- Last updated: 2026-09-03 (Buenos Aires) by the phase-6 pre-fork audit session -->

# Pre-Fork Catalogue Audit

One row per practice inherited from pre-fork BestPractice (the original 52,
numbered `PRACTICES.md` catalogue, plus Alex's practice 53 added on `main`
after the fork point), verdict against this plan's architecture: does it
still mean and do the same thing, or did something about how it works
change under Precedent. Named as required before phase 6 starts migrating a
consumer repo by [What phase 5 should carry forward](../PRACTICE_ENGINE_PLAN.md#what-phase-5-should-carry-forward)
and restated as still not done by [spec/PHASE5_DEEPCHECK.md](PHASE5_DEEPCHECK.md);
built here, closing that gap.

**A sortable render of the table below** (multi-column sort, per-column
filters, per [tabular-shared-renderer](../practices/tabular-shared-renderer.md))
ships alongside this source: [PREFORK_AUDIT.html](PREFORK_AUDIT.html) —
rebuild with `python3 tools/doc_html.py` after editing the table.

**Practices native to Precedent** (no `source_practice_number:` —
`disclose-landing`, `checkable-gets-checked`, `code-cites-practice`, and any
added since) are out of scope for this table by definition: there is
nothing pre-fork to compare them against.

## The table

| Slug | BestPractice # | Verdict | Alex told? | Why |
|---|---|---|---|---|
| [repo-is-memory](../practices/repo-is-memory.md) | 1 | rewritten | yes (below) | Promoted on-demand → resident (always loaded) |
| [orientation-map](../practices/orientation-map.md) | 2 | rewritten | yes (below) | Promoted resident + gained a real `checked_by` |
| [quick-index](../practices/quick-index.md) | 3 | rewritten | yes (below) | Promoted resident + gained a real `checked_by` |
| [environment-gotchas](../practices/environment-gotchas.md) | 4 | rewritten | yes (below) | Promoted resident + gained a real `checked_by` |
| [cite-the-incident](../practices/cite-the-incident.md) | 5 | rewritten | yes (below) | Scope narrowed to `practices/**`, gained `gates: ["review"]` and a real `checked_by` |
| [convention-to-audit](../practices/convention-to-audit.md) | 6 | active-as-is | — | Citation-link only |
| [registry-source-of-truth](../practices/registry-source-of-truth.md) | 7 | active-as-is | — | Citation-link only |
| [generated-artifact-provenance](../practices/generated-artifact-provenance.md) | 8 | rewritten | yes (below) | Gained a real `checked_by` |
| [merge-runbook](../practices/merge-runbook.md) | 9 | active-as-is | — | Citation-link only |
| [capture-gate](../practices/capture-gate.md) | 10 | active-as-is | — | Citation-link only |
| [doc-references-are-links](../practices/doc-references-are-links.md) | 11 | rewritten | yes (below) | `checked_by` re-pointed from `tools/doc_lint.py` to `tools/precedent_check.py` |
| [reply-links-files](../practices/reply-links-files.md) | 12 | rewritten | yes (below) | Promoted resident, gained `gates: ["reply"]` (`checked_by` stays `null`) |
| [session-bootstrap](../practices/session-bootstrap.md) | 13 | rewritten | yes (below) | Gained a real `checked_by` |
| [practice-export-loop](../practices/practice-export-loop.md) | 14 | rewritten | yes (below) | Gained a real `checked_by` — Rule/Why/Story stay byte-for-byte unchanged (a separate 2026-09-01 consideration already logged) |
| [scrub-gate](../practices/scrub-gate.md) | 15 | rewritten | yes (below) | Gained a real `checked_by` |
| [volatile-rules-carry-dates](../practices/volatile-rules-carry-dates.md) | 16 | active-as-is | — | Citation-link only |
| [acronyms-glossary](../practices/acronyms-glossary.md) | 17 | rewritten | yes (below) | Gained a real `checked_by` |
| [no-version-suffix](../practices/no-version-suffix.md) | 18 | rewritten | yes (below) | Gained a real `checked_by` |
| [computed-numbers-in-scripts](../practices/computed-numbers-in-scripts.md) | 19 | rewritten | yes (below) | Gained a real `checked_by` |
| [mistakes-become-rules](../practices/mistakes-become-rules.md) | 20 | active-as-is | — | `checked_by` genuinely still `null` — a deliberate, considered no (proportionality guard resists automation) |
| [second-pass-capture](../practices/second-pass-capture.md) | 21 | active-as-is | — | Citation-link only |
| [parallel-artifact-ledger](../practices/parallel-artifact-ledger.md) | 22 | active-as-is | — | Routing-scope glob narrowed only; `checked_by` stays `null` |
| [layered-practice-packs](../practices/layered-practice-packs.md) | 23 | rewritten | **already logged** | Two dated `CHANGES_TO_TELL_ALEX.md` entries already cover this |
| [quote-discipline](../practices/quote-discipline.md) | 24 | active-as-is | — | Untouched beyond mechanical index-clause authoring |
| [outward-summary-discipline](../practices/outward-summary-discipline.md) | 25 | active-as-is | — | Citation-link only |
| [docs-are-current-state](../practices/docs-are-current-state.md) | 26 | rewritten | yes (below) | Gained a real `checked_by` |
| [label-describes-content](../practices/label-describes-content.md) | 27 | rewritten | yes (below) | Gained a real `checked_by` |
| [frame-from-audience-question](../practices/frame-from-audience-question.md) | 28 | active-as-is | — | Citation-link only |
| [variant-re-derives](../practices/variant-re-derives.md) | 29 | active-as-is | — | Citation-link only |
| [scripts-assert-properties](../practices/scripts-assert-properties.md) | 30 | rewritten | yes (below) | Gained a real `checked_by` |
| [no-rewrite-for-warnings](../practices/no-rewrite-for-warnings.md) | 31 | rewritten | yes (below) | Gained a real `checked_by` |
| [verify-postcondition](../practices/verify-postcondition.md) | 32 | rewritten | yes (below) | Promoted resident + gained a real `checked_by` |
| [docs-track-models](../practices/docs-track-models.md) | 33 | rewritten | yes (below) | Gained a real `checked_by` |
| [readers-vocabulary](../practices/readers-vocabulary.md) | 34 | active-as-is | — | Citation-link only |
| [build-buy-decompose](../practices/build-buy-decompose.md) | 35 | active-as-is | — | Citation-link only |
| [section-order-by-frequency](../practices/section-order-by-frequency.md) | 36 | active-as-is | — | Untouched beyond mechanical index-clause authoring |
| [github-setup-disclosed](../practices/github-setup-disclosed.md) | 37 | rewritten | yes (below) | Scope narrowed to `.github/**`, gained a real `checked_by` |
| [lead-with-what-it-is](../practices/lead-with-what-it-is.md) | 38 | active-as-is | — | `applies_to` widened (+`SETUP.md`, +`GETTING_STARTED.md`) — a scope correction, not a Rule/enforcement change |
| [pr-template-honest-gates](../practices/pr-template-honest-gates.md) | 39 | active-as-is | — | Untouched beyond mechanical index-clause authoring |
| [check-source-architecture](../practices/check-source-architecture.md) | 40 | active-as-is | — | Citation-link only |
| [search-by-purpose](../practices/search-by-purpose.md) | 41 | rewritten | yes (below) | Gained a real `checked_by`; `occasion` wording also rewritten (a routing-trigger fix, not a Rule change) |
| [verify-decomposition](../practices/verify-decomposition.md) | 42 | active-as-is | — | `occasion` wording rewritten (minor routing fix); citation-link logged |
| [affordance-is-shared](../practices/affordance-is-shared.md) | 43 | active-as-is | — | Citation-link only (one of the four fixed wrong-citation cases, already logged) |
| [two-check-levels](../practices/two-check-levels.md) | 44 | rewritten | yes (below) | Gained a real `checked_by` |
| [merge-authorization-keyword](../practices/merge-authorization-keyword.md) | 45 | active-as-is | — | Citation-link only |
| [tabular-shared-renderer](../practices/tabular-shared-renderer.md) | 46 | active-as-is | — | Citation-link only (one of the four fixed wrong-citation cases, already logged) |
| [permutation-frontier-column](../practices/permutation-frontier-column.md) | 47 | active-as-is | — | Citation-link only (one of the four fixed wrong-citation cases, already logged) |
| [index-remembers-past](../practices/index-remembers-past.md) | 48 | rewritten | yes (below) | Gained a real `checked_by` |
| [deliverables-look-like-output](../practices/deliverables-look-like-output.md) | 49 | rewritten | yes (below) | Gained a real `checked_by` |
| [engine-plus-host-shims](../practices/engine-plus-host-shims.md) | 50 | rewritten | yes (below) | Gained a real `checked_by`; today's `PreToolUse`-hook work is a new *application* of the pattern, not a change to this file (already logged separately) |
| [one-formatter-per-quantity](../practices/one-formatter-per-quantity.md) | 51 | active-as-is | — | Citation-link only |
| [name-both-sides-of-ledger](../practices/name-both-sides-of-ledger.md) | 52 | active-as-is | — | Untouched beyond mechanical index-clause authoring |
| [todo-is-a-handoff](../practices/todo-is-a-handoff.md) | 53 | active-as-is | — | Alex's own post-fork addition, converted unmodified; already logged |

## Two systemic gaps this audit found, bigger than any one row

Neither is a single-practice miss — both are a whole *mechanism* that
landed across many inherited practices at once without ever being logged
as its own event in [CHANGES_TO_TELL_ALEX.md](../CHANGES_TO_TELL_ALEX.md),
whose own scope statement says plainly: "changes what its `checked_by`
actually enforces goes here." Both are now logged there
(2026-09-03), in full, rather than only summarized here.

**1. The phase-4 enforcement rollout was unlogged.** 24 of the 53 inherited
practices gained a real `checked_by` — moving from purely advisory (a
session had to notice and follow the prose) to mechanically checked. 16 of
the 24 were mentioned in `CHANGES_TO_TELL_ALEX.md` only for the unrelated
citation-link sweep, whose own text ("no `checked_by` enforcement changed")
is true of that specific commit but left the separate, earlier
enforcement-adding commits undisclosed; 8 were absent from the file
entirely.

**2. The phase-2 resident-tier promotion was unlogged.** Six inherited
practices were promoted from `tier: on-demand` to `tier: resident` — always
loaded into every session via `AGENTS.md`'s generated block, rather than
reached on demand. BestPractice pre-fork had no tier concept at all, so
this is a first-order change to how these six practices reach a session.
None of the six practices' own files, nor any prior `CHANGES_TO_TELL_ALEX.md`
entry, ever named this.

## What was checked and found clean

- **No `status:` frontmatter value other than `active`** anywhere in
  `practices/*.md` — no inherited practice is self-declared superseded or
  merged (`layered-practice-packs`' pack-mechanism note is the only
  "superseded" language anywhere, already logged).
- **No populated `supersedes:` field** on any file.
- **The whole-catalogue editorial passes** — the Rule/Detail split, the
  index-clause authoring pass, the routing-glob narrowing pass
  (`tools/routing_scope.json`) — are genuinely non-substantive by their own
  commit messages' own stated reasoning, and are not treated as individual
  gaps here, the same way the citation sweep already isn't.
