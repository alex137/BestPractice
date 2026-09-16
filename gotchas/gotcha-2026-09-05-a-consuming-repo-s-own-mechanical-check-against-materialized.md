---
slug:            gotcha-2026-09-05-a-consuming-repo-s-own-mechanical-check-against-materialized
status:          retired
noted:           2026-09-05
severity:        null
retired:         "2026-09-05"
retires_when:    null
---
## Symptom

A consuming repo's own mechanical check against materialized

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A consuming repo's own mechanical check against materialized
  `tools/checks/`/`practices/` output cannot just call
  `precedent_resolve.load_config()` and trust every source it lists.** A
  repo-local (or team, or individual) source's own check script belongs
  under that source's own declared `path` (`local/tools/checks/` for a
  source declared `path: "local"`), never directly in the consuming
  repo's own `tools/checks/` — that is `precedent_materialize.py`'s own
  *output* directory, deleted and rewritten from every declared source on
  every `precedent_sync_views.py` run, so a hand-added file there
  survives only until the next sync. A dependent repo built exactly this
  mechanical check (verify every materialized `check_*.py` has a
  byte-identical twin in its source) and shipped a first version that
  resolved sources live to decide what counts as reachable — it passed
  locally, then failed the repo's own CI on the very next push, on `main`
  itself, flagging every check script sourced from its team and
  individual sources. A team source is a live sibling clone outside the
  repo; an individual source resolves only via a private, non-repo
  user-level config — neither exists in a bare CI checkout, and never
  will, so "this source didn't resolve here" is not evidence of an
  orphaned file. The fix: attribute by the *committed* `MANIFEST.json`'s
  own `checks` list (already written by `precedent_materialize.py`,
  recording exactly which source produced each file) instead of by live
  resolution — a file with no entry there at all is the real signature of
  a hand-dropped orphan and always fails; a recorded file whose source
  simply is not reachable in the current environment is skipped, never
  failed.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
