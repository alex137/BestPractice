---
slug:              todo-2026-09-20-the-load-budget-registry-asserts-loads-nothing-verifies
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-20
closed:            null
---
## What

- **[tools/session_load_budgets.json](../tools/session_load_budgets.json)
  declares what every session loads, and nothing checks that any of it is
  loaded.** The check behind
  [session-load-budget](../practices/session-load-budget.md) measures each
  declared surface against its ceiling. It never asks the prior question:
  **does this surface reach a session at all?** A file that no harness loads
  passes its ceiling comfortably forever.

  **Found 2026-09-20, the expensive way.** `.precedent/SESSION_PRACTICES.md`
  was declared an always-loaded surface on 2026-09-13, with a ceiling
  described as *"the whole of what those sources may add to every session
  here"*. In a practice set it added nothing to any session for the next
  seven days — the file was rendered and never read, because Claude Code
  auto-loads instruction files only
  ([spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md](../spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md)).
  Three rounds of fixes went past it. **The registry is exactly where a
  session would check, and the registry said yes.**

  **The registry is now right about the set case** — the SessionStart hook
  injects the render — but nothing stops the next entry being wrong the same
  way, and one live instance is still unexamined: **a CONSUMER repo's copy of
  the same surface**. There the file is written by a consumer-side hook and
  pointed at by the same Standing Instruction sentence, which is the exact
  shape that failed in a set. Whether a consumer session actually carries
  those team and individual practices before its first turn has, as far as
  this item's author could find, never been measured — only declared.

  **What a check could plausibly assert**, cheapest first: that every
  declared surface is either an instruction file the harness auto-loads
  (`CLAUDE.md`, `AGENTS.md`, or a file `@`-imported by one), or is named by a
  hook that emits it as `additionalContext`. Both are greppable from the
  repository. A surface that is neither is the finding — and it is a finding
  worth having even when the ceiling is green, because a green ceiling on an
  unloaded surface is the most convincing wrong answer the registry can give.

  **Not started.** Costed at nothing yet; recorded while the incident that
  produced it is legible.
  **Disposition:** wait

## How It Closes

Not open once `precedent_check.py`'s session-load-budget check (or a check
beside it) asserts a delivery route for every declared surface, and the
consumer-repo case above has been measured rather than assumed.

## Notes

Raised by the session that fixed the set-side half of the same defect.
