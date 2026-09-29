---
slug:              todo-2026-09-29-source-checks-adopt-generated-blocks
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "generated_blocks.py reaching main, then each practice set's engine refresh"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-29
closed:            null
---
## What

- <a id="source-checks-adopt-generated-blocks"></a>**Move the practice
  sets' own checks onto
  [`generated_blocks.py`](../tools/generated_blocks.py), the engine's one
  answer to "is this line inside a generated block?"**, added 2026-09-29.

  The engine writes generated text in two marker styles: `<!--gen:NAME-->`
  from [`doc_sync.py`](../tools/doc_sync.py), and the loader block's `BEGIN GENERATED` /
  `END GENERATED` pair from [`build_views.py`](../tools/build_views.py). Until that date every engine
  tool that skipped generated text matched the markers itself, and each
  knew only one style. A shared set's check had the same blind spot and
  hit it first. Its no-stale-counts check knew only the `gen:` style, so
  when that set gained its first resident practice, the loader block's
  "1 of 20 practices" read as a stale hand-written count, and a Promote
  was refused over generated text. That set fixed its own copy the same
  day. Its check still matches the markers itself, though, so the next
  marker change reaches the engine and not that set.

  - The shared writing set's no-stale-counts check: replace its own
    marker matching with `generated_blocks.mask()` or `.blank()`, imported
    from the vendored engine beside it, the same way these checks already
    import `precedent_resolve`.
  - **In the same pass:** grep each set's `tools/checks/` for `gen:` and
    `GENERATED`. That check was found because it fired, not because
    anything looked for it, and the same was true of the 2026-09-10
    helpers ([source-checks-adopt-engine-helpers](todo-2026-09-10-source-checks-adopt-engine-helpers.md)).

  **Order matters.** A set's check can import the helper only once that
  set's vendored engine carries it. The helper reaches a set when it
  reaches `main` here and the set's engine is refreshed. Changing the check
  before then would make it crash on the import.

  **Enforced, not just recorded** (Morgan, 2026-09-29: *"we should check
  this also"*). `precedent_check.py --only checks-use-generated-blocks`
  names any check under `tools/checks/` or `local/tools/checks/` that
  spells a marker itself. The helper and the check arrive in the same
  engine refresh. After that refresh, the shared writing set's check is
  named at its next Promote to `staging`. Into `pre-staging` it is named
  only when a change touches that file (checks-follow-the-tier). As of
  2026-09-29 it is the only check in the four sets that the new check
  names.

## How It Closes

`checks-use-generated-blocks` passes in every practice set: each set's
own checks either use [`generated_blocks.py`](../tools/generated_blocks.py)
or match no generated-block markers at all. A session rooted in each
set does the work there, and each set's approvers decide its merge.

## Notes
