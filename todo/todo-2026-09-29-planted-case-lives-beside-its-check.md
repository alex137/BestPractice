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

## Notes

- **2026-10-11: a GOOD sample drifts too, and colocation alone would not
  catch it.** `a243d9c0` made `practice-file-shape` require `## Why`,
  `## Story` and `## Install`. The check's planted case stayed green -- its
  clean run reads the real tree, which already had the sections -- but the
  standalone test `check_practice_file_shape_judges_one_file_at_a_time`
  built its well-formed control by hand with `## Rule` only, so the control
  read as malformed and staging went red. Moving each BAD plant beside its
  check would not have helped: the drift was in a hand-written GOOD sample.
  When this item is done, build each check's good control from a real
  catalogue file rather than by hand, so it moves when the catalogue does.
  The push-time half -- a changed check now runs its own harness tests --
  is [spec/CHANGED_CHECK_RUNS_ITS_TESTS_PLAN.md](../spec/CHANGED_CHECK_RUNS_ITS_TESTS_PLAN.md).
