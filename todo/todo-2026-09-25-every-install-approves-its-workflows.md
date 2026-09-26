---
slug:              todo-2026-09-25-every-install-approves-its-workflows
kind:              manual
domain:            vendoring
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "each install's next Update Vendors, where step 10(g) asks Morgan about every workflow file that stays"
noted:             2026-09-25
closed:            null
---
## What

**Every install still carries workflow files nobody has approved under
[ci-workflow-approved](../practices/ci-workflow-approved.md).** The check
fails every push in a repo until each one is approved or deleted, so each
install meets it at its next Update Vendors. This item closes when every
install passes `python3 tools/precedent_check.py --only
ci-workflow-approved`.

**How to find them:** the usage export Morgan pulls from GitHub names every
repo and workflow file that billed. On 2026-09-25, a dozen private consumers
still carried their own `light-check.yml`, and three carried other
repo-owned checks. One was fixed that day: the one ci-workflow-approved's Story is
about. The rest meet the check at their next update. A name is a lead,
never a verdict: read each file before deciding anything.

**The shape to look for first** is the one that cost the first repo: a
`push:` trigger on `main` in a repo where work lands by pull request. Every
merge is then a push to `main`, and GitHub writes the merge commit without
the working-branch `[skip ci]`, so each merge bills a runner. The
pull-request runs were already being skipped.

## Story

Morgan, 2026-09-25, on seeing one repo bill 11 minutes on a day he
expected close to zero: "please make sure these legacy migration issues are
fully solved". The repo that prompted it was fixed the same day. Two others
billed that day too. One could not be attached from the session that wrote
this item, so it went out as a handoff; the other is being handled in its
own session.
