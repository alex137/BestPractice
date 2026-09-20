---
slug:            gotcha-2026-09-14-a-session-can-push-branches-but-cannot-delete-a-remote-branc
status:          live
noted:           2026-09-14
severity:        null
retired:         null
retires_when:    null
---
## Symptom

Measured 2026-09-14

## Story

**Measured 2026-09-14**, after a session had spent a whole conversation
offering to delete merged branches and never once trying.

`git push origin --delete <branch>` fails:

```
error: RPC failed; HTTP 403 curl 22 The requested URL returned error: 403
send-pack: unexpected disconnect while reading sideband packet
fatal: the remote end hung up unexpectedly
```

**The second and third lines are what make this waste an hour.** They are the
symptoms of a dropped connection, so the obvious reading is "the network
blipped, retry" — and a retry produces the same three lines, which reads as a
flaky remote rather than a settled answer. Only the first line, which scrolls
past first, says what actually happened.

**It is a capability limit, not a transient.** Proved by running both halves
back to back: the delete failed twice, and an ordinary `git push -u origin
<new-branch>` in the same working tree, seconds later, succeeded and printed
the pull-request URL. So the credential carries write access to *create* refs
and not to *remove* them, and nothing in the tooling says so up front.

**What this costs is credibility rather than work.** A session that offers
"say the word and I'll delete those branches" is promising something it cannot
do, and the person finds out only when they take it up. Offer to *list* merged
branches; leave the deletion to the person, who has a one-click Delete branch
button on every merged pull request page.

**Do not probe this with a throwaway branch.** The obvious test — push a
scratch branch to prove pushes still work — leaves behind a branch that,
by the very limit being tested, cannot then be removed. The session that
wrote this entry did exactly that and added `claude/push-capability-probe`
to the remote permanently.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
