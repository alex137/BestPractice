---
slug:              todo-2026-09-10-retire-a-practice-source
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing; it is queued for size rather than permission. The sequence above is already true and already executed once, so this item is writing it down where the next retirement will look, not deciding it. Disposition `wait` ([open-item-disposition](../practices/open-item-disposition.md))."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-10
closed:            null
---
## What

- <a id="retire-a-practice-source"></a>**Write the retirement sequence for a practice SOURCE, from the one real
   run.** `precedent-team-tms` was retired 2026-09-10 — the first time a
   whole source has been taken out of service rather than a file or a
   directory inside one, which is what
   [decommission-deletes-files](../practices/decommission-deletes-files.md) and
   [tools/precedent_decommission.py](../tools/precedent_decommission.py) cover.
   [spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md) covers moving a
   practice between levels and stops there.

   **The ordering is the whole of it, and it is the reverse of the obvious
   one: remove the declarations first, delete the repository last.** A
   consumer that still declares a source whose repository is gone gets
   [tools/precedent_sync_views.py](../tools/precedent_sync_views.py)'s refusal —
   *"refusing to WRITE from an incomplete source set … Syncing anyway would
   DELETE every practice those sources contribute"* — which is the right
   refusal and an avoidable one. Delete last and no consumer ever sees it.

   **What the run established, worth writing up as procedure:**
   - Move the practices out first, per MOVING_PRACTICES.md's two-step (land
     at the destination, verify it THERE, then deduplicate at the source).
     Precedence is by LEVEL, not by set, so a move between two team sets
     preserves any override of an individual-level same-slug practice.
   - Check the destination does not already define the slug. Two sources at
     the same level claiming one slug is a hard refusal, not a merge.
   - Then strip every declaration — templates first, since a template is
     what makes the NEXT repo declare a dead source.
   - Then delete the repository.

   **Blocked-on:** nothing; it is queued for size rather than permission.
   The sequence above is already true and already executed once, so this
   item is writing it down where the next retirement will look, not
   deciding it. Disposition `wait`
   ([open-item-disposition](../practices/open-item-disposition.md)).

## How It Closes

Not open until: nothing; it is queued for size rather than permission. The sequence above is already true and already executed once, so this item is writing it down where the next retirement will look, not deciding it. Disposition `wait` ([open-item-disposition](../practices/open-item-disposition.md)).

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
