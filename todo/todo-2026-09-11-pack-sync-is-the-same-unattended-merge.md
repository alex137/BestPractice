---
slug:              todo-2026-09-11-pack-sync-is-the-same-unattended-merge
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          ""let's get rid of pack-sync" -- Morgan retired the practice, same reasoning as bestpractice-sync."
decision_strength: decided
waiting_on:        null
noted:             2026-09-11
closed:            2026-09-11
---
## What

- <a id="pack-sync-is-the-same-unattended-merge"></a>**`pack-sync` mandates the unattended self-merging run that
  `bestpractice-sync` was just retired for.** Morgan retired
  `bestpractice-sync` on 2026-09-11 — *"now that it's getting more complex,
  I'm more hesitant about syncing it automatically"* — and it was the
  universal half of a pair. `pack-sync`, still active in the maintainers'
  set, is the same compare-then-update workflow pointed at that team's own
  **private** source, and its own Story calls it "an unattended self-merging
  run". The reasoning that retired the first applies to the second without
  modification, and arguably harder: the private half is the one whose
  auto-merged pull request nobody outside the team can review.

  It stays in force because the instruction named `bestpractice-sync` and
  nothing else, and **a decision is not widened on the person's behalf**.
  What was done instead: both its Rule and its Install had defined
  themselves by pointing at the retired sibling ("same shape as", "same
  reason as"), and both now say it in their own words, because a rule in
  force must not be readable only through a retired one.

  **DONE 2026-09-11**, hours after it was opened. Morgan: *"let's get rid of
  pack-sync"*, `strength: decided`. It is `status: retired` with
  `in_force_at: none`, and `bestpractice-sync`'s Story — which said this one
  was "left open deliberately" — now says what actually happened.

  **The few hours in between are the part worth keeping.** The instruction
  that retired the first practice named the first practice. A session that
  had widened it would have got the same end state and learned nothing; a
  session that had said nothing would have left a rule in force that its
  owner had already stopped believing in. Raising it cost one line to ask
  and one line to answer.

  **One thing genuinely went with the rule, and it is named rather than
  glossed.** `pack-sync` carried a design decision its sibling did not: the
  private source needs its own repository credential, and a missing one
  **skips** the update rather than failing the workflow — while raising a
  tracked issue every time it skips, so a token never set or later revoked
  is noticed the same day instead of by chance. That pattern is not about
  syncing, and it survives as `automation-issues`, still in force in that
  set, which says the same thing for any unattended job.

  **What is now true across the whole system:** no practice anywhere asks
  for an unattended merge. The update path is `Update Vendors`
  ([vendor-update-runbook](../practices/vendor-update-runbook.md)), started by
  a person, with that team set's `drift-notice` telling a session at session start that a
  source has moved.

## How It Closes

Already closed 2026-09-11 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
