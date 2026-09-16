---
slug:              todo-2026-09-12-provenance-stamp-for-instantiated-copies
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing but the work. It was deliberately out of scope of the approved change, which was the practice and the occasion widening."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-12
closed:            null
---
## What

- <a id="provenance-stamp-for-instantiated-copies"></a>**A file instantiated
  from a template carries no record that it was, so nothing can check
  whether it drifted.** Raised 2026-09-12 while landing
  [fix-the-original](../practices/fix-the-original.md), which is the advisory
  version of this and says so in its own Detail section. Two mechanical
  designs were built and measured against this tree that day, and both were
  declined for a stated reason: same-basename divergence across the repo and
  all four attached sources reported 12 identical against **100 divergent**
  basenames, nearly all of them correct work (per-case test fixtures, and
  the per-source `approvers.json` files whose purpose is to differ); the
  narrower template-to-instantiation similarity check reported six pairs,
  four identical and two divergent, where **both divergences are legitimate
  and documented in the instance's own header**. So divergence is not the
  signal — a copy that legitimately differs and a copy that drifted are
  indistinguishable to a differ. **The checkable version is a provenance
  stamp**: an instantiated file records the template and the commit it came
  from, the way
  [generated-artifact-provenance](../practices/generated-artifact-provenance.md)
  already does for generated output, after which "your origin moved and you
  did not" is a lookup rather than a guess. Two live instances of the cost
  are already recorded — `commit-identity.sh` one version behind in all five
  real private sets, and the `register` field in the item above, added to a
  live `identity.json` on 2026-09-10 and still absent from the skeleton
  every other set is built from.
  **Blocked on / out of scope:** nothing but the work. It was deliberately
  out of scope of the approved change, which was the practice and the
  occasion widening.
  **Disposition:** wait

## How It Closes

Not open until: nothing but the work. It was deliberately out of scope of the approved change, which was the practice and the occasion widening.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
