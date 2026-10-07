---
slug:            gotcha-2026-10-07-a-refused-push-means-the-commit-before-it-did-not-run-either
status:          live
noted:           2026-10-07
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A session runs `git add ... && git commit ... && git push` in one Bash
call. The push check refuses it, and the session tells its person the work
was committed and only the push failed. `git status` shows the changes
still uncommitted, and `git log` has no new commit.

## Story

**2026-10-03 and 2026-10-05, a consumer repository.** A Claude Code
PreToolUse hook judges the whole Bash command before any of it starts, and
a refusal stops all of it: the add and the commit never ran. The refusal
said only "The push check REFUSED this push of <repo>", which reads as if
the earlier steps had gone through. Both times the session reported a
commit that did not exist.

## Fix

Since 2026-10-07 every refusal the commit, push and merge gates give says
near the top that nothing in the refused command ran. The wording is
written by the tools (`hook_reason()` in
[tools/precedent_push_check.py](../tools/precedent_push_check.py),
[tools/doc_lint.py](../tools/doc_lint.py) and
[tools/precedent_merge_check.py](../tools/precedent_merge_check.py)), so it
reached every repository without a hook change.

**In the session:** commit in a call of its own, check `git status`, then
push in a separate call. After any refusal, check `git status` and
`git log -1` before saying what happened.
