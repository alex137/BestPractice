---
slug:            gotcha-2026-09-13-git-log-format-p-silently-reports-no-parents-at-all-for-a-co
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

`git log --format=%P` silently reports no parents at all for a commit sitting at a shallow clone's boundary, even when it really has two.

## Story

**`git log --format=%P` silently reports no parents at all for a commit
sitting at a shallow clone's boundary, even when it really has two.** A
`checked_by` script that told merge commits from ordinary ones worked
perfectly against a full clone, then misclassified the exact boundary commit
the moment it ran against a fresh `--depth 1` clone of the same repo —
reproduced directly, not suspected. Git's pretty-printers respect the shallow
graft; the commit object's own header still records both parents. `git
cat-file -p <sha>` reads that header and is unaffected — count lines starting
with `parent ` instead of parsing `%P`.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
