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

What has to be true: the mark survives a new container, and a cloud session
can write it. Measured: a branch push works there; a ref outside branches
(`refs/precedent/...`) is refused with 403.

1. **Keep no mark at all: report what others landed since your own last
   commit in the repository.** Nothing to store and nothing to push, so it
   works in every environment, with no access beyond reading the repository.
   The report reads "since you last committed here, on DATE". Cost: until
   you commit in that repository again, each new container repeats the same
   list. The container's own mark still stops a repeat inside one session.
   The wording changes from "since you were last told" to "since your last
   commit".
2. **An orphan branch, `precedent/others-did`.** Pushable today. It shares
   no history with the tiers, so it never rides a Promote. Costs: one extra
   branch in every repository's branch list; the branch sweep and the
   "branches you can delete" lists must leave it out; and a workflow that
   runs on a push to any branch runs on every mark. BestPractice's
   `leak-gate.yml` does, so it would bill one job per mark until that
   workflow skips the branch. Deleting it by accident only restarts the
   baseline.
3. **A file on the landing branch** -- how the mark worked until
   2026-10-08. Pushable. It was moved off because a mark commit landed on
   staging and rode the next Produce to main, every day.
4. **Write the ref through GitHub's API** (blob, tree, commit, then the ref
   under `refs/precedent/`). The API needs the repository attached with
   access "push", which a session usually is not. Unmeasured whether the
   proxy allows it. The most code of any option.
5. **Keep every repository's marks in your individual set.** One place per
   person. A session in another repository needs push access to the
   individual set to write it, and it normally has read access only, so this
   fails in the same sessions it is meant to fix.
6. **A GitHub issue or a repository variable holding the mark.** Visible
   to every collaborator, needs API access with "push", and a variable
   needs admin rights. Worse than 4 on every count.
7. **Leave it as it is.** Cloud sessions re-baseline in every new container,
   and the report fires only from a machine that can push the ref.

**My pick is 1.** It needs no permission anywhere, and "since your last
commit here" is close to what the report is for. Its one cost, a repeated
list until you commit, is small in the repositories you work in. If
repeats are not acceptable, 2 is the one that works today.

## Notes

Found from a relay by the session that ran Update Vendors in a consuming
repository on 2026-10-10. The refusal message used to carry no reason,
because the helper kept git's stdout and a refused push explains itself on
stderr. That is fixed beside this item, with the harness test
`check_others_did_says_why_its_push_was_refused`.
