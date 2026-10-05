---
slug:              todo-2026-10-05-move-repo-maintenance-into-universal
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "Morgan's go-ahead, which he gave on 2026-10-05 for the working-style half only, and a raise to universal's occasion allowance, which is his decision"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-05
closed:            null
---
## What

- <a id="repo-maintenance-into-universal"></a>**Move the repo-maintenance
  set's rules into universal and retire the set.**

  Morgan proposed it on 2026-10-05, to cut the number of sets each install
  clones. Its subject, running a repository that vendors a practice layer,
  is every install's. Fourteen of its rules are in force. Two of them,
  fresh-before-write and session-trailer, already have active universal
  copies.

## Proposed

Move each with [tools/precedent_move.py](../tools/precedent_move.py), the
same way as the working-style fold
([todo-2026-10-05-finish-folding-the-working-style-set-away.md](todo-2026-10-05-finish-folding-the-working-style-set-away.md)).
Three things to watch:

- Universal's `occasion_share_tokens` (2,250) has to rise by about what
  this set uses. A consumer that declared it loads the same total.
- Several rules say "this team's repos" and need rewording for a public,
  general audience.
- `deep-check` is not a copy of `two-check-levels`: its by-request read of
  the repo against itself is the part universal lacks. On 2026-09-06 a
  session dropped it as redundant and a routine check went missing for a
  day ([very-deep-check](../practices/very-deep-check.md)'s Story).
