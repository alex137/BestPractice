---
slug:              todo-2026-09-07-undeclared-deprecated-files
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "that design call. The cheaper half is not blocked and is worth doing first — teaching [very-deep-check](../practices/very-deep-check.md)'s housekeeping pass to look for dead paths by hand, which is where a judgment a script cannot make already belongs."
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
  It was not built because it fires hardest on the one case this repo
  *deliberately* holds — every consumer's paused `bestpractice-upstream-sync.yml`,
  parked on `workflow_dispatch` on purpose per
  [`relax-the-pinned-branch-hold`](todo-2026-09-06-relax-the-pinned-branch-hold.md) —
  so shipping it means every consuming repo starts failing a check for
  doing what this repo told it to do. Making it honest needs a way to
  declare a pause with a stated condition for lifting it, which is a
  design call rather than a check.

  **Blocked on:** that design call. The cheaper half is not blocked and is
  worth doing first — teaching
  [very-deep-check](../practices/very-deep-check.md)'s housekeeping pass to
  look for dead paths by hand, which is where a judgment a script cannot
  make already belongs.

## How It Closes

Not open until: that design call. The cheaper half is not blocked and is worth doing first — teaching [very-deep-check](../practices/very-deep-check.md)'s housekeeping pass to look for dead paths by hand, which is where a judgment a script cannot make already belongs.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
