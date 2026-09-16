---
slug:              todo-2026-09-07-consumers-need-refresh-after-promotion
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the refresh itself belongs in each consumer, run under that repo's own gates — that consumer has an open session and its own deep check, and doing it from here would be the unreviewed cross-repo change this run has been finding all day. The engine-side guard is blocked on a design call (which baseli"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            null
---
## What

- <a id="consumers-need-refresh-after-promotion"></a>**A consumer that vendors an OLD universal catalogue loses a promoted
  practice at its next sync, silently.** Found 2026-09-07, immediately after
  promoting `fail-gracefully` and `bold-key-phrases` from
  `precedent-team-repo-maintenance` to universal.

  The shape: a consuming repo vendors universal as tracked files at a pinned
  commit, and resolves its team source live. Promotion deletes the practice
  from the team set (correctly — that is what stops the same-level
  collision) and adds it to universal. A consumer whose vendored universal
  copy predates the promotion then has it in **neither** source, and the next
  [precedent_sync_views.py](../tools/precedent_sync_views.py) run rewrites
  `practices/` from what resolves — removing both rules from its catalogue
  with nothing reporting a loss, because a practice that no longer resolves
  is not a violation of anything.

  **Verified concrete, not predicted.** A private consumer repo
  vendors universal at `process/upstream`, pinned to `c7a1436` — the commit
  before the promotion. Its `process/upstream/practices/` carries neither
  practice; its materialized `practices/` still carries both, from the team
  source that no longer has them. It has not re-synced yet, so nothing is
  lost — the window is open, not closed.

  **The remedy is a vendored-catalogue refresh in each consumer**, before
  its next sync, not a change here. `process/upstream/tools/checkin.py
  update <bestpractice-clone>` is the mechanism.

  **The general lesson is bigger than these two practices**: promoting or
  moving a practice between levels is a change every consumer must be
  brought forward for, and today nothing tells a consumer that the ground
  moved. Worth considering whether
  [precedent_sync_views.py](../tools/precedent_sync_views.py) should refuse —
  or at minimum say loudly — when a sync would DELETE a practice that its
  committed `MANIFEST.json` records as present, rather than doing it
  quietly. That is the same "could not check versus checked and found
  nothing" line [fail-gracefully](../practices/fail-gracefully.md) draws.

  **CORRECTION, 2026-09-07: the loss is not silent, and this item said it
  was.** `precedent_sync_views.py --check` already names each one precisely —
  *"practices/fail-gracefully.md is not produced by any declared source — a
  sync would delete it (practice)"* — verified by running it against the real
  consumer. What is true is narrower: a **real** sync (`materialize()` does
  `shutil.rmtree(practices_dir)` and rewrites) announces nothing, so a
  session that syncs without `--check` and does not read the resulting
  `git status` sees no notice. The removal is visible; nothing puts it in
  front of you at the moment it happens.

  **The obvious fix was attempted and backed out, and that is worth knowing
  before someone tries it again.** Making `sync_views` refuse a removal
  unless `--allow-removals` is passed: implemented, tested against the real
  consumer (refused, naming both practices, nothing written; proceeded with
  the flag). It then failed the harness in **three separate legitimate
  flows** — a repo declaring `visibility: public`, which withholds
  private-source practices by design; a sync already carrying
  `--allow-missing-sources`, which is the same acknowledgement asked twice;
  and a cross-source fixture that re-syncs after its sources change. Each was
  fixable in isolation and a fourth appeared each time. That is the "fires on
  correct work" failure this project has measured the cost of, so the guard
  was reverted rather than shipped tired.

  What the attempt established, for whoever picks it up: the signal exists
  and is exact (`drift()` already computes it), the flag plumbing is simple,
  and **the whole difficulty is telling a stale-source removal from a
  deliberate one**. Withholding, a dropped source, and an upstream retirement
  are all legitimate removals that look identical to the tree. A workable
  version probably compares against the *committed* `MANIFEST.json` rather
  than the working tree, so it asks "did the repository lose a rule it had
  recorded?" instead of "does the tree differ from the plan?" — that was not
  tried.

  **BUILT, 2026-09-07, on the committed-manifest baseline.** A sync now
  refuses to write when it would remove a practice this repository's
  **committed `MANIFEST.json`** records and whose source is **still
  declared** — the stale-vendor case, and the one this item is about. The
  baseline is the whole difference from the reverted attempt: "the tree
  differs from the plan" is true constantly, while "this repository
  published a catalogue containing rule X and X is about to vanish" is
  narrow enough to refuse on. Four consequences, each closing one of the
  false positives that killed the first version:

  - No committed manifest — a fresh install, a scratch fixture — and there
    is no baseline, so the guard does not apply.
  - A **withheld** slug is excluded: a public repo keeps private-level text
    out of its tracked tree deliberately.
  - A slug whose recorded **source name is not among the declared ones** is
    refused as well, since 2026-09-14. It used to be reported and written,
    on the reasoning that dropping a source is a decision somebody just
    made -- which is true of a drop and false of a rename. See item 92.
  - A slug whose source **is** still declared, and which that source no
    longer produces, is refused. `--allow-removals` overrides it.

  Verified against the real consumer (refused, naming both practices and
  their source, nothing written) and covered by a 7-case harness test.

  **Two mistakes in building it, both worth keeping.** The first version read
  `res['practices']` as a list of records when it is a **dict keyed by slug**
  — so it computed an empty set, and the "cannot establish it, return empty"
  fallback then swallowed that, leaving the guard silently inert while
  reporting nothing. It passed its own positive control that way. A fallback
  meant to fail safe is what hid it; the unreadable case now says so out loud
  instead. Second, the test fixture deleted the team source's only practice,
  which tripped a *different*, pre-existing guard (a source gone completely
  empty) — so the fixture proved the wrong thing, just as confidently.

  **Blocked on:** the refresh itself belongs in each consumer, run under
  that repo's own gates — that consumer has an open session and its own
  deep check, and doing it from here would be the unreviewed cross-repo
  change this run has been finding all day. The engine-side guard is blocked
  on a design call (which baseline to compare against), not on the work.

## How It Closes

Not open until: the refresh itself belongs in each consumer, run under that repo's own gates — that consumer has an open session and its own deep check, and doing it from here would be the unreviewed cross-repo change this run has been finding all day. The engine-side guard is blocked on a design call (which baseli

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
