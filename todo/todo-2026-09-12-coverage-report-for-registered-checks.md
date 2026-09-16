---
slug:              todo-2026-09-12-coverage-report-for-registered-checks
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the design call above — which repo's registry defines the expected set — and deliberately out of scope of the change that raised it, which was the pass 2 question alone (itself pending review)."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-12
closed:            null
---
## What

- <a id="coverage-report-for-registered-checks"></a>**Have the very deep check
  print a per-repo coverage table for every registered check.** Raised
  2026-09-12 alongside pass 2's `does-it-ever-run` question in
  [very-deep-check](../practices/very-deep-check.md), which asks a session to
  record, for every registered check in every repo in force, what it actually
  did — passed, violated, skipped and why, or never registered there — and to
  read each practice's `checked_by` against that. Today that is a session
  assembling it by hand, repo by repo, which is exactly the enumerate-rather-
  than-sample failure the question next to it warns about.
  [tools/very_deep_check.py](../tools/very_deep_check.py) is the right home: its
  job per the Rule is to enumerate the scope and print the passes.

  **Why it was not built with the question.** Three things measured
  2026-09-12 put it well past a small, testable addition. **Per-check results
  are not in stdout** — this repo reports `43 passed` and prints not one
  per-check pass line, and an attached source prints only its skips, so a
  table cannot be built by parsing output and has to call each repo's registry
  directly. **Each repo runs its own vendored engine at its own commit** — an
  attached source here is pinned several commits behind this checkout — so the
  registries genuinely differ, and which one is authoritative for "was this
  check registered there at all" is a design call, not a detail. And **a
  source set's vendored engine omits [precedent_resolve.py](../tools/precedent_resolve.py)**, so importing a
  foreign copy has to survive modules that are simply absent. The honest
  version is the question, now; the better one is this item, per
  `loader-comment-names-an-unvendored-check`'s
  own reasoning about not letting a claim stay false while a design question
  is open.

  **This produces the count
  [`provenance-check-skips-in-a-source-set`](todo-2026-09-11-provenance-check-skips-in-a-source-set.md)
  is blocked on** — that item says nobody has counted which universal checks
  skip in a source set or what each would have caught, and names the count as
  the thing needed before the design call. A coverage table is that count,
  taken across every repo in force rather than one at a time.

  **Blocked on / out of scope:** the design call above — which repo's registry
  defines the expected set — and deliberately out of scope of the change that
  raised it, which was the pass 2 question alone (itself pending review).
  **Disposition:** wait ([open-item-disposition](../practices/open-item-disposition.md))

## How It Closes

Not open until: the design call above — which repo's registry defines the expected set — and deliberately out of scope of the change that raised it, which was the pass 2 question alone (itself pending review).

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
