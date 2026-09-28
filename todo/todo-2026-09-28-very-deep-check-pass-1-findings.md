---
slug:              todo-2026-09-28-very-deep-check-pass-1-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-28
closed:            null
---
## What

What the 2026-09-28 very deep check's pass 1 found and did not fix. Both
items this file held after the first day were fixed the same day in a
second round (the install-once drift report in `precedent_update.py`, and
the SessionStart hook running `bootstrap.sh` locally without its package
install or machine-wide git setup). What that fix turned up:

- **For Morgan: `commit-identity.sh` still makes machine-wide writes in a
  local session.** The shipped Claude Code settings wire it as its own
  SessionStart hook with no remote-only gate, so on a person's own computer
  it sets the global git identity (declared identities only), installs a
  global `core.hooksPath`, and tries to relink `/etc/localtime`. The
  recommendation is to gate those three steps on `CLAUDE_CODE_REMOTE`
  and keep its repo-local part.
- **Codex and Gemini CLI local sessions still run the package install**:
  their shipped hook files run `tools/bootstrap.sh` without
  `PRECEDENT_LOCAL_SESSION`, and neither harness sets a variable that tells
  local from hosted. Recorded in the harness ledger's 2026-09-28 row.
