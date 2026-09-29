---
slug:              todo-2026-09-29-received-practice-edits-are-overwritten
kind:              analysis
domain:            vendoring
severity:          medium
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "no per-file record of what a sync wrote: MANIFEST.json names each received practice and check and its source, but not the commit or content it was written from, so there is no BASE to merge a local edit against"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-29
closed:            null
---
## What

**A local edit to a practice or check a consumer received through
`MANIFEST.json` is overwritten, silently, on every sync.** The materializer
rebuilds those files from the live sources each time, and nothing compares
what is on disk with what it last wrote. That is worse than the refusal the
engine and `process/upstream/` layers gave before
[spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md](../spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md):
there, a person at least heard about the edit.

That plan resolves local edits in two layers (engine files in `tools/`, and
`process/upstream/`) and left this one out of version 1 because the
three-way merge it uses needs BASE, the text the file was received as, and
nothing records it here.

## What would close it

1. Record, per materialized file, the source commit (or a content hash) it
   was written from, in `MANIFEST.json` beside the source name it already
   carries.
2. Before overwriting, compare the file on disk with that record. A
   mismatch is a local edit: run it through
   [tools/precedent_local_edits.py](../tools/precedent_local_edits.py)'s
   rules, the same as the other two layers, and let `send` carry it to the
   set that owns it (`received_owners()` already names the owner).
3. A test with a consumer-shaped fixture: an edited received practice
   survives a sync, or is reported, never silently lost.

Closes when a received practice or check with a committed local edit is
never overwritten without being reported.
