---
slug:            gotcha-2026-09-13-head-origin-branch-and-a-clean-tree-is-not-evidence-that-you
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

`HEAD == origin/<branch>` and a clean tree is NOT evidence that your work landed — it is the exact reading you get when your commit has been thrown away.

## Story

**`HEAD == origin/<branch>` and a clean tree is NOT evidence that your work
landed — it is the exact reading you get when your commit has been thrown
away.** 2026-09-07: a session committed on local `precedent-beta-v01`, then
ran `git checkout -B precedent-beta-v01 origin/precedent-beta-v01`, which
**silently discarded the commit it had just made**. Its verification printed
`HEAD=a7e503c beta=a7e503c dirty=0` and read as success: every ref matched,
nothing was uncommitted, and the change was in neither the tree nor the
remote. A concurrent session's push made the hashes advance, which made the
output look *more* convincing. **Commit on the working branch, never on the
branch you are about to reset** — `git checkout -B` is a reset. And **verify
the CONTENT, not the refs**: `git show origin/<branch>:<file> | grep <a phrase
from your change>`, grepping for a phrase distinctive to your own edit rather
than a common one. Recovery: the commit is unreferenced, not gone — `git
reflog` lists it and `git cherry-pick` restores it.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
