---
slug:            gotcha-2026-09-03-git-log-format-p-silently-reports-no-parents-at-all-for-a-co
status:          retired
noted:           2026-09-03
severity:        null
retired:         "2026-09-03"
retires_when:    null
---
## Symptom

`git log --format=%P` silently reports no parents at all for a commit

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **`git log --format=%P` silently reports no parents at all for a commit
  sitting at a shallow clone's boundary, even when it really has two.** Writing a mechanical check for `precedent-team-repo-maintenance`
  (a `checked_by` script that needed to tell a merge commit apart from an
  ordinary one, to exempt merges from a per-commit rule) used `%P` and
  worked perfectly against a full clone, then silently misclassified the
  exact commit sitting at the shallow boundary as parentless the moment the
  same script ran against a fresh `--depth 1` clone of the same repo —
  reproduced directly, not just suspected. Git's pretty-printers respect
  the shallow graft for traversal purposes even though the commit object's
  own header still genuinely records both parents. `git cat-file -p <sha>`
  reads that header directly and is unaffected — count lines starting with
  `parent ` instead of parsing `%P`, anywhere a check needs to know a
  shallow-clone-safe parent count or parent list.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
