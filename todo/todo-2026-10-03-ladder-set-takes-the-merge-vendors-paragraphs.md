---
slug:              todo-2026-10-03-ladder-set-takes-the-merge-vendors-paragraphs
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "BestPractice main carrying tools/precedent_merge_vendors.py (the next Produce), then an Update Vendors in precedent-shared-ladder, so the script its two paragraphs name is in that set's engine"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-03
closed:            null
---
## What

- <a id="ladder-set-takes-the-merge-vendors-paragraphs"></a>**Land
  `claude/2026-10-03-merge-takes-vendor-update-xxf54` in
  precedent-shared-ladder once its engine has the script.**

  BestPractice staging added a paragraph to `go-update` and one to
  `vendor-update-runbook` (a merge runs
  [tools/precedent_merge_vendors.py](../tools/precedent_merge_vendors.py)),
  while pre-staging was moving `go-update` into the ladder set. Merging
  staging into pre-staging kept the move here, and the two paragraphs were
  committed to the ladder set's own copies on that branch. The ladder set's
  check refuses them for now: its vendored engine predates the script, so a
  repo vendoring it would get the rule and not the script it names. That is
  right until main has the script.

## Closes when

The branch has landed on the ladder set's pre-staging, after an Update
Vendors there that brings in an engine containing
[precedent_merge_vendors.py](../tools/precedent_merge_vendors.py), and that set's deep check passes.
