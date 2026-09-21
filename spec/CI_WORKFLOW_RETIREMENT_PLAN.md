---
title:         Retired CI workflow files stop costing minutes on their own
kind:          proposal
status:        accepted
opened:        2026-09-20
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Four asks from a live incident (a fresh usage-report pull found retired workflow files still billing real minutes) — auto-deletion when it is safe, and where detection/judgment belongs instead. All four built and tested: engine auto-delete on retirement (safe by hash match), an advisory check flagging a workflow file outside what the vendored engine tracks, and a very-deep-check pass enumerating the same candidates across every repo in scope. A live false positive, found and verified mid-session, is what made items 2-4 compare by content tracking rather than by filename."
---

# Retired CI workflow files stop costing minutes on their own

This is the plan Morgan asked for, mid-incident, about BestPractice (BP)
itself: *"can we update the BP system and code so that whenever a
workflow/action/yml is no longer in use, that the file is deleted?"* —
plus three follow-ons in the same conversation. It sits beside [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md),
which is about *minutes and cost*; this one is about the *mechanism* that
leaves a retired file on disk in the first place, which turned out to need
its own document once the four asks and the two follow-ons were all named.

## The incident this responds to

A fresh Actions usage-report CSV pull (2026-09-20) found several personal
repos still billing real minutes against workflow files
[spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md) had already named as
retired — not a one-time finding, the same shape twice, two weeks apart.
Disabling a workflow via the GitHub UI stops the billing immediately but
leaves the dead file in the tree, which is its own cost: confusion for the
next session, risk of accidental re-enablement, and a repo that no longer
tells the truth about what it runs. Morgan's own words: *"even though a
user can stop them on GitHub, it creates confusion and complexity and risk
and cost."*

## What's built (item 1 + migration parity)

**`tools/precedent_vendor_engine.py`'s `_remove_retired_ci_workflow_files`
now deletes a retired CI workflow file, not just reports it** — but only
when the file is still exactly what the manifest last recorded a hash for.
This mirrors `_remove_dropped_engine_files`'s existing safety rule for an
ordinary `tools/*.py` engine file: only ever delete a copy nobody has
touched since it was last checked.

Covered by `check_vendor_engine_retires_ci_workflow_files` in
`tools/verify_harness.py` (14 cases, all passing) — split into the case
that existed before (file present, hash mismatch → kept and reported) and
a new one this change adds (file present, hash matches → deleted and
reported).

**Migration and "Update Vendors" needed no separate fix.** Both route
through the same `refresh()` function this change already covers — a
brand-new install uses `seed`, which has nothing to retire yet, but an
existing repo taking an update or being migrated uses `status`/`refresh`
either way ([practices/vendor-update-runbook.md](../practices/vendor-update-runbook.md),
[spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)).
`practices/vendor-update-runbook.md`'s step 10 is updated to say so, and to
narrow its manual retired-file table to the two cases the automatic
mechanism still can't reach (below).

## Touched, precisely

Morgan approved "yes, but only if untouched" and then asked for enough
detail to actually think it through. This is that detail.

**"Untouched" means: the file's current on-disk SHA-256 still matches the
hash already recorded in this repo's own `tools/ENGINE_MANIFEST.json`
under `ci_workflows_sha256` for that exact path.** That recorded hash is
whatever the engine itself last wrote there — from the original
`record_ci_workflow_files()` call at install or refresh time, or a later
`record-ci` re-baseline. A match means "no change since the manifest last
looked," which is the identical standard `_ci_workflow_drift()` already
uses everywhere else in this file to mean "not drifted" — nothing weaker
was invented for this function.

**A file the manifest has no hash for at all is never a candidate, full
stop.** `_remove_retired_ci_workflow_files` only ever iterates paths that
are already keys in `ci_workflows_sha256`; a completely untracked file
never enters its `dropped` list. This is why the pre-2026-09-14 legacy
files (`light-check.yml`, `bestpractice-upstream-sync.yml`,
`status-claims-check.yml`, `platform-docs-check.yml`,
`unified-prompt-check.yml`, `practice-links-travel.yml`,
`sync-voice-guidelines-to-sound-human.yml`, `voice-guidelines-sync.yml`)
are untouched by this mechanism no matter what — they predate the tracking
system entirely, so there is no recorded hash to compare against. Those
still need [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md)'s Phase B sweep,
by hand, per repo.

**One real gap, left open rather than closed.** "Matches the recorded
hash" proves the file has not changed *since the manifest last checked it*
— it does not prove the file was never hand-edited at any point in its
history. A file can be hand-edited, then have that edit accepted as
correct via the `record-ci` subcommand (exactly what that subcommand is
for — re-baseline a hand-fixed file's hash without a `refresh --force`
overwriting the fix back to the generic template). If that same file's
workflow is *later* retired, `_remove_retired_ci_workflow_files` reads the
hand-edited-but-accepted content as "untouched" (it matches what was last
recorded) and deletes it — a hand-customized file, not the stock template.

This requires two separate events in sequence (a hand-edit accepted via
`record-ci`, then that exact workflow being retired afterward) and is the
same class of risk `_remove_dropped_engine_files` already accepts for
ordinary `tools/*.py` files with no separate protection either — so this
is not a new risk this change introduces, it is an existing, accepted
tradeoff extended to CI workflow files for consistency. **Closing it
completely would need the manifest to distinguish "hash recorded from the
original template" from "hash recorded because a hand-edit was accepted"**
— a `ci_workflows_hand_confirmed` marker set `record-ci` would populate,
checked here before ever deleting. Worth doing if this gap turns out to
matter in practice; not built now, since nobody has hit it yet and it would
add a second piece of manifest state to keep in sync for a compound
scenario that has not happened. Flagged here so it is a decision on record,
not a blind spot.

## What's built (items 2–4)

### Item 2 — `workflow-file-outside-vendoring`: detect, never auto-delete

**Detect and fail, not auto-remove — and never by filename.** Every other
check in this repo that looks at generated or vendored content gates and
does not fix (`views-drift`, `precedent-check`'s own non-`--strict`
leniency), and the false positive below (found while building this)
settled the second half: matching by name was the mistake, so this
compares by **tracking**, not content-hash-against-a-template as first
proposed — a consumer repo has no local copy of
`templates/github-actions/*.template` to hash against, but it always has
its own `tools/ENGINE_MANIFEST.json`.

`precedent_vendor_engine._untracked_ci_workflow_files()` returns every
`.github/workflows/*.yml`/`*.yaml` file on disk that this repo's manifest
does not list under `ci_workflow_files`, and that is not a known
`RETIRED_CI_WORKFLOW_FILES` entry. Registered in `precedent_check.py` as
`workflow-file-outside-vendoring` — `'tree'` scope,
**`advisory=True`** (never fails a build; the manifest only ever tracks
one file per kind by design, so it cannot tell a leftover from a
legitimate hand-authored check on its own), backed by a real practice file
([practices/workflow-file-outside-vendoring.md](../practices/workflow-file-outside-vendoring.md))
carrying `applies_to: [".github/workflows/**"]` so it fires reliably when
a workflow file is touched, not only within a rotation window. Carries a
declared-decline exemption (`ci_workflow_outside_vendoring_exempt` in
`precedent.json`, reason mandatory, same shape as `filename-separator`'s),
and flags a stale exemption entry rather than honoring it silently.
Covered by `check_workflow_file_outside_vendoring_detects_candidates` in
`tools/verify_harness.py` (10 cases).

**Scope note this design corrects:** `deep-check.yml` only runs on *this*
repository, which is already clean (verified 2026-09-20 — see
[spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md)). The actual leak lives in
personal repos running `precedent-check.yml.template`, not `deep-check.yml`
— this check is registered in `precedent_check.py` itself, which is
vendored into both, so it reaches consumer/source repos through the
ordinary "Update Vendors" refresh with no separate rollout step.

### Item 3/4 — a `very_deep_check.py` section, folded in rather than a second mechanism

Built as one new ledger section, `CI WORKFLOW FILES OUTSIDE VENDORING`,
rather than a wholly separate "very deep check for orphaned files" —
`very_deep_check.py`'s ledger already has a per-section keep/cheapen/retire
model built for exactly this kind of question, and a second top-level
command would be one more thing sessions have to remember to run.
**Scoped to workflow files** (not an open-ended "any orphaned file of any
sort" detector — no agreed definition exists yet for what "orphaned" means
for a doc, a script, or a generated file; widen later if a real second
case shows up).

`_workflow_liveness_scan()` reuses the *same*
`_untracked_ci_workflow_files()` item 2 calls — one implementation, not two
(Pass 2's own item 8: "are there two of anything that should be one?") —
over every repo in scope: this checkout plus every `FATAL_MISSING_LEVELS`
source reachable on disk, the same set `ORPHANS` already computes. **Scope
is stated honestly, not aspirationally**: no mechanism anywhere in
`very_deep_check.py` discovers a repo that *vendors from* this one, so
"any consuming repo" was never actually reachable — the printed section
header says so. Deliberately worded as *candidates*, never a verdict
(`_orphan_scan`'s existing four kinds are confident claims against a firm
list; this is not that, and reusing that wording would have been the exact
mistake below, repeated in the tool's own voice). Documented as
[practices/very-deep-check.md](../practices/very-deep-check.md) Pass 2's
new item 18, citing the incident below. Covered by
`check_very_deep_check_workflow_liveness_scan` in `tools/verify_harness.py`
(4 cases).

## The false positive that shaped items 2–4's design

The same conversation that produced this plan also produced a fleet-wide
sweep recommendation — light-check.yml classified as a retired duplicate of
`bestpractice-docs.yml` in eleven personal repos, based on matching
filenames against [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md)'s own
workflow-name table. Verified against one of those repos directly (not
relayed): its `light-check.yml` runs `tools/light_check.py`, a distinct,
required check (merge-conflict markers, invalid JSON/YAML/Python,
secret-shaped strings, broken doc links, vendored-tree integrity — that
repo's own `two-check-levels` light check), not a leftover copy of
anything BestPractice ever templated. **Filename matching was never
sufficient evidence; content is.** This is why items 2 and 3 above compare
content against a known-current template rather than checking a name
against a retired-name list, and why the remaining ten repos on that sweep
list still need the same per-repo verification before anything on them is
touched, not a blind repeat of the same shortcut.

## Status

- **Built and tested, all four items**: engine auto-delete on retirement
  (item 1), covering both "Update Vendors" and migration through the
  shared `refresh()` path; `workflow-file-outside-vendoring`, an advisory
  check in `precedent_check.py`/`precedent-check.yml.template` (item 2);
  and the `CI WORKFLOW FILES OUTSIDE VENDORING` section in
  `very_deep_check.py`, documented as Pass 2 item 18 (items 3-4).
- **Documented, open rather than closed**: the `record-ci`-then-retirement
  gap in "untouched," above.
- **Not this document's job**: the actual cost backlog — the
  pre-2026-09-14 legacy files still costing real money — still needs the
  per-repo, content-verified sweep [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md)'s
  Phase B describes. What's built here catches a *future* recurrence of
  this exact incident shape and surfaces candidates for that sweep; it
  does not replace doing the sweep.
