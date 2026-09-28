---
slug:              todo-2026-09-06-actions-as-enforcement-layer
kind:              analysis
domain:            null
severity:          null
status:            dropped
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Overtaken the other way: source-sets-run-no-ci and actions-minutes-are-scarce moved enforcement into the local push check and the session hooks, and Actions minutes are kept for the tier branches."
decision_strength: assented
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-28
---
## What

- <a id="actions-as-enforcement-layer"></a>**Lean further into GitHub Actions as the enforcement layer.** The
   markdown-lint workflow ([GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md)) proves
   the pattern: checks run in CI, so they bind every contributor — human,
   Claude Code, ChatGPT, anyone — regardless of whether the agent has a
   shell. Candidates to add: [practice_audit.py](../tools/practice_audit.py)
   (manifest drift + scrub gate) as a required PR check; a deck-build
   check when deck sources change; a check that flags agent-authored
   commits on PR branches (attribution convention). Field evidence
   (2026-08, a dependent repo's first member PRs): merges made through
   the GitHub web UI, so the merge-runbook gates — capture, export,
   audits — never ran, and every commit landed authored as the agent.
   Runbook gates bind only sessions that run the runbook; required CI
   checks bind every path to the default branch.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.

**Closed 2026-09-28 (dropped).** Overtaken the other way: source-sets-run-no-ci and actions-minutes-are-scarce moved enforcement into the local push check and the session hooks, and Actions minutes are kept for the tier branches. Morgan approved the very deep check's pass-4 recommendation to close it, 2026-09-28 ("Make the changes you recommend"); strength: assented.
