---
slug:            gotcha-2026-10-01-a-harness-check-run-in-a-linked-worktree-turns-the-main-clone-bare
status:          live
noted:           2026-10-01
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

After running [verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py) checks from a scratch `git worktree` of
this repository, `git status` in the main clone fails with
`fatal: this operation must be run in a work tree`, and `git worktree list`
shows the main clone as `(bare)`. The scratch worktree also fills with
commits that are not this repository's, such as one titled
`installed, catalogue vendored`, so a `git bisect run` there loops on the
same step.

## Story

**2026-10-01, in this repository.** A Debut was refused, and a session
bisected pre-staging with `check_update_vendors_survives_an_upstream_deletion`
as the test, from a linked worktree under its scratchpad. The bisect never
finished: the test's fixture commits landed in the worktree it ran in, and
the worktree's HEAD moved onto them. Afterwards `.git/config` in the main
clone said `bare = true`. A linked worktree shares its `config` with the
main clone, so whatever the check ran there reached the main clone too. The
same check run from the main clone itself left it clean. Which call leaks is
not yet traced.

## Fix

Run harness checks from the main clone, or from a separate full `git clone`
into a scratch directory, never from a `git worktree` of the repository you
care about. If it has already happened: `git config core.bare false` in the
main clone restores it (the files and HEAD are untouched), and
`git worktree remove --force` the scratch worktree.
