---
slug:              todo-2026-09-19-pr-template-todo-md-wording-is-stale-post-migration
kind:              manual
domain:            mechanism
severity:          minor
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-19
closed:            2026-09-19
---
## What

- <a id="pr-template-todo-md-wording-is-stale-post-migration"></a>**This
  repo's PR template still told contributors to work with `TODO.md`
  directly**, stale since the 2026-09-16 todo/gotcha migration turned
  `TODO.md` into a frozen redirect stub (open items now live one per file
  under `todo/`, and a PR touching `TODO.md` is refused by CI). Both
  [`.github/pull_request_template.md`](../.github/pull_request_template.md)
  (this repo's own instantiated copy) and
  [`templates/pull_request_template.md.template`](../templates/pull_request_template.md.template)
  (the generic template every dependent repo installs) carried the
  identical stale wording -- confirmed it wasn't local drift: the generic
  template is the actual source of the problem, not a copy that fell
  behind it.

## How It Closes

Fixed directly in both files. Landed twice, independently and
concurrently: this branch's own edit, and (reaching `precedent-beta-v01`
first) another session's `6dfdad5` "Fix stale TODO.md wording in PR
templates" plus `1e2c2d2` "Fix remaining stale TODO.md reference in PR
templates" -- the merge conflict that produced surfaced the duplicate, and
this branch's wording deferred to the already-landed one rather than
re-litigating an equivalent fix. A direct edit is correct here either
way -- this repo's own copy isn't tracked against a recorded manifest hash
the way a dependent repo's materialized copy is, and the generic template
is this repo's own content to edit directly (`AGENTS.md`'s "Direct edits
are fine for content about this repo itself").

## Notes

A dependent repo that vendored the old template wording before this fix
picks it up on its next `Update Vendors` / `checkin.py update` run,
same as any other template change -- nothing repo-specific to coordinate.
