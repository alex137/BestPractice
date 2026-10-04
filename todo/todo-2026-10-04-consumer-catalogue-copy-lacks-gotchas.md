---
slug:              todo-2026-10-04-consumer-catalogue-copy-lacks-gotchas
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-04
closed:            null
---
## What

- <a id="consumer-catalogue-copy-lacks-gotchas"></a>**A consumer's catalogue
  copy has no `gotchas/` at all, though the vendoring rules say it ships.**
  Found while making `precedent_local_edits.py status` fetch the vendored-from
  commit (so it can finally judge a consumer's catalogue): run in a consumer
  synced to `f83459fc`, it listed 67 `gotchas/` files as local changes. They
  are not edits. `checkin.vendoring_rule('gotchas/…')` says they ship
  ("traps a session using Precedent can hit"), but the consumer's
  `process/upstream/` has no `gotchas/` directory, so `local_changes()` reads
  each one as deleted here. Two consequences:
  - `send --layer catalogue` would offer those "deletions" upstream.
  - A session there that greps the vendored gotchas, as
    `environment-gotchas` tells it to, finds none.

  Not in scope for the PR that surfaced it. **Why queued:** the fix needs a
  decision on which side is wrong, the rule or the update's copy step, and a
  look at a consumer's update log to see where the directory went.
