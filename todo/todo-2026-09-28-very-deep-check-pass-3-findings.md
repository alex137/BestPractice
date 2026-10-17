---
slug:              todo-2026-09-28-very-deep-check-pass-3-findings
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
noted:             2026-09-28
closed:            2026-10-17
---
## What

What the 2026-09-28 very deep check's pass 3 found and did not fix. The
AGENTS.md preamble, the individual resident block (and the headroom notice
that missed it) and the templates' inline gotchas were fixed the same day.

- Five rules moved to universal on 2026-09-28 are still in force from
  repo-maintenance's copies (shared outranks universal); their notes say
  so. **The dedupe waits on a condition, not a person**: every consumer of
  that set has to take the new universal catalogue first, or a consumer
  still on the old one loses the rule entirely. It closes when the
  consumers' next Update Vendors carries BestPractice past the commit that
  added the five.

## Closed

Closed 2026-10-17 by the very deep check, pass 4, on its own condition. The dedupe it waited on is moot: the repo-maintenance set was retired 2026-10-06 and is listed deleted in tools/deleted_sets.json (2026-10-08), so its five copies no longer outrank anything.
