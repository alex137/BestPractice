---
slug:              todo-2026-09-21-refresh-deletes-a-workflow-another-file-depends-on
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

**The engine refresh deleted a workflow that another paused workflow named as
the place its checks had been folded into, and neither file noticed.** Two
commit-scope checks now run nowhere, and nothing reported it.

The chain, measured 2026-09-21 against each repository's own `origin/main`:

1. `commit-identity.yml` in the individual source ran that repository's two
   private commit-scope checks -- the commit-author one and the date-offset one
   -- on every non-draft pull request.
2. It was **paused** that same day, and its own header says why, in as many
   words: *"Both checks below now run as steps in
   `.github/workflows/precedent-check.yml`'s single job ... so every event this
   file used to answer is already covered, by a job that is billed anyway."*
   Its `on:` block now carries only `workflow_dispatch`.
3. Hours later `source-sets-run-no-ci` landed, `CI_WORKFLOW_TEMPLATES['source']`
   went empty, and `_remove_retired_ci_workflow_files` deleted
   `precedent-check.yml` from all four sets on the next refresh.
4. The fold's destination is gone. The pause's premise was true when it was
   written and false four hours later. Both checks run nowhere.

## Why it is the engine's problem and not that repository's

[tools/precedent_decommission.py](../tools/precedent_decommission.py) already refuses to delete a workflow whose `on:`
block carries a live trigger, and reports every file that still names it —
sixteen of them for `commit-identity.yml`. That gate exists because a sweep on
2026-09-20 deleted nine live checks across nine repositories on a filename and
all nine had to be restored.

**The refresh path does not go through that gate.**
`_remove_retired_ci_workflow_files` sweeps by recognised `kind` and deletes,
with no blocker scan and no report of who named the file. So the one mechanism
built for exactly this failure was bypassed by the one caller most likely to
trigger it — an engine update, which is the moment a repository is least
watched.

## The shape of the fix

Not "run the whole decommission gate on every refresh" — that is heavy and
would block routine updates. The narrow version: **before deleting a retired
workflow, grep the destination tree for its filename and print every file that
names it**, as a warning on the refresh's own output, not a refusal. A file
that names a workflow it expects to run is the signal; a record that merely
cites it by name is noise, and a human reading four lines can tell them apart
where a predicate cannot.

The deeper rule this is an instance of is worth stating whether or not the
guard gets built: **a mechanism paused because its job moved elsewhere is
coupled to wherever it moved, and nothing in either file records the coupling.**
The pause note named its destination in prose. Prose is not a check.

## Not yet fixed in the affected repository

Restoring the two checks is work in `themorgan/precedent-individual`, which
this session cannot push to — the git proxy refuses a credential for that owner
(403, measured 2026-09-21). The right home for them is that repository's own
push gate rather than any workflow: a local gate costs no Actions minutes and
so survives `source-sets-run-no-ci` unchanged, which the CI fold did not.
