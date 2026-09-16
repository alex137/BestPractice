---
slug:              todo-2026-09-11-provenance-check-skips-in-a-source-set
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
noted:             2026-09-11
closed:            null
---
## What

- <a id="provenance-check-skips-in-a-source-set"></a>**A universal
   practice's mechanical check could not bind a source set, so sets relied on
   checks that silently skipped there.** **Largely resolved**: the mechanism
   below shipped as `binds_publishers` (#261, 2026-09-12) and reached all four
   sets on 2026-09-13. What keeps this item open is only the last paragraph —
   the other 41 checks that still skip, which is per-check judgment rather
   than a sweep. The diagnosis is written in the present tense of 2026-09-11;
   read it as the state that motivated the fix.
   [tools/precedent_check.py](../tools/precedent_check.py) skips any check whose
   practice is not in force in the repo it runs in — correct for a consuming
   repo, where a check belonging to an unresolved source has nothing to say.
   A **source set** is the case that breaks: it vendors `precedent_check.py`
   as part of the engine, and its `practices/` holds its own practices only,
   so every universal check in the vendored file skips itself there.

   **Measured 2026-09-11**, in a real individual set:
   `python3 tools/precedent_check.py --only generated-artifact-provenance`
   reports `0 passed, 0 violated, 1 skipped`. That is the check that runs
   `build_views.py --check`, i.e. the one that would have caught the stale
   `MAP.md` that started
   `loader-comment-names-an-unvendored-check`.
   The views drift gate shipped for that one case runs `build_views.py`
   directly and does not depend on this; **every other universal check is
   still skipping in every source set**, and nobody has counted which ones
   those are or what each would have caught.

   **Shapes worth weighing, none chosen:** vendor the universal practice
   FILES a check needs into a source set (they are public, and the set
   already vendors the engine that reads them); let a check declare that it
   binds any repo running the engine rather than any repo holding its
   practice; or accept it and say so in `precedent_check.py`'s own output,
   so `1 skipped` in a source set reads as a designed gap rather than an
   accident. Today it reads as neither — the line says the practice belongs
   to a source this repo does not resolve, which is true and sounds benign.

   **The count came in, and the design call is made — 2026-09-12.** The count
   is on
   [`practice-consistency-across-team-repos`](todo-2026-09-07-practice-consistency-across-team-repos.md):
   in a team source, 12 checks passed and **42 skipped, all 42 that one
   cause**. Not one rule going unenforced in a source set — most of the
   catalogue, in the repositories that publish it.

   **Shape 2 was chosen, narrowed**: a check declares `binds_publishers=True`
   and then runs in a repo that publishes a `practices/` tree, whether or not
   that practice's own text is vendored in. Not shape 1 (vendor the practice
   FILES a source set needs), which adds a second copy of rule text to every
   set and so recreates the drift this item is about — the one re-declared
   copy that then existed never agreed with universal's, and was retired on
   2026-09-13 once the flag reached its set. Not shape 3 (accept it
   and reword the output), which makes the gap legible and leaves the
   publishing repos unchecked.

   Two properties make it safe, and both are asserted:
   **publisher-ness is declared, not detected** — `kind: source` in
   `tools/ENGINE_MANIFEST.json`, which
   [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
   already writes and reads back, because an authored `practices/` tree and a
   materialized one are identical on disk; and **the failure message is still
   the rule** — it cannot print a Rule that is not there, so it prints the
   upstream URL on the branch the manifest records, rather than
   `(no practice file for ...)`.

   Three checks carry the flag, each with its incident beside it:
   `practice-links-travel`, `catalogue-carries-stories`,
   `generated-artifact-provenance`. Measured on a real team source, one engine
   version either side of the change: **12 passed / 43 skipped → 14 passed /
   41 skipped**, and a diff of the per-check statuses confirms those two
   stopped skipping and nothing else changed state. A planted copy of the link
   that really shipped is caught, with the repair named.
   The mechanism is at
   [spec/ENFORCEMENT.md](../spec/ENFORCEMENT.md)'s "A check can bind the repo that
   PUBLISHES a practice"; the control is `verify_harness.py`'s
   `check_publisher_bound_checks_run_in_a_source_set`, which fails if the gate
   exception is removed.

   **What is left, and why it is not blocked-on:** the other 41. Widening the
   flag is per-check judgment — it removes the gate, it does not make a check
   that needs resolved sources work without them — and the enumeration belongs
   to [`coverage-report-for-registered-checks`](todo-2026-09-12-coverage-report-for-registered-checks.md),
   which is the count taken across every repo in force rather than one at a
   time. **That was outstanding and is now done (2026-09-13):** the one
   re-declared copy of `catalogue-carries-stories` in a team source was
   redundant once the flag reached it, and its `checked_by: null` misstated
   its own coverage. It was retired in that set — `status: active` to
   `deduplicated` with an `in_force_at`, in a separate commit from the engine
   refresh, as this item asked, and in the same pull request that deleted the
   single-rule workflow. **The file was kept, not deleted**, per that set's
   withdrawn-practice convention. Reported from a session rooted there; not
   verifiable from this repo, which cannot read a private cross-owner set.

   **Disposition:** wait ([open-item-disposition](../practices/open-item-disposition.md)).

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
