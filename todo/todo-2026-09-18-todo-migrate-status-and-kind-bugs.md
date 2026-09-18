---
slug:              todo-2026-09-18-todo-migrate-status-and-kind-bugs
kind:              analysis
domain:            mechanism
severity:          notable
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-18
closed:            null
---
## What

- <a id="todo-migrate-status-and-kind-bugs"></a>**[tools/todo_migrate.py](../tools/todo_migrate.py) writes a `status` value `build_todo_index.py` doesn't
  recognize, and silently drops the classic format's kind signal.** A
  session working in a real four-source Precedent consumer
  (`themorgan/GetEmailsFromGmail`) ran `todo_migrate.py` for real against
  that repo's 32-item `docs/TODO.md` and reported two bugs. This item
  verifies both against this repo's own code and history, not just the
  report.

  **Bug 1 — `status: closed` is not a status `build_todo_index.py`
  recognizes.** [`build_plan()`](../tools/todo_migrate.py) (line 430) writes
  `status = 'closed' if item.checked else 'open'`, but
  [`build_todo_index.py`](../tools/build_todo_index.py)'s own vocabulary
  (lines 142, 213) only recognizes `open` and `done`/`dropped` — matching
  [spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](../spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
  line 92, which states plainly that `status` is `open` \| `done` \|
  `dropped`. An item written `status: closed` vanishes from both
  `todo/TODO.md` and `todo/CLOSED.md` — no error, a clean-looking run.

  **This is not hypothetical — it is already live in this repo.**
  [todo/todo-2026-09-17-access-probe-plant-not-detected.md](todo-2026-09-17-access-probe-plant-not-detected.md)
  is a hand-written item (nothing to do with `todo_migrate.py`) that also
  carries `status: closed`. Running `build_todo_index.py --check` and
  regenerating both output files in memory confirms that item is absent
  from both. The likely cause: `status: closed` is a *legal* value
  elsewhere in this repo — [tools/doc_lifecycle.py](../tools/doc_lifecycle.py)
  uses it correctly for `spec/*.md` briefs and records — so it's an easy,
  natural mistake to reach for on a todo item, and nothing catches it.

  **Bug 2 — `guess_kind()` never recovers the classic format's own kind
  signal, and the reported fix only covers a signal I couldn't confirm
  existed.** [`guess_kind()`](../tools/todo_migrate.py) (lines 221–230)
  falls through to phrase heuristics and defaults to `analysis` when they
  don't fire. The report claimed this repo's own
  [templates/TODO.md.template](../templates/TODO.md.template) "taught every
  consumer for years" to end each item with an explicit `(**analysis**)`-
  style parenthetical, and recommended a regex to catch it. I tested that
  regex against a fixture built from the report's own description — it
  works, correctly extracting the marked kind and falling through cleanly
  to the heuristics when no marker is present.

  But checking this repo's actual history turned up no evidence for the
  claimed convention, in either real shape this repo has used: the
  template's real classic version (`git show 28a7dedc~1`) signals kind by
  **section heading** (`## Analyses (agent-doable)`, `## Verify before
  external use`, `## Decisions (user's call)`), never a per-item marker;
  and this repo's own dogfooded pre-migration `TODO.md` (`git show
  9a08363b~1`) was a flat anchor-tagged list with neither headings nor
  markers, relying entirely on the phrase heuristics. I built a fixture
  matching the template's real section-heading shape and confirmed an item
  filed under `## Decisions (user's call)` still comes out `analysis` —
  with or without the marker-regex fix — because `parse_todo_items` never
  records which heading a bullet falls under before `guess_kind` runs. The
  marker convention may be real in `GetEmailsFromGmail`'s own drifted copy
  of the template (out of scope to check from here), but the fix as
  proposed treats an unverified signal while leaving the one this repo can
  actually document still broken.

## How It Closes

Four changes, verified but not yet applied:

1. [tools/todo_migrate.py](../tools/todo_migrate.py) line 430: `status =
   'done' if item.checked else 'open'` (a checkbox alone can't distinguish
   done from dropped — default to `done` per the report's own reasoning,
   and say so in `--help` so a real migration knows to hand-correct
   abandoned-reading items).
2. [todo/todo-2026-09-17-access-probe-plant-not-detected.md](todo-2026-09-17-access-probe-plant-not-detected.md):
   correct `status: closed` to `status: done` by hand — this instance
   predates and is independent of bug 1's tool fix, so fixing the tool
   alone won't repair it.
3. `parse_todo_items` in [tools/todo_migrate.py](../tools/todo_migrate.py):
   track the `##` heading enclosing each bullet, and have a recognized
   heading (Analyses/Verify/Decisions/Manual or Physical) set `kind`
   directly, ahead of the phrase heuristics — this is the verified classic
   convention, not the unconfirmed marker one.
4. Add the reported `KIND_MARKER_RE` check as an additional fallback,
   ordered after heading detection and before the phrase heuristics — it's
   additive and tested clean, so it costs nothing if no consumer actually
   uses it, and helps if one does.

Optional, not required to close this item: `build_todo_index.py` currently
drops an unrecognized `status` value silently rather than failing loud —
a guard there would have caught both live instances of bug 1 immediately
instead of leaving them invisible.

## Notes

2026-09-18: opened after reviewing an external bug report against the real
code, history, and a live instance already in this repo (see `## What`).
Verified both bugs and re-scoped bug 2's fix; not yet implemented — this
item is unblocked, agent-doable work, filed rather than done this turn
because it was raised as a write-up-and-recommend request, not an
implement request.
