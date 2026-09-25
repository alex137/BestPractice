---
slug:            gotcha-2026-09-25-a-session-cannot-push-a-ref-outside-refs-heads
status:          live
noted:           2026-09-25
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A push to a ref that is not a branch, such as `refs/precedent/promote-lock`,
fails from a Claude Code on the web session:

```
send-pack: unexpected disconnect while reading sideband packet
fatal: the remote end hung up unexpectedly
```

`git ls-remote` shows nothing was created. A retry fails the same way.

## Story

**Measured 2026-09-25**, twice, a few seconds apart, from a session rooted
in this repository. The idea was a lock for Promote that lived in a ref
GitHub never runs workflows for: `leak-gate.yml` fires on a push to any
branch, so a lock kept on a branch would spend Actions minutes on every
claim and release. A ref under `refs/precedent/` would have avoided that.

The session's git proxy refuses it. The error has the same shape as the
refused remote-branch delete
([gotcha-2026-09-14](gotcha-2026-09-14-a-session-can-push-branches-but-cannot-delete-a-remote-branc.md)),
minus the HTTP 403 line, and the cause is most likely the same: a web session
may create and move branches, and nothing else. Pushes to ordinary branches
from the same session, minutes before and after, went through normally.

## Fix

Don't design anything that needs a session to write a ref outside
`refs/heads/`. If a mechanism needs shared state on origin, it has to be a
branch. A branch that only ever moves forward can act as a compare-and-swap,
since a non-fast-forward push is refused. Its commits should carry `[skip ci]`
so a workflow triggered by pushes doesn't run on each update.
