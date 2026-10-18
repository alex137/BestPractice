---
slug:              todo-2026-10-18-landing-guard-refusal-promises-checks
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

precedent-shared-ladder's [`tools/landing_pr_guard.py`](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/landing_pr_guard.py) refuses a high-risk
push to the landing branch and says "open a pull request into staging, and
merge it once its checks pass". In BestPractice no workflow runs on pull
requests into `staging`, so that sentence sends a session to wait for checks
that never start. A session did exactly that on 2026-10-18
([gotcha](../gotchas/gotcha-2026-10-18-no-check-runs-on-a-pull-request-into-staging.md)).

BestPractice's land tool now prints the right next step after the refusal
(`pull_request_route_note` in
[tools/precedent_branches.py](../tools/precedent_branches.py)). The guard's
own wording is still wrong at the source. The fix there: have `refusal()`
call `precedent_branches.pull_request_route_note(root, landing)` when it
can import it, or say "merge it once its checks pass, or at once if the
pull request shows none". Closes when that lands on the ladder set's
landing branch.
