---
slug:              todo-2026-09-14-engine-root-in-a-vendored-tree
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

- <a id="engine-root-in-a-vendored-tree"></a>**Five engine tools read the
  wrong repo when vendored, and five more have not been checked.** Fixed
  2026-09-14 for the five a consuming repo actually runs —
  [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py),
  [tools/precedent_source_names.py](../tools/precedent_source_names.py),
  [tools/precedent_gate.py](../tools/precedent_gate.py),
  [tools/precedent_show.py](../tools/precedent_show.py) and
  [tools/precedent_paths.py](../tools/precedent_paths.py) — by a shared
  `consuming_repo_root()` that recognises the `process/upstream/tools/`
  layout from the consumer's own `process/manifest.json`. Harness case:
  `check_vendored_engine_reads_the_consumer_root`.

  **Still carrying the bare `_ENGINE_DIR.parent` default:**
  [tools/build_views.py](../tools/build_views.py),
  [tools/build_codeowners.py](../tools/build_codeowners.py),
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py),
  [tools/precedent_session_check.py](../tools/precedent_session_check.py) and
  [tools/todo_progress.py](../tools/todo_progress.py). Deliberately not changed
  in the same pass: these are publisher- and session-side rather than
  reader-side, and for at least `build_views.py` the vendored tree arguably
  IS the right root — it has its own views to build. **The open question is
  per tool, not one verdict**, which is why this is an item rather than a
  finished sweep.

  **Why the reader-side five were worth fixing on sight.** The symptom is
  the one this whole project exists to prevent: in a real consumer,
  `process/upstream/tools/precedent_show.py default-register` answered
  *"unknown slug"* for a team practice that repo has in force, and the push
  gate printed a NOTE saying three team sources "did NOT resolve" at paths
  under `process/` that nothing has ever written to. Every one of those
  readings is confident, specific, and about the wrong repository — the
  shape of wrongness that gets believed.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
