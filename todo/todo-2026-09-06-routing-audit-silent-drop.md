---
slug:              todo-2026-09-06-routing-audit-silent-drop
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
closed:            2026-09-05
---
## What

- <a id="routing-audit-silent-drop"></a>~~**Investigate why `routing-audit` fell through, audit the plan for    other silent drops.**~~ **Part 1 done (2026-09-04)** — root cause and
    scan for other drops in
    [spec/UNBUILT_PLAN_ITEMS.md](../spec/UNBUILT_PLAN_ITEMS.md)'s "Part 1,
    answered" section; the one adjacent gap it found is [`wire-the-very-deep-check-list`](#wire-the-very-deep-check-list) below.
    **Part 2 (pre-register and run a real evaluation of the two new audit
    mechanisms before trusting their output) is pre-registered and run
    twice** —
    [evals/routing/PREDICTION_AUDIT_JUDGMENT.md](../evals/routing/PREDICTION_AUDIT_JUDGMENT.md)
    and
    [_RUN2.md](../evals/routing/PREDICTION_AUDIT_JUDGMENT_RUN2.md) — each a
    smaller single-session eval than the routing eval's own multi-run
    discipline; see [spec/ATTENTION_CEILING.md](../spec/ATTENTION_CEILING.md)'s
    dated 2026-09-04 and 2026-09-05 sections for both results (6/6 and 6/6
    once run 2's own pre-registration error was corrected in the write-up)
    and their stated caveats. Run 2 also found a real gap in run 1's own
    `parallel-artifact-ledger` fix (a ledger with no audit backing it) —
    fixed the same session, `tools/precedent_check.py`'s new
    `parallel-artifact-ledger` check. Left open: both documents' own read
    that two 6-case runs are a stronger signal than one but still not a
    replacement for the routing eval's fuller multi-run discipline, if this
    ever needs to be trusted at higher stakes than an on-demand backstop.

## How It Closes

Already closed 2026-09-05 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
