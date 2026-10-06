---
slug:              todo-2026-10-05-confirm-main-deep-check-after-the-actions-outage
kind:              manual
domain:            mechanism
severity:          null
status:            done
disposition:       ask
remind_on:         null
blocked_on:        "GitHub Actions recovering from its 2026-10-05 degraded availability"
batch:             null
decision:          "merge #897 into main without its GitHub test, once, because of the outage"
decision_strength: decided
waiting_on:        null
noted:             2026-10-05
closed:            2026-10-05
---
## What

- [ ] **Confirm main's Deep check once Actions is back.** On 2026-10-05,
  GitHub announced degraded availability for Actions. Runs sat queued with
  no runner, and the ones on main were cancelled after 15 minutes. Morgan
  said "Produce, skip the GitHub test", so
  [alex137/BestPractice#897](https://github.com/alex137/BestPractice/pull/897)
  (the practice standing field, the binary-conflict fix, two gotchas) went
  into main on the full local check alone. That check passed on the exact
  tree. When Actions works again, read the Deep check run on main's merge
  commit `315c080f`. If it never ran or was cancelled, re-run it once. If
  it fails, fix it as usual.

## How It Closes

Closes when a Deep check on main, at `315c080f` or later, has passed.

## Notes

The skip is recorded on the pull request itself, in a comment, so Alex
sees why the gate was skipped.

**Closed 2026-10-05.** Deep check run 37379169605 on main passed at `4116bb7a`, which descends from `315c080f` (checked 2026-10-05, very deep check pass 4). The run at `315c080f` itself, 37372997436, had failed.
