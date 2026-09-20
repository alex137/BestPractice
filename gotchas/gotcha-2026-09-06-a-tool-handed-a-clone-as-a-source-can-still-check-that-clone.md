---
slug:            gotcha-2026-09-06-a-tool-handed-a-clone-as-a-source-can-still-check-that-clone
status:          retired
noted:           2026-09-06
severity:        null
retired:         "2026-09-06"
retires_when:    null
---
## Symptom

A tool handed a clone as a *source* can still check that clone out from

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A tool handed a clone as a *source* can still check that clone out from
  under you.** `process/upstream/tools/checkin.py update <bestpractice-clone>`,
  run from a consuming repo, opened with `git checkout <default-branch>` and
  `git pull` **inside the clone you passed it**. On 2026-09-06 that silently
  moved a session's BestPractice checkout off `precedent-beta-v01` onto
  `main`, mid-session — and the command had already FAILED its own guard by
  then, so the mutation was pure collateral. The session noticed only because
  `templates/practice-set-*/` and thirty tools had vanished from a tree it had
  just been working in, and briefly read that as another session having deleted
  real work. `git status` was clean and `git log` looked sane, because nothing
  was damaged: it was simply a different branch. **If files you were just
  using disappear, check `git rev-parse --abbrev-ref HEAD` before concluding
  anything was lost** — and on a dirty tree the checkout would have failed and
  left the pull half-applied instead, which is worse. Fixed forward the same
  day: `update()` now reads the source ref with `git archive` (no checkout, no
  pull, no HEAD movement — the guarantee
  [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) already
  made explicitly), and mirrors the branch the consumer's own
  `process/manifest.json` records rather than the clone's configured default —
  every consumer tracks `precedent-beta-v01` while `main` is still the
  default, so the old code would have mirrored `main` over a beta-vendored
  tree, a wholesale revert dressed as an update. Both properties are asserted
  in [tools/verify_harness.py](../tools/verify_harness.py) with negative
  controls.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
