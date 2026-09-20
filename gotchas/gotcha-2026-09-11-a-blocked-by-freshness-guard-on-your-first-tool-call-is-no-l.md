---
slug:            gotcha-2026-09-11-a-blocked-by-freshness-guard-on-your-first-tool-call-is-no-l
status:          retired
noted:           2026-09-11
severity:        null
retired:         "2026-09-11"
retires_when:    null
---
## Symptom

A `BLOCKED by freshness-guard` on your first tool call is no longer the new-branch false positive it was until 2026-09-11

## Story

<details>
<summary>The full entry as it stood until 2026-09-11</summary>

- **A `BLOCKED by freshness-guard` on your first tool call is no longer the
  new-branch false positive it was until 2026-09-11 — so read what it
  actually says before reaching for the override.** The guard used to treat
  "origin has no such branch" and "origin could not be reached" as the same
  failure, and refused the first write of every newly created branch; the
  remedy it named, `git fetch origin <branch>`, could not succeed against a
  ref that does not exist, so the only way forward a session found was
  `git config precedent.freshness.override true` — which switches freshness
  checking off for that checkout permanently, including the stale-base check
  that catches the single most expensive failure class in this file. Fixed in
  both copies here: `git ls-remote --exit-code --heads origin <branch>`
  separates the two, and only the branch-absent case is waved through — with
  the base-branch check still running on it. **What stays true is the shape
  of the trap**, since the override is still on offer in every block message:
  a refusal naming a remedy that cannot work is the moment to ask what the
  guard actually measured, not to disable it. **An unreachable origin still
  blocks, deliberately.** The 2026-09-09 incident, and the push-the-branch
  workaround it had to use, are entry 30 in
  [record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md).

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
