---
slug:            gotcha-2026-10-08-a-vendored-copy-can-claim-a-commit-it-does-not-hold
status:          live
noted:           2026-10-08
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A consuming repository has just finished Update Vendors, and its records
say it took BestPractice at a given commit: `process/manifest.json` and
`tools/ENGINE_MANIFEST.json` both name it. Yet fixes that commit carries do
not show there. Its light check still reports broken links that commit
fixed, and two rules that commit has active still read as deduplicated
stubs, "in force nowhere". A comparison of `process/upstream/` against
BestPractice at that commit finds most of the copy different, and files the
trimmed copy no longer carries are back.

## Story

**2026-10-08.** A consuming repository took Update Vendors to BestPractice
`main` in eleven runs, across a move of `main` part-way through. Its
session then reported, among other things, the same broken links and the
same "orphaned" rules it had reported that morning, both already fixed
upstream. Checked against BestPractice at the recorded commit, 440 of the
604 files under its `process/upstream/` differed, and
`process/upstream/tools/` held 99 files the copy had stopped carrying on
2026-09-30. So the upstream fixes had not failed. The copy was not the
version its records named.

How it got there, reproduced the same day: a run ended FAILED with the
mirrored copy staged. The person ran `practice_audit.py --redecide`, which
edits `process/manifest.json`. The next run put the staged files back to
HEAD, all except the manifest, because it had changed. That left the new
commit recorded over the old text. From then on, Update Vendors read every
old file as a committed local edit ("upstream has not changed this file, so
your edit stays") and kept it. A later put-back also restored the dropped
`tools/` files and never deleted them again. Nothing checked, at DONE, that
the copy was the commit the records name.

## Fix

Three changes in BestPractice, 2026-10-08:

- Update Vendors verifies the postcondition before it says DONE: the
  vendored copy is exactly what the recorded commit gives under the copy
  rules, apart from what the repository keeps on purpose. Where it is not,
  the difference is re-mirrored and reported; a local edit nobody has
  resolved is reported, never overwritten.
- A run records the paths it wrote and deleted, so a later run, even on a
  newer engine, knows them as its own, and a put-back re-applies the
  deletions too.
- A declined file's copy is upstream's text at the recorded commit, so a
  decline is judged against one basis everywhere.

**If you meet the symptom anyway:** compare `process/upstream/` with
BestPractice at the commit `process/manifest.json` records. A copy that
differs is stale, and one clean Update Vendors run re-mirrors it.
