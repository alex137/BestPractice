---
slug:              todo-2026-10-08-a-consumer-cannot-tell-its-copy-is-stale-without-a-clone
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        Morgan's call on changing process/manifest.json's format
noted:             2026-10-08
closed:            null
---
## What

A consuming repository finished Update Vendors with a vendored copy that was
not the commit its records named
([the gotcha](../gotchas/gotcha-2026-10-08-a-vendored-copy-can-claim-a-commit-it-does-not-hold.md)).
Update Vendors now checks that before it says DONE, so the copy is right
when the update ends. Nothing in the consumer itself can tell, afterwards,
that the copy has drifted from its record: `process/manifest.json` records
the commit, and per-file hashes only for adopted files; the engine manifest
covers engine files only. Any check needs a BestPractice clone to compare
with.

## Proposed

`checkin.py record` stores a fingerprint of the copy as it stands after the
local-edit rules have run, and a consumer check (needing no clone) compares
the copy with it, exempting kept edits by name. This changes
`process/manifest.json`'s format, which every consumer vendors, so it is
Morgan's to decide, not a session's.

## How It Closes

Morgan decides: built (and a consumer whose copy drifts after an update is
refused by its own check), or dropped with his reason.
