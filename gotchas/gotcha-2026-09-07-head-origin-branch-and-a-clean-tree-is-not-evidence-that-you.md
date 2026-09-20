---
slug:            gotcha-2026-09-07-head-origin-branch-and-a-clean-tree-is-not-evidence-that-you
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

`HEAD == origin/<branch>` and a clean tree is NOT evidence that your

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **`HEAD == origin/<branch>` and a clean tree is NOT evidence that your
  work landed — it is the exact reading you get when your commit has been
  thrown away.** 2026-09-07: a session edited `TODO.md` while sitting on
  local `precedent-beta-v01`, committed there, then ran its usual
  push-and-merge sequence — `git push origin <feature-branch>` (which
  reported *"Everything up-to-date"*, correctly, because the feature branch
  had not moved), then
  `git checkout -B precedent-beta-v01 origin/precedent-beta-v01`, which
  **silently discarded the commit it had just made**. Its verification step
  then printed `HEAD=a7e503c beta=a7e503c dirty=0` and read as success:
  every ref matched, nothing was uncommitted, and the change was in neither
  the local tree nor the remote. A concurrent session's own push to the
  same branch made the hashes advance, which made the output look *more*
  convincing, not less.
  Two habits close it. **Commit on the working branch, never on the branch
  you are about to reset** — `git checkout -B` is a reset, and a
  scripted push-then-checkout sequence will run it whether or not you have
  uncommitted history there. And **verify the CONTENT, not the refs**:
  `git show origin/<branch>:<file> | grep <a phrase from your change>`
  answers the question `verify-postcondition` actually asks, where ref
  equality only answers a proxy for it. The first grep written that day
  matched a coincidental phrase already present elsewhere in the file and
  briefly confirmed the wrong thing — so grep for a phrase distinctive to
  your own edit, not a common one.
  Recovery, when it happens: the commit is not gone, it is unreferenced.
  `git reflog` still lists it (`commit: <your message>`), and
  `git cherry-pick <that hash>` onto the working branch restores it.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
