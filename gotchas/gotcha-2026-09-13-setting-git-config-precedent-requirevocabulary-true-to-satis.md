---
slug:            gotcha-2026-09-13-setting-git-config-precedent-requirevocabulary-true-to-satis
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

Setting `git config precedent.requireVocabulary true` to satisfy the leak gate makes `verify_harness.py` fail two of its own leak-gate checks.

## Story

**Setting `git config precedent.requireVocabulary true` to satisfy the leak
gate makes `verify_harness.py` fail two of its own leak-gate checks.** The two
gates want opposite environments and neither says so, which is why it costs an
hour every time. Run them separately: `python3 tools/leak_gate.py` with
`PRECEDENT_LEAK_BLOCKLIST` exported, and `env -u PRECEDENT_LEAK_BLOCKLIST
python3 tools/verify_harness.py` with the git config unset. **Unset the config
when you are done** rather than leaving it on the clone — a later session
running the harness hits this again with no idea why.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
