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
same check run from the main clone itself left it clean.

**Traced 2026-10-06.** `git bisect run` exports `GIT_DIR` to the command it
runs, and in a linked worktree that is `.git/worktrees/<name>`. Every
fixture built its environment from the harness's own, so the fixture's
`git init --bare` re-initialised that directory as bare, writing
`core.bare = true` into the config the main clone shares, and its
`git commit` landed on the worktree's HEAD. A git hook running the harness
would pass `GIT_DIR` and `GIT_INDEX_FILE` the same way.

## Fix

Since 2026-10-06 the harness drops git's repository variables (`GIT_DIR`,
`GIT_WORK_TREE`, `GIT_INDEX_FILE` and the rest) when it starts, so its
fixtures reach only their own temporary repositories. Planted case:
`check_harness_drops_inherited_git_repository_variables`, which fails on the
old harness with the main clone bare and the worktree's HEAD moved. The
harness does not refuse to start in a linked worktree: Promote and the merge
check run the full push check, harness included, in a throwaway linked
worktree, and that run carries no `GIT_DIR`.

Another tool run under `git bisect run` that builds repositories from its
own environment can still do this, so drop those variables for the test
command (`env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE ...`). If it has
already happened: `git config core.bare false` in the
main clone restores it (the files and HEAD are untouched), and
`git worktree remove --force` the scratch worktree.
