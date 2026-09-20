---
slug:            gotcha-2026-09-06-a-git-helper-that-returns-stdout-and-drops-the-exit-code-wil
status:          retired
noted:           2026-09-06
severity:        null
retired:         "2026-09-06"
retires_when:    null
---
## Symptom

A git helper that returns stdout and drops the exit code will hand you a

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A git helper that returns stdout and drops the exit code will hand you a
  ref *name* where a commit hash belongs.** `git rev-parse <missing-ref>` exits
  non-zero but *prints the ref you asked for* on stdout, so
  `_git(...'rev-parse', ref) or <fallback>` never falls back: it binds the
  truthy string `origin/precedent-beta-v01` and carries it forward as a hash.
  Reached continuous integration on 2026-09-06 as `precedent-beta-v01 @ origin/prece has no
  tools/build_views.py` — a 12-char truncation of a ref name. Use
  `rev-parse --verify --quiet` (silent, exit 1) whenever a ref may be absent.
  Note the trigger: a *non-repo* prints nothing, so the plain form looks fine
  for years — it only echoes on an **unborn `HEAD`** (a repo with no commits) or
  a missing ref, which is why this survived so long. Audited across
  [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) on
  2026-09-06 and found twice more: `status()` reported a clone that simply has
  no `SOURCE_BRANCH` as *"upstream has moved — run `refresh`"*, a false alarm
  wired to what was then a destructive remedy; and `seed()` recorded
  `source_commit: "HEAD"` into `ENGINE_MANIFEST.json`, after which every later
  comparison read as "moved" forever. A sweep found the same one-liner in
  [tools/routing_audit.py](../tools/routing_audit.py), where it was persisting a
  review record at commit `"HEAD"`.
  The same swallowed exit code hid a failing `git checkout` in a dirty tree
  during the very session that fixed this, making a broken negative control
  look like a passing test — so treat "the command reported nothing" as no
  evidence at all.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
