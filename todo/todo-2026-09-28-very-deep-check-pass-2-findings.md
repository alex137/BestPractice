---
slug:              todo-2026-09-28-very-deep-check-pass-2-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-28
closed:            2026-10-17
---
## What

What the 2026-09-28 very deep check's pass 2 found and did not fix. The
noisy "other sources' checks" report, the gotcha fallback, the grandfather
lists and the isolation decision were fixed the same day.

- **For Morgan and Alex:** in BestPractice, `ci-workflow-approved` skips as
  the engine's origin, so `leak-gate.yml` (every push, every branch) and
  `deep-check.yml` are approved by nobody. Morgan asked for an explanation
  before deciding (2026-09-28); the recommendation given was to narrow
  `leak-gate.yml` to the tier branches, since every session's push check
  already runs the leak gate, and approve both in his own words.
- **For Morgan:** `precedent-individual/.github/workflows/engine-refresh.yml`
  is a manual button that opens a pull request into `main`, which
  promote-only forbids, and duplicates the one-command update. Explained
  2026-09-28; the recommendation is to delete it.

## Closed

Closed 2026-10-17 by the very deep check, pass 4, on its own condition. Both bullets met: deep-check.yml and leak-gate.yml carry Morgan's approval in precedent.json's github_ci_approved ("Both yml are fine and approved.", 2026-10-11), and the individual set's engine-refresh.yml is gone (the set carries no workflow).
