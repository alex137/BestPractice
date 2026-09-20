---
slug:            gotcha-2026-09-01-a-session-s-local-checkout-can-be-stale-enough-to-look-compl
status:          retired
noted:           2026-09-01
severity:        null
retired:         "2026-09-01"
retires_when:    null
---
## Symptom

A session's local checkout can be stale enough to look complete while

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A session's local checkout can be stale enough to look complete while
  missing real, merged work — with no error.** A session opened here on
  2026-09-01 had a local `precedent-beta-v01` that shared **zero** commits
  with origin's tip: phases 1.5 through 4, every `spec/*.md` brief, and
  `CHANGES_TO_TELL_ALEX.md` simply did not exist locally. `git status`
  reported "up to date with origin" because that check runs against
  whatever the remote-tracking ref happened to be at last fetch, and no
  fetch had happened yet. Reading the tree, running the harness, anything
  short of `git fetch` first would have silently analyzed or built on a
  months-stale snapshot. [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh)
  now fetches the current branch and warns loudly (never fails the
  session — a git failure here must not block startup) if local `HEAD`
  differs from origin's, distinguishing "behind" from "shares no history
  at all" (a force-push or rewrite, the worse case). If you see that
  warning, and your working tree is clean: `git checkout -B <branch>
  origin/<branch>`.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
