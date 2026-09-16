---
slug:            gotcha-2026-09-13-git-clone-with-no-branch-asks-the-server-which-branch-to-che
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

`git clone` with no `--branch` asks the SERVER which branch to check out, and the answer is a setting on a web page that nothing in this repository can see.

## Story

**`git clone` with no `--branch` asks the SERVER which branch to check out,
and the answer is a setting on a web page that nothing in this repository can
see.** The remote's `HEAD` symref is whatever the repository's default branch
is set to, and git follows it silently. 2026-09-09: two practice-source
repositories had it pointed at a feature branch, so every session-start clone
landed on an older tree and a plain sync would have overwritten newer
committed text — exit 0, no warning. **The consuming repo had never been
stale; the clone had been pointed somewhere else**, and `git pull --ff-only`
follows whatever branch the checkout is on, so it stayed wrong every session
afterwards. **The lesson that outlived the fix: when a rule forbids asking a
question, check whether something else is asking it for you.** The guard
against this reads Python, so it never saw a `git clone` making the same
inference on our behalf — the class is open even though this instance is shut.
Pinned since 2026-09-10 in
[tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py); a
clone you run by hand is still yours to branch explicitly. Full incident:
entry 36.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
