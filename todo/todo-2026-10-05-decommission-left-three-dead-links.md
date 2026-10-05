---
slug:              todo-2026-10-05-decommission-left-three-dead-links
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "out of scope for the repo-maintenance fold that found it; the links themselves are fixed, the cause is not"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-05
closed:            null
---
## What

- <a id="decommission-left-dead-links"></a>**Find out why retiring
  `templates/github-actions/precedent-check.yml.template` left three
  relative links to it.**

  Commit `94277c00` (2026-10-01) deleted the template and recorded it in
  `process/decommissioned_paths.json`. Two links in
  [spec/CI_MINUTES_PLAN.md](../spec/CI_MINUTES_PLAN.md) and one in
  [todo-2026-09-14-source-set-push-triggers.md](todo-2026-09-14-source-set-push-triggers.md)
  went on pointing at it. `doc_lint.py` fails them, but only runs on files a
  commit touches, so nothing reported them until the `light-check` check,
  ported into universal on 2026-10-05, read the whole tree. They now point
  at the template's last commit on GitHub.

## Proposed

[tools/precedent_decommission.py](../tools/precedent_decommission.py)
says it blocks while any tracked file still mentions the path, and
`rename-updates-links` says it catches what is left after. Check whether the
deletion went through the tool at all, and if it did, which of the two let
a relative link to a deleted file through.
