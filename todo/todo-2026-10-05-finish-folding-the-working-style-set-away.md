---
slug:              todo-2026-10-05-finish-folding-the-working-style-set-away
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "the five universal drafts landing on main, then Update Vendors in every repository that declares precedent-shared-working-style, so no consumer sees those rules in force nowhere"
batch:             null
decision:          "fold precedent-shared-working-style away: default-register and assorted-notes to precedent-shared-writing, the other five to universal"
decision_strength: decided
waiting_on:        null
noted:             2026-10-05
closed:            null
---
## What

- <a id="finish-folding-working-style"></a>**Withdraw the last five rules
  from the working-style set, then stop declaring it.**

  Morgan decided on 2026-10-05 that the working-style set goes away. The
  same day, default-register and assorted-notes moved to the writing set,
  and five more were drafted into universal with
  [tools/precedent_move.py](../tools/precedent_move.py):
  answer-first-ask-before-long-work, their-constraints-are-given,
  report-up-the-chain, revert-needs-no-trailer and
  organize-scattered-content. Their working-style copies stay active, as
  the tool requires, until universal carries them everywhere.

## Proposed

Once the blocker clears, run `precedent_move.py --dedupe-only` for each of
the five, from working-style to universal. Then remove
`precedent-shared-working-style` from `sources` in each `precedent.json`
that declares it, and say the set is retired in its own README. The
assorted-notes check script stays in the working-style repo until then:
its deduplicated stub still links it.

Archiving the repository on GitHub is Morgan's call.
