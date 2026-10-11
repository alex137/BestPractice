---
slug:              todo-2026-09-26-retire-precedent-beta-v01
kind:              manual
domain:            vendoring
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Retired 2026-10-11: Promote no longer keeps the alias in step, and precedent.json no longer says it is kept. Deleting the branch on GitHub is Morgan's one click."
decision_strength: decided
waiting_on:        null
noted:             2026-09-26
closed:            2026-10-11
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

**Closed 2026-10-11 (done).** Morgan: "finish the retirement now", after
being shown that the branch still existed and Promote still carried the
alias (strength: decided). The stated condition -- no install's refresh
naming the old branch -- was not measured across installs; he chose to
proceed without it. What was found first: the branch was last moved
2026-10-09 and sat 207 commits behind `staging`, every commit on it already
in `staging`, because the alias step had stopped firing once pre-staging
retired. Steps 1 and 2 landed together (Promote's alias step, its rebuild
and sync sources, and the `precedent.json` sentence); the old name stays
recognized as a tier and protected from deletion offers, and
`RETIRED_BRANCH_NAMES` still renames it in any install. Step 3 is
Morgan's: delete it from the
[branch list filtered to precedent-beta-v01](https://github.com/alex137/BestPractice/branches/all?query=precedent-beta-v01).
