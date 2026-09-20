---
slug:              todo-2026-09-10-stale-days-does-not-travel
kind:              decision
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
noted:             2026-09-10
closed:            null
---
## What

- <a id="stale-days-does-not-travel"></a>**Decide whether the four private
   practice sets should declare their own `branch_stale_days`.** Found
   2026-09-10 by the first real cross-repo run of the widened branch sweep
   ([practices/very-deep-check.md](../practices/very-deep-check.md), pass 4),
   in a session that had all four sources resolved.

   **What was measured.** BestPractice reads its declared 30, so its stale
   list is the two-or-three branches nobody has touched in a month. None of
   the four sources declares the key, so each falls back to the engine's
   conservative default and their section headings read `>= 90 days`. It
   changes no answer today — the oldest merged branch in any source is 10
   days, so at 30 those lists would still be empty — which is exactly why
   it is an open item and not a bug: it is latent until the first source
   branch crosses 30 days, and then it is silent.

   **Both answers are defensible, which is why nobody should pick one from
   here.** Per-repo declaration is the design working as written
   ([constants-are-risk-inputs](../practices/constants-are-risk-inputs.md)) —
   a set's cadence is genuinely its own, and a repo that releases weekly
   wants a different number from one that does not. Against that: all five
   repositories are one person's, worked in the same sessions at the same
   pace, and a threshold that differs across them by *omission* rather than
   by choice is the kind of accident this key exists to make visible.

   **blocked-on:** the four sets are under a different owner, so this cannot
   be done from a session rooted in this repository at all — `add_repo`
   refuses the cross-owner attachment (confirmed again 2026-09-10, matching
   the AGENTS.md gotcha). It needs a session rooted under that owner, which
   is a person's act.

   **Disposition:** wait (2026-09-10, Morgan) — raised with him in the
   thread that found it and not yet answered. Left at `wait` deliberately:
   only the person an item waits on may set it to `ask`, and a session
   stamping that for him is the session giving itself permission to chase.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
