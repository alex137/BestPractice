---
slug:              todo-2026-09-06-team-check-cites-retired-practice
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-06
---
## What

- <a id="team-check-cites-retired-practice"></a>~~**`precedent-team-repo-maintenance`' `check_deep_check.py` cites a practice
    retired in that same set.**~~ **Resolved by reversal, 2026-09-06.** The
    premise was the bug: `deep-check` was never redundant with
    `very-deep-check` — they are unrelated rules of different kind and
    cadence (see
    [practices/very-deep-check.md](../practices/very-deep-check.md)'s corrected
    `## Story`). `deep-check` is restored to `active` in the team set, so the
    `# practice: deep-check` citation resolves again and there is nothing to
    move. This is the incident that motivated
    [decisions/2026-09-06-deduplication-not-retirement.md](../decisions/2026-09-06-deduplication-not-retirement.md).

## How It Closes

Already closed 2026-09-06 -- see the item's own text above for what
finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../`.
