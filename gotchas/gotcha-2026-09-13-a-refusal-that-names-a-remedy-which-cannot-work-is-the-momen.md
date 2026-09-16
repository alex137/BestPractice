---
slug:            gotcha-2026-09-13-a-refusal-that-names-a-remedy-which-cannot-work-is-the-momen
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A refusal that names a remedy which cannot work is the moment to ask what the guard actually measured, not to disable it.

## Story

**A refusal that names a remedy which cannot work is the moment to ask what
the guard actually measured, not to disable it.** The freshness guard used to
refuse the first write of every newly created branch and name `git fetch
origin <branch>` — impossible against a ref that does not exist — so the only
way forward a session found was `git config precedent.freshness.override
true`, which switches freshness checking off for that checkout permanently,
including the stale-base check that catches the single most expensive failure
class in this file. Fixed 2026-09-11 in both copies here: `git ls-remote
--exit-code --heads origin <branch>` separates "origin has no such branch"
from "origin could not be reached", and only the branch-absent case is waved
through, with the base-branch check still running on it. **An unreachable
origin still blocks, deliberately.** The override is still on offer in every
block message, which is why the shape above outlived the fix. Entries 30 and
35.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
