---
slug:              todo-2026-09-28-very-deep-check-pass-3-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-28
closed:            null
---
## What

What the 2026-09-28 very deep check's pass 3 found and the same day did not
fix. The stale names, retired commands, contradictions and dead pointers it
found in all five repos were fixed that day.

- **For Morgan: AGENTS.md's preamble is ~3,460 tokens every session.** The
  command bullets (~1,650 tokens) each restate their practice and
  occasion-index line; the recommendation is one line each, with
  `precedent_vocabulary.py` as the list. "Say the read out loud and
  confirm" appears three times.
- **For Morgan: the individual resident block is at ~539 of 550 tokens**,
  and the headroom notice does not check `resident_block_tokens`. The
  cheapest move is audience-register's three bullets to its Detail.
- Five rules moved to universal on 2026-09-28 are still in force from
  repo-maintenance's copies (shared outranks universal); their notes now
  say so. The dedupe half waits until every consumer of that set has taken
  the new universal catalogue.
- The three shipped AGENTS templates still carry an inline gotchas section,
  which resident `environment-gotchas` rules out (filed 2026-09-21, B1).
  Moving it to a pointer changes every consumer's AGENTS.md on its next
  update.
