---
slug:            gotcha-2026-10-07-a-ledger-written-in-a-worktree-misses-in-every-clone
status:          live
noted:           2026-10-07
severity:        notable
retired:         null
retires_when:    every consuming repository has taken the engine that ignores the .git probe
---
## Symptom

The full check spends minutes in `scripts-assert-properties` (the model
audit) although no model changed, and afterwards the model audit's ledger
shows as modified: every line rewritten, with only its `reads` different.

## Story

**2026-10-07, a consumer repository.** Its full check took about five
minutes, and one check, the model audit, took most of it. Run by hand the
audit skipped all 70 scripts; inside the check it re-ran all of them. Every
fact recorded an existence read of the repository's own `.git` entry, and
that entry is a directory in a clone but a file in a worktree. The landing
job runs in a worktree, so the ledger it committed said `file`; every clone
saw `dir`, missed every fact, re-ran every script and rewrote the ledger,
which the next landing flipped back.

## Fix

Since 2026-10-07 [tools/fact_ledger.py](../tools/fact_ledger.py) neither
records nor checks a read of `.git` itself (`checkout_layout()`); a ledger
already carrying one holds again with no re-run. The git state work can
see is recorded separately, as kind `g`. A repository still on the older
engine gets the fix with Update Vendors.
