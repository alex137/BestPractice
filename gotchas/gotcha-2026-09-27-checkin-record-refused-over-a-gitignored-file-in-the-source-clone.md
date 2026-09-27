---
slug:            gotcha-2026-09-27-checkin-record-refused-over-a-gitignored-file-in-the-source-clone
status:          retired
noted:           2026-09-27
severity:        null
retired:         "2026-09-27"
retires_when:    null
---
## Symptom

`checkin.py record` refused with "not identical to the vendored tree" and
named `.claude/settings.local.json` (or something under `.precedent/`) in
the BestPractice clone: a gitignored file that is not upstream content.

## Story

A consumer's Update Vendors, 2026-09-27. `record` refused because the
BestPractice source clone held `.claude/settings.local.json`, which
`commit-identity.sh` writes into every clone it runs in at session start
to carry the person's timezone. The file is gitignored on purpose. But
`record` and `status` compared the vendored tree against the clone's
folder on disk, so any file sitting there counted, committed or not. The
session deleted the file and re-recorded, which worked once. The next
session start wrote it straight back, so the next update would have
failed the same way.

`push` had the same bug in the other direction: it deleted every file in
the clone that the vendored tree lacked, so it would have removed that
settings file, the session's gitignored practices file under `.precedent/`, and any uncommitted
file a person had there. `update` was never affected, because it has read
its source with `git archive` since 2026-09-06.

A second bug turned up in the same place: `record` wrote the clone's
`HEAD` into `upstream.commit`, so a clone checked out on some other branch
stamped that branch's commit as the upstream one.

## Fix

Fixed at the root in [tools/checkin.py](../tools/checkin.py). `record`
and `status` now extract `origin/<pinned branch>` and compare against that
committed tree, and `record` stamps that commit. `push` deletes only files
`git ls-files` lists. [tools/verify_harness.py](../tools/verify_harness.py)'s
`check_checkin_ignores_files_git_does_not_track_in_the_clone` puts the
stray files in a clone and fails on the old code: 4 of its 6 cases went
red when measured.

A consumer whose vendored copy is older still gets the fix on its first
update after this one. `update` mirrors the new copy of the tool into
`process/upstream/tools/` before `record` runs, and that was checked end to
end with the settings file present. **Don't delete the file to get past
`record`.** If it ever complains about one again, that's a bug.
