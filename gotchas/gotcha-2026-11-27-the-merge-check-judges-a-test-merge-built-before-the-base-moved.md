---
slug:            gotcha-2026-11-27-the-merge-check-judges-a-test-merge-built-before-the-base-moved
status:          live
noted:           2026-11-27
severity:        notable
retired:         null
retires_when:    the merge check notices that the test merge's first parent is no longer the base branch's tip and waits for GitHub to rebuild it, or says so in its refusal
---
## Symptom

A pull request is refused by the merge check for something a fix on `main`
has already cured. The refusal names "the merge GitHub would make" and a
commit hash, and the hash is the same one it named before the fix landed.

## Story

2026-11-27. The merge check refused a pull request because of a fault in
one of the checks it runs. The fix went in as a pull request of its own and
merged into `main`. The first pull request was tried again a minute later
and refused in the same words, over the same test-merge commit.

GitHub builds `refs/pull/N/merge` when the pull request's head moves, and
rebuilds it lazily when the base moves. For a while after the base branch
takes a new commit, the ref still holds the merge of the head into the
**old** base. The merge check runs the push check in a worktree of that
commit, so it ran the old, unfixed copy of the check and reported what the
old copy found.

[tools/precedent_merge_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_merge_check.py) already
waits when the test merge's second parent is not the pull request's head.
Nothing makes it wait when the first parent is no longer the base branch's
tip.

## Fix

**Bring the base into the branch and push**: `git merge origin/main`, push,
then merge the pull request. The head moves, GitHub builds a new test merge
on the new base, and the check judges that.

Before spending time on the refusal itself, compare the hash it names with
the one in the earlier refusal. The same hash after the base has moved
means the check is reading a stale merge, not that the fix failed.
