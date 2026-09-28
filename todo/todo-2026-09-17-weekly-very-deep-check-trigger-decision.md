---
slug:              todo-2026-09-17-weekly-very-deep-check-trigger-decision
kind:              manual
domain:            null
severity:          null
status:            dropped
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Not pursued: a person can start a very deep check by name, so a weekly Routine fails crons-are-a-last-resort, and the check is kept to the literal ask because it is expensive."
decision_strength: assented
waiting_on:        "Morgan"
noted:             2026-09-17
closed:            2026-09-28
---
## What

Decide on, and if approved create, the weekly `very-deep-check` Routine
discussed 2026-09-17. The design is worked out: a weekly cron, fresh
session per fire, resuming from
[spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md)'s next unfinished
pass, fixing small findings and pushing them to `precedent-beta-v01` via a
pull request — never merging, never touching `main` — and filing anything
that needs Morgan's own judgment call (the base-branch row-by-row carry
list, a keep/cheapen/retire call on a quiet section) as its own `ask` item
rather than deciding it.

Still open: whether the Routine's own `notifications: {push, email}`
completion alert is wanted on top of GitHub's ordinary PR notification, or
whether the PR notification alone is enough. Nothing has been created yet.

## How It Closes

`status` becomes `done` when Morgan has settled the notification setting
and either the trigger is created, or he decides not to pursue it.

## Notes

2026-09-17: written on "Todo reminder" — `remind_on` is this Saturday
(2026-09-19); raise it again then if it's still open.

**Closed 2026-09-28 (dropped).** Not pursued: a person can start a very deep check by name, so a weekly Routine fails crons-are-a-last-resort, and the check is kept to the literal ask because it is expensive. Morgan approved the very deep check's pass-4 recommendation to close it, 2026-09-28 ("Make the changes you recommend"); strength: assented.
