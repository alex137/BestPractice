---
slug:              todo-2026-09-19-migration-dropped-54-items
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

- <a id="migration-dropped-54-items"></a>**The 2026-09-16 todo/gotcha
  migration (`9a08363b`) dropped 54 of the 161 items in the pre-migration
  `TODO.md` — about a third, not the two this session first tripped over
  while tracing stale links from other repositories
  ([`todo-2026-09-10-source-checks-adopt-engine-helpers`](todo-2026-09-10-source-checks-adopt-engine-helpers.md)
  and
  [`todo-2026-09-08-split-team-sets-by-subject`](todo-2026-09-08-split-team-sets-by-subject.md),
  both reconstructed and closed already).** This item catalogues the other
  54 and closes with the root cause found and fixed, rather than
  reconstructing all 54 by hand in the same session that found them — the
  risk of transcription error rises with every one done under time
  pressure, and a systemic loss like this deserves a considered pass, not
  a rushed one.

  **Corrected count, and why it moved from an earlier 51/148 to 54/161.**
  The first sweep counted only `<a id="...">`-tagged top-level items (148
  found by scanning for the literal anchor tag) and missed a THIRD shape
  entirely: a bare `- **Title.**` bullet with no anchor at all, whose
  migrated slug is generated from its title text rather than read off the
  document. `tools/todo_migrate.py`'s own parser — corrected below — finds
  161 real top-level items in `git show 9a08363b^:TODO.md`: 119 numbered
  (`51. <a id="...">`), 29 unnumbered (`- <a id="...">`), and 13 bare bullets
  with no anchor at all. Of those 161, 54 have neither a
  [`spec/TODO_GOTCHA_MIGRATION_MAP.md`](../spec/TODO_GOTCHA_MIGRATION_MAP.md)
  row nor a `todo/` file, confirmed by running the corrected parser against
  the real pre-migration text and diffing its output against both, not by
  hand-counting.

  **Root cause, found and fixed.** `tools/todo_migrate.py`'s
  `TODO_ANCHOR_RE`, `TODO_BARE_RE` and `TODO_CHECKBOX_RE` matched a literal
  `-\s+` bullet marker only — never `\d+\.\s+` — so a numbered item's
  start line could never be recognized as the start of anything. This is
  NOT proven to be the sole or even primary cause of the original 2026-09-16
  loss: several numbered items (e.g. `actions-as-enforcement-layer`) DO
  have real `todo/` files from that exact commit, so whatever actually ran
  was not simply "this regex over the raw file" — most likely a large,
  partly manual pass through a 7,240-line file with no completeness check
  anywhere catching what it missed. But the regex gap is real, reproducible
  today, and would cause the identical failure on the next repo to run
  this tool — `precedent-individual`, per its own `not_binding` exemption,
  has not migrated its `TODO.md` yet. **Fixed regardless of attribution**:
  the three regexes now accept either bullet shape, and
  `parse_todo_items` ends with a new `_assert_no_dropped_items` guard that
  compares every `<a id="...">` in the source text against every item it
  actually produced and refuses (`TodoShapeError`) on any gap — verified
  two ways: it fires when the old dash-only regex is reinstated over a
  2-item synthetic case, and running the corrected parser over the real
  `9a08363b^:TODO.md` produces exactly the 161-item, zero-gap result cited
  above.

  **The 54, each with the shape it used:**
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
  - `done-2026-09-06-the-individual-source-bootstrap-hook-is-inst` (numbered, no anchor)
  - `done-2026-09-06-a-missing-individual-source-is-no-longer-sil` (numbered, no anchor)
  - `rpp-migration-audited` (numbered)
  - `migrated-practices-lost-their-stories` (numbered)
  - `team-check-cites-retired-practice` (numbered)
  - `convert-team-set-retired-statuses` (numbered)
  - `build-codeowners-check-flag` (numbered)
  - `cache-freshness-verdict` (numbered)
  - `a-scheduled-freshness-channel-exists-only-for-whoever-builds` (bare-bold, no anchor)
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
  - `register-is-a-live-field-in-one-identity-json-and-absent-fro` (bare-bold, no anchor)
  - `roll-binds-publishers-out-to-the-source-sets` (unnumbered)
  - `session-load-under-20k` (numbered)
  - `vendor-engine-ref-not-on-cli` (numbered)
  - `agents-md-ceiling-policy` (numbered)
  - `setup-default-is-the-loader` (numbered)
  - `generated-views-are-owned-paths` (numbered)
  - `shallow-clone-self-heal-hardening` (numbered)
  - `ledger-gap-shallow-clone-hardening` (numbered)

## How It Closes

The root cause is fixed (`tools/todo_migrate.py`, this branch, verified
above) — that half of this item is done. What remains:

1. For each of the 54, decide whether it is `status: done` or genuinely
   still `status: open` (most read so far look done or resolved, going by
   `~~strikethrough~~` markers and "DONE"/"Resolved" language in their
   text, but that was only confirmed for the 2 already closed), and
   reconstruct each as a `todo/todo-<date>-<slug>.md` file plus a
   migration-map row, the same way the 2 already-closed ones were done —
   verbatim from the pre-migration text, links repointed to where they now
   resolve, `precedent_check.py --full-sweep` clean before committing.
2. Regenerate `todo/TODO.md` and `todo/CLOSED.md`
   (`python3 tools/build_todo_index.py`) once all 54 are in.
3. Once `precedent-individual` (or any other not-yet-migrated repo) runs
   `tools/todo_migrate.py --apply` on its own `TODO.md`, confirm the new
   guard actually ran clean there too — a silent success on a repo whose
   `TODO.md` happens to have no shape gap would not, by itself, prove the
   guard is doing anything.

**Blocked-on:** nothing external — this is sizable (54 items, several with
long, dense prose) rather than blocked.

## Notes

2026-09-19: filed with 51/148, corrected same day to 54/161 after building
and testing the `todo_migrate.py` fix described above, which is what
surfaced the true total. See
[`spec/CROSS_REPO_DRIFT_BRIEF.md`](../spec/CROSS_REPO_DRIFT_BRIEF.md) for
the cross-repo investigation that led here — a session rooted in
`precedent-team-writing`, working from that brief, reported a dead
citation to `split-team-sets-by-subject`'s old anchor, which is what
prompted tracing it here.

Morgan asked directly whether this was real or simulated. It is real: every
count above comes from `git show`/`git log` against this repository's
actual history (commit `9a08363b`, `9a08363b^`) and from actually running
the patched `tools/todo_migrate.py` against that real text, not from a
hypothetical or constructed example.
