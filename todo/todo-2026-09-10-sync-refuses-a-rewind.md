---
slug:              todo-2026-09-10-sync-refuses-a-rewind
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing external — it is queued for size, not for permission. It carries no disposition, so it is `wait` ([open-item-disposition](../practices/open-item-disposition.md))."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-10
closed:            null
---
## What

- <a id="sync-refuses-a-rewind"></a>**Make `precedent_sync_views.py` refuse a sync that would rewind a
   practice's content, not just one that would remove the practice
   outright.** It already refuses at practice granularity: `_lost_practices`
   blocks a write that would remove a practice the committed
   `MANIFEST.json` records whose source is still declared. The 2026-09-09
   incident slipped underneath that, because the practice file still
   existed and only its CONTENT went backwards — a Story block and a clause
   of the Rule, replaced by an older revision of the same file.
   **Do not build this as "refuse a sync that deletes text."** A legitimate
   practice edit deletes text, and that tool's own comments record that a
   broader first attempt at this died of false positives. A content hash
   cannot tell an edit from a rewind either: both look like a different
   hash. What distinguishes them is the source's own commit, which the
   manifest does not currently record. So: record the source commit per
   source at sync time, and refuse when the incoming commit is an ancestor
   of the recorded one.
   **One trap to design around:** `git merge-base` on a shallow clone
   reports "no common ancestor" for branches that genuinely share history
   (see [AGENTS.md](../AGENTS.md)'s gotcha). The ancestry test needs a bounded
   deepen and must degrade honestly rather than reading exit 1 as
   "unrelated".
   **Approved for later, `strength: assented`** (2026-09-10, Morgan): he
   approved the branch pin, the off-branch report and the `--repo` refusal
   as one pass and left this one queued. Recorded `assented` rather than
   `decided` because it is agreement to this session's own proposal
   ([decision-strength](../practices/decision-strength.md)).
   **Blocked-on:** nothing external — it is queued for size, not for
   permission. It carries no disposition, so it is `wait`
   ([open-item-disposition](../practices/open-item-disposition.md)).

## How It Closes

Not open until: nothing external — it is queued for size, not for permission. It carries no disposition, so it is `wait` ([open-item-disposition](../practices/open-item-disposition.md)).

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
