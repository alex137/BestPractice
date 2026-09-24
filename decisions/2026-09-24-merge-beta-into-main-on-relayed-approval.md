---
date: '2026-09-24'
question: |
  Morgan asked a session to merge `precedent-beta-v01` into `main`
  (213 commits, 187 files) and stated that Alex had approved it. Does that
  satisfy local/practices/merge-target-is-beta-branch.md's reservation of
  major `main` merges for Alex's go-ahead?
decision: |
  Yes, and the merge was performed. This is the case
  2026-09-21-merge-beta-into-main-on-relayed-approval.md already settled
  (strength: decided): an approval Morgan relays from Alex satisfies the
  gate. Under current-rule-governs the session applied that decision
  instead of reopening it.

  WHAT THIS RECORD DOES NOT ESTABLISH: this session never saw Alex's own
  words. Morgan's message was "Alex approved, merge precedent-beta-v01
  into main". Nothing here should be read as "Alex decided this" -- only
  as "Morgan stated Alex had approved".

  The first fold-in (PR #583) did not include switching the engine pin
  (SOURCE_BRANCH in tools/precedent_vendor_engine.py and
  tools/precedent_refresh_sources.py) from `precedent-beta-v01` to
  `main`, because Morgan's message approved the merge without mentioning
  it. He then said "Yes, switch other repos to update from main" (PR
  #584), and later the same day: "Follow your recommendation, merge it
  into the fold-in into main, and go update, it's alex-approved." A
  second fold-in carried it onto `main`, under the same relayed-approval
  reading.
alternatives: ["Ask Morgan again whether the relay covers the gate, as on
                2026-09-21",
               "Switch the engine pin in the same merge without a separate
                yes"]
decided_by: Morgan
strength: decided
---

## What was verified before merging

The clone was unshallowed first (`git fetch --unshallow`), because a
shallow clone gives wrong ancestry figures that look plausible
([gotcha-2026-09-13](../gotchas/gotcha-2026-09-13-this-repo-is-normally-cloned-depth-1-and-several-tools-degra.md)).

`merge-base(origin/main, origin/precedent-beta-v01)` is `c5a3b923`, and its
tree equals `origin/main`'s tree (`fb1e0a5f`). So `main` contributes no
content of its own, and the merge result is exactly the branch's tree.
Nothing can be silently dropped.

The branch tip's tree is identical to `6cc49af3`, which passed the deep
check that same day: `verify_harness.py --as-ci` (both shards, 0 failed),
`doc_lint.py`, `leak_gate.py`, `precedent_check.py --full-sweep`
(0 violated) and `doc_sync.py`.

## The second fold-in, later the same day

PR #584 was merged into `precedent-beta-v01` and folded into `main` right
after. The two had to land together: a repo refreshing in between would
read the new pin from staging and then the old one back from `main`.
The same checks were repeated on the unshallowed clone before merging:
`main` contributed no content of its own, and the branch tip passed the
deep check. The one exception was `merge-target-is-beta-branch`, which
fails whenever `precedent-beta-v01` is an ancestor of `main` and clears
once the next commit lands on the branch.
