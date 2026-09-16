---
slug:              todo-2026-09-14-sync-views-blames-a-dropped-source-for-a-retirement
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
noted:             2026-09-14
closed:            null
---
## What

- <a id="sync-views-blames-a-dropped-source-for-a-retirement"></a>**A
  retired practice is reported as one whose SOURCE was dropped, and a
  renamed source would read identically.** On 2026-09-14
  [tools/precedent_sync_views.py](../tools/precedent_sync_views.py) removed four
  practices from a consumer and explained them as *"removing 4 practice(s)
  whose source is no longer declared in precedent.json, which is what
  dropping a source means"*, naming a source name that had been renamed
  three days earlier. The removals were correct — all four are `status:
  retired` at source, which
  [tools/precedent_resolve.py](../tools/precedent_resolve.py) reports
  accurately — but the reason given was not, because the check is against
  the name recorded in the materialized `MANIFEST.json`, and a RENAME makes
  every one of that source's files look orphaned.

  **The hazard is the counterfactual, not this run.** Had those four not
  been retired, the same rename would have deleted them from the consumer
  under the same reassuring sentence. The fix is to distinguish the two
  states before writing the message: a practice whose source resolves but
  whose `status` is `retired`, versus one whose source is genuinely gone.

  **Done 2026-09-14, the safety half: the silent write is gone.** An
  unmatched recorded source now REFUSES like the still-declared bucket
  already did, and the message names the three states the name-matching
  cannot separate — dropped, renamed, retired at source — instead of
  asserting the commonest one. `--allow-removals` proceeds once the person
  knows which they have. Covered by two new cases in
  [tools/verify_harness.py](../tools/verify_harness.py)'s
  `check_sync_refuses_to_lose_a_recorded_practice`, including the one the
  fixture had to be corrected to reach: **a rename alone loses nothing** —
  the source still resolves and still produces the same slugs, so the guard
  has no occasion to fire — and the damage needs a rename PLUS a practice
  that really goes. A fixture asserting the rename alone passes for the
  wrong reason.

  **Still open, and this item stays open for it: the tool still cannot TELL
  the three apart.** It refuses safely rather than distinguishing, which is
  what the condition above asks for. Two ways to actually distinguish, in
  order of durability: record something rename-proof in `MANIFEST.json` (a
  URL or an id) instead of matching on the source's name, which removes the
  ambiguity rather than catching it; or call
  [tools/precedent_source_names.py](../tools/precedent_source_names.py), whose
  `renamed=True` (landed in PR #347, still unconsumed) reports a rename
  GitHub redirects — precise, but a network call inside a tool that
  otherwise runs offline, so it needs the refusal underneath it either way.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
