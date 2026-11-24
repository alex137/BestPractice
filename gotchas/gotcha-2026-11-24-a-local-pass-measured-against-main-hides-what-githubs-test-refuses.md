---
slug:            gotcha-2026-11-24-a-local-pass-measured-against-main-hides-what-githubs-test-refuses
status:          live
noted:           2026-11-24
severity:        notable
retired:         null
retires_when:    the local check and GitHub's test judge a change against the same base, or a merge into main is refused while the pull request's own check is red
---
## Symptom

Every local check passes, the pull request merges, and GitHub's test on
`main` is red. Three merges later it is still red, and Update Vendors in
every other repository has been quietly staying on an older commit. The
local lint had printed the finding the whole time, under a heading that
said "warning".

## Story

2026-11-23 and 24, in this repository. A session landed three pull requests
into `main` over a few hours. Each had passed the pre-push check and
[precedent_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py)
with "0 violated".

**The local run and GitHub's run judged different changes.** With the
shared practice set on disk, this checkout lands on `main`, so a local
run of it measured "the commits this branch carries since
`origin/main`": one or two, each already clean. GitHub's runner has no
practice sets beside it, so it measures against `staging`, and saw every
commit `main` carried since `staging`: nineteen. Two unexpanded
abbreviations inside quoted text in a note were a warning on the lines a
local run was judging and a violation on the lines GitHub was.

**The first failing step hid a second failure.** GitHub's test runs the
checks, then the full harness. The checks failed, so the harness never
ran, on any of the three merges. Run by hand the way GitHub runs it, it
had a failure of its own waiting: the new practice's line in the opening
index had put the universal set 14 tokens over its allowance. A change to
Update Vendors had gone to `main` with only one hand-picked test behind it.

**The red check was there to be read and was not.** This repository's rule
is to merge into `main` without waiting on the full local check, because
GitHub's check on the pull request reports afterwards. The session took
"without waiting" as "without looking". The pull request's check was red
before each merge; a bot opened an issue and commented on it three times.
The session found out from another project's coordinator, hours later.

## Fix

**Read the pull request's own check before merging the next thing, and
after merging the first.** "Merge and be told" only works if somebody
reads what they are told. One look at the check, or at the open
`main-test-failed` issue, would have stopped it at the first merge.

**To see what GitHub will see, run the checks in a bare copy:** a clone
with no practice sets beside it and an empty home folder, checked out as
`main`. The line "the N commit(s) this branch carries since origin/staging
are in scope" is the tell that the scope matches GitHub's.

**A warning in the local lint on a file you added is a failure waiting for
a wider scope.** Fix it when it is printed.

**When the first step of a test fails, nothing after it has been tested.**
After fixing it, run the rest before trusting the merges that went in
behind it.
