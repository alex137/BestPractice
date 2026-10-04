---
slug:              todo-2026-10-04-consumer-catalogue-copy-lacks-gotchas
kind:              manual
domain:            mechanism
severity:          null
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-04
closed:            2026-10-04
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

## Resolution

Closed 2026-10-04 on its condition, the same day it was opened, by tracing it rather than waiting for a decision. Neither the rule nor the copy step was wrong. The consumer had these files until an update on 2026-09-30, made while the copy rules briefly left `gotchas/` out, deleted them. The rules shipped `gotchas/` again from 2026-10-01, but `precedent_local_edits.py` read every file upstream has and the copy lacks as the consumer's own deletion, so each later update "kept the local edit" and never copied them back. Fixed at the cause: a missing file counts as a local edit only when the consumer itself removed it, never when a vendor sync did (`_deleted_here`; test `check_a_sync_deletion_is_not_a_local_edit`). The consumer's next update brings the 67 files back.

