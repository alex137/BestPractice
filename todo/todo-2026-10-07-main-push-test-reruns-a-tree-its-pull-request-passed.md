---
slug:              todo-2026-10-07-main-push-test-reruns-a-tree-its-pull-request-passed
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-07
closed:            null
---
## What

Merging a Promote's pull request into `main` starts deep-check.yml's push
run on the merge commit. Its "Already tested?" job is meant to stop it in
seconds when those exact files already passed. On 2026-10-07 it did not:
the merge of #957 (`de548da3`) re-ran the whole suite for 30 minutes
(01:23 to 01:53 UTC), and the next Promote into main waited about 16
minutes of that before it would start.

The files were identical: the merge commit's tree equals the tree of the
pull request's head, `35f4829d`, which had just passed. The skip refused
anyway because it also requires every parent of the merge to be an
ancestor of the tested commit, and `main`'s parent, `8cfab19f`, is the
merge commit GitHub made for the Promote before. Staging never contains
that commit, so after one Promote into main the next one's push run can
never skip. The run on `8cfab19f` itself did skip, in 15 seconds, because
its own first parent was already in staging.

## Proposed

Two ways, not yet chosen:

1. **The Promote builds its copy branch as staging merged with `main`**,
   so `main` is an ancestor of the pull request's head and the skip's
   ancestry rule holds as written. Costs a merge commit in each copy.
2. **The skip accepts a passing `pull_request` run on the head** when the
   merge commit's first parent is the base that run was tested against.
   GitHub's pull-request run tests exactly that merge, same parents and
   same files, so nothing it judges by history differs. Changes the skip's
   contract, which has to say so in one line (review-against-a-contract).

## How It Closes

A Promote's merge into `main` shows the push run skipped, and the next
Promote into main does not wait on it.
