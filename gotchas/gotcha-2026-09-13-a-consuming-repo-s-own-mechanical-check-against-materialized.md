---
slug:            gotcha-2026-09-13-a-consuming-repo-s-own-mechanical-check-against-materialized
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A consuming repo's own mechanical check against materialized `tools/checks/`/`practices/` output cannot resolve sources live and trust every one it lists.

## Story

**A consuming repo's own mechanical check against materialized
`tools/checks/`/`practices/` output cannot resolve sources live and trust
every one it lists.** A repo-local source's check script belongs under that
source's own declared `path` (`local/tools/checks/`), never directly in the
consuming repo's `tools/checks/` — that is `precedent_materialize.py`'s
**output** directory, deleted and rewritten on every sync, so a hand-added
file there survives until the next one. A dependent repo shipped exactly this
check resolving sources live; it passed locally, then failed its own CI on
`main`, flagging every script sourced from its team and individual sources.
**A team source is a sibling clone outside the repo and an individual source
resolves via a private user-level config — neither exists in a bare CI
checkout, so "this source didn't resolve here" is not evidence of an orphan.**
Attribute by the committed `MANIFEST.json`'s own `checks` list instead: a file
with no entry there is the real signature of a hand-dropped orphan; a recorded
file whose source is unreachable is skipped, never failed.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
