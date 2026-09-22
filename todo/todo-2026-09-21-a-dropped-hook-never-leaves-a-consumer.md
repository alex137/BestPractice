---
slug:              todo-2026-09-21-a-dropped-hook-never-leaves-a-consumer
kind:              manual
domain:            vendoring
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

**A hook dropped upstream stays installed in every consumer, forever.**
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) has
exactly two removal paths — `_remove_dropped_engine_files` for `tools/` and
`_remove_retired_ci_workflow_files` for `.github/workflows/`. There is no
third for `.claude/hooks/`, and the manifest's own `hook_files` /
`hooks_sha256` keys go on recording the orphan with nothing that will ever
clear them.

Found 2026-09-21 by the very deep check's new deletion-propagation table
(`very-deep-check` pass 2, item 8b) on the first run of the question it
asks — which is the same question that exposed the CI-workflow asymmetry
the day before.

## The three columns, for hooks

| | Reaches an installed repo? |
|---|---|
| **Addition** | **No** — a hook is vendored only into a repo whose `settings.json` already wires that name, and a new hook cannot be wired to a file that is not there yet. Already filed as [todo-2026-09-21-a-new-hook-cannot-reach-an-installed-consumer](todo-2026-09-21-a-new-hook-cannot-reach-an-installed-consumer.md) |
| **Change** | Yes — a wired hook is rewritten on every refresh |
| **Deletion** | **No** — no mechanism exists |

## Why it matters

This is the shape the CI-workflow path had until 2026-09-21, and that one
cost real checks: a template dropped from the shipping list without a
tombstone left the installed file in every repository, tracked by nothing,
looking exactly as intentional as a live one. A hook is worse in one
respect — it **runs**, on every session, in every repo that still carries
it, long after upstream stopped shipping it.

Nothing is known to be affected today; no hook has been dropped since the
mechanism was measured. This is the gap, not an incident.

## What would close it

Mirror `_remove_dropped_engine_files` for hooks: diff the previous
manifest's `hook_files` against what the current `HOOK_SOURCE_DIR` ships
*and* what the destination still wires, delete the difference where the
on-disk hash still matches what the manifest recorded, and keep a
hand-edited copy with a warning rather than deleting it — the same standard
the engine path already uses. It wants a planted harness case in both
directions, as the dependent-reporting case got.

**Not done here** because it changes what a refresh does to somebody else's
repository, which is a bigger step than the check that found it.
