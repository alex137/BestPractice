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

## The third fold-in, later the same day

Morgan: "Alex gives his go ahead", in answer to a session that had said
the fold-in would carry PR #586 (CI cadence, with a new
`commit-identity.sh` hook) as well as PR #587 (the session-practices file
trimmed back under precedent-individual's 5,200-token ceiling). Read as
the same relayed approval as the two above, covering both. As before,
this session never saw Alex's own words.

Checked on an unshallowed clone before merging: `main` contributed no
content of its own, and the branch tip's tree was identical to the commit
that passed `verify_harness.py --as-ci` and CI. That run had one local
failure: `commit-identity.sh` copies not byte-identical. It came from a
precedent-individual clone on disk whose `bootstrap/` copy predates #586,
failed identically on the branch tip, and CI cannot see it.

## The fourth fold-in, later the same day

Morgan: "Alex gives his go ahead to merge into main", in answer to a
session that had said #589 (`ci_on_branches`, a personal switch that skips
CI on working branches) was on `precedent-beta-v01` and waiting for this
merge. Read as the same relayed approval as the three above. As before,
this session never saw Alex's own words.

Checked on an unshallowed clone before merging (PR #590): `main`
contributed no content of its own, and the branch tip's tree was identical
to `df17a4d`, which passed CI on #589. The local `--as-ci` run had the same
one failure as the third fold-in, from the same on-disk
precedent-individual clone.

## The fifth fold-in, later the same day

Morgan: "Alex gives his goahead to merge precedent-beta-v01 into main on
precedent", after a session had said the fold-in would carry #591 (every
Update Vendors retires the old install's leftovers) and #592 (every install
follows `precedent-beta-v01` again, for now). Read as the same relayed
approval as the four above. As before, this session never saw Alex's own
words.

#592 undid the second fold-in's pin switch, and so had to reach `main` as
well: an install pinned to `main` reads `SOURCE_BRANCH` from the engine it
vendored from there, and would otherwise never be pointed back.

Checked on an unshallowed clone before merging (PR #593): `main`
contributed no content of its own (merge-base tree `c15d6f5` is `main`'s
tree), and the branch tip's tree (`dbfaa4d`) was identical to #592's head,
which passed CI and a local `verify_harness.py --as-ci` with 0 failed.
After the merge, `main`'s tree is `dbfaa4d`.
