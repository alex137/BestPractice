---
slug:              todo-2026-10-20-individual-set-charged-to-each-repo-ceiling
kind:              decision
domain:            mechanism
severity:          medium
status:            open
disposition:       null
remind_on:         null
blocked_on:        Morgan's decision on where the individual set's share of the session file is charged
batch:             null
decision:          null
decision_strength: null
waiting_on:        Morgan
noted:             2026-10-20
closed:            null
---
## What

The ceiling on the session practices file (in
[tools/session_load_budgets.json](../tools/session_load_budgets.json))
charges the person's individual set to each repository. In one voice
repository on 2026-10-20, about 1,176 of the 1,510 tokens it measured were
the individual set, against the repository's 400-token ceiling. The
repository's own part, about 334, was inside it. The session check failed
at every session start and pointed the repository at a reduction pass it
could not do.

PR #1313 made the overage message name that split
([tools/precedent_session_check.py](../tools/precedent_session_check.py),
`_individual_part`). It did not change what is charged.

## The choice

Sets a person brings (`brings`) are already charged to a budget of the
person's own, `brought_sets_tokens` in their individual set
(`_charge_brought_share`). The individual set itself is not.

1. **Charge the individual set the same way:** a budget of the person's
   own, declared in their individual set (for example
   `individual_set_tokens`), and each repository's ceiling covers only what
   the repository and its declared shared sets add. Small change, reusing
   the `brought_sets_tokens` path. No declared budget keeps today's
   behaviour.
2. **Leave it charged to the repository,** with the split message from PR
   #1313. Each repository raises its own ceiling to fit the person's set,
   and has to raise it again whenever that set grows.

My pick is 1: the repository cannot shorten the individual set, so a
ceiling that counts it fails for a reason nobody there can fix.

## Closes when

Morgan has chosen, and either the budget is built with a harness test that
fails on today's code, or the item records his choice to keep it as it is.
