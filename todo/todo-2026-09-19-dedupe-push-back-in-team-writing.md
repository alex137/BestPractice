---
slug:              todo-2026-09-19-dedupe-push-back-in-team-writing
kind:              manual
domain:            mechanism
severity:          minor
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "this PR merging into precedent-beta-v01, and every repository consuming precedent-team-writing taking the new universal catalogue"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-19
closed:            null
---
## What

- <a id="dedupe-push-back-in-team-writing"></a>**Run the second half of the
  `push-back` move.** `tools/precedent_move.py --to universal` drafted
  `push-back` into this repo's `practices/` (this PR) and left the source
  copy in `precedent-team-writing` `status: active`, by design
  ([spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md): universal
  lands only through the PR merging). Once this merges, run:

  ```
  python3 tools/precedent_move.py --dedupe-only \
      --slug push-back \
      --from team --from-path <precedent-team-writing checkout> \
      --to universal --to-path <this checkout>
  ```

  in a `precedent-team-writing` checkout, but only after every repository
  consuming that set has taken the new universal catalogue (INSTALL.md §2
  step 0, or "Update Vendors") -- a consumer still vendoring the old one
  would see the rule in neither source.

## How It Closes

Run `--dedupe-only`, commit the resulting `status: deduplicated` /
`in_force_at: push-back` copy in `precedent-team-writing`, and mark this
item `done`.

## Notes

Opened while drafting the universal landing (2026-09-19), so the follow-up
isn't only remembered in this PR's own thread.
