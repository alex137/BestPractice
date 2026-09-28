---
slug:              todo-2026-09-28-very-deep-check-pass-2-findings
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

What the 2026-09-28 very deep check's pass 2 found and the same day did not
fix. The mechanism defects it found in the check itself and in five
enforced checks were fixed that day on `claude/very-deep-check-2amsjs`.

- **The new "other sources' checks" report is noisy in BestPractice.**
  Running each declared source's checks here (added 2026-09-28) finds five
  violations that read as false positives in the engine's own repo:
  `deep-check` wants `tools/checks/tests/run_all.sh` (a consumer's file),
  `light-check` flags a link inside an eval fixture, `no-stale-counts` flags
  a dated measurement in INSTALL.md, `session-trailer` flags one historical
  commit, `assorted-notes` flags a philosophy link. Each needs a verdict:
  exempt here with a reason, or fix.
- `environment-gotchas`' pre-migration fallback still validates an inline
  index rather than saying "migrate to gotchas/"; changing it fails every
  unmigrated consumer, so it waits for a decision.
- `grandfathered_commit_shas` in two shared sets' `precedent.json` is read
  by nothing since 2026-09-25; keep it as a record with a comment saying so.
- **For Morgan and Alex:** in BestPractice, `ci-workflow-approved` skips as
  the engine's origin, so `leak-gate.yml` (every push, every branch) and
  `deep-check.yml` are approved by nobody. Approve them in your own words,
  or narrow the triggers.
- **For Morgan:** `precedent-individual/.github/workflows/engine-refresh.yml`
  is dispatch-only, and if clicked opens a PR into `main`, against
  promote-only; it duplicates the one-command update. Delete it, or pin its
  base to the landing branch.
- **For Morgan:** `decisions/2026-09-01-relax-private-repo-isolation.md`
  says the relaxation is reinstated no later than phase 7; phase 7 merged
  and nothing reinstated or extended it.
