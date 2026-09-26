---
slug:              todo-2026-09-26-retire-precedent-beta-v01
kind:              manual
domain:            vendoring
severity:          null
status:            open
disposition:       ask
remind_on:         "2026-09-26"
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-26
closed:            null
---
## What

**Retire `precedent-beta-v01`** -- Morgan, 2026-09-26: "Todo reminder to
retire precedent-beta-v01".

`precedent-beta-v01` is staging's name before the 2026-09-25 rename. It is
kept only as an alias: every Promote moves it to the same commit as
`staging` (`LEGACY_STAGING` in
[tools/precedent_branches.py](../tools/precedent_branches.py)), so an
install whose own text still names it -- a `git clone --branch` line in its
`tools/bootstrap.sh`, links in its own instructions file -- keeps working. Git has no
branch redirect: GitHub's rename redirect covers web links only, never
`git clone` or `git fetch`, so deleting the branch breaks those lines
outright.

## Done when

The retirement condition is the one
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
`RETIRED_BRANCH_NAMES` block already names: **no install's refresh reports
a line naming `precedent-beta-v01`**. Check that first; this repo's own
`retired-branch-name-ships` check passed on 2026-09-26, but that covers only
what this repo and the practice sets ship, not the text inside each install.

Then, in order:

1. Take the alias step out of Promote (`LEGACY_STAGING` and the "also moved
   precedent-beta-v01" step in
   [tools/precedent_branches.py](../tools/precedent_branches.py)).
2. Drop the alias sentence from [precedent.json](../precedent.json).
3. Morgan deletes the branch with GitHub's own **Delete** button, from the
   [branch list filtered to precedent-beta-v01](https://github.com/alex137/BestPractice/branches/all?query=precedent-beta-v01).
   A session cannot delete a remote branch
   ([never-delete-a-remote-branch](../practices/never-delete-a-remote-branch.md)).

Deleting before step 1 lands makes the next Promote try to move a branch
that is gone.
