---
slug:              todo-2026-09-19-migration-dropped-54-items
kind:              analysis
domain:            mechanism
severity:          notable
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-19
closed:            2026-09-19
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
  - ~~`agents-md-over-its-ceiling`~~ (numbered) — closed, restored as [`todo-2026-09-14-agents-md-over-its-ceiling.md`](todo-2026-09-14-agents-md-over-its-ceiling.md)
  - ~~`prefork-catalogue-audit-table`~~ (numbered) — closed, restored as [`todo-2026-09-06-prefork-catalogue-audit-table.md`](todo-2026-09-06-prefork-catalogue-audit-table.md)
  - ~~`routing-audit-silent-drop`~~ (numbered) — closed, restored as [`todo-2026-09-06-routing-audit-silent-drop.md`](todo-2026-09-06-routing-audit-silent-drop.md)
  - ~~`team-repo-and-document-template`~~ (numbered) — closed, restored as [`todo-2026-09-06-team-repo-and-document-template.md`](todo-2026-09-06-team-repo-and-document-template.md)
  - ~~`wire-the-very-deep-check-list`~~ (numbered) — closed, restored as [`todo-2026-09-06-wire-the-very-deep-check-list.md`](todo-2026-09-06-wire-the-very-deep-check-list.md)
  - ~~`ledger-root-commit-exemption`~~ (numbered) — closed, restored as [`todo-2026-09-06-ledger-root-commit-exemption.md`](todo-2026-09-06-ledger-root-commit-exemption.md)
  - ~~`ledger-ci-step-invisible`~~ (numbered) — closed, restored as [`todo-2026-09-06-ledger-ci-step-invisible.md`](todo-2026-09-06-ledger-ci-step-invisible.md)
  - ~~`gate-and-paths-unreachable-source`~~ (numbered) — closed, restored as [`todo-2026-09-06-gate-and-paths-unreachable-source.md`](todo-2026-09-06-gate-and-paths-unreachable-source.md)
  - ~~`materialized-links-dead`~~ (numbered) — closed, restored as [`todo-2026-09-06-materialized-links-dead.md`](todo-2026-09-06-materialized-links-dead.md)
  - ~~`sweep-judgment-only-practices`~~ (numbered) — closed, restored as [`todo-2026-09-06-sweep-judgment-only-practices.md`](todo-2026-09-06-sweep-judgment-only-practices.md)
  - ~~`consumer-source-names`~~ (numbered) — closed, restored as [`todo-2026-09-06-consumer-source-names.md`](todo-2026-09-06-consumer-source-names.md)
  - ~~`headline-duplicate-retired`~~ (numbered) — closed, restored as [`todo-2026-09-06-headline-duplicate-retired.md`](todo-2026-09-06-headline-duplicate-retired.md)
  - ~~`done-2026-09-06-the-individual-source-bootstrap-hook-is-inst`~~ (numbered, no anchor) — closed, restored as [`todo-2026-09-06-done-2026-09-06-the-individual-source-bootstrap-hook-is-inst.md`](todo-2026-09-06-done-2026-09-06-the-individual-source-bootstrap-hook-is-inst.md)
  - ~~`done-2026-09-06-a-missing-individual-source-is-no-longer-sil`~~ (numbered, no anchor) — closed, restored as [`todo-2026-09-06-done-2026-09-06-a-missing-individual-source-is-no-longer-sil.md`](todo-2026-09-06-done-2026-09-06-a-missing-individual-source-is-no-longer-sil.md)
  - ~~`rpp-migration-audited`~~ (numbered) — closed, restored as [`todo-2026-09-06-rpp-migration-audited.md`](todo-2026-09-06-rpp-migration-audited.md)
  - ~~`migrated-practices-lost-their-stories`~~ (numbered) — closed, restored as [`todo-2026-09-06-migrated-practices-lost-their-stories.md`](todo-2026-09-06-migrated-practices-lost-their-stories.md)
  - ~~`team-check-cites-retired-practice`~~ (numbered) — closed, restored as [`todo-2026-09-06-team-check-cites-retired-practice.md`](todo-2026-09-06-team-check-cites-retired-practice.md)
  - ~~`convert-team-set-retired-statuses`~~ (numbered) — closed, restored as [`todo-2026-09-06-convert-team-set-retired-statuses.md`](todo-2026-09-06-convert-team-set-retired-statuses.md)
  - ~~`build-codeowners-check-flag`~~ (numbered) — closed, restored as [`todo-2026-09-06-build-codeowners-check-flag.md`](todo-2026-09-06-build-codeowners-check-flag.md)
  - ~~`cache-freshness-verdict`~~ (numbered) — closed, restored as [`todo-2026-09-06-cache-freshness-verdict.md`](todo-2026-09-06-cache-freshness-verdict.md)
  - ~~`a-scheduled-freshness-channel-exists-only-for-whoever-builds`~~ (bare-bold, no anchor) — closed, restored as [`todo-2026-09-06-a-scheduled-freshness-channel-exists-only-for-whoever-builds.md`](todo-2026-09-06-a-scheduled-freshness-channel-exists-only-for-whoever-builds.md)
  - ~~`bold-rule-for-heading-dense-pages`~~ (numbered) — open, blocked, restored as [`todo-2026-09-07-bold-rule-for-heading-dense-pages.md`](todo-2026-09-07-bold-rule-for-heading-dense-pages.md)
  - ~~`team-maintainers-is-a-roster-name`~~ (unnumbered) — closed, restored as [`todo-2026-09-11-team-maintainers-is-a-roster-name.md`](todo-2026-09-11-team-maintainers-is-a-roster-name.md)
  - ~~`freshness-also-names-the-old-set-name`~~ (unnumbered) — closed, restored as [`todo-2026-09-11-freshness-also-names-the-old-set-name.md`](todo-2026-09-11-freshness-also-names-the-old-set-name.md)
  - ~~`individual-copy-points-at-a-retired-slug`~~ (unnumbered) — closed, restored as [`todo-2026-09-11-individual-copy-points-at-a-retired-slug.md`](todo-2026-09-11-individual-copy-points-at-a-retired-slug.md)
  - ~~`pack-sync-is-the-same-unattended-merge`~~ (unnumbered) — closed, restored as [`todo-2026-09-11-pack-sync-is-the-same-unattended-merge.md`](todo-2026-09-11-pack-sync-is-the-same-unattended-merge.md)
  - ~~`loader-comment-names-an-unvendored-check`~~ (numbered) — closed, restored as [`todo-2026-09-07-loader-comment-names-an-unvendored-check.md`](todo-2026-09-07-loader-comment-names-an-unvendored-check.md)
  - ~~`philosophy-sync`~~ (numbered) — closed, restored as [`todo-2026-09-07-philosophy-sync.md`](todo-2026-09-07-philosophy-sync.md)
  - ~~`build-views-stdout-count`~~ (unnumbered) — closed, restored as [`todo-2026-09-16-build-views-stdout-count.md`](todo-2026-09-16-build-views-stdout-count.md)
  - ~~`blocklist-stem-not-full-name`~~ (unnumbered) — closed, restored as [`todo-2026-09-07-blocklist-stem-not-full-name.md`](todo-2026-09-07-blocklist-stem-not-full-name.md)
  - ~~`park-it-to-individual-set`~~ (unnumbered) — closed, restored as [`todo-2026-09-08-park-it-to-individual-set.md`](todo-2026-09-08-park-it-to-individual-set.md)
  - ~~`private-set-audit-branches`~~ (unnumbered) — closed, restored as [`todo-2026-09-08-private-set-audit-branches.md`](todo-2026-09-08-private-set-audit-branches.md)
  - ~~`voice-and-styleguide-as-practices`~~ (unnumbered) — closed, restored as [`todo-2026-09-08-voice-and-styleguide-as-practices.md`](todo-2026-09-08-voice-and-styleguide-as-practices.md)
  - ~~`audit-trail-item-placement`~~ (numbered) — closed, restored as [`todo-2026-09-09-audit-trail-item-placement.md`](todo-2026-09-09-audit-trail-item-placement.md)
  - ~~`cross-owner-add-repo-push`~~ (numbered) — open, blocked, restored as [`todo-2026-09-09-cross-owner-add-repo-push.md`](todo-2026-09-09-cross-owner-add-repo-push.md)
  - ~~`deduplicate-practice-links-travel`~~ (numbered) — closed, restored as [`todo-2026-09-11-deduplicate-practice-links-travel.md`](todo-2026-09-11-deduplicate-practice-links-travel.md)
  - ~~`views-drift-gate-rollout-to-existing-sets`~~ (numbered) — closed, restored as [`todo-2026-09-11-views-drift-gate-rollout-to-existing-sets.md`](todo-2026-09-11-views-drift-gate-rollout-to-existing-sets.md)
  - ~~`cross-source-resident-block-over-cap`~~ (numbered) — closed, restored as [`todo-2026-09-11-cross-source-resident-block-over-cap.md`](todo-2026-09-11-cross-source-resident-block-over-cap.md)
  - ~~`source-clone-keeps-no-credential`~~ (numbered) — closed, restored as [`todo-2026-09-11-source-clone-keeps-no-credential.md`](todo-2026-09-11-source-clone-keeps-no-credential.md)
  - ~~`universal-adapters-undeclared`~~ (numbered) — closed, restored as [`todo-2026-09-12-universal-adapters-undeclared.md`](todo-2026-09-12-universal-adapters-undeclared.md)
  - ~~`leak-gate-is-background-level`~~ (numbered) — closed, restored as [`todo-2026-09-12-leak-gate-is-background-level.md`](todo-2026-09-12-leak-gate-is-background-level.md)
  - ~~`leak-gate-is-background-dedup`~~ (numbered) — closed, restored as [`todo-2026-09-13-leak-gate-is-background-dedup.md`](todo-2026-09-13-leak-gate-is-background-dedup.md)
  - ~~`check-gate-reads-status`~~ (numbered) — closed, restored as [`todo-2026-09-13-check-gate-reads-status.md`](todo-2026-09-13-check-gate-reads-status.md)
  - ~~`chief-of-staff-session`~~ (numbered) — closed, restored as [`todo-2026-09-13-chief-of-staff-session.md`](todo-2026-09-13-chief-of-staff-session.md)
  - ~~`morgan-prose-name`~~ (unnumbered) — closed, restored as [`todo-2026-09-12-morgan-prose-name.md`](todo-2026-09-12-morgan-prose-name.md)
  - ~~`register-is-a-live-field-in-one-identity-json-and-absent-fro`~~ (bare-bold, no anchor) — closed, restored as [`todo-2026-09-12-register-is-a-live-field-in-one-identity-json-and-absent-fro.md`](todo-2026-09-12-register-is-a-live-field-in-one-identity-json-and-absent-fro.md)
  - ~~`roll-binds-publishers-out-to-the-source-sets`~~ (unnumbered) — closed, restored as [`todo-2026-09-12-roll-binds-publishers-out-to-the-source-sets.md`](todo-2026-09-12-roll-binds-publishers-out-to-the-source-sets.md)
  - ~~`session-load-under-20k`~~ (numbered) — closed, restored as [`todo-2026-09-13-session-load-under-20k.md`](todo-2026-09-13-session-load-under-20k.md)
  - ~~`vendor-engine-ref-not-on-cli`~~ (numbered) — closed, restored as [`todo-2026-09-14-vendor-engine-ref-not-on-cli.md`](todo-2026-09-14-vendor-engine-ref-not-on-cli.md)
  - ~~`agents-md-ceiling-policy`~~ (numbered) — closed, restored as [`todo-2026-09-14-agents-md-ceiling-policy.md`](todo-2026-09-14-agents-md-ceiling-policy.md)
  - ~~`setup-default-is-the-loader`~~ (numbered) — closed, restored as [`todo-2026-09-14-setup-default-is-the-loader.md`](todo-2026-09-14-setup-default-is-the-loader.md)
  - ~~`generated-views-are-owned-paths`~~ (numbered) — closed, restored as [`todo-2026-09-14-generated-views-are-owned-paths.md`](todo-2026-09-14-generated-views-are-owned-paths.md)
  - ~~`shallow-clone-self-heal-hardening`~~ (numbered) — closed, restored as [`todo-2026-09-15-shallow-clone-self-heal-hardening.md`](todo-2026-09-15-shallow-clone-self-heal-hardening.md)
  - ~~`ledger-gap-shallow-clone-hardening`~~ (numbered) — closed, restored as [`todo-2026-09-15-ledger-gap-shallow-clone-hardening.md`](todo-2026-09-15-ledger-gap-shallow-clone-hardening.md)

## How It Closes

Closed 2026-09-19. All 54 are reconstructed as their own `todo/` files with
migration-map rows, `todo/TODO.md`/`todo/CLOSED.md` regenerated, full check
suite clean. 52 of the 54 restored `status: done` or `dropped`, matching
what their own pre-migration text already said; 2
(`cross-owner-add-repo-push`, `bold-rule-for-heading-dense-pages`) restored
`status: open` because their own text describes a real, unresolved blocker
as of the pre-migration snapshot — this item does not claim to have closed
those two, only to have given them back their own file and history. What
`precedent-individual` (or any other not-yet-migrated repo) still needs,
separately: run `tools/todo_migrate.py --apply` on its own `TODO.md` and
confirm the new guard runs clean there too — a silent success on a repo
whose `TODO.md` happens to have no shape gap would not, by itself, prove
the guard is doing anything.

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

Also added a matching completeness guard to `parse_gotcha_items` (same
commit as the guard above) — checked directly against
`record/GOTCHAS.md`/`record/GOTCHAS_ARCHIVE.md`'s real pre-migration text
and found clean, 44 and 33 items respectively, matching the migration
commit's own claim exactly. Gotchas were not affected by this bug; only
`TODO.md`'s messier multi-shape bullet list was.

8 of the 54 restored this session, the shortest ones first (struck through
above): `prefork-catalogue-audit-table`, `team-repo-and-document-template`,
`consumer-source-names`,
`done-2026-09-06-a-missing-individual-source-is-no-longer-sil`,
`rpp-migration-audited`, `team-check-cites-retired-practice`,
`private-set-audit-branches`, `ledger-gap-shallow-clone-hardening` — all
`status: done` or `dropped` in the original text, verbatim from
`git show 9a08363b^:TODO.md`, links repointed, `precedent_check.py
--full-sweep` clean. 46 remained after this pass, corrected from an
earlier "44" said in chat by mis-subtracting 10 restored against a 54
total when only 8 had been restored at that point (the first 2 predate
this item and were never part of its own count).

2026-09-19, later the same day: the remaining 46 restored, using
`tools/todo_migrate.py --slug` in dry-run mode against the real
pre-migration text (for accurate `noted` dates via its own git
archaeology) as a first draft, then correcting `status`/`kind`/`decision`
fields by reading each item's own text — the tool defaults every
non-checkbox item to `status: open`, which is wrong for the 44 that are
actually done or dropped, so that correction was done by hand for all 46,
not trusted from the tool. All 46 verbatim from `git show
9a08363b^:TODO.md`, links and old-style `TODO.md`-anchor citations repointed
(several of the anchor citations resolve to other items in this same
batch), `precedent_check.py --full-sweep` and the full harness clean
before committing. This item is now closed; the two still-open
reconstructed items stand on their own, in their own files.
