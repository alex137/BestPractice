---
slug:            gotcha-2026-09-28-stale-shallow-entries-for-deleted-branches-survive-unshallow
status:          live
noted:           2026-09-28
severity:        minor
retired:         null
retires_when:    null
---
## Symptom

`git rev-parse --is-shallow-repository` keeps printing `true` after
`git fetch --unshallow` exits 0, and after a full-depth fetch of every
branch. The branch tool refuses with "the clone is still shallow (the fetch did
not complete), so the history checks cannot run".

## Story

On 2026-09-28 a Promote in two practice-set clones stopped at its full
check for exactly that reason. Each clone's `.git/shallow` listed 17
boundary commits, and none of them was reachable from any branch, remote
branch or reflog: they were left by shallow fetches of branches that had
since been deleted on GitHub. A fetch deepens only the history of refs it
fetches, so no fetch can ever reach those commits, and git keeps listing
them. The history every live branch needs was already complete; the file
alone made the clone read as shallow.

## Fix

Confirm no entry is reachable before touching anything:
`git rev-list --all --reflog` must contain none of the SHAs in
`.git/shallow`. Then move the file aside rather than deleting it
(`mv .git/shallow .git/shallow.stale-<date>`), and check with
`git fsck --connectivity-only` that every branch's history is intact.
If any entry is reachable, the clone really is shallow: deepen it
instead (`git fetch --depth=<large> origin`).

**Prevention: nothing mechanical, deliberately**, because the recovery
edits git's own `.git/shallow`, and is safe only after the reachability
check above. A tool that did it unattended and misjudged one entry would
make a really shallow clone read as complete, and the checks that read
history would then run on history that is not there. Today the failure
is loud and safe instead: the full check
([tools/precedent_push_check.py](../tools/precedent_push_check.py))
refuses to run on a clone that still reads as shallow. (Written 2026-10-06, after the 2026-10-05 very
deep check found no answer recorded.)
