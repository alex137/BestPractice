---
slug:              todo-2026-09-07-undeclared-deprecated-files
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing any more: the one objection to the mechanical workflow check (a deliberately paused bestpractice-upstream-sync.yml in every consumer) ended 2026-09-24, when that file was retired. Out of scope for the change that retired it; a session can now build the check."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            null
---
## What

- <a id="undeclared-deprecated-files"></a>**Nothing finds a deprecated file nobody declared.**
  [decommission-deletes-files](../practices/decommission-deletes-files.md) landed
  2026-09-07 with an audit ([precedent_decommission.py](../tools/precedent_decommission.py))
  and a check that holds a decommissioning afterwards. Both work from a
  declaration: the audit is run by a person at the moment of decommissioning,
  and the check reads `process/decommissioned_paths.json`. Neither can look at a
  tree and say *this file is dead*. So the practice covers the moment a
  mechanism is decommissioned deliberately, and covers nothing at all in the case
  Morgan actually raised it against — a repo left alone for years, where
  the decommissioning moment passed without anyone noticing it was one.

  **One candidate was designed and rejected, so the next session does not
  re-derive it.** A check on `.github/workflows/`: a workflow whose only
  trigger is `workflow_dispatch`, or whose schedule is commented out, is a
  decommissioning someone started and never finished. It is mechanical, it is
  cheap, and it targets exactly the shape this practice was raised about.
  **It was rejected on 2026-09-07 for a reason that no longer holds.** It
  fired hardest on the one case this repo then held on purpose — every
  consumer's `bestpractice-upstream-sync.yml`, parked on
  `workflow_dispatch` per
  [`relax-the-pinned-branch-hold`](todo-2026-09-06-relax-the-pinned-branch-hold.md) —
  so shipping it would have failed every consuming repo for doing what
  this repo told it to do. On 2026-09-24 that file was retired and the
  refresh now deletes it (Morgan, strength: decided), so the check no
  longer has a deliberate hold to trip over. A repo that pauses a
  workflow of its own on purpose can still say so: `local_ci_workflows` in
  `precedent.json` takes a path and a reason, which is the declaration
  this paragraph used to say was missing.

  **Not blocked any more; out of scope for the change that unblocked it.**
  The cheaper half landed 2026-09-17 (Notes).

## How It Closes

When something finds a deprecated file nobody declared: the mechanical `.github/workflows/` check above, honouring `local_ci_workflows` as the declared exception, or a decision that the very-deep-check pass is enough.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

2026-09-17: the cheaper half landed — [very-deep-check](../practices/very-deep-check.md)'s
Pass 4 now carries a "Deprecated files nothing has decommissioned" item that
reads every mechanism in force against whether anything still calls it, runs
[tools/precedent_decommission.py](../tools/precedent_decommission.py) on what
plainly does not, and asks the session's user wherever the verdict is
unclear, rather than guessing (Morgan, strength: decided). **Still blocked
on the design call above** — nothing here declares a deliberate pause with a
stated condition for lifting it, so a mechanical scan of `.github/workflows/`
for a paused schedule would still fire identically on a deliberate hold and
an abandoned one; that half stays open.

2026-09-24: the design call this item waited on was needed only because of
one deliberate hold, `bestpractice-upstream-sync.yml`, and that file is now
retired. `precedent_vendor_engine.py refresh` recognises it and
`bestpractice-docs.yml` by content and deletes them in every install on its
next `Update Vendors`, and
[vendor-update-runbook](../practices/vendor-update-runbook.md) step 10 has
the session read every other leftover name. So the old install's leftovers
are covered; this item is left with the general case, a dead file of the
repo's own.
