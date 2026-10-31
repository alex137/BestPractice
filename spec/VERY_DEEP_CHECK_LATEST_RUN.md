---
title:         Very Deep Check, 2026-10-30 — What It Found and What Was Done
kind:          record
status:        closed
opened:        2026-10-30
closed:        2026-10-31
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The full account of the most recent very deep check: what it read, what each pass found, what was fixed and where, and what is left for a person. The next run rewrites it; git history keeps this one."
---
# Very Deep Check, 2026-10-30 — What It Found and What Was Done

The full record of the latest run (the next run rewrites this file; git
history keeps each earlier one). The ledger of every run is
[VERY_DEEP_CHECK.md](VERY_DEEP_CHECK.md); this is the long form behind its
"Current run" row.

**Scope:** asked for on the phrase, so BestPractice and the three sets it
declares (the individual set, the ladder set, the writing set). BestPractice
was read on `staging` at 1f476e78, which is `main` (d8b68a02) plus one open
item; each set on its own `main`. The session ran steps 1-5 itself, from
22:12 Buenos Aires time, then split the four passes across seven helpers in
worktrees of their own, from about 01:40 to about 03:15, and merged their
branches. Another session was running Update Vendors in another repository
throughout; it pushed nothing to these four.

**Two things went wrong during the run, and they are part of the record.**
The container's worker restarted twice in the first hour; nothing was lost,
because every step had been pushed or was re-readable from disk, and the
helpers were told to push after every commit for that reason. And two
helpers fixed the same two faults from different sides (the ladder's words
in universal's reply rules, and history counted by no-stale-counts); the
session kept one fix of each and dropped the other, as each merge commit
says.

## The Short Version

- **The full harness was red on `main` before any change**: one case of 865,
  a timing record still naming two tests deleted that morning. Fixed, and the
  push check now refuses that leftover (a1c59fe7).
- **About 65 findings across the four repositories, by the helpers' own
  counts; about 40 fixed in the run**, each code fix with a planted case that
  fails on the old code.
- **A session without the ladder set on disk was told the wrong landing
  branch** (`main`, skipping `staging`). Fixed at the cause (38ff2aa9).
- **The check found faults in itself again**: its freshness gate refused the
  branch its own practice tells a run to cut, its SECOND LISTS scan flagged a
  file that cites practices one per test, its stage table printed "none" for
  Produce, and it listed the `coord` board branch as unmeasurable work every
  run. All fixed.
- **Every pass is partial**, said here rather than rounded up; what was not
  reached is named under each pass and in
  [todo-2026-10-30-very-deep-check-findings](../todo/todo-2026-10-30-very-deep-check-findings.md),
  with Morgan's calls first.

## Pass 1 — Can an Adopter Install, Update and Move Practices?

Four rehearsals in scratch with a clean home directory and no `PRECEDENT_*`
variables: the guided install from a fresh clone of `main`, an update of a
consumer installed from `main` as of 2026-10-16, a migration from the
classic layout (steps 1, 3 and 7), and a practice move from an individual set
to a shared one. No real consumer was attached.

Fixed: a fresh install reported four code-owner practices as reachable by no
channel (the check stopped one hop short of `tools/bootstrap.sh`); the
installer's fill-in list named placeholders inside a generated block and an
escaped pattern; Update Vendors listed every changed upstream practice as a
file rewritten outside the vendored trees; a session start with
`tools/bootstrap.sh` missing printed nothing locally and failed in the cloud;
the developer guide's example still pointed at the retired
`process/upstream`; and a new individual set's report never said its
`identity.json` still held placeholders, so its first commit was refused.
Commits ccce6f4c, 8051886a, 2b8c4706.

Left: universal's `reply_check.json` reaches no installed repository (a call
for Morgan); migration steps 8 and 9, the other move directions, and every
harness other than Claude Code.

## Pass 2 — Do the Mechanisms Do What They Claim?

Answered: questions 1, 2, 3, 8, 8a, 18, 20, 21, 22, 24, 25 and 26. Partly:
4, 5, 6, 7, 11, 13, 14 and 19. Not attempted: 8b, 9, 10, 12, 15, 16, 17 and
27.

Fixed:

- **The landing branch.** The ladder was read from sets on disk, so a set not
  yet cloned looked like "off the ladder", and a session was told `main`. A
  missing declared set now answers `staging` and names the set to attach
  (38ff2aa9).
- **The freshness gate** accepts a branch cut from `origin/main`, as the
  practice says to cut one (20cd1dfa).
- **SECOND LISTS** asks for names close together, not a file that mentions
  most practices somewhere (cc18b26a); the section also went from about 76 s
  to about 3.5 s.
- **Universal's reply rules quoted the ladder's step labels**, which kept
  `set-words-stay-in-their-set` red here. The labels are gone from the
  examples, the Consider reading moved into the ladder set, and the reply
  checker now merges a set's partial requirement key by key (b8e29c5a, with
  the ladder's fab9724).
- **The writing set's two checks** run against BestPractice: the dated-name
  check now reads the untracked practice-hooks file the engine runs, and
  no-stale-counts skips `kind: record` documents, Story sections and
  frontmatter. BestPractice declares its record directories exempt, each
  with a reason and a root fix.
- **CHECKS BY STAGE** reads the moves tool a set supplies (f235db0e); a
  set-independence test planted its own guard instead of reading the ladder's
  file (a9273d86); the API budget's visibility audit skips names that occur
  only in tests, about 54 calls fewer (ecfdb860); four gotchas gained their
  Prevention answer and one its measured cause (59767bfe); an exclusion can
  match on a file's own `status:` (7bcd9b1c).
- **The branch sweep** treats `coord` and `result-cache` as machinery, never
  as unlanded work (3d1df9b8).

## Pass 3 — Does the Writing Hold Together?

BestPractice, about 60 percent: AGENTS.md read end to end (recorded in
`record/holistic-reads.json`), the tool's link, moved-claim, currency and
tier sections judged, and searches for retired names across every practice.
Fixed: AGENTS.md stated the landing rule three times and the light check
twice, and credited `--run-tests` to the wrong tool; three cross-repository
links; the developer, shared-set and Actions guides; the vendor-update
runbook's Rule naming three retired workflows; the document-project template
still telling every session to attach every source; two branch practices
pointing at a retired Boildown item; install-question counts; the practice
format's examples. Commits 81fa8a0b to 90af940d.

The sets, about two thirds: every Rule of the writing set's 19 and the
ladder's 36 active practices, each set's AGENTS.md, and both mechanical
sweeps in each. Fixed: TEMPLATE FRESHNESS no longer calls an optional
`reply_check.json` a gap; PRACTICES.md's frozen count and its false
"twenty"; the ladder's README, `promote` and source file brought up to the
2026-10-19 move; the ladder README's headings; the individual set's
`CLAUDE.md`; both shared sets' `.gitignore` taken to the template's shape.

## Pass 4 — Catalogue, Backlog, Branches

- **Branches:** every branch of every repository read. Nine carry unlanded
  work and all nine should go, each with its reason on the review page; none
  needs landing. Base-branch drift none; the endgame merge rehearsal clean,
  on full clones.
- **Catalogue:** the 29 pairs that read alike were judged and none merged;
  most are the ladder's stage practices, each owning its own command. The
  practices changed since 2026-10-17 were read in the writing set and in part
  of the ladder set. Fixed: `install` still told a session to copy the
  individual hook by hand; two ladder practices still said they lived in the
  individual set.
- **Backlog:** the 24 unblocked items worked: two closed on their own
  conditions, six asked, sixteen left with a reason. Three gotchas retired on
  their stated conditions; two incident entries answered.

## Morgan's Calls

Asked in the run's reply, each with the session's pick, at the top of
[todo-2026-10-30-very-deep-check-findings](../todo/todo-2026-10-30-very-deep-check-findings.md):
shipping universal's reply rules to adopters, re-approving three workflow
files, the `spec/` count exemption, the session-start deepen, two items to
close or park, the first person in the moved ladder practices, the ladder's
hardcoded file header, the writing set's hook here, the set generator's
first-run gap, splitting the four longest Rules, a one-time visibility probe,
the old receipts branch, and a real consumer for Pass 1.

## What Is Left

Everything not fixed, with the reason, is in
[todo-2026-10-30-very-deep-check-findings](../todo/todo-2026-10-30-very-deep-check-findings.md).
The largest gap is the test review (question 27), which needs a whole-suite
re-timing in a session of its own.

## The Harness, After the Fixes

Not re-run whole: the helpers shared four cores, so each ran only its own
cases by name. On the merged branch, every test the run added or changed
passed by name, the whole practice-check sweep came back with 0
violated, and the deep check passed. Each set's full sweep came back with 0
violated on its merged branch.

## Warnings

<!--vdc-embed:warnings: never hand-edit -- written by tools/very_deep_check.py's WARNINGS section; refresh with --refresh-warnings -->
Measured 2026-10-30: **2069 warning(s), 1844 still open** (neither fixed nor excluded). For comparison, open at the previous run: 2019.

| Source | Kind | Warnings | Open | Excluded for good | Excluded until a date |
|---|---|---|---|---|---|
| doc_lint | unlinked file reference | 2019 | 1795 | 224 | 0 |
| doc_lint | open item naming no blocker | 47 | 47 | 0 | 0 |
| doc_lint | process residue | 2 | 2 | 0 | 0 |
| precedent_check | enforcement-lives-with-its-practice | 1 | 0 | 0 | 1 |

**Exclusions decided this run: 0.**

Exclusions live in [tools/warning_exclusions.json](../tools/warning_exclusions.json); [tools/warning_review.py](../tools/warning_review.py) lists every open group.
<!--/vdc-embed:warnings-->

## Incidents

Pass 2, question 20: every incident filed since the run before this one,
asked what now catches it. **These verdicts were redone on 2026-10-31.** The
run's helper wrote one for each incident, but its scratch file was deleted
before they reached the repository, and nothing refused the account without
them. Morgan, 2026-10-31 (strength: decided): "Yes do the test review and
redo the incident verdicts. Act and booked and produce."

The list is INCIDENT COVERAGE's own: `_incident_coverage()` in
[tools/very_deep_check.py](../tools/very_deep_check.py), called directly for
the window since 2026-10-17 and cut at 2026-10-30, gives the same 62
incidents the run printed (the ledger's 2026-10-30 entry predates the change
that keeps the list). Each verdict comes from the incident's own text and a
search of `tools/` for what it names; every check named below was confirmed
to exist on `staging` at 2e8a3087. A lead the tool printed only because a
test shares a word with the Fix is said so where it misled.

**Counts: 43 covered, 14 judgment-only, 5 with a planted case owed.** The
owed ones are listed with a one-line spec under the Notes of
[todo-2026-10-30-very-deep-check-findings](../todo/todo-2026-10-30-very-deep-check-findings.md).

| Date | Incident | What catches it now | Verdict |
|---|---|---|---|
| 2026-10-17 | [gotcha-2026-10-17-auto-mode-refuses-a-shell-rewrite-of-a-hook-installer-that-edit-lets-through](../gotchas/gotcha-2026-10-17-auto-mode-refuses-a-shell-rewrite-of-a-hook-installer-that-edit-lets-through.md) | Nothing in this repository can: the refusal is Claude Code's auto-mode classifier judging a shell command. The Edit route loses nothing, and the file's Prevention paragraph says so. | judgment-only |
| 2026-10-17 | [gotcha-2026-10-17-the-harness-times-file-conflicts-on-every-merge](../gotchas/gotcha-2026-10-17-the-harness-times-file-conflicts-on-every-merge.md) | The merge driver, planted by `check_harness_times_merge_without_a_conflict`; a stale name by `check_as_ci_parts_partition_the_suite`; the push check refuses a deleted test that keeps its time. | covered |
| 2026-10-17 | [todo-2026-07-19-two-published-commits-carry-the-wrong-timezone-offset-and-pr](../todo/todo-2026-07-19-two-published-commits-carry-the-wrong-timezone-offset-and-pr.md) | Every push's quick tier runs `commit_dates` and `session_trailer` ([tools/precedent_push_check.py](../tools/precedent_push_check.py)); `session-trailer` is planted in `check_precedent_check_fires`, the offset in `check_commit_identity_prevents_the_wrong_offset`. | covered |
| 2026-10-17 | [todo-2026-09-06-nine-practices-carry-an-empty-why](../todo/todo-2026-09-06-nine-practices-carry-an-empty-why.md) | Nothing. `practice-file-shape` asks for a `## Why` heading and refuses only an empty `## Rule`; none is empty today. | planted case owed |
| 2026-10-17 | [todo-2026-09-06-relax-the-pinned-branch-hold](../todo/todo-2026-09-06-relax-the-pinned-branch-hold.md) | `check_update_refuses_while_a_branch_is_pinned`; the scheduled sync the hold guarded against is deleted. | covered |
| 2026-10-17 | [todo-2026-09-06-upstream-only-registries-ride-along-in-vendored-engine-files](../todo/todo-2026-09-06-upstream-only-registries-ride-along-in-vendored-engine-files.md) | Half of it: `check_doc_sync_reads_a_consumers_own_pairs`. Nothing runs [tools/model_audit.py](../tools/model_audit.py) as a vendored copy to show it reads the consumer's `tools/model_audit_host.json` rather than BestPractice's list. | planted case owed |
| 2026-10-17 | [todo-2026-09-06-wire-the-clone-free-engine-freshness-check-into-the-path-a-p](../todo/todo-2026-09-06-wire-the-clone-free-engine-freshness-check-into-the-path-a-p.md) | [tools/precedent_engine_freshness.py](../tools/precedent_engine_freshness.py) names a behind engine at session start and at the push and merge gates: `check_freshness_covers_every_declared_source`, `check_catalogue_hook_runs_the_freshness_notice`. | covered |
| 2026-10-17 | [todo-2026-09-07-audience-register-sharpening](../todo/todo-2026-09-07-audience-register-sharpening.md) | Nothing mechanical: how plain a reply reads is a judgment, and the rule is Morgan's own, in his individual set. | judgment-only |
| 2026-10-17 | [todo-2026-09-07-consumers-need-refresh-after-promotion](../todo/todo-2026-09-07-consumers-need-refresh-after-promotion.md) | `check_sync_refuses_to_lose_a_recorded_practice`: a sync never drops a practice the committed manifest records while its source is declared. | covered |
| 2026-10-17 | [todo-2026-09-07-the-branch-sweep-and-the-source-refresh-tool-disagree-about-](../todo/todo-2026-09-07-the-branch-sweep-and-the-source-refresh-tool-disagree-about-.md) | Nothing to catch: Morgan bounded the sweep to the checkout and its declared sources (2026-09-21), so the wider scope it asked for is withdrawn. | judgment-only |
| 2026-10-17 | [todo-2026-09-07-the-commit-identity-mechanism-does-not-reach-an-attached-sib](../todo/todo-2026-09-07-the-commit-identity-mechanism-does-not-reach-an-attached-sib.md) | The container-wide identity and zone: `check_commit_identity_derives_declared_timezone`, `check_commit_identity_prevents_the_wrong_offset`; `commit_author` in every push's quick tier. | covered |
| 2026-10-17 | [todo-2026-09-07-universal-code-cites-team-slug](../todo/todo-2026-09-07-universal-code-cites-team-slug.md) | `code-cites-practice`, planted in `check_precedent_check_fires`, for the anchored form. A bare mention stays unseen, as the check's own blind spot declares. | covered |
| 2026-10-17 | [todo-2026-09-08-level-repo-naming](../todo/todo-2026-09-08-level-repo-naming.md) | A naming decision, taken; the names it settled are held by the `source-naming` check. | judgment-only |
| 2026-10-17 | [todo-2026-09-08-small-calls-vs-brainstorm](../todo/todo-2026-09-08-small-calls-vs-brainstorm.md) | Two prose rules, now reconciled in universal `small-calls`. Whether a thread is a brainstorm is a reading, so nothing mechanical. | judgment-only |
| 2026-10-17 | [todo-2026-09-08-vdc-pass1-partial-again](../todo/todo-2026-09-08-vdc-pass1-partial-again.md) | How much of Pass 1 a run reaches is the run's call; later runs completed it. The account check holds Pass 2's questions, not Pass 1's rehearsals. | judgment-only |
| 2026-10-17 | [todo-2026-09-09-cross-owner-add-repo-push](../todo/todo-2026-09-09-cross-owner-add-repo-push.md) | A measurement of `add_repo`, an outside system, and answered: one session holds both owners' repositories and pushes here. | judgment-only |
| 2026-10-17 | [todo-2026-09-09-decision-strength-private-sources](../todo/todo-2026-09-09-decision-strength-private-sources.md) | `decision-strength`, registered in each set's vendored engine; a set whose engine falls behind is named by `check_freshness_covers_every_declared_source`. | covered |
| 2026-10-17 | [todo-2026-09-09-source-hook-drift](../todo/todo-2026-09-09-source-hook-drift.md) | A set's engine hooks are stubs running the vendored tool, kept current by Update Vendors: `check_bestpractice_engine_hooks_are_stubs`, `check_update_on_stubs_stages_nothing_under_claude`. | covered |
| 2026-10-17 | [todo-2026-09-10-private-owner-allowlist-inert](../todo/todo-2026-09-10-private-owner-allowlist-inert.md) | `check_public_tree_bakes_in_no_owner_account`; the leak gate, with the individual list, in every push's quick tier. | covered |
| 2026-10-17 | [todo-2026-09-10-retire-a-practice-source](../todo/todo-2026-09-10-retire-a-practice-source.md) | `check_retired_sets_are_dropped_only_when_nothing_is_lost`, `check_deleted_set_is_not_an_unresolved_source`. | covered |
| 2026-10-17 | [todo-2026-09-11-provenance-check-skips-in-a-source-set](../todo/todo-2026-09-11-provenance-check-skips-in-a-source-set.md) | `binds_publishers`, planted by `check_publisher_bound_checks_run_in_a_source_set`; the per-check remainder is an open item of its own. | covered |
| 2026-10-17 | [todo-2026-09-11-source-load-ceilings](../todo/todo-2026-09-11-source-load-ceilings.md) | Each set's `session-load-budget` against its own registry, `check_update_seeds_the_session_load_registry`, and this run's TOKEN BUDGETS, which fired a planted overage in all four repositories. | covered |
| 2026-10-17 | [todo-2026-09-13-universal-prose-does-not-reach-a-source-set](../todo/todo-2026-09-13-universal-prose-does-not-reach-a-source-set.md) | The very deep check runs `bootstrap_source.verify()` on each real set; `check_verify_reports_a_source_wired_for_fewer_moments` plants a mis-wired one. | covered |
| 2026-10-17 | [todo-2026-09-13-wire-individual-hook-in-existing-sets](../todo/todo-2026-09-13-wire-individual-hook-in-existing-sets.md) | The same `verify()` run and planted case. | covered |
| 2026-10-17 | [todo-2026-09-14-classic-install-wires-loader-hooks](../todo/todo-2026-09-14-classic-install-wires-loader-hooks.md) | The section 1 install is retired and refused: `check_practice_audit_loader`. | covered |
| 2026-10-17 | [todo-2026-09-14-close-detect-declaration-unpushed](../todo/todo-2026-09-14-close-detect-declaration-unpushed.md) | The git proxy refusing a push across owners, an outside system. Close detection itself is planted by `check_close_detection_fires_only_when_all_conditions_hold`. | judgment-only |
| 2026-10-17 | [todo-2026-09-14-engine-root-in-a-vendored-tree](../todo/todo-2026-09-14-engine-root-in-a-vendored-tree.md) | `check_vendored_engine_reads_the_consumer_root`; a vendored `process/upstream/` copy no longer carries `tools/`. | covered |
| 2026-10-17 | [todo-2026-09-14-github-budget-into-the-source-sets](../todo/todo-2026-09-14-github-budget-into-the-source-sets.md) | A file that arrives with the next engine refresh; a behind engine is named by `check_freshness_covers_every_declared_source`. | covered |
| 2026-10-17 | [todo-2026-09-14-no-history-checks-unpushed](../todo/todo-2026-09-14-no-history-checks-unpushed.md) | Nothing. Both identity checks skip an unborn HEAD with their own message, and their code says a test asserts that wording; none does, here or in the individual set. | planted case owed |
| 2026-10-17 | [todo-2026-09-14-one-unrelated-item-at-the-close](../todo/todo-2026-09-14-one-unrelated-item-at-the-close.md) | What a closing reply carries, a wording rule read by judgment. | judgment-only |
| 2026-10-17 | [todo-2026-09-14-project-maintainers-registry](../todo/todo-2026-09-14-project-maintainers-registry.md) | `check_codeowners_stamp_hashes_only_the_registry`, `check_bootstrapped_shared_set_carries_current_codeowners`. | covered |
| 2026-10-17 | [todo-2026-09-14-set-cannot-show-a-universal-practice](../todo/todo-2026-09-14-set-cannot-show-a-universal-practice.md) | Nothing in a set. `check_show_loads_a_practice_from_a_declared_source` plants a consumer, never a set whose own `practices/` lacks the universal ones. | planted case owed |
| 2026-10-17 | [todo-2026-09-14-team-sets-carry-no-engine-refresh-workflow](../todo/todo-2026-09-14-team-sets-carry-no-engine-refresh-workflow.md) | The finding underneath, a stale set engine nobody is told about, is named at session start and every push and merge gate (`check_freshness_covers_every_declared_source`). Sets run no workflow, by decision. | covered |
| 2026-10-17 | [todo-2026-09-15-go-merge-direct-edit-narrowing-check](../todo/todo-2026-09-15-go-merge-direct-edit-narrowing-check.md) | Overtaken: Go merge retired on 2026-09-20 and landing goes through `--land`. | judgment-only |
| 2026-10-17 | [todo-2026-09-18-no-stale-counts-undercounts-a-multi-source-catalogue](../todo/todo-2026-09-18-no-stale-counts-undercounts-a-multi-source-catalogue.md) | Cases H and I of the writing set's [test_no_stale_counts.sh](https://github.com/themorgan/precedent-shared-writing/blob/main/tools/checks/tests/test_no_stale_counts.sh). | covered |
| 2026-10-17 | [todo-2026-09-19-revisit-examples-vendoring](../todo/todo-2026-09-19-revisit-examples-vendoring.md) | A vendoring decision (Morgan, 2026-09-17); the friction measured was a one-time leftover. | judgment-only |
| 2026-10-17 | [todo-2026-09-21-branch-delete-links-not-yet-vendored-to-consumers](../todo/todo-2026-09-21-branch-delete-links-not-yet-vendored-to-consumers.md) | A rollout through Update Vendors into consumers this repository cannot read. | judgment-only |
| 2026-10-17 | [todo-2026-09-21-measure-the-billing-floor-fix-on-one-repo](../todo/todo-2026-09-21-measure-the-billing-floor-fix-on-one-repo.md) | Overtaken: the sets run no workflows. A workflow added unasked is refused by `ci_workflows` in every push's quick tier. | judgment-only |
| 2026-10-17 | [todo-2026-09-22-the-endgame-merge-rehearsal-is-red-in-ci-green-locally](../todo/todo-2026-09-22-the-endgame-merge-rehearsal-is-red-in-ci-green-locally.md) | `check_endgame_merge_finds_the_silent_drop` runs the rehearsal with no global git identity and plants a refused merge, which must read as an error. The run's findings listed it as owed; it is planted now. | covered |
| 2026-10-17 | [todo-2026-09-28-very-deep-check-pass-2-findings](../todo/todo-2026-09-28-very-deep-check-pass-2-findings.md) | `ci_workflows` (`ci-workflow-approved`) refuses a workflow whose content no approval matches. | covered |
| 2026-10-17 | [todo-2026-09-28-very-deep-check-pass-3-findings](../todo/todo-2026-09-28-very-deep-check-pass-3-findings.md) | Moot: the set whose copies outranked universal is retired and deleted. | judgment-only |
| 2026-10-17 | [todo-2026-10-14-delete-pre-staging-code](../todo/todo-2026-10-14-delete-pre-staging-code.md) | `check_update_vendors_reports_live_pre_staging_mentions`, `check_update_vendors_retires_pre_staging`. Whether it closed before its condition is a separate line in the findings item. | covered |
| 2026-10-17 | [todo-2026-10-17-debut-misses-what-only-main-lacks](../todo/todo-2026-10-17-debut-misses-what-only-main-lacks.md) | `check_debut_judges_the_change_against_main_too`, `check_main_test_pass_closes_the_issue`. | covered |
| 2026-10-17 | [todo-2026-10-17-very-deep-check-findings](../todo/todo-2026-10-17-very-deep-check-findings.md) | Each fix in its round shipped a case that fails on the old code. Six read by name: `check_public_consumer_does_not_materialize_private_text`, `check_stale_render_heal_never_overwrites_with_less`, `check_a_set_in_a_linked_worktree_does_not_load_itself_twice`, `check_a_person_with_no_individual_set_can_be_a_code_owner`, `check_commit_identity_leaves_a_laptops_global_config_alone`, and the ladder set's [test_landing_takes_a_pr.sh](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/checks/tests/test_landing_takes_a_pr.sh). The other bullets were not each re-read. | covered |
| 2026-10-18 | [gotcha-2026-10-18-a-pretooluse-hook-reads-a-transcript-that-lacks-the-call-it-guards](../gotchas/gotcha-2026-10-18-a-pretooluse-hook-reads-a-transcript-that-lacks-the-call-it-guards.md) | `check_answer_first_gate_holds_a_change_until_the_question_is_answered` plants a transcript that records the guarded call late and one that never does. The tool's lead, `check_reply_check_keeps_quiet_while_a_batch_runs`, only shares the word `tool_use_id`. | covered |
| 2026-10-18 | [gotcha-2026-10-18-no-check-runs-on-a-pull-request-into-staging](../gotchas/gotcha-2026-10-18-no-check-runs-on-a-pull-request-into-staging.md) | `check_land_refusal_says_whether_a_pull_request_gets_checks`; the gotcha retired on 2026-10-31. | covered |
| 2026-10-18 | [gotcha-2026-10-18-the-answer-first-gate-cannot-see-text-written-between-tool-calls](../gotchas/gotcha-2026-10-18-the-answer-first-gate-cannot-see-text-written-between-tool-calls.md) | `check_answer_first_gate_holds_a_change_until_the_question_is_answered` holds the gate to one refusal per question. The root, a long mid-turn text never written to the transcript, is Claude Code's. | covered |
| 2026-10-18 | [todo-2026-10-18-harness-branch-named-in-instructions-not-caught](../todo/todo-2026-10-18-harness-branch-named-in-instructions-not-caught.md) | The ladder set's [test_session_branch_name.sh](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/checks/tests/test_session_branch_name.sh). | covered |
| 2026-10-18 | [todo-2026-10-18-landing-guard-refusal-promises-checks](../todo/todo-2026-10-18-landing-guard-refusal-promises-checks.md) | The ladder set's test_landing_takes_a_pr.sh, and `check_land_refusal_says_whether_a_pull_request_gets_checks` here. | covered |
| 2026-10-19 | [gotcha-2026-10-19-a-fixture-that-fakes-home-keeps-the-real-attach-folder](../gotchas/gotcha-2026-10-19-a-fixture-that-fakes-home-keeps-the-real-attach-folder.md) | `check_one_tree_per_source_whichever_way_links_run`, whose case "a tree in the home folder that is another repository is never adopted" fails on the old code. | covered |
| 2026-10-19 | [gotcha-2026-10-19-an-advisory-reply-requirement-is-never-shown-to-anyone](../gotchas/gotcha-2026-10-19-an-advisory-reply-requirement-is-never-shown-to-anyone.md) | `check_turn_start_names_what_the_last_reply_left_out` (an advisory requirement is named at the next turn); `check_cloud_setup_script_writes_each_hook_once` (the Stop entry). | covered |
| 2026-10-19 | [todo-2026-10-19-deferred-main-run-reads-as-passed](../todo/todo-2026-10-19-deferred-main-run-reads-as-passed.md) | `check_main_test_cadence`. | covered |
| 2026-10-19 | [todo-2026-10-19-rule-links-enforcement-lives-in-the-engine](../todo/todo-2026-10-19-rule-links-enforcement-lives-in-the-engine.md) | `enforcement-lives-with-its-practice`; `check_reply_check_refuses_an_unlinked_branch_or_file` tests the machinery under a made-up name. | covered |
| 2026-10-20 | [todo-2026-10-20-individual-set-charged-to-each-repo-ceiling](../todo/todo-2026-10-20-individual-set-charged-to-each-repo-ceiling.md) | `check_individual_set_is_charged_to_its_own_budget`. | covered |
| 2026-10-20 | [todo-2026-10-20-ladder-set-names-the-boildown-moments](../todo/todo-2026-10-20-ladder-set-names-the-boildown-moments.md) | `boildown-moments-named`, planted in `check_precedent_check_fires` and held by `check_boildown_moments_named`, and run by each set's vendored engine. | covered |
| 2026-10-27 | [gotcha-2026-10-27-a-citation-of-a-set-practice-passes-locally-and-fails-on-github](../gotchas/gotcha-2026-10-27-a-citation-of-a-set-practice-passes-locally-and-fails-on-github.md) | `code-cites-practice` at the Debut and in GitHub's test after a Produce, never before a push. Nothing plants the set-on-disk direction, and nothing catches a relative link to an untracked file a set installs before GitHub does. | planted case owed |
| 2026-10-27 | [todo-2026-10-20-branch-page-data-in-a-file](../todo/todo-2026-10-20-branch-page-data-in-a-file.md) | `check_branch_cleanup_refresh_writes_only_what_it_checked`, `check_branch_cleanup_page_script_parses`. | covered |
| 2026-10-28 | [todo-2026-10-20-set-tests-and-engine-contract](../todo/todo-2026-10-20-set-tests-and-engine-contract.md) | `bound-set-tool-calls-only-declared-names` and `reply-rules-hold-their-examples`, held by `check_bound_set_tools_and_reply_examples_are_held_in_any_set`; `check_update_runs_a_set_s_own_tests_after_an_engine_refresh`. | covered |
| 2026-10-29 | [gotcha-2026-10-29-a-note-line-that-reports-a-state-lands-in-the-upstream-review](../gotchas/gotcha-2026-10-29-a-note-line-that-reports-a-state-lands-in-the-upstream-review.md) | `check_refresh_names_an_in_place_hook_no_engine_path_keeps`, which runs only where the ladder set is installed. | covered |
| 2026-10-29 | [todo-2026-10-29-landing-runs-the-tests-it-reaches](../todo/todo-2026-10-29-landing-runs-the-tests-it-reaches.md) | `check_a_landing_names_the_checks_it_reaches`, `check_harness_reach_selects_what_a_change_reaches`. Running the checks a landing prints is that session's to do. | covered |
| 2026-10-29 | [todo-2026-10-29-staging-suite-and-reader-own-files](../todo/todo-2026-10-29-staging-suite-and-reader-own-files.md) | Issue 2: `check_doc_lint_fires` (the reader's own `AGENTS.md` in a shipped practice). Issue 1 was decided: the daily run stays as it is. | covered |
| 2026-10-30 | [todo-2026-10-30-vendor-update-leftovers-in-the-ladder-and-individual-sets](../todo/todo-2026-10-30-vendor-update-leftovers-in-the-ladder-and-individual-sets.md) | The ladder set's test_landing_takes_a_pr.sh (a file already on main) and [ladder_branches_cases.py](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/checks/tests/ladder_branches_cases.py) (PROMOTE REFUSED); `check_session_start_lists_a_red_main_first` (the cause leads the line). | covered |

## Checks by stage

<!--vdc-embed:checks-by-stage: never hand-edit -- written by tools/very_deep_check.py's CHECKS BY STAGE section -->
Read from each repository's own push check and branch tool by this run (`tools/very_deep_check.py`, CHECKS BY STAGE). Before a push to staging or main only the quick tier may run: the bare essentials and the leak gate (Morgan, 2026-10-16 and 2026-10-17).

### this checkout

| Stage | Before | After |
|---|---|---|
| Booked, onto staging | basic tier (a plain push: basic) | nothing automatic; GitHub: none |
| Produce, into main | none tier (`--full` on request: none; a plain push, or a pull request that is not a fast move's copy: basic) | GitHub: deep-check.yml (pull request into it), deep-check.yml (push), leak-gate.yml (push); else the full local suite on main |
| Debut, on staging | nothing | nothing (it is the full tier and moves nothing) |

The quick tier (6): `leak_gate` 16 s, `leak_gate_commits` 4 s, `doc_lint` 1 s, `commit_author` 0 s, `commit_dates` 0 s, `session_trailer` 0 s.

The full tier adds: `verify_harness`, `precedent_check`, `doc_sync`, `deep_check`.

Clean: nothing but the quick tier runs before a push.

### precedent-individual

| Stage | Before | After |
|---|---|---|
| Booked, onto staging | basic tier (a plain push: basic) | nothing automatic; GitHub: none |
| Produce, into main | none tier (`--full` on request: none; a plain push, or a pull request that is not a fast move's copy: basic) | GitHub: none; else the full local suite on main |
| Debut, on staging | nothing | nothing (it is the full tier and moves nothing) |

The quick tier (10): `build_views` 1 s, `leak_gate` 16 s, `leak_gate_commits` 4 s, `doc_lint` 1 s, `generated_files` 2 s, `rename_links` 0 s, `ci_workflows` 0 s, `commit_author` 0 s, `commit_dates` 0 s, `session_trailer` 0 s.

The full tier adds: `precedent_check`, `deep_check`, `consumer_shape`.

Clean: nothing but the quick tier runs before a push.

### precedent-shared-writing

| Stage | Before | After |
|---|---|---|
| Booked, onto staging | basic tier (a plain push: basic) | nothing automatic; GitHub: none |
| Produce, into main | none tier (`--full` on request: none; a plain push, or a pull request that is not a fast move's copy: basic) | GitHub: none; else the full local suite on main |
| Debut, on staging | nothing | nothing (it is the full tier and moves nothing) |

The quick tier (10): `build_views` 1 s, `leak_gate` 16 s, `leak_gate_commits` 4 s, `doc_lint` 1 s, `generated_files` 2 s, `rename_links` 0 s, `ci_workflows` 0 s, `commit_author` 0 s, `commit_dates` 0 s, `session_trailer` 0 s.

The full tier adds: `precedent_check`, `deep_check`, `consumer_shape`.

Clean: nothing but the quick tier runs before a push.

### precedent-shared-ladder

| Stage | Before | After |
|---|---|---|
| Booked, onto staging | basic tier (a plain push: basic) | nothing automatic; GitHub: none |
| Produce, into main | none tier (`--full` on request: none; a plain push, or a pull request that is not a fast move's copy: basic) | GitHub: none; else the full local suite on main |
| Debut, on staging | nothing | nothing (it is the full tier and moves nothing) |

The quick tier (10): `build_views` 1 s, `leak_gate` 16 s, `leak_gate_commits` 4 s, `doc_lint` 1 s, `generated_files` 2 s, `rename_links` 0 s, `ci_workflows` 0 s, `commit_author` 0 s, `commit_dates` 0 s, `session_trailer` 0 s.

The full tier adds: `precedent_check`, `deep_check`, `consumer_shape`.

Clean: nothing but the quick tier runs before a push.
<!--/vdc-embed:checks-by-stage-->

## Token budgets

<!--vdc-embed:token-budgets: never hand-edit -- written by tools/very_deep_check.py's TOKEN BUDGETS section -->
Measured 2026-10-30.

**Every budget is under its limit and approved, and every check fired on a planted overage.**

| Repo | Budget | Measured | Limit | Used | Approved max | Status |
|---|---|---:|---:|---:|---:|---|
| BestPractice | session-load total | 8,140 | 10,000 | 81% | 10,000 | ok; AGENTS.md 5,768 + CLAUDE.md 55 + .precedent/SESSION_PRACTICES.md 2,317 |
| a private individual set | session-load total | 5,868 | 10,000 | 59% | 10,000 | ok; AGENTS.md 1,160 + CLAUDE.md 92 + .precedent/SESSION_PRACTICES.md 4,616 |
| precedent-shared-writing | session-load total | 6,059 | 10,000 | 61% | 10,000 | ok; AGENTS.md 1,102 + CLAUDE.md 111 + .precedent/SESSION_PRACTICES.md 4,846 |
| precedent-shared-ladder | session-load total | 6,252 | 10,000 | 63% | 10,000 | ok; AGENTS.md 1,352 + CLAUDE.md 111 + .precedent/SESSION_PRACTICES.md 4,789 |

**Do the checks fire?** Each repo's own check, run on a throwaway copy with the budget planted under what it measures (each one clean first):

| Repo | Planted | Check | Result |
|---|---|---|---|
| BestPractice | session-load total lowered under its size | `session-load-budget` | fired |
| BestPractice | session-load total raised 5,000 with no approval | `budget-within-approval` | fired |
| a private individual set | session-load total lowered under its size | `session-load-budget` | fired |
| a private individual set | session-load total raised 5,000 with no approval | `budget-within-approval` | fired |
| precedent-shared-writing | session-load total lowered under its size | `session-load-budget` | fired |
| precedent-shared-writing | session-load total raised 5,000 with no approval | `budget-within-approval` | fired |
| precedent-shared-ladder | session-load total lowered under its size | `session-load-budget` | fired |
| precedent-shared-ladder | session-load total raised 5,000 with no approval | `budget-within-approval` | fired |

Rough tokens (words x 1.3). "near" is within the registry's `headroom_floor_pct` of the limit.
<!--/vdc-embed:token-budgets-->

## Set independence

<!--vdc-embed:set-independence: never hand-edit -- written by tools/very_deep_check.py's SET INDEPENDENCE section -->
Read by this run from `python3 tools/precedent_check.py --only enforcement-lives-with-its-practice` (`tools/very_deep_check.py`, SET INDEPENDENCE). A practice set's rules, checks and tests live in the set; BestPractice runs them and never names one set's rule in its code, its tests or a universal practice.

**To fix in this pass: 1.**

- `tools/verify_harness.py`: names the set precedent-shared-ladder in a test: a set's practices are tested in the set, beside the check; an engine test uses a planted name

**Held in the engine on purpose: 0** (the plan of record's part 3, [ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md](ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md), waiting on the person's go-ahead): none.
<!--/vdc-embed:set-independence-->

## Test review

<!--vdc-embed:test-review: never hand-edit -- written by tools/very_deep_check.py's TEST WORTH section; refresh with --refresh-tests -->
Every test each repository owns, what it costs and whether it is still worth that (`tools/very_deep_check.py`, TEST WORTH; [test_review.py](../tools/test_review.py)). Verdicts live in each repository's `tools/test_verdicts.json`.

### this checkout

870 test(s), 865 timed, 3660 s recorded in all. Judged: 0. Never judged: 870. To judge again: 0. Cheapen or retire owed: 0. Carrying a lead: 58. Times measured 2026-10-09, 4 cores, --as-ci; tests added since by --record-new-times, each scaled to this basis.

| Importance | Tests | Seconds |
|---|---:|---:|
| not judged yet | 870 | 3660 |

The slowest, against their importance:

| Test | Seconds | Verdict | Importance |
|---|---:|---|---|
| `check_precedent_check_fires` | 777.5 | not judged | - |
| `check_update_vendors_leaves_the_copy_its_record_names` | 160.1 | not judged | - |
| `check_unlanded_work_is_reported_before_the_passes` | 120.6 | not judged | - |
| `check_send_carries_a_local_edit_upstream` | 102.3 | not judged | - |
| `check_update_vendors_is_one_command` | 92.1 | not judged | - |
| `check_kept_agents_md_divergence_is_recorded` | 82.8 | not judged | - |
| `check_main_test_repo_setting` | 71.0 | not judged | - |
| `check_update_vendors_reruns_pinned_to_its_first_commit` | 70.2 | not judged | - |
| `check_changed_files_only_judges_the_change` | 65.0 | not judged | - |
| `check_update_vendors_declined_catalogue_copy_is_upstreams` | 64.6 | not judged | - |
| `check_update_vendors_survives_an_upstream_deletion` | 53.3 | not judged | - |
| `check_update_vendors_resolves_local_edits` | 50.2 | not judged | - |
| `check_update_vendors_resolves_hook_and_engine_path_edits` | 49.0 | not judged | - |
| `check_update_vendors_redecided_decline_sticks` | 48.7 | not judged | - |
| `check_update_rerun_after_failed_takes_its_own_output` | 48.5 | not judged | - |

Carrying a lead and not yet judged (58):

- `check_source_precedence`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_cross_source_resident_budget`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_doc_lint_fires`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_stale_freshness_also_says_delete_it`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_resident_rule_links_are_placed_for_the_block`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_source_names_detects_a_rename`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_update_vendors_retires_the_team_level_word`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_dropped_set_and_proxy_and_template_refs`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_dropped_set_prose_successors_and_families`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_session_practices_load_without_publishing`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_update_vendors_lets_an_override_through_the_view_sync`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_update_vendors_repoints_renamed_shared_sets`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_run_all_trusts_only_unchanged_shipped_tests`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_engine_written_leftovers_leave_by_content`: names tools/precedent_others_did.py (decommissioned)
- `check_legacy_leftovers_retired_by_content`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_precedent_check_fires`: names practice brief-it (deduplicated); names the word 'team (as a level)' (retired 2026-09-18)
- `check_retired_words_are_found_and_history_is_left`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_loader_block_advertises_only_live_channels`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_source_sets_can_learn_they_are_stale`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_materialize_bridges_loader`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_shipped_tests_name_their_owner_and_fail_at_home`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_materialize_carries_harness_adapters`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_practice_ships_its_files`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_show_flags_unreachable_materialized_source`: names the word 'team (as a level)' (retired 2026-09-18)
- `check_sync_refuses_to_lose_a_recorded_practice`: names the word 'team (as a level)' (retired 2026-09-18)
- and 33 more

### precedent-individual

3 test(s), 0 timed, 0 s recorded in all. Judged: 0. Never judged: 3. To judge again: 0. Cheapen or retire owed: 0. Carrying a lead: 1.

| Importance | Tests | Seconds |
|---|---:|---:|
| not judged yet | 3 | 0 |

Carrying a lead and not yet judged (1):

- `tools/checks/tests/test_file_header.sh`: names the pre-staging tier below staging (retired 2026-10-14)

### precedent-shared-writing

7 test(s), 0 timed, 0 s recorded in all. Judged: 0. Never judged: 7. To judge again: 0. Cheapen or retire owed: 0. Carrying a lead: 1.

| Importance | Tests | Seconds |
|---|---:|---:|
| not judged yet | 7 | 0 |

Carrying a lead and not yet judged (1):

- `tools/checks/tests/test_no_stale_counts.sh`: names the word 'team (as a level)' (retired 2026-09-18)

### precedent-shared-ladder

9 test(s), 0 timed, 0 s recorded in all. Judged: 0. Never judged: 9. To judge again: 0. Cheapen or retire owed: 0. Carrying a lead: 0.

| Importance | Tests | Seconds |
|---|---:|---:|
| not judged yet | 9 | 0 |
<!--/vdc-embed:test-review-->
