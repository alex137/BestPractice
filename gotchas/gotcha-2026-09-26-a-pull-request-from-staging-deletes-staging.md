---
slug:            gotcha-2026-09-26-a-pull-request-from-staging-deletes-staging
status:          live
noted:           2026-09-26
severity:        null
retired:         null
retires_when:    "a ruleset on the repository restricts deleting main, staging and pre-staging"
---
## Symptom

Right after a pull request into `main` is merged, `staging` is gone from
origin:

```
git fetch origin staging
fatal: couldn't find remote ref staging
```

Every Promote, push check and freshness notice that reads `origin/staging`
then fails or skips.

## Story

**2026-09-25, late**, the first merge of staging into main (#629, Alex's
approval relayed by Morgan). The pull request was opened with `staging`
itself as its source branch, and shortly after it merged, `staging` no
longer existed on origin.

**The cause is not established, and the first explanation given was
wrong.** The session said GitHub's "Automatically delete head branches"
setting had deleted it. Measured the next day through the API, that
setting is OFF (`delete_branch_on_merge: false`), and a later pull request
from a throwaway branch into main was merged without its source being
deleted. The repository's event feed shows staging being created on both
days and no deletion. What is left: GitHub offers a **"Delete branch"**
button on every merged pull request's page for its source branch, and a
click there -- by a person, or by any session driving a browser -- does
exactly this. That is a hypothesis, not a measurement.

Nothing was lost: `staging`'s last commit was contained in `main`, and the
old name `precedent-beta-v01` still pointed at it. It was restored at that
exact commit through GitHub's branch API, since the push gate refuses a
direct push to staging for a person with `promote_only` on.
`precedent_branches.py --ensure-tiers --apply`, the tool meant for a missing
tier, could not do it: it looked for `staging` to rebuild `staging` from.

Morgan: *"I think staging should never be deleted. This worries me."*

## Fix

Whatever the cause, a tier branch that is never a pull request's source
cannot be deleted from a merged pull request's page, by a setting or by a
button.

- **A pull request into main comes from a throwaway copy of staging**,
  never from staging: `git push origin origin/staging:refs/heads/to-main-DATE`,
  then a pull request from that copy. Measured working 2026-09-26 (#633):
  staging stayed where it was.
- **The merge gate enforces it.** [tools/precedent_merge_check.py](../tools/precedent_merge_check.py)
  reads the pull request's source branch from GitHub's API and refuses to
  merge one that comes from `main`, `staging`, `pre-staging` or
  `precedent-beta-v01` of the same repository, naming the copy command. It
  fails open when the API cannot be reached.
- **A missing staging is rebuilt** by `--ensure-tiers --apply`, from the old
  name when it exists, else from main.
- The durable fix, for whoever has admin rights on the repository: a
  ruleset restricting deletion of `main`, `staging` and `pre-staging`,
  which refuses every route, button included. That is this entry's
  retirement condition.
