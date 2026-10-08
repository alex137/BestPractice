---
slug:              todo-2026-10-08-a-consumer-cannot-tell-its-copy-is-stale-without-a-clone
kind:              manual
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"#2 fine also, approved\" -- build the fingerprint and the clone-free check"
decision_strength: decided
waiting_on:        null
noted:             2026-10-08
closed:            2026-10-08
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

## Notes

**Decided 2026-10-08, Morgan: "#2 fine also, approved" (strength:
decided). Built the same day.**

- `process/manifest.json` keeps `upstream.copy_tree`, the git tree id of
  the copy as recorded. One key: a tree id is already one hash over every
  path and content hash, and once the copy is committed the tree it names is
  in the repository's own history, so the check can list the files that
  differ without a per-file map in the manifest
  ([INSTALL.md section 5](../INSTALL.md#5-the-manifest-schema-processmanifestjson)).
- [tools/checkin.py](../tools/checkin.py) `record` writes it; Update
  Vendors writes it again once the copy matches its record after the
  local-edit rules ran, and not while a file in the copy is left for the
  person.
- The `vendored-copy-matches-record` check in
  [tools/precedent_check.py](../tools/precedent_check.py) compares, names
  each drifted file and fails, so a consumer whose copy drifts after an
  update is refused by its own check. Files marked `diverged` or
  `local-only`, and paths kept under `kept_template_divergences` with a
  reason, are exempt. A declined file is not: its copy stays upstream's
  text, since the decline is judged by it. A manifest without the key is
  could not verify until the next Update Vendors.
