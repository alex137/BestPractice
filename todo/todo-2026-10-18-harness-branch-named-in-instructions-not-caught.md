---
slug:              todo-2026-10-18-harness-branch-named-in-instructions-not-caught
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        push access to themorgan/precedent-shared-ladder in a session working on it
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-18
closed:            null
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
