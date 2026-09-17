---
slug:              todo-2026-09-17-access-probe-plant-not-detected
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-17
closed:            null
---
## What

- <a id="access-probe-plant-not-detected"></a>**[tools/verify_harness.py](../tools/verify_harness.py)'s
  `check_precedent_check_fires` reports `access-probe-is-wired`'s planted
  violation as undetected.** Found 2026-09-17, running the deep-check suite
  before pushing an unrelated documentation move.

  The self-test swaps the invocation line in `.claude/hooks/session-start.sh`
  and `templates/bootstrap.sh` for a different script name, then expects
  `python3 tools/precedent_check.py --only access-probe-is-wired` to fail on
  the copy. It came back `1 passed, 0 violated` instead — the planted
  violation went uncaught.

  **Confirmed unrelated to the documentation move.** Both wiring files were
  last touched at `a09843d3`, well before this session's commit, and carry
  the correct invocation line
  (`python3 tools/precedent_access_check.py .`) in the real tree — this is
  the self-test's own detection failing on a scratch copy, not a real gap in
  either file.

  **Not investigated further** — out of scope for the task this session was
  doing ([practices/very-deep-check.md](../practices/very-deep-check.md)'s
  pass 2, question 3, "does anything named `--check` write" and the sibling
  questions there, is the closest existing lens; nobody has read
  `_access_probe_is_wired` or the plant fixture against them yet).
