---
slug:            gotcha-2026-09-13-a-harness-run-that-overlaps-a-write-to-the-tree-fails-on-a-c
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A harness run that overlaps a write to the tree fails on a change belonging to no commit, and the count alone cannot tell you that.

## Story

**A harness run that overlaps a write to the tree fails on a change belonging
to no commit, and the count alone cannot tell you that.** `verify_harness.py`
reads the tree as it goes, over a hundred-odd checks and several minutes. On
2026-09-07 a run came back `1 failed` because a negative-control test had
briefly planted a failing check into `verify_harness.py` **while the run was
still in progress**. The failure was real, reproducible, and belonged to no
commit; two earlier runs and four later ones on the identical tree were clean.
`1 failed` renders identically whether it is self-inflicted, a real flake, or
a real bug. Run the harness to completion before editing anything it reads,
including its own controls, and never run two at once. The run recaps every
failure by name before the summary, so `tail -5` tells these apart.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
