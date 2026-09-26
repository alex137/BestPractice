---
slug:              todo-2026-09-26-frontmatter-field-order-goes-blocking
kind:              manual
domain:            vendoring
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the four practice sets taking the engine update that carries frontmatter-field-order and running its fixer"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-26
closed:            null
---
## What

**Make `frontmatter-field-order` blocking.** It shipped ADVISORY on
2026-09-26, in [tools/precedent_check.py](../tools/precedent_check.py), with
the order itself as `FIELD_ORDER` in
[tools/frontmatter_yaml.py](../tools/frontmatter_yaml.py) and the fixer as
`python3 tools/frontmatter_yaml.py --fix-order`. BestPractice's own 49
misordered practices were fixed in the same change.

The step left is removing `advisory=True` from the check's registration
(and `advisory=True` from its planted case in
[tools/verify_harness.py](../tools/verify_harness.py)).

## Condition

Blocked on the sets, not on anything here. On 2026-09-26 the drift was:
precedent-individual 11 of 33, precedent-shared-repo-maintenance 7 of 44,
precedent-shared-working-style 3 of 9, precedent-shared-writing 3 of 21.
Each set gets the check through Update Vendors
([vendor-update-runbook](../practices/vendor-update-runbook.md)) and clears
its own findings with the fixer on its next push. This closes when
`python3 tools/frontmatter_yaml.py --check-order` reports 0 out of order in
all four sets and the check is made blocking. Turning it blocking before
then makes each set's next Update Vendors red with nothing BestPractice can
fix from its side.
