---
slug:            gotcha-2026-09-05-a-scope-tree-check-in-tools-precedentcheck-py-can-silently
status:          retired
noted:           2026-09-05
severity:        null
retired:         "2026-09-05"
retires_when:    null
---
## Symptom

A `scope: 'tree'` check in `tools/precedent_check.py` can silently

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A `scope: 'tree'` check in `tools/precedent_check.py` can silently
  report a false *pass* on an under-fetched local clone, not just degrade
  loudly like the two entries above.** `parallel-artifact-ledger` walks
  `git log --no-merges -- <member-dir>` for each harness-adapter directory
  and fails on any commit whose hash isn't in `templates/harness/LEDGER.md`.
  2026-09-05: a local run reported `0 violated`, but GitHub Actions' own
  checkout of the exact same commit reported a real violation (twice) —
  `templates/harness/LEDGER.md` was missing a row for a commit from
  five weeks before the ledger file existed. The local clone's history
  simply didn't reach back far enough for `git log` to find that commit at
  all, so the check had nothing to flag — an empty result read as "clean,"
  not as "couldn't check." `git fetch --depth=1000 origin <branch>` (or
  deeper — this check needs the *entire* history of the directories it
  walks, not just enough for the current branch's own diff) before
  trusting a clean local run of any `scope: 'tree'` check.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
