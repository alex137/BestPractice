---
slug:            gotcha-2026-09-26-engine-made-commits-came-out-as-the-bot-and-a-reused-pass-l
status:          live
noted:           2026-09-26
severity:        notable
retired:         null
retires_when:    every practice set and consumer has refreshed its vendored engine past the commit that routes engine commits through precedent_identity.commit_env()
---
## Symptom

Promote, the sync into pre-staging, the Promote lock, or an engine refresh
makes a commit, and **the commit is authored by the container's bot**
(`Claude <noreply@anthropic.com>`), sometimes in the repository's fallback
zone too. Nothing refuses it at the time. Later, the repository's own
`precedent_check.py --full-sweep` fails `commit-author` on its staging
branch. Re-running Promote does not help, because its full check fails
inside its worktree on `consumer_shape`: "`.git` here is not a directory".

## Story

2026-09-26. A session was started with four practice sets attached and no
repository as its root, so no SessionStart hook ran for any of them (the
general form of that is
[gotcha-2026-09-25](gotcha-2026-09-25-a-session-rooted-above-every-repo-it-touches-gets-hooks-and.md)).
Git kept the container's global identity, and
`~/.config/precedent/config.json` did not exist.
`PRECEDENT_COMMIT_NAME` and `PRECEDENT_COMMIT_EMAIL` were in the
environment, and nothing turned them into git's author. It ran Promote in
all four sets. Every merge commit it made was authored by the bot.

Four separate holes lined up:

1. **The engine never stated an author.** [precedent_branches.py](../tools/precedent_branches.py)'s
   `_merge_env()` had set `TZ` since the -0400 incident of 2026-09-25, and
   left the author to `git config`. The refresh commits in
   [precedent_refresh_sources.py](../tools/precedent_refresh_sources.py) did the same.
2. **The backstop cannot see these commits.** The global
   `commit-identity.sh` backstop is a `pre-commit` hook. `git merge` and
   `git commit-tree` never run `pre-commit`, so every merge and lock commit
   the engine makes goes past it.
3. **A reused pass skipped the author check.** Promote's full check found
   "this exact tree already passed ... in another checkout" and ran nothing.
   The pass is keyed on the tree, and a Promote merge has exactly the tree
   its checked parents had, so `commit_author` never judged the new commits.
4. **`consumer_shape` refused the only place Promote runs it.** Promote
   checks inside a linked worktree, and [precedent_consumer_shape.py](../tools/precedent_consumer_shape.py)
   refused any checkout whose `.git` is a file. So every Promote in a
   source that really ran the suite failed. The first round only passed
   because it reused a receipt.

Measured against `37fc3b5`: with only [precedent_branches.py](../tools/precedent_branches.py) reverted,
the new harness case shows the merge and lock commits authored by the bot
**with the right zone**. That asymmetry is hole 1.

This class of commit had reached published branches about a dozen times
before. Each time it was fixed per session or grandfathered per SHA.

## Fix

In the engine, so it does not depend on where a session starts:

- `precedent_identity.commit_env(repo)` is the one helper every engine
  commit runs under. It sets `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL` from the
  declared identity and `TZ` from `precedent_time`'s ladder, and leaves
  `GIT_COMMITTER_*` alone. In a repository with an `identity.json` and no
  resolvable author it raises `IdentityRequired`, and Promote prints
  `REFUSED: no commit was made`. Shell callers use
  `precedent_identity.py --commit-env REPO`, as `freshness-guard.sh` does
  for its one merge.
- [precedent_push_check.py](../tools/precedent_push_check.py) always runs `commit_author` and `commit_dates`,
  even when it reuses a local or shared pass for the tree.
- [precedent_consumer_shape.py](../tools/precedent_consumer_shape.py) gives its copy a git directory of its own
  when run from a linked worktree or a submodule. The copy is named after
  the main checkout.

Proven by `check_engine_commits_state_their_author` and
`check_history_checks_never_ride_a_reused_pass` in
[tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py). Both were run
against the `37fc3b5` engine files and went red there.

**The zone still needs the environment.** In a session with no config file,
the person's zone reaches a shared set only through `PRECEDENT_COMMIT_TZ`.
Both modules already honour it. Without it, a shared set applies its
`fallback_timezone`, as designed. Set it beside `PRECEDENT_COMMIT_NAME` and
`_EMAIL` ([documentation/PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)).

Commits already published are not rewritten or grandfathered by this fix.
Each repository deals with its own.
