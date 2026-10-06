---
slug:              todo-2026-10-03-ladder-set-takes-the-merge-vendors-paragraphs
kind:              manual
domain:            mechanism
severity:          null
status:            done
disposition:       ask
remind_on:         null
blocked_on:        "BestPractice main carrying tools/precedent_merge_vendors.py (the next Produce), then an Update Vendors in precedent-shared-ladder, so the script its two paragraphs name is in that set's engine"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-03
closed:            2026-10-06
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

## Notes

2026-10-06: closed on its condition. The ladder set's engine carries
[precedent_merge_vendors.py](../tools/precedent_merge_vendors.py), the
branch merged cleanly, and it landed on the set's pre-staging in
[precedent-shared-ladder#13](https://github.com/themorgan/precedent-shared-ladder/pull/13)
with the set's `precedent_check.py --full-sweep` at 0 violated. The same
pull request brought the set's copies of `the-boildown` and
`vendor-update-runbook` up to universal's (very deep check of 2026-10-05,
pass 3); `universal-change-reaches-overrides` now names such a copy at the
push that changes universal's.

