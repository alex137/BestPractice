---
slug:              todo-2026-09-17-access-probe-plant-not-detected
kind:              manual
domain:            null
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-17
closed:            2026-09-17
---
## What

- <a id="access-probe-plant-not-detected"></a>**Fixed. [tools/verify_harness.py](../tools/verify_harness.py)'s
  `check_precedent_check_fires` reported `access-probe-is-wired`'s planted
  violation as undetected.** Found 2026-09-17, running the deep-check suite
  before pushing an unrelated documentation move.

  **Root cause.** [tools/precedent_check.py](../tools/precedent_check.py)'s
  `_access_probe_is_wired` treats three files as candidate wiring:
  `.claude/hooks/session-start.sh`, `tools/bootstrap.sh` and
  `templates/bootstrap.sh` — any one invoking the probe is enough. The
  self-test's `_plant_unwired_probe` neutralized only the first and third.
  Since this repo's real `tools/bootstrap.sh` genuinely invokes the probe
  and the plant never touched it, the scratch copy the self-test built was
  never actually in violation — the check was correctly reporting a clean
  tree, not failing to catch a dirty one. Both the check's third candidate
  and the plant function were added in the same commit, `cd23da93`
  (2026-09-14); the plant's loop just never covered all three from the
  start.

  **Fix.** Added `tools/bootstrap.sh` to `_plant_unwired_probe`'s loop.
  Verified both directions by hand: with all three files patched, `python3
  tools/precedent_check.py --only access-probe-is-wired` now reports the
  violation; against the unpatched real tree it still reports clean.
