---
slug:              todo-2026-09-21-leak-gate-self-heals-by-cloning-into-home
kind:              manual
domain:            security
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

[tools/leak_gate.py](../tools/leak_gate.py) self-heals a missing private
blocklist by **cloning the individual practice set into `$HOME`**. Whether
the vocabulary layer runs therefore depends on whether that clone succeeds —
which differs between a developer's container, a CI runner, and any machine
without the credential.

Found 2026-09-21 by the session smoke-testing `leak-gate.yml` before
installing it, alongside the `--structural-only` bug fixed the same day. Its
conclusion, and it is the right one: **the gate's verdict is not
reproducible across environments, so a local pass does not predict CI.**

## Why It Matters

A leak gate is supposed to answer one question the same way everywhere. This
one answers it differently depending on whether a network clone worked. Two
distinct problems live in that:

- **A gate that silently scans less** where the clone failed. The existing
  PARTIAL reporting says so, which is the mitigation — but the exit code is
  the same, and a workflow reads the exit code.
- **A gate that performs a network write to `$HOME` as a side effect of
  being asked a question.** That is surprising in a pre-push hook and more
  surprising on a shared runner.

Fixing `--structural-only` (2026-09-21) removes this for the CI path
specifically: that flag now drops the vocabulary layer outright rather than
merely not requiring it, so the workflow's answer no longer depends on
whether a clone happened. **The local path is unchanged and still
environment-dependent.**

## What Would Close It

A decision, then a small change. Candidates, none chosen:

1. **Never clone as a side effect.** Resolve what is already on disk; if the
   private list is absent, report PARTIAL and carry on. Self-healing moves
   to an explicit command a person runs.
2. **Clone only when a session-start hook asks for it**, never from inside a
   scan, so the scan is pure.
3. **Keep it, and make the exit code carry the difference** — a distinct
   status for "scanned completely" versus "scanned the publishable half
   only", so a caller can tell them apart without parsing prose.

Option 1 is the one that makes the gate reproducible, which is what the
finding is actually about.
