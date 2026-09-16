---
slug:            gotcha-2026-09-06-inherited-audits-that-have-nothing-to-inspect-say-so-rather-
status:          retired
noted:           2026-09-06
severity:        null
retired:         "2026-09-06"
retires_when:    null
---
## Symptom

Inherited audits that have nothing to inspect say so, rather than

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **Inherited audits that have nothing to inspect say so, rather than
  passing or failing.** [tools/practice_audit.py](../tools/practice_audit.py)
  wants a `process/manifest*.json` this repo does not have, because this
  repo is the upstream it audits a *dependent* repo against. It used to
  exit non-zero for that reason — permanently red, so nobody ran it — and
  [tools/doc_sync.py](../tools/doc_sync.py) and
  [tools/model_audit.py](../tools/model_audit.py), whose `PAIRS` and
  `INSTRUMENTED` lists were then empty, printed `OK` on having inspected
  nothing: a confident all-clear from a scan that never ran. All three now
  say NOT APPLICABLE with the reason, and
  [tools/precedent_check.py](../tools/precedent_check.py) reports that as
  skipped rather than passed. (`PAIRS` and `INSTRUMENTED` have both since
  been filled in here — two documents and one script — so only
  `practice_audit.py` is still NOT APPLICABLE in this repo. Corrected
  2026-09-06; the entry had gone on asserting all three were empty.)

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
