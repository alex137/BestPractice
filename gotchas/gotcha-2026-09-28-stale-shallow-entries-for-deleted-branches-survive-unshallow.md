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
