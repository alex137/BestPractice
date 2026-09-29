---
slug:              todo-2026-09-29-planted-case-lives-beside-its-check
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "out of scope for the 2026-09-29 engine-fixes batch: it moves every planted case in the harness"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-29
closed:            null
---
## What

- <a id="planted-case-lives-beside-its-check"></a>**Put each check's
  planted case beside the check, so there is no second file to forget.**

  Every check [`precedent_check.py`](../tools/precedent_check.py)
  registers needs a planted case in `check_precedent_check_fires` in
  [`verify_harness.py`](../tools/verify_harness.py): a copy of the tree
  with the violation planted, run with `--only SLUG`, which has to fail.
  The check lives in one file and its case in another, a harness that runs
  to tens of thousands of lines, so adding a check means remembering a
  second edit in a second file. On
  2026-09-29 a new check reached pre-staging without its case, and the
  Debut to staging failed on the harness's "every registered check has a
  planted case" assertion, twenty minutes in.

  The same day's fix is a check, not a removal:
  [`precedent_push_check.py`](../tools/precedent_push_check.py)'s
  changed-files step now reads both files as text and names a registered
  check with no case, in seconds, at pre-staging. That catches the
  mistake. It does not stop it being possible (upstream-fix, point 5).

  **The removal:** let a check's registration carry its plant -- for
  example a `plant=` argument to `@check`, or a small `plants` table next
  to the check -- and have the harness build its cases from the registry,
  so a check without a plant cannot be registered at all. Then the
  changed-files read above can go.

  **Why it waits:** it touches every planted case in the harness and the
  fixture code they share, which is a batch of its own, not a rider on
  the engine fixes it came out of.
