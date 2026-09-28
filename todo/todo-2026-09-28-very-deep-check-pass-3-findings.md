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

What the 2026-09-28 very deep check's pass 3 (coherence read, universal and
private sides) found and did **not** fix in the same run. Private-side items
that could be fixed in the sets themselves were fixed there.

- AGENTS.md's preamble is ~3,460 tokens every session. The command bullets
  (~1,650 tokens) each restate their practice and occasion-index line; split
  them to one line each with `precedent_vocabulary.py` as the list. "Say the
  read out loud and confirm" appears three times. A call for Morgan.
- `landing branch` and `Boildown` have no `defines:` entry.
- documentation/PER_MACHINE_SETUP.md does not describe an individual set's
  `bootstrap/pre-commit-fix`.
- Morgan's individual resident block is at ~539 of 550 tokens and the
  headroom notice does not check `resident_block_tokens`.
- `so-what-test` (individual) vs the reply sections a gate requires (The
  Boildown, Files touched): say those are not inventory to cut.
- `push-directly`'s named-branch form vs Morgan's `promote-only`: neither
  mentions the other; for him "push directly to main" can never pass the gate.
- `rule-links` (writing) overrides `doc-references-are-links` and drops its
  other two clauses (`≈` not `~`; no raw HTML `target=` anchors).
- "Deep check" names both the mechanical push suite (`two-check-levels`) and
  repo-maintenance's `deep-check` review; settle the keyword.
- `todo-gate` (repo-maintenance) says remove or check off items; the todo
  system closes on a condition and never removes.
- Five rules moved to universal on 2026-09-28 are still in force from
  repo-maintenance's copy (shared outranks universal) and have begun to
  drift; nothing tracks the dedupe half of the move.
- The light check's "wire it into CI" (repo-maintenance `light-check`,
  universal `two-check-levels`) contradicts `source-sets-run-no-ci` and
  `actions-minutes-are-scarce`.
- Filed 2026-09-21 and still true: the three shipped AGENTS templates carry an
  inline gotchas section that contradicts resident `environment-gotchas`
  (todo-2026-09-21-pass-3-coherence-read-findings, B1).
