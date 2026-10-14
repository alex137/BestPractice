---
slug:              todo-2026-10-14-delete-pre-staging-code
kind:              manual
domain:            engine
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "every repository Morgan uses Precedent in has run Update Vendors with the engine that retires pre-staging for everyone (spec/PRE_STAGING_RETIREMENT_PLAN.md), so none still carries a pre-staging branch or a landing_branch of pre-staging"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-14
closed:            null
---
## What

Delete the engine code that only served the pre-staging tier, and its
tests: `--sync-pre-staging`, Promote's pre-staging-into-staging path, the
`retire_pre_staging` setting, `retire_pre_staging_step` in
[tools/precedent_update.py](../tools/precedent_update.py) and what only it uses, and the harness checks
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
