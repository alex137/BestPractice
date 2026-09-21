---
slug:              todo-2026-09-11-consumer-views-drift-uncheckable-in-ci
kind:              manual
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
noted:             2026-09-11
closed:            null
---
## What

- <a id="consumer-views-drift-uncheckable-in-ci"></a>**A consuming repo's
   generated loader block cannot be drift-checked in CI, and today nothing
   checks it anywhere.** A consuming repo materializes `practices/` from the
   sources it resolves. A team source is a sibling clone outside the repo; an
   individual source resolves through a private user-level config. Neither
   exists in a bare CI checkout, so there is nothing on a runner to
   regenerate the block from — and
   [tools/build_views.py](../tools/build_views.py) deliberately exits 0 with
   `NOT VERIFIABLE` rather than calling the difference drift, which is
   right for a person and a silent green for a gate.

   So templates/github-actions/views-drift.yml.template — since 2026-09-19 a
   job inside
   [precedent-check.yml.template](../templates/github-actions/precedent-check.yml.template)
   — refuses that layout outright rather than shipping a check that passes
   blind, and what covers a consuming repo is a session remembering to run
   `python3 tools/precedent_sync_views.py --repo . --check` where the sources
   do resolve. That is exactly the "session discipline only" state
   [.github/workflows/deep-check.yml](../.github/workflows/deep-check.yml) was
   added here to end.

   **Shapes worth weighing:** a self-hosted or credentialed runner that can
   clone the private sources (moves the problem into secret management for
   somebody else's repo); a committed manifest of source content hashes the
   block was built from, so CI can at least detect *"the block was built
   against different inputs than these"* without resolving anything; or
   accept it and make the session-start path loud instead, since
   [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
   already reports stale sources at session start and could report a drifted
   block in the same line. The middle one is the only one that gates in CI.

   **blocked-on:** a consuming repo to measure against — the shapes above
   differ mostly in what a real adopter's CI can be asked to hold.

   **Disposition:** wait ([open-item-disposition](../practices/open-item-disposition.md)).

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
