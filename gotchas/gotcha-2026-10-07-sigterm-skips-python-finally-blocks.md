---
slug:            gotcha-2026-10-07-sigterm-skips-python-finally-blocks
status:          live
noted:           2026-10-07
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

After an Update Vendors run was cut short, HEAD is a commit whose message
starts "precedent_update: the staged update, committed only so the deep
check judges it as committed -- undone right after". It was never undone.

## Story

**2026-10-06, a consumer repository.** The run was started under
`timeout 590`. When the time ran out, `timeout` sent SIGTERM, and Python's
default handling of SIGTERM ends the process without running `finally`
blocks -- unlike Ctrl-C, which raises `KeyboardInterrupt` and does run them.
The `finally` that undoes the stand-in commit in
[tools/precedent_update.py](../tools/precedent_update.py)'s
`judged_as_committed()` never ran. The rerun found nothing to stage and did
not look at HEAD, so the stand-in stayed; a real commit made on top of it
would have been the one the next undo removed.

## Fix

Since 2026-10-07 `judged_as_committed()` turns SIGTERM into an exception
while the stand-in exists, so its `finally` runs, and every run starts by
undoing a stand-in it finds at HEAD (`undo_leftover_standin()`, a
`git reset --soft HEAD~1` that keeps the changes staged).

**In general:** cleanup that must survive `timeout` or a killed terminal
needs a SIGTERM handler that raises; `finally` alone is not enough. And do
not run a git-changing command under a short `timeout` at all.
