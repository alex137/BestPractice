---
slug:            gotcha-2026-09-13-a-stale-checkout-is-indistinguishable-from-missing-work-and-
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A stale checkout is indistinguishable from missing work, and the guard cannot save the sessions that most need it.

## Story

**A stale checkout is indistinguishable from missing work, and the guard
cannot save the sessions that most need it.** A session once came up 366
commits behind and concluded that files which had landed days earlier "did not
exist"; another had a local branch sharing **zero** commits with origin. `git
status` says "up to date with origin" in both cases, because it compares
against a remote-tracking ref nothing has refreshed.
[.claude/hooks/freshness-guard.sh](../.claude/hooks/freshness-guard.sh) now
**repairs** rather than warns — on a clean tree that is strictly behind it
fast-forwards, which makes the harness re-read the instruction files — and
warns only for diverged, no-shared-history and dirty-tree states, because a
hook that discards work is worse than any stale checkout. **What no guard
covers, and why this stays here: it does not run for a repo attached
mid-session, or when the harness rooted the session one directory above the
repo.** So before concluding anything is missing or unfinished, run `git fetch
origin <branch>` and `git rev-list --count HEAD..origin/<branch>` yourself.
Three incidents and the guard's full design history are in the archive.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
