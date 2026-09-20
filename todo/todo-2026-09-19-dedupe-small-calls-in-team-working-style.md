---
slug:              todo-2026-09-19-dedupe-small-calls-in-team-working-style
kind:              manual
domain:            mechanism
severity:          minor
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "this PR merging into precedent-beta-v01, and every repository consuming precedent-team-working-style taking the new universal catalogue"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-19
closed:            null
---
## What

- <a id="dedupe-small-calls-in-team-working-style"></a>**Run the second half
  of the `small-calls` move.** `tools/precedent_move.py --to universal`
  drafted `small-calls` into this repo's `practices/` (this PR) and left the
  source copy in `precedent-team-working-style` `status: active`, by design
  ([spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md): universal lands
  only through the PR merging). Once this merges, run:

  ```
  python3 tools/precedent_move.py --dedupe-only \
      --slug small-calls \
      --from team --from-path <precedent-team-working-style checkout> \
      --to universal --to-path <this checkout>
  ```

  in a `precedent-team-working-style` checkout, but only after every
  repository consuming that set has taken the new universal catalogue
  (INSTALL.md §2 step 0, or "Update Vendors") -- a consumer still vendoring
  the old one would see the rule in neither source.

## How It Closes

Run `--dedupe-only`, commit the resulting `status: deduplicated` /
`in_force_at: small-calls` copy in `precedent-team-working-style`, and mark
this item `done`.

## Notes

Opened while drafting the universal landing (2026-09-19), alongside the
matching item for `push-back` in `precedent-team-writing`
(`todo-2026-09-19-dedupe-push-back-in-team-writing.md`) -- moved together
per Morgan's own instruction ("Move both push-back and small-calls to
universal") since `push-back`'s Story names `small-calls` as its paired
opposite case.
