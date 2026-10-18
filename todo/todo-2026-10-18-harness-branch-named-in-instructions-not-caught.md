---
slug:              todo-2026-10-18-harness-branch-named-in-instructions-not-caught
kind:              analysis
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
noted:             2026-10-18
closed:            2026-10-18
---
## What

A ladder-set session's push was refused by `tools/branch_name_guard.py
--pre-push` for a harness branch name (`claude/...`), and nothing warned at
session start. The session-start note added in precedent-shared-ladder
670f23e (`harness-branch-settled-at-start`) did not fire, for two reasons:

1. That commit is still only on precedent-shared-ladder's `staging`, not
   `main`.
2. It looks only at a checkout sitting on a harness name. Here the harness
   name was in the session's instructions, and the session created the branch
   itself after start, so no checkout was on it yet.

The fix belongs in precedent-shared-ladder, in `tools/branch_name_guard.py
--session-start`. Have it also fire when the session's designated branch (in
the instructions, or in the session's outcome branches) is a harness name.
Failing that, tell every ladder session at start to name its branch with
[`precedent_branch_name.py`](../tools/precedent_branch_name.py) before its first commit. Add a case to
`tools/checks/tests/test_session_branch_name.sh`.

Filed here because the BestPractice session that took the other root issues
from the same Update Vendors run (branch
`2026-10-18-themorgan-root-fixes-from-update-vendors-y7plp-mahoa`) had no
push access to the ladder set. It closes when the fix lands on the ladder
set's landing branch.

## Closed

Closed 2026-10-18 on its own condition: the fix landed on the ladder set's
landing branch, `staging`, in
[themorgan/precedent-shared-ladder#106](https://github.com/themorgan/precedent-shared-ladder/pull/106)
(merge commit 6127317). It took the item's fallback, not its first choice:
nothing inside the container carries the session's instructions or outcome
branches, so `tools/branch_name_guard.py --session-start` now tells every
cloud ladder session not already on a tool-made branch to name its branch
with [`precedent_branch_name.py`](../tools/precedent_branch_name.py) and never to create a `claude/` or
`session/` branch, even when the instructions name one. New cases in
`tools/checks/tests/test_session_branch_name.sh`. Consumers get it at the
ladder set's next move into `main`.
