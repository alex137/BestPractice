---
slug:            gotcha-2026-09-07-setting-git-config-precedent-requirevocabulary-true-to-satis
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

Setting `git config precedent.requireVocabulary true` to satisfy the leak

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **Setting `git config precedent.requireVocabulary true` to satisfy the leak
  gate makes `verify_harness.py` fail two of its own leak-gate checks.** The
  two gates want opposite environments and neither says so. 2026-09-07,
  running the full deep check before a push: `leak_gate.py` refused with
  *"this clone has declared that it HAS a private-term blocklist ... and
  PRECEDENT_LEAK_BLOCKLIST is not set"*, which the gotcha above tells you to
  fix by setting both. With both set, `verify_harness.py` then reported
  `2 failed` — *"the default blocklist is applied with no environment
  variable set"* and *"a clean tree now reports OK rather than PARTIAL"* —
  because those cases assert the gate's behaviour for a clone that has
  declared nothing. Neither failure is a real defect and neither is caused by
  whatever you are changing, which is exactly why it costs a session an hour.
  Run them in different environments: `python3 tools/leak_gate.py` with
  `PRECEDENT_LEAK_BLOCKLIST` exported, and
  `env -u PRECEDENT_LEAK_BLOCKLIST python3 tools/verify_harness.py` with the
  git config unset. Unset the config when you are done rather than leaving it
  on the clone — a later session running the harness will hit this again with
  no idea why.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
