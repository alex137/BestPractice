---
slug:              todo-2026-09-07-stem-note-reaches-the-sets
kind:              analysis
domain:            null
severity:          null
status:            dropped
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            2026-09-07
---
## What

- <a id="stem-note-reaches-the-sets"></a>~~**Refresh the private sets' vendored engine so the stem-coverage note
  actually runs where the blocklist lives.**~~ **WRONG, and withdrawn the same
  day it was written (2026-09-07). There is nothing to refresh.**

  The item asserted that each private set was running a stale copy of
  [tools/leak_gate.py](../tools/leak_gate.py) and
  [tools/very_deep_check.py](../tools/very_deep_check.py), and that the set
  holding the blocklist was therefore still reading its entries as literal
  strings. **Neither file is vendored into a source set or a consumer** —
  they are in neither `ENGINE_FILES` nor `CONSUMER_ENGINE_FILES`
  ([tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py),
  which now says so where the lists are defined). Both run only from a
  BestPractice checkout, against whatever repositories the session can see,
  so the fix reached every repo the moment it merged here.

  **How it went wrong is the part worth keeping.** The occasion index
  offers `cross-source-rollout` whenever a change touches how the engine
  works, and it is a real practice — it just did not apply, because these
  files are not part of what a source set holds. The premise went unchecked:
  one lookup in the file that defines those lists would have closed it. A
  practice firing correctly is not evidence that its premise holds
  ([search-by-purpose](../practices/search-by-purpose.md) asks the same
  question one step earlier — look before concluding).

  The anchor stays rather than being deleted, so anything already linking
  here still resolves ([rename-updates-links](../practices/rename-updates-links.md)).

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
2026-09-16: corrected by hand to `status: dropped` -- the migration tool
sets every item open by construction, but this one's own text says it was
withdrawn the same day it was written (its premise was wrong); it survived
step 2's pruning pass on purpose because its own text asks for the anchor
to stay for link stability, not because the work was still open.
