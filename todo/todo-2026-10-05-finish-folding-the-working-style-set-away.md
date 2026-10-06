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

**Only the edits that retire it, from 2026-10-06.** Morgan (strength:
decided): *"We are deprecating repo maintenance and working style ... you
should not make edits to them unless the edits relate to their deprecation
or graceful deprecation. Please don't forget this."* A finding in the set is
fixed where the rule lives now, or recorded here and left. The push check
refuses any other edit to a set whose `precedent-source.json` says it is
retired.

## Proposed

Once the blocker clears, run `precedent_move.py --dedupe-only` for each of
the five, from working-style to universal. Then remove
`precedent-shared-working-style` from `sources` in each `precedent.json`
that declares it, and say the set is retired in its own README. The
assorted-notes check script stays in the working-style repo until then:
its deduplicated stub still links it.

The places that told a new install to declare the set changed on
2026-10-05, ahead of this: the starter template's
[precedent.json](../templates/document-project/precedent.json) and its
README, the guided setup in [SETUP.md](../SETUP.md), and INSTALL.md's
table of which shared sets a repo declares.

**BestPractice stopped declaring it, 2026-10-05.** Universal and the
writing set carry every rule the set still held active, so this repository
loses nothing by dropping it from its own `precedent.json`; the very deep
check run that day was reading the set as in force here. The set copies are
not deduplicated yet, and other repositories that declare it still do.

Archiving the repository on GitHub is Morgan's call.

**How the declarations come out, from 2026-10-06.** Once the set's copies
are deduplicated, add `"retired": {"date": ..., "folded_into": [...]}` to
the set's own `precedent-source.json`. Update Vendors then drops the set
from every repository that declares it, on that repository's next update,
and the very deep check reports any still declaring it -- in both cases
only once every active rule it held is in force elsewhere.
