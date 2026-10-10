---
slug:              todo-2026-10-10-others-did-mark-cannot-be-pushed-from-a-cloud-session
kind:              decision
domain:            engine
severity:          notable
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "Morgan's choice of where the mark lives"
batch:             null
decision:          null
decision_strength: null
waiting_on:        Morgan
noted:             2026-10-10
closed:            null
---
## What

**From a cloud session, the others-did mark cannot be pushed to where it
lives, so the daily "what others landed" report may never fire there.**
[tools/precedent_others_did.py](../tools/precedent_others_did.py) keeps each
person's mark on origin's `refs/precedent/others-did`, a ref outside every
branch. Measured 2026-10-10 in a consuming repository: the session's git
proxy answers that push with HTTP 403, while branch pushes to the same
repository go through. The mark then lives in the container only, and a new
container starts the baseline over.

## Options

1. **An orphan branch, `precedent/others-did`.** Pushable from a cloud
   session today. It shows in every repository's branch list, and the
   branch sweep and the "branches you can delete" lists would have to leave
   it alone. It never rides a Promote: it shares no history with the tiers.
2. **Write the ref through the GitHub API** (create the blob, tree and
   commit, then the ref), which the proxy may treat differently from a git
   push. Unmeasured, and much more code than a push.
3. **Leave it.** Cloud sessions keep re-baselining, and the report only
   fires from a machine that can push the ref.

My pick is 1: it is measured to work, and a branch nobody merges is the
standard home for data like this. Its cost is one extra branch name per
repository.

## Notes

Found from a relay by the session that ran Update Vendors in a consuming
repository on 2026-10-10. The refusal message used to carry no reason,
because the helper kept git's stdout and a refused push explains itself on
stderr. That is fixed beside this item, with the harness test
`check_others_did_says_why_its_push_was_refused`.
