---
slug:              todo-2026-10-14-delete-pre-staging-code
kind:              manual
domain:            engine
severity:          null
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-14
closed:            2026-10-17
---
## What

Delete the engine code that only served the pre-staging tier, and its
tests: `--sync-pre-staging`, Promote's pre-staging-into-staging path, the
`retire_pre_staging` setting, `retire_pre_staging_step` in
[tools/precedent_update.py](../tools/precedent_update.py) and what only it uses, the pre-staging
branch in [templates/bootstrap.sh](../templates/bootstrap.sh)'s base-branch choice, the
`retire_pre_staging` key in Morgan's identity.json, and the harness checks
for all of these (practice: decommission-deletes-files).

## Why it waits

Pre-staging was retired for everyone on 2026-10-14
([spec/PRE_STAGING_RETIREMENT_PLAN.md](../spec/PRE_STAGING_RETIREMENT_PLAN.md)).
The step that moves a repository off it runs at that repository's next
Update Vendors, and it uses the code this item deletes. Deleting it first
would strand any repository that has not updated yet.

## Closes when

Update All Vendors has run with that engine and no repository's origin
has a `pre-staging` branch or a precedent.json `landing_branch` of
`pre-staging`; then the code is deleted, the full suite passes, and this
item closes.

## Notes

- 2026-10-17, Morgan, strength: decided: "pre-staging is deprecated so it
  should no longer do this and any mention of pre-staging it finds should
  be fixed to assume its deprecation." So the code goes now, and every
  mention of pre-staging is rewritten to assume it is retired (history in
  a `## Story` stays history). Before deleting the step that moves a
  repository off pre-staging, check every repository Precedent is used in
  for a leftover `pre-staging` branch or `landing_branch` and move any
  work on it into `staging` first, so nothing is lost. Handed to the
  session doing the enforcement plan's part 3, which is splitting the same
  file (precedent_branches.py): deleting pre-staging first leaves less to
  move.
- 2026-10-17, checked every repository Precedent is used in. A leftover
  `pre-staging` branch, already contained in `staging`: four repositories.
  Still landing on `pre-staging`, with two commits not in `staging`: one
  private repository, last touched 2026-09-28. Its work moves into its `staging` before the
  retirement step is deleted; that merge waits on Morgan's word, since it
  writes to another repository.
- 2026-10-17, the step that moves a repository off pre-staging became a
  migration, [tools/migration_retire_pre_staging.py](../tools/migration_retire_pre_staging.py),
  which Update Vendors runs without naming it (PR #1184). It is kept, not
  deleted, so a repository that has not updated loses nothing, and the
  instruction above to check every repository first no longer applies.
  A sweep across many repositories needs Morgan's approval first, naming
  each (Morgan, 2026-10-17, decided: "ANYTHING TO OPEN ALL THE REPOS MUST
  GET SESSION USER APPROVAL").
- 2026-10-17, closed. The code is deleted and every mention in active use
  is gone (the engine, its tests, the practices' rules, the templates and
  settings); pre-staging is named only in
  [tools/migration_retire_pre_staging.py](../tools/migration_retire_pre_staging.py),
  its test, and history. The condition above waited for Update All
  Vendors because deleting the step first would strand a repository that
  had not updated. Morgan's decision the same day ("the code goes now",
  above) and the migration change that: the step is kept as a migration,
  so no repository is stranded, and the migration file is deleted on its
  own once no repository needs it. Read as met on that basis; reopen if
  the Update All Vendors run is still wanted first.
