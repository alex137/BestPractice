---
slug:              todo-2026-09-19-migration-dropped-51-items
kind:              analysis
domain:            mechanism
severity:          notable
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-19
closed:            null
---
## What

- <a id="migration-dropped-51-items"></a>**The 2026-09-16 todo/gotcha
  migration (`9a08363b`) dropped 51 of the 148 items in the pre-migration
  `TODO.md` — not just the two this session happened to trip over while
  tracing stale links from other repositories
  ([`todo-2026-09-10-source-checks-adopt-engine-helpers`](todo-2026-09-10-source-checks-adopt-engine-helpers.md)
  and
  [`todo-2026-09-08-split-team-sets-by-subject`](todo-2026-09-08-split-team-sets-by-subject.md),
  both reconstructed and closed already).** This item catalogues the other
  50 and proposes how to close them, rather than reconstructing all 50 by
  hand in the same session that found them — the risk of transcription
  error rises with every one done under time pressure, and a systemic
  count like this deserves a considered pass, not a rushed one.

  **The measurement, exactly:** every `<a id="...">` anchor in
  `git show 9a08363b^:TODO.md` (148 found — one anchor did not match the
  extraction regex and was not investigated further) checked against every
  old-slug row in
  [`spec/TODO_GOTCHA_MIGRATION_MAP.md`](../spec/TODO_GOTCHA_MIGRATION_MAP.md)
  as it stood before this item was filed, and independently against every
  filename actually present under `todo/` (so a legitimately renamed slug
  would not false-positive as missing). 51 anchors had neither — no map
  row, no file. Two are now closed (above); the other 50 are listed below,
  each confirmed absent from both `todo/` and the map at the time of this
  writing.

  **Not a simple format bug.** The pre-migration file used two list
  markers for items — numbered (`51. <a id="...">`, 119 of the 148) and
  unnumbered (`- <a id="...">`, 29 of the 148) — and it would be a tidy
  explanation if the migration tool only recognized one shape. It
  recognized both: of the 50 remaining missing items, 38 are numbered and
  12 are unnumbered. Whatever dropped these 50 (and the 2 already fixed),
  it was not a single marker-format blind spot, which is why this is filed
  as an investigation rather than a one-line tool patch.

  **The 50, each with the marker it carried:**
  - `agents-md-over-its-ceiling` (numbered)
  - `prefork-catalogue-audit-table` (numbered)
  - `routing-audit-silent-drop` (numbered)
  - `team-repo-and-document-template` (numbered)
  - `wire-the-very-deep-check-list` (numbered)
  - `ledger-root-commit-exemption` (numbered)
  - `ledger-ci-step-invisible` (numbered)
  - `gate-and-paths-unreachable-source` (numbered)
  - `materialized-links-dead` (numbered)
  - `sweep-judgment-only-practices` (numbered)
  - `consumer-source-names` (numbered)
  - `headline-duplicate-retired` (numbered)
  - `rpp-migration-audited` (numbered)
  - `migrated-practices-lost-their-stories` (numbered)
  - `team-check-cites-retired-practice` (numbered)
  - `convert-team-set-retired-statuses` (numbered)
  - `build-codeowners-check-flag` (numbered)
  - `cache-freshness-verdict` (numbered)
  - `bold-rule-for-heading-dense-pages` (numbered)
  - `team-maintainers-is-a-roster-name` (unnumbered)
  - `freshness-also-names-the-old-set-name` (unnumbered)
  - `individual-copy-points-at-a-retired-slug` (unnumbered)
  - `pack-sync-is-the-same-unattended-merge` (unnumbered)
  - `loader-comment-names-an-unvendored-check` (numbered)
  - `philosophy-sync` (numbered)
  - `build-views-stdout-count` (unnumbered)
  - `blocklist-stem-not-full-name` (unnumbered)
  - `park-it-to-individual-set` (unnumbered)
  - `private-set-audit-branches` (unnumbered)
  - `voice-and-styleguide-as-practices` (unnumbered)
  - `audit-trail-item-placement` (numbered)
  - `cross-owner-add-repo-push` (numbered)
  - `deduplicate-practice-links-travel` (numbered)
  - `views-drift-gate-rollout-to-existing-sets` (numbered)
  - `cross-source-resident-block-over-cap` (numbered)
  - `source-clone-keeps-no-credential` (numbered)
  - `universal-adapters-undeclared` (numbered)
  - `leak-gate-is-background-level` (numbered)
  - `leak-gate-is-background-dedup` (numbered)
  - `check-gate-reads-status` (numbered)
  - `chief-of-staff-session` (numbered)
  - `morgan-prose-name` (unnumbered)
  - `roll-binds-publishers-out-to-the-source-sets` (unnumbered)
  - `session-load-under-20k` (numbered)
  - `vendor-engine-ref-not-on-cli` (numbered)
  - `agents-md-ceiling-policy` (numbered)
  - `setup-default-is-the-loader` (numbered)
  - `generated-views-are-owned-paths` (numbered)
  - `shallow-clone-self-heal-hardening` (numbered)
  - `ledger-gap-shallow-clone-hardening` (numbered)

  **What is not yet known:** why `tools/todo_migrate.py` dropped these
  specific 51 and not the other 97 — no common pattern (all-numbered,
  all-unnumbered, all in one contiguous range, all one `kind`) was checked
  yet. That is the first step in closing this.

## How It Closes

A session with time to do this properly:

1. Reads `tools/todo_migrate.py`'s actual parsing logic against the
   pre-migration `TODO.md` (`git show 9a08363b^:TODO.md`) and finds what
   the 51 dropped items have in common that the other 97 don't — malformed
   markup, an edge case in the anchor/heading regex, a length limit,
   something else. Fixing the tool itself matters only if this migration
   is ever re-run elsewhere (per `vendor-update-runbook`'s 2026-09-19
   addition, a repo that has not yet migrated — `precedent-individual`, on
   the evidence of its own `not_binding` exemption — runs this exact tool
   next); it does not by itself recover what's already missing here.
2. For each of the 50, decides whether it is `status: done` (most of the
   ones read while filing this looked done or resolved, going by their
   surrounding `~~strikethrough~~` markers and "DONE"/"Resolved" language
   — but that was not checked for all 50, only the 3 read in enough depth
   to confirm the 2 already fixed) or genuinely still `status: open`, and
   reconstructs each as a `todo/todo-<date>-<slug>.md` file plus a
   migration-map row, the same way the 2 already-closed ones were done —
   verbatim from the pre-migration text, links repointed to where they now
   resolve, `precedent_check.py --full-sweep` clean before committing.
3. Regenerates `todo/TODO.md` and `todo/CLOSED.md`
   (`python3 tools/build_todo_index.py`) once all 50 are in.

**Blocked-on:** nothing external — this is sizable (50 items, several with
long, dense prose) rather than blocked. Filed rather than started in the
same turn that found it, per `answer-first-ask-before-long-work`.

## Notes

2026-09-19: filed. See
[`spec/CROSS_REPO_DRIFT_BRIEF.md`](../spec/CROSS_REPO_DRIFT_BRIEF.md) for
the cross-repo investigation that led here — a session rooted in
`precedent-team-writing`, working from that brief, reported a dead
citation to `split-team-sets-by-subject`'s old anchor, which is what
prompted tracing it here and finding the other 49.
