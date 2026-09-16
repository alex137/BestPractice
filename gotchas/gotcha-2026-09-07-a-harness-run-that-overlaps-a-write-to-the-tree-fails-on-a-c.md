---
slug:            gotcha-2026-09-07-a-harness-run-that-overlaps-a-write-to-the-tree-fails-on-a-c
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

A harness run that overlaps a write to the tree fails on a change

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A harness run that overlaps a write to the tree fails on a change
  belonging to no commit, and the count alone cannot tell you that.**
  [tools/verify_harness.py](../tools/verify_harness.py) reads the tree as it
  goes, over more than a hundred checks and several minutes. On 2026-09-07 a
  run came back `1 failed` because a negative-control test — for a fix being
  made in that same session — had briefly planted a failing check into
  `verify_harness.py` while the run was still in progress. The failure was
  real, reproducible on demand, and belonged to no commit. Two earlier runs
  and four later ones on the identical tree were clean, which is what a
  genuine intermittent looks like too: `1 failed` renders identically
  whether it is self-inflicted, a real flake, or a real bug. Run the harness
  to completion before editing anything it reads, including its own control
  tests, and never run two at once. Since 2026-09-07 the run recaps every
  failure BY NAME immediately before the summary line, so `tail -5` is
  enough to tell these apart — before that it printed only the count, and a
  failure hundreds of lines up was lost the moment anyone re-ran.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
