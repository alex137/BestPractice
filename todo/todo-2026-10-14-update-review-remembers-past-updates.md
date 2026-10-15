---
slug:              todo-2026-10-14-update-review-remembers-past-updates
kind:              manual
domain:            engine
severity:          null
status:            open
disposition:       parked
remind_on:         null
blocked_on:        null
batch:             null
decision:          "left out: a warning is shown again at each update rather than reviewed once and silenced"
decision_strength: decided
waiting_on:        null
noted:             2026-10-14
closed:            null
---
## What

Make the upstream review that Update Vendors prints
([tools/precedent_upstream_review.py](../tools/precedent_upstream_review.py))
remember warnings judged at earlier updates, not only the commits the
current update lands. Today a warning judged last week is shown again this
week. With the memory, each warning is reviewed once, the first time it
appears, and again only if its wording changes.

**Disposition:** parked (2026-10-14, Morgan)

## Notes

Proposed 2026-10-14 by a consuming repository's Update Vendors handoff
(item D: ten notes printed on every update with nothing to do). The notes
themselves were already stopped at their source in the engine (9fd5ed82,
dba91c45, 2026-10-12); the ten came from the older engine's first pass of a
self-replacing refresh. What remained was this memory.

Morgan, 2026-10-14, after the trade was laid out (a warning judged harmless
once would never come back, even if it later started to matter): "Okay
leave it out." Strength: decided. Not to be proposed again unless repeated
warnings at updates become a problem in their own right.
