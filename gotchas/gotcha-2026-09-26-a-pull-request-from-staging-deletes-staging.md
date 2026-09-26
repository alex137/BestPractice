---
slug:            gotcha-2026-09-26-a-pull-request-from-staging-deletes-staging
status:          live
noted:           2026-09-26
severity:        null
retired:         null
retires_when:    "the repository's \"Automatically delete head branches\" setting is off, or a ruleset restricts deleting main, staging and pre-staging"
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
itself as its source branch. BestPractice has GitHub's **"Automatically
delete head branches"** turned on, which deletes the branch a merged pull
request came FROM, on the assumption that it was a one-off feature branch.
So merging #629 deleted `staging`.

Nothing was lost: `staging`'s last commit was contained in `main`, and the
old name `precedent-beta-v01` still pointed at it. It was restored at that
exact commit through GitHub's branch API, since the push gate refuses a
direct push to staging for a person with `promote_only` on.
`precedent_branches.py --ensure-tiers --apply`, the tool meant for a missing
tier, could not do it: it looked for `staging` to rebuild `staging` from.

Morgan: *"I think staging should never be deleted. This worries me"*, and
*"Alex can't do that now and I don't have permission to edit that setting
in github"*. So the fix could not be the setting. GitHub only ever deletes a
pull request's SOURCE, never its target, and the only step that made a tier
branch a source was the pull request into main.

## Fix

- **A pull request into main comes from a throwaway copy of staging**,
  never from staging: `git push origin origin/staging:refs/heads/to-main-DATE`,
  then a pull request from that copy. GitHub deletes the copy; staging
  stays.
- **The merge gate enforces it.** [tools/precedent_merge_check.py](../tools/precedent_merge_check.py)
  reads the pull request's source branch from GitHub's API and refuses to
  merge one that comes from `main`, `staging`, `pre-staging` or
  `precedent-beta-v01` of the same repository, naming the copy command. It
  fails open when the API cannot be reached.
- **A missing staging is rebuilt** by `--ensure-tiers --apply`, from the old
  name when it exists, else from main.
- The durable fix, for whoever has admin rights on the repository: turn off
  Settings → General → Pull Requests → "Automatically delete head
  branches", or add a ruleset restricting deletion of `main`, `staging` and
  `pre-staging`. That is this entry's retirement condition.
