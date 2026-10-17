---
slug:              todo-2026-10-17-debut-misses-what-only-main-lacks
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "a design call on what a Debut compares against; out of scope for the Produce that found it"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-17
closed:            null
---
## What

Two gaps the Produce of 2026-10-17 ran into, both on the way to main.

- <a id="debut-compares-against-staging"></a>**A Debut can pass on a staging that fails GitHub's test on main.**
  The checks that judge a change by what it adds (rename-updates-links
  among them) take the landing branch, staging, as their base. GitHub's
  test on the pull request into main takes main. So a file deleted on
  staging by one session, and still named somewhere, never reaches a local
  check once the deletion has landed on staging, and only fails after the
  merge into main. On 2026-10-17 the Debut passed on staging at 98d6991b,
  and GitHub's test on main then failed rename-updates-links on three
  references to `tools/precedent_others_did.py`, which had moved into the
  ladder set that morning. Fixed by #1175 and #1176. What would have caught
  it: the Debut, or Produce's quick checks, also judging the change scope
  against main.
- <a id="issue-close-step-on-pr-runs"></a>**The deep-check workflow opens an issue when main's test fails on a pull request, and closes it only on a push to main.**
  After the fix passed on its pull request run, issue #1174 stayed open
  and was closed by hand. Either step should read the same event.

## How It Closes

When a Debut or a Produce judges branch-scope checks against main as well
as staging, and the workflow's close step runs on the same events as its
open step.

## Notes

2026-10-17: found by the session that ran "Debut then produce" for Morgan.
