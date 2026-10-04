---
slug:            gotcha-2026-09-30-an-unfetched-remote-ref-says-a-merge-never-happened
status:          live
noted:           2026-09-30
severity:        moderate
retired:         null
retires_when:    null
---
## Symptom

`git branch -r --contains SHA` or `git log origin/<branch>` says a commit
is not on a remote branch, and it is. A session tells the person a change
never reached the branch while it is already there, and sometimes already
moved further.

## Story

On 2026-09-29 Morgan rejected a ceiling raise, and the session that made it
reverted its BestPractice half and left the precedent-individual branch
`claude/derived-session-ceiling-7qk2` unmerged. At 22:29 (-0300) a different
session merged that branch into precedent-individual's pre-staging, and a
Promote carried it to main. Asked later, the first session read
`origin/pre-staging` in a clone that had not fetched since before 22:29 and
reported that the raise never reached pre-staging. The ref was right about
the moment of its last fetch and wrong about the remote. It came to light when
another session read precedent-individual's main and found the raised
ceiling still there.

## Fix

Fetch in the same command as any claim about what a remote holds: `git fetch
-q origin BRANCH && git branch -r --contains SHA`. Where a fetch is not
possible, say how old the reading is instead of stating it as fact. The
practice that says so is [check the state you wanted](../practices/verify-postcondition.md),
in its Detail.
The raise itself could not ride a merge again unnoticed:
`precedent_check.py --only budget-within-approval` compares the budgets in
force with the person's approvals at every gate.
